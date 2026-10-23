"""Models, features and metrics for the cloud model search (IPP task 1, magnetic part).

Used by cloud_search.py. Same protocol as ipp1_common.py: masked loss, targets standardised on the training
rows, errors from ipp1_common.score. Everything here is fitted on the rows it is given, never on test rows.
"""
import time

import lightgbm as lgb
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as Fn
from sklearn.decomposition import PCA
from sklearn.ensemble import ExtraTreesRegressor

from ipp1_common import TARGETS, score

IDX = {t: i for i, t in enumerate(TARGETS)}
LIM = [IDX["R_limiter"], IDX["Z_limiter"]]
CLS = IDX["is_limited"]
SUMMARY = [t for t in TARGETS if t not in ("R_limiter", "Z_limiter", "is_limited")]


def summary(res):
    """Mean relative error (RMSE / spread) over the 13 targets without the limiter point; as in ipp1_inputs.py."""
    return float(np.mean([res[t]["nrmse"] for t in SUMMARY]))


def objective(res):
    """What the hyperparameter search minimises on the inner validation discharges: the summary error plus a
    term for the limiter point, which would otherwise be invisible next to 13 easy targets."""
    return summary(res) + 0.2 * float(np.mean([res["R_limiter"]["nrmse"], res["Z_limiter"]["nrmse"]]))


# ----- input features: every variant is one affine map x -> x @ A + b, so it folds into the first layer -----

def fit_features(kind, xtr, names):
    """Return (A, b) of an affine map fitted on xtr. kind: raw | diff | pcaK.

    raw: standardised inputs. diff: standardised inputs plus differences of neighbouring coils inside the IPR group
    and inside the FL group (each difference rescaled to unit variance). pcaK: the first K whitened principal
    components of the standardised inputs.
    """
    n = xtr.shape[1]
    mu, sd = xtr.mean(0), xtr.std(0) + 1e-9
    A = np.diag(1.0 / sd).astype(np.float64)
    b = -mu / sd
    if kind == "raw":
        pass
    elif kind == "diff":
        cols = []
        for prefix in ("IPR", "FL"):
            idx = [i for i, c in enumerate(names) if c.startswith(prefix)]
            cols += [(idx[i], idx[i + 1]) for i in range(len(idx) - 1)]
        D = np.zeros((n, len(cols)))
        for k, (i, j) in enumerate(cols):
            D[j, k], D[i, k] = 1.0, -1.0
        Dz = (xtr - mu) / sd @ D
        D = D / (Dz.std(0) + 1e-9)
        A = np.hstack([A, A @ D])
        b = np.concatenate([b, b @ D])
    elif kind.startswith("pca"):
        k = int(kind[3:])
        pca = PCA(n_components=k, whiten=True, svd_solver="full").fit((xtr - mu) / sd)
        W = pca.components_.T / np.sqrt(pca.explained_variance_)
        A = A @ W
        b = (b - pca.mean_) @ W
    else:
        raise ValueError(kind)
    return A.astype(np.float32), b.astype(np.float32)


# ----- networks -----

ACT = {"silu": nn.SiLU, "gelu": nn.GELU, "relu": nn.ReLU, "tanh": nn.Tanh, "mish": nn.Mish}


class MLP(nn.Module):
    def __init__(self, n_in, n_out, width, depth, act, dropout):
        super().__init__()
        layers, d = [], n_in
        for _ in range(depth):
            layers += [nn.Linear(d, width), ACT[act]()] + ([nn.Dropout(dropout)] if dropout else [])
            d = width
        self.f = nn.Sequential(*layers, nn.Linear(d, n_out))

    def forward(self, x):
        return self.f(x)


class ResMLP(nn.Module):
    """Linear stem, residual blocks x + W2 act(W1 x) (second linear starts at zero), linear head."""

    def __init__(self, n_in, n_out, width, depth, act, dropout):
        super().__init__()
        self.stem = nn.Linear(n_in, width)
        self.blocks = nn.ModuleList()
        for _ in range(depth):
            b = nn.Sequential(nn.Linear(width, width), ACT[act](), nn.Dropout(dropout), nn.Linear(width, width))
            nn.init.zeros_(b[3].weight)
            nn.init.zeros_(b[3].bias)
            self.blocks.append(b)
        self.act = ACT[act]()
        self.head = nn.Linear(width, n_out)

    def forward(self, x):
        h = self.stem(x)
        for b in self.blocks:
            h = h + b(h)
        return self.head(self.act(h))


