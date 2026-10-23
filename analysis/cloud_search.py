#!/usr/bin/env python
"""Large model search for the magnetic part of IPP task 1 (cloud run, all CPU cores).

    HACKATHON_HOME=<hackathon folder> python -I analysis/cloud_search.py tune     [--folds 0 1 2 3 4]
    HACKATHON_HOME=<hackathon folder> python -I analysis/cloud_search.py evaluate [--folds ...]
    HACKATHON_HOME=<hackathon folder> python -I analysis/cloud_search.py latency
    HACKATHON_HOME=<hackathon folder> python -I analysis/cloud_search.py noisy --config nn_best
    python -I analysis/cloud_search_report.py        (tables, figures, results/cloud-search.{md,json})

Protocol (same as the baseline): 5 outer folds by whole discharge (ipp1_common.group_folds), masked loss, errors
from ipp1_common.score. Nesting: for every outer fold the training discharges are split once more by discharge
(80 / 20); all hyperparameters are chosen on that inner validation split and never see the outer test fold.
Then each chosen configuration is retrained on the whole outer training set and predicts the outer test fold.
Predictions go to $HACKATHON_HOME/out/cloud-search/ (outside git); the report script scores them.
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

# One thread per process: the cores are used by running one model per core, which is faster for these small networks.
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np
import optuna
import torch
from sklearn.model_selection import GroupShuffleSplit

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script folder
import ipp1_common as C
from cloud_search_lib import (LIM, CLS, fit_extratrees, fit_features, fit_gate_net, fit_lgbm, fit_lgbm_gate,
                              fit_net, n_params, objective, net_pipeline)

WORK = (C.OUT / "cloud-search").resolve()
N_FOLDS = 5
T0 = time.time()
D = {}  # per-process data, filled by init_worker


def log(*a):
    msg = f"[{time.time() - T0:7.0f}s pid {os.getpid()}] " + " ".join(str(x) for x in a)
    print(msg, flush=True)
    with open(WORK / "log.txt", "a") as f:
        f.write(msg + "\n")


def init_worker():
    torch.set_num_threads(1)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    df, X, Y, G, M = C.load()
    D.update(names=[c for c in df.columns if c.startswith(("IPR", "FL"))], X=X, Y=Y, G=G, M=M,
             folds=C.group_folds(X, Y, G, N_FOLDS))


def data(which):
    """Inputs of the clean or the noisy file; targets and rows are those of the clean file."""
    if which == "clean":
        return D["X"]
    if "Xn" not in D:
        dfn, Xn, Yn, Gn, _ = C.load(noisy=True)
        assert Xn.shape == D["X"].shape and (Gn == D["G"]).all(), "noisy file has different rows"
        assert np.allclose(np.nan_to_num(Yn), np.nan_to_num(D["Y"])), "noisy file has different targets"
        D["Xn"] = Xn
    return D["Xn"]


def inner_split(k):
    tr, _ = D["folds"][k]
    a, b = next(GroupShuffleSplit(1, test_size=0.2, random_state=k).split(tr, groups=D["G"][tr]))
    return tr[a], tr[b]


# ----- search spaces -----

def suggest(t, family):
    """Draw a configuration; returns (arch, feature kind, hyperparameter dict). Also rebuilds one from a FixedTrial."""
    if family in ("nn", "lim_nn"):
        lim = family == "lim_nn"  # specialist on the limited rows only: fewer rows, so more epochs are cheap
        arch = t.suggest_categorical("arch", ["mlp", "resmlp"])
        feat = t.suggest_categorical("feat", ["raw", "diff", "pca16", "pca24"])
        hp = dict(width=t.suggest_categorical("width", [64, 128, 192, 256] if lim else [64, 128, 192, 256, 384]),
                  depth=t.suggest_int("depth", 1, 4),
                  act=t.suggest_categorical("act", ["silu", "gelu", "relu", "tanh", "mish"]),
                  dropout=t.suggest_float("dropout", 0.0, 0.2, step=0.05),
                  lr=t.suggest_float("lr", 3e-4, 1e-2, log=True), wd=t.suggest_float("wd", 1e-6, 1e-2, log=True),
                  epochs=t.suggest_int("epochs", 40, 300 if lim else 120, step=10),
                  batch=t.suggest_categorical("batch", [128, 256, 512] if lim else [256, 512, 1024]),
                  sched=t.suggest_categorical("sched", ["onecycle", "cosine", "constant"]),
                  loss=t.suggest_categorical("loss", ["mse", "huber"]))
        if hp["loss"] == "huber":
            hp["delta"] = t.suggest_float("delta", 0.3, 3.0, log=True)
        if not lim:
            hp["w_lim"] = t.suggest_float("w_lim", 0.5, 5.0, log=True)
            hp["w_cls"] = t.suggest_float("w_cls", 0.3, 3.0, log=True)
        return arch, feat, hp
    if family == "attn":
        hp = dict(d_model=t.suggest_categorical("d_model", [16, 32]), layers=t.suggest_int("layers", 1, 2),
                  heads=t.suggest_categorical("heads", [2, 4]), act=t.suggest_categorical("act", ["silu", "gelu"]),
                  dropout=t.suggest_float("dropout", 0.0, 0.1, step=0.05),
                  lr=t.suggest_float("lr", 5e-4, 5e-3, log=True), wd=t.suggest_float("wd", 1e-6, 1e-2, log=True),
                  epochs=t.suggest_int("epochs", 20, 60, step=10),
                  batch=t.suggest_categorical("batch", [256, 512, 1024]),
                  sched=t.suggest_categorical("sched", ["onecycle", "cosine"]),
                  loss=t.suggest_categorical("loss", ["mse", "huber"]))
        if hp["loss"] == "huber":
            hp["delta"] = t.suggest_float("delta", 0.3, 3.0, log=True)
        hp["w_lim"] = t.suggest_float("w_lim", 0.5, 5.0, log=True)
        hp["w_cls"] = t.suggest_float("w_cls", 0.3, 3.0, log=True)
        return "attn", "raw", hp
    if family in ("lgbm", "lim_lgbm"):
        hp = dict(n_estimators=t.suggest_int("n_estimators", 100, 600, step=100),
                  lr=t.suggest_float("lr", 0.02, 0.3, log=True), num_leaves=t.suggest_int("num_leaves", 8, 128, log=True),
                  min_child=t.suggest_int("min_child", 5, 100, log=True), subsample=t.suggest_float("subsample", 0.5, 1.0),
                  colsample=t.suggest_float("colsample", 0.5, 1.0),
                  reg_lambda=t.suggest_float("reg_lambda", 1e-3, 10.0, log=True))
        return "lgbm", t.suggest_categorical("feat", ["raw", "diff", "pca24"]), hp
    if family == "et":
        hp = dict(n_estimators=100, min_leaf=t.suggest_categorical("min_leaf", [1, 2, 4, 8]),
                  max_features=t.suggest_categorical("max_features", [0.5, 0.8, 1.0]))
        return "et", t.suggest_categorical("feat", ["raw", "diff", "pca24"]), hp
    raise ValueError(family)


def hp_from_params(family, params):
    return suggest(optuna.trial.FixedTrial(params), family)


TRIALS = {"nn": 48, "attn": 8, "lgbm": 12, "et": 6, "lim_nn": 30, "lim_lgbm": 20}
LIM_ROWS = lambda M: M[:, LIM[0]] & M[:, LIM[1]]  # noqa: E731  the limiter point exists (limited configuration)


def lim_objective(pred2, Y2):
    return float(np.mean([np.sqrt(np.mean((pred2[:, j] - Y2[:, j]) ** 2)) / Y2[:, j].std() for j in range(2)]))


def trial_value(trial, fold, family):
    itr, iva = inner_split(fold)
    X, Y, M = D["X"], D["Y"], D["M"]
    arch, feat, hp = suggest(trial, family)
    A, b = fit_features(feat, X[itr], D["names"])
    Ftr, Fva = X[itr] @ A + b, X[iva] @ A + b
    t0 = time.time()
    if family in ("nn", "attn"):
        def prune(step, v):
            trial.report(v, step)
            if not np.isfinite(v) or trial.should_prune():
                raise optuna.TrialPruned()
        _, net, hist = fit_net(arch, hp, Ftr, Y[itr], M[itr], seed=0, val=(Fva, Y[iva], M[iva]),
                               checkpoints=(0.4, 0.7, 1.0), callback=prune)
        value = hist[-1]
        trial.set_user_attr("params_count", n_params(net))
    elif family == "lgbm":
        value = objective(C.score(fit_lgbm(Ftr, Y[itr], M[itr], hp)[0](Fva), Y[iva], M[iva]))
    elif family == "et":
        value = objective(C.score(fit_extratrees(Ftr, Y[itr], M[itr], hp)[0](Fva), Y[iva], M[iva]))
    else:  # limiter specialists: trained and judged on the limited rows only
        a, v = itr[LIM_ROWS(M[itr])], iva[LIM_ROWS(M[iva])]
        Ftr, Fva = X[a] @ A + b, X[v] @ A + b
        Y2a, Y2v = Y[a][:, LIM], Y[v][:, LIM]
        if family == "lim_nn":
            predict, _, _ = fit_net(arch, hp, Ftr, Y2a, np.ones_like(Y2a, bool), seed=0)
        else:
            predict = fit_lgbm(Ftr, Y2a, np.ones_like(Y2a, bool), hp)[0]
        value = lim_objective(predict(Fva), Y2v)
    trial.set_user_attr("seconds", time.time() - t0)
    return value


def make_study(fold, family, rank=0):
    path = WORK / "tune" / f"fold{fold}_{family}.db"
    storage = optuna.storages.RDBStorage(f"sqlite:///{path}", engine_kwargs={"connect_args": {"timeout": 120}})
    return optuna.create_study(
        study_name=f"{family}{fold}", storage=storage, load_if_exists=True, direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=100 * fold + 7 + rank, multivariate=True, constant_liar=True, n_startup_trials=15),
        pruner=optuna.pruners.PercentilePruner(80.0, n_startup_trials=15, n_warmup_steps=0))


def run_study(job):
    """Run (a share of) one nested study; several processes can work on the same study through its sqlite file."""
    fold, family, n_total, rank = job
    study = make_study(fold, family, rank)
    t0 = time.time()

    def report(st, tr):
        best = min((t.value for t in st.trials if t.state.name == "COMPLETE"), default=float("nan"))
        log(f"fold {fold} {family} trial {tr.number} {tr.state.name} value "
            f"{tr.value if tr.value is not None else float('nan'):.4f} best {best:.4f} ({tr.user_attrs.get('seconds', 0):.0f}s)")
    study.optimize(lambda t: trial_value(t, fold, family), n_trials=n_total, callbacks=[
        report, optuna.study.MaxTrialsCallback(n_total, states=(optuna.trial.TrialState.COMPLETE, optuna.trial.TrialState.PRUNED,
                                                                optuna.trial.TrialState.FAIL))],
                   catch=(ValueError, RuntimeError))
    done = [t for t in study.trials if t.state.name in ("COMPLETE", "PRUNED")]
    if len(study.trials) < n_total or any(t.state.name == "RUNNING" for t in study.trials):
        return fold, family  # another process of this study is still running; the last one to finish writes the summary
    best_by = {}
    for key in ("arch", "feat", "loss", "sched", "act", "width", "depth", "batch"):
        groups = {}
        for t in study.trials:
            if t.state.name == "COMPLETE" and key in t.params:
                groups.setdefault(str(t.params[key]), []).append(t)
        if groups:
            best_by[key] = {v: {"best": min(x.value for x in ts), "median": float(np.median([x.value for x in ts])),
                                "n": len(ts), "best_trial": min(ts, key=lambda x: x.value).number}
                            for v, ts in groups.items()}
    wall = sum(t.user_attrs.get("seconds", 0) for t in study.trials)
    out = {"fold": fold, "family": family, "n_trials": len(done), "seconds": wall,
           "best_value": study.best_value, "best_trial": study.best_trial.number, "best_params": study.best_params,
           "trial_params": {str(t.number): t.params for t in study.trials if t.state.name == "COMPLETE"},
           "trial_values": {str(t.number): t.value for t in study.trials if t.state.name == "COMPLETE"},
           "choices": best_by}
    json.dump(out, open(WORK / "tune" / f"fold{fold}_{family}.json", "w"), indent=1)
    log(f"fold {fold} {family} DONE {len(done)} trials ({wall:.0f} CPU-s), best inner objective {study.best_value:.4f}")
    return fold, family


PARALLEL = {"nn": 2, "attn": 2}  # processes per study; the others are short


def cmd_tune(args):
    (WORK / "tune").mkdir(parents=True, exist_ok=True)
    trials = {**TRIALS, **{k: int(v) for k, v in (x.split("=") for x in args.trials)}}
    cost = {"attn": 6, "nn": 5, "lim_nn": 3, "lgbm": 3, "et": 2, "lim_lgbm": 1}  # longest first
    jobs = [(f, fam, trials[fam], r) for fam in args.families for f in args.folds for r in range(PARALLEL.get(fam, 1))
            if not (WORK / "tune" / f"fold{f}_{fam}.json").exists()]
    for f, fam, _, _ in jobs:
        make_study(f, fam)  # create the studies before the workers race for them
    jobs.sort(key=lambda j: (-cost[j[1]], j[3]))
    log(f"tune: {len(jobs)} studies on {args.workers} workers", jobs)
    with mp.get_context("spawn").Pool(args.workers, init_worker) as pool:
        for fold, fam in pool.imap_unordered(run_study, jobs):
            pass


# ----- evaluation: retrain the chosen configurations on the whole outer training set -----

def load_tune(fold, family):
    p = WORK / "tune" / f"fold{fold}_{family}.json"
    return json.load(open(p)) if p.exists() else None


def candidates(fold):
    """Neural configurations to evaluate for one fold, all chosen on inner validation: the best overall, the best
    per architecture and the best per feature kind (so the report can show what each choice is worth)."""
    tj = load_tune(fold, "nn")
    out = {"nn_best": tj["best_params"]}
    for key, tag in (("arch", "arch"), ("feat", "feat")):
        for v, info in tj["choices"][key].items():
            out[f"nn_{tag}-{v}"] = tj["trial_params"][str(info["best_trial"])]
    seen, uniq = {}, {}
    for name, p in out.items():  # drop duplicates but remember every name that points at the same configuration
        k = json.dumps(p, sort_keys=True)
        seen.setdefault(k, []).append(name)
    for names in seen.values():
        uniq[names[0]] = (out[names[0]], names)
    return uniq


def eval_specs(fold, n_seeds, families):
    specs = [dict(fold=fold, name="ridge", kind="ridge", seed=0)]
    specs += [dict(fold=fold, name=f"baseline_s{s}", kind="baseline", seed=s) for s in range(5)]
    if "nn" in families and load_tune(fold, "nn"):
        for name, (params, aliases) in candidates(fold).items():
            seeds = range(n_seeds) if name == "nn_best" else range(1)
            specs += [dict(fold=fold, name=f"{name}_s{s}", kind="nn", seed=s, family="nn", params=params,
                           aliases=aliases) for s in seeds]
    if "attn" in families and load_tune(fold, "attn"):
        specs += [dict(fold=fold, name=f"attn_s{s}", kind="nn", seed=s, family="attn",
                       params=load_tune(fold, "attn")["best_params"]) for s in range(5)]
    for fam in ("lgbm", "et"):
        if fam in families and load_tune(fold, fam):
            specs.append(dict(fold=fold, name=fam, kind=fam, seed=0, family=fam, params=load_tune(fold, fam)["best_params"]))
    if "lim_nn" in families and load_tune(fold, "lim_nn"):
        specs += [dict(fold=fold, name=f"lim_nn_s{s}", kind="lim_nn", seed=s, family="lim_nn",
                       params=load_tune(fold, "lim_nn")["best_params"]) for s in range(5)]
    if "lim_lgbm" in families and load_tune(fold, "lim_lgbm"):
        specs.append(dict(fold=fold, name="lim_lgbm", kind="lim_lgbm", seed=0, family="lim_lgbm",
                          params=load_tune(fold, "lim_lgbm")["best_params"]))
    if "gate" in families:
        specs += [dict(fold=fold, name="gate_nn", kind="gate_nn", seed=0), dict(fold=fold, name="gate_lgbm", kind="gate_lgbm", seed=0)]
    return specs


GATE_HP = dict(width=128, depth=3, act="silu", dropout=0.0, lr=3e-3, wd=1e-4, epochs=40, batch=512, sched="onecycle")
GATE_LGBM = dict(n_estimators=300, lr=0.05, num_leaves=31, min_child=20, subsample=0.8, colsample=0.8, reg_lambda=1.0)


def eval_task(spec):
    """Train one model on the outer training rows and save its predictions for the outer test rows."""
    fold, name, kind = spec["fold"], spec["name"], spec["kind"]
    train, test = spec.get("train", "clean"), spec.get("test", "clean")
    tag = "" if (train, test) == ("clean", "clean") else f"__tr-{train}_te-{test}"
    out = WORK / "pred" / f"fold{fold}" / f"{name}{tag}.npy"
    if out.exists():
        return name
    out.parent.mkdir(parents=True, exist_ok=True)
    tr, te = D["folds"][fold]
    Xtr, Xte = data(train)[tr], data(test)[te]
    Y, M = D["Y"], D["M"]
    t0 = time.time()
    save = None
    if kind == "ridge":
        pred = C.fit_ridge(Xtr, Y[tr], M[tr])(Xte)
    elif kind == "baseline":
        pred = C.fit_mlp(Xtr, Y[tr], M[tr], 60, seed=fold + 5 * spec["seed"])[0](Xte)  # seed 0 is the seed of ipp1_baseline.py
    elif kind in ("nn", "lim_nn", "lgbm", "et", "lim_lgbm"):
        arch, feat, hp = hp_from_params(spec["family"], spec["params"])
        if kind in ("lim_nn", "lim_lgbm"):
            rows = LIM_ROWS(M[tr])
            Xfit, Yfit = Xtr[rows], Y[tr][rows][:, LIM]
        else:
            Xfit, Yfit = Xtr, Y[tr]
        Mfit = np.ones_like(Yfit, bool) if kind in ("lim_nn", "lim_lgbm") else M[tr]
        A, b = fit_features(feat, Xfit, D["names"])
        Ffit, Fte = Xfit @ A + b, Xte @ A + b
        if kind in ("nn", "lim_nn"):
            predict, net, _ = fit_net(arch, hp, Ffit, Yfit, Mfit, seed=spec["seed"])
            save = {"arch": arch, "hp": hp, "A": A, "b": b, "ym": predict.ym, "ys": predict.ys, "state": net.state_dict(),
                    "n_in": Ffit.shape[1], "n_out": Yfit.shape[1]}
        elif kind in ("lgbm", "lim_lgbm"):
            predict, models = fit_lgbm(Ffit, Yfit, Mfit, hp)
            save = {"A": A, "b": b, "models": models, "kind": "lgbm"}
        else:
            predict, models = fit_extratrees(Ffit, Yfit, Mfit, hp)
            save = {"A": A, "b": b, "models": models, "kind": "et"}
        pred = predict(Fte)
    elif kind in ("gate_nn", "gate_lgbm"):
        y = M[tr][:, CLS] * (Y[tr][:, CLS] > 0.5)
        A, b = fit_features("raw", Xtr, D["names"])
        if kind == "gate_nn":
            pred = fit_gate_net(GATE_HP, Xtr @ A + b, y, spec["seed"])[0](Xte @ A + b)
        else:
            pred = fit_lgbm_gate(Xtr @ A + b, y, GATE_LGBM)[0](Xte @ A + b)
    else:
        raise ValueError(kind)
    np.save(out, np.asarray(pred, dtype=np.float32))
    if save is not None and fold == 0 and tag == "" and spec["seed"] == 0:
        (WORK / "models").mkdir(exist_ok=True)
        torch.save(save, WORK / "models" / f"{name}.pt")
    with open(WORK / "timing.jsonl", "a") as f:
        f.write(json.dumps({"fold": fold, "name": name + tag, "seconds": round(time.time() - t0, 1)}) + "\n")
    log(f"fold {fold} {name}{tag} trained in {time.time() - t0:.0f}s")
    return name


def cmd_evaluate(args):
    specs = [s for f in args.folds for s in eval_specs(f, args.ens, args.families)]
    cost = {"attn": 6, "nn": 4, "lim_nn": 3, "et": 5, "lgbm": 3, "baseline": 2}
    specs.sort(key=lambda s: -cost.get(s.get("family", s["kind"]), 1))
    p = WORK / "aliases.json"
    aliases = json.load(open(p)) if p.exists() else {}
    aliases.update({f"{s['fold']}/{s['name']}": s["aliases"] for s in specs if "aliases" in s})
    json.dump(aliases, open(p, "w"), indent=1)
    log(f"evaluate: {len(specs)} models on {args.workers} workers")
    with mp.get_context("spawn").Pool(args.workers, init_worker) as pool:
        for _ in pool.imap_unordered(eval_task, specs):
            pass


def cmd_noisy(args):
    """Train clean -> test noisy and train noisy -> test noisy / clean for the recommended configuration."""
    specs = []
    for f in args.folds:
        params = candidates(f)[args.config][0] if args.config != "baseline" else None
        for train, test in (("clean", "noisy"), ("noisy", "noisy"), ("noisy", "clean")):
            for s in range(args.ens):
                base = dict(fold=f, train=train, test=test, seed=s)
                if args.config == "baseline":
                    specs.append(dict(base, name=f"baseline_s{s}", kind="baseline"))
                else:
                    specs.append(dict(base, name=f"{args.config}_s{s}", kind="nn", family="nn", params=params))
    log(f"noisy: {len(specs)} models for {args.config}")
    with mp.get_context("spawn").Pool(args.workers, init_worker) as pool:
        for _ in pool.imap_unordered(eval_task, specs):
            pass


def cmd_latency(args):
    """One sample, one thread, whole pipeline (features, forward pass, scaling); machine otherwise idle."""
    from cloud_search_lib import build_net, latency_ms
    torch.set_num_threads(1)
    _, X, _, _, _ = C.load()
    x1 = X[100].copy()
    res = {}
    for p in sorted((WORK / "models").glob("*.pt")):
        s = torch.load(p, weights_only=False)
        if "state" in s:
            net = build_net(s["arch"], s["hp"], s["n_in"], s["n_out"])
            net.load_state_dict(s["state"])
            net.eval()
            fn, count = net_pipeline(s["A"], s["b"], net, s["ym"], s["ys"]), n_params(net)
        else:
            A, b, models = s["A"], s["b"], s["models"]
            fn = lambda x, A=A, b=b, models=models: [m.predict((x @ A + b)[None]) for m in models]  # noqa: E731
            count = (sum(t["num_leaves"] for m in models for t in m.booster_.dump_model()["tree_info"])
                     if s["kind"] == "lgbm" else sum(e.tree_.node_count for m in models for e in m.estimators_))
        res[p.stem] = {**latency_ms(fn, x1, n=200 if s.get("kind") == "et" else 3000), "parameters": int(count)}
        log(f"latency {p.stem}: {res[p.stem]}")
    W, bias = np.random.default_rng(0).normal(size=(24, 16)).astype(np.float32), np.zeros(16, np.float32)
    res["ridge_linear"] = {**latency_ms(lambda x: x @ W + bias, x1), "parameters": W.size + bias.size}  # a ridge fit is one affine map
    base = C.Net(24, 16).eval()
    x = torch.from_numpy(((X[100] - X.mean(0)) / X.std(0)).astype(np.float32))[None]
    with torch.no_grad():
        res["baseline_untrained_net"] = {**latency_ms(lambda _: base(x), None), "parameters": n_params(base)}
    json.dump({"threads": 1, "cpu": "see results/cloud-search.md", "latency_ms": res},
              open(WORK / "latency.json", "w"), indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("tune", "evaluate", "latency", "noisy"):
        p = sub.add_parser(name)
        p.add_argument("--workers", type=int, default=os.cpu_count())
        p.add_argument("--folds", type=int, nargs="+", default=list(range(N_FOLDS)))
    sub.choices["tune"].add_argument("--families", nargs="+", default=list(TRIALS))
    sub.choices["tune"].add_argument("--trials", nargs="*", default=[], help="family=count overrides")
    sub.choices["evaluate"].add_argument("--families", nargs="+", default=["nn", "attn", "lgbm", "et", "lim_nn", "lim_lgbm", "gate"])
    sub.choices["evaluate"].add_argument("--ens", type=int, default=10)
    sub.choices["noisy"].add_argument("--config", default="nn_best")
    sub.choices["noisy"].add_argument("--ens", type=int, default=5)
    args = ap.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    init_worker()  # the parent needs the data for the latency stage
    {"tune": cmd_tune, "evaluate": cmd_evaluate, "noisy": cmd_noisy, "latency": cmd_latency}[args.cmd](args)