class AttnNet(nn.Module):
    """Every input value is one token (value times a learned vector plus a learned coil embedding), transformer
    encoder layers over the tokens, flattened into a small head."""

    def __init__(self, n_in, n_out, d_model, layers, heads, act, dropout, head_width=128):
        super().__init__()
        self.w = nn.Parameter(torch.randn(n_in, d_model) * 0.5)
        self.e = nn.Parameter(torch.randn(n_in, d_model) * 0.1)
        layer = nn.TransformerEncoderLayer(d_model, heads, 2 * d_model, dropout, activation="gelu",
                                           batch_first=True, norm_first=True)
        self.enc = nn.TransformerEncoder(layer, layers, enable_nested_tensor=False)
        self.head = nn.Sequential(nn.Flatten(), nn.Linear(n_in * d_model, head_width), ACT[act](),
                                  nn.Linear(head_width, n_out))

    def forward(self, x):
        return self.head(self.enc(x.unsqueeze(-1) * self.w + self.e))


def build_net(arch, hp, n_in, n_out):
    if arch == "mlp":
        return MLP(n_in, n_out, hp["width"], hp["depth"], hp["act"], hp["dropout"])
    if arch == "resmlp":
        return ResMLP(n_in, n_out, hp["width"], hp["depth"], hp["act"], hp["dropout"])
    if arch == "attn":
        return AttnNet(n_in, n_out, hp["d_model"], hp["layers"], hp["heads"], hp["act"], hp["dropout"])
    raise ValueError(arch)


def n_params(net):
    return int(sum(p.numel() for p in net.parameters()))


def target_weights(hp, n_out):
    """Loss weights per target: the limiter pair and is_limited get their own multipliers (only for the 16 targets)."""
    w = np.ones(n_out, dtype=np.float32)
    if n_out == len(TARGETS):
        w[LIM] = hp.get("w_lim", 1.0)
        w[CLS] = hp.get("w_cls", 1.0)
    return w


def fit_net(arch, hp, F, Y, M, seed, val=None, checkpoints=(), callback=None):
    """Train one network on features F with a loss masked to the targets that exist.

    hp: width, depth, act, dropout, lr, wd, epochs, batch, sched (onecycle|cosine|constant), loss (mse|huber|bce),
    delta (Huber), w_lim, w_cls. At each fraction of training in `checkpoints` the objective on val=(F, Y, M) is
    appended to the returned history and passed to callback(index, value), which may raise to stop (pruning).
    Returns (predict, net, history); predict maps features to raw targets and carries the target mean and spread
    as predict.ym and predict.ys.
    """
    torch.manual_seed(seed)
    bce = hp["loss"] == "bce"  # a single 0/1 target, raw logit output
    ym = np.zeros(Y.shape[1]) if bce else np.nanmean(Y, 0)
    ys = np.ones(Y.shape[1]) if bce else np.nanstd(Y, 0) + 1e-9
    ft = torch.from_numpy(F.astype(np.float32))
    yt = torch.from_numpy(np.nan_to_num((Y - ym) / ys).astype(np.float32))
    wm = torch.from_numpy(M.astype(np.float32)) * torch.from_numpy(target_weights(hp, Y.shape[1]))
    net = build_net(arch, hp, F.shape[1], Y.shape[1])
    opt = torch.optim.AdamW(net.parameters(), lr=hp["lr"], weight_decay=hp["wd"])
    bs, ep = hp["batch"], hp["epochs"]
    per_epoch = (len(ft) + bs - 1) // bs
    total = ep * per_epoch
    if hp["sched"] == "onecycle":
        sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=hp["lr"], total_steps=total)
    elif hp["sched"] == "cosine":
        warm = max(1, int(0.03 * total))
        sched = torch.optim.lr_scheduler.LambdaLR(
            opt, lambda s: min(1.0, (s + 1) / warm) * (0.01 + 0.99 * 0.5 * (1 + np.cos(np.pi * min(1.0, s / total)))))
    else:
        sched = None

    def predict(Fx):
        net.eval()
        with torch.no_grad():
            out = net(torch.from_numpy(Fx.astype(np.float32))).numpy() * ys + ym
        net.train()
        return out

    marks = {int(round(f * ep)): f for f in checkpoints}
    history = []
    net.train()
    for e in range(1, ep + 1):
        perm = torch.randperm(len(ft))
        for i in range(0, len(ft), bs):
            b = perm[i:i + bs]
            out = net(ft[b])
            if bce:
                l = Fn.binary_cross_entropy_with_logits(out, yt[b], reduction="none")
            elif hp["loss"] == "huber":
                l = Fn.huber_loss(out, yt[b], reduction="none", delta=hp["delta"])
            else:
                l = (out - yt[b]) ** 2
            loss = (l * wm[b]).sum() / wm[b].sum().clamp_min(1.0)
            opt.zero_grad()
            loss.backward()
            opt.step()
            if sched is not None:
                sched.step()
        if val is not None and e in marks:
            history.append(objective(score(predict(val[0]), val[1], val[2])))
            if callback is not None:
                callback(len(history) - 1, history[-1])
    net.eval()
    predict.ym, predict.ys = ym, ys
    return predict, net, history


def fit_gate_net(hp, F, y, seed):
    """Binary classifier for is_limited (BCE); returns probability(F)."""
    hp = dict(hp, loss="bce")
    predict, net, _ = fit_net("mlp", hp, F, y[:, None].astype(np.float32), np.ones((len(y), 1), bool), seed)
    return (lambda Fx: 1.0 / (1.0 + np.exp(-predict(Fx)[:, 0]))), net


# ----- tree models: one model per target -----

def _std(Y):
    ym, ys = np.nanmean(Y, 0), np.nanstd(Y, 0) + 1e-9
    return ym, ys


def fit_lgbm(F, Y, M, hp, n_jobs=1, seed=0):
    ym, ys = _std(Y)
    models = []
    for j in range(Y.shape[1]):
        k = M[:, j]
        m = lgb.LGBMRegressor(n_estimators=hp["n_estimators"], learning_rate=hp["lr"], num_leaves=hp["num_leaves"],
                              min_child_samples=hp["min_child"], subsample=hp["subsample"], subsample_freq=1,
                              colsample_bytree=hp["colsample"], reg_lambda=hp["reg_lambda"], n_jobs=n_jobs,
                              random_state=seed, verbose=-1)
        models.append(m.fit(F[k], (Y[k, j] - ym[j]) / ys[j]))
    return lambda Fx: np.column_stack([m.predict(Fx) for m in models]) * ys + ym, models


def fit_lgbm_gate(F, y, hp, n_jobs=1, seed=0):
    m = lgb.LGBMClassifier(n_estimators=hp["n_estimators"], learning_rate=hp["lr"], num_leaves=hp["num_leaves"],
                           min_child_samples=hp["min_child"], subsample=hp["subsample"], subsample_freq=1,
                           colsample_bytree=hp["colsample"], reg_lambda=hp["reg_lambda"], n_jobs=n_jobs,
                           random_state=seed, verbose=-1).fit(F, y)
    return lambda Fx: m.predict_proba(Fx)[:, 1], m


def fit_extratrees(F, Y, M, hp, n_jobs=1, seed=0):
    ym, ys = _std(Y)
    models = []
    for j in range(Y.shape[1]):
        k = M[:, j]
        m = ExtraTreesRegressor(n_estimators=hp["n_estimators"], min_samples_leaf=hp["min_leaf"],
                                max_features=hp["max_features"], n_jobs=n_jobs, random_state=seed)
        models.append(m.fit(F[k], (Y[k, j] - ym[j]) / ys[j]))
    return lambda Fx: np.column_stack([m.predict(Fx) for m in models]) * ys + ym, models


# ----- latency: the whole pipeline from 24 raw numbers to the outputs, one sample, one thread -----

def latency_ms(fn, x1, n=3000, warm=300):
    for _ in range(warm):
        fn(x1)
    ts = np.empty(n)
    for i in range(n):
        a = time.perf_counter()
        fn(x1)
        ts[i] = (time.perf_counter() - a) * 1000
    return {"median": float(np.median(ts)), "p99": float(np.percentile(ts, 99))}


def net_pipeline(A, b, net, ym, ys):
    """Single-sample predictor of a trained network: affine features, forward pass, un-standardise."""
    def run(x):
        with torch.no_grad():
            return net(torch.from_numpy(x @ A + b)[None]).numpy()[0] * ys + ym
    return run
