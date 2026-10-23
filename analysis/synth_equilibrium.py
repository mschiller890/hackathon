"""Synthetic tokamak equilibria with a KNOWN plasma, for a closed test of the probe-signal -> shape mapping.

SIMULATED, NOT COMPASS DATA. Nothing here reads or copies any IPP file; the vessel contour, probe
positions and parameter ranges are invented and only COMPASS-sized (R0 about 0.56 m, a about 0.2 m).

Model: Solov'ev solutions of the Grad-Shafranov equation (constant p' and F F'), built as in
Cerfon and Freidberg, Phys. Plasmas 17, 032502 (2010). In units of the plasma major radius R0p,
x = R / R0p, y = (Z - Zs) / R0p,

    psi = x^4/8 + A (x^2 ln x / 2 - x^4/8) + sum_i c_i phi_i(x, y),     Delta* psi = (1 - A) x^2 + A,

where phi_i are homogeneous solutions. The c_i are fixed by requiring the boundary psi = 0 to pass through
the outer, inner and top points of a requested (a, kappa, delta) shape, with the matching curvatures.
Two configurations: "limited" (up-down symmetric, 7 coefficients) and "diverted" (lower X point,
12 coefficients). The truth (axis, X point, boundary extremes) is then measured on the finished solution
with Newton iterations on analytic derivatives, not copied from the requested parameters.

Probe signals (16 tangential field probes, 8 flux loops on an invented vessel contour) are evaluated
exactly from the same analytic psi at the probe positions. Because a Solov'ev solution is analytic
everywhere, it carries current outside the separatrix too; see results/synthetic-validation.md.

Usage: python -I analysis/synth_equilibrium.py   (self-checks and a timing line)
"""
import numpy as np

MU0 = 4e-7 * np.pi
VESSEL_CENTER = (0.56, 0.0)
VESSEL_HALF = (0.30, 0.55)   # invented generic contour: a rounded box (superellipse), not the COMPASS vessel
VESSEL_POWER = 3.0
N_COILS, N_LOOPS = 16, 8
SIGNAL_NAMES = [f"IPR{i + 1:02d}" for i in range(N_COILS)] + [f"FL{i + 1:02d}" for i in range(N_LOOPS)]
TARGET_NAMES = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity",
                "R_x_point", "Z_x_point", "is_limited"]


# ---------- symbolic-free calculus on terms c * x^a * y^b * (ln x)^k ----------
class Terms:
    """A sum of terms c x^a y^b (ln x)^k with integer a, b, k; exact derivatives and vectorised evaluation."""

    def __init__(self, terms):
        t = np.array([tt for tt in terms if tt[0] != 0], dtype=float).reshape(-1, 4)
        self.c, self.a, self.b, self.k = t[:, 0], t[:, 1].astype(int), t[:, 2].astype(int), t[:, 3].astype(int)

    def _terms(self):
        return list(zip(self.c, self.a, self.b, self.k))

    def dx(self):
        out = []
        for c, a, b, k in self._terms():
            if a:
                out.append((c * a, a - 1, b, k))
            if k:
                out.append((c * k, a - 1, b, k - 1))
        return Terms(out)

    def dy(self):
        return Terms([(c * b, a, b - 1, k) for c, a, b, k in self._terms() if b])

    def __call__(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        if not len(self.c):
            return np.zeros(x.shape)
        # tables of the few distinct powers, then gathers: several times faster than a pow per term
        lx = np.log(x)
        xp = {a: x ** a for a in set(self.a)}
        yp = {b: y ** b for b in set(self.b)}
        lp = {k: lx ** k for k in set(self.k)}
        out = np.zeros(x.shape)
        for c, a, b, k in zip(self.c, self.a, self.b, self.k):
            out += c * xp[a] * yp[b] * lp[k]
        return out


def _derivs(t):
    tx, ty = t.dx(), t.dy()
    return {"f": t, "x": tx, "y": ty, "xx": tx.dx(), "xy": tx.dy(), "yy": ty.dy()}


# Homogeneous solutions of Delta* psi = 0 (Cerfon and Freidberg 2010): (coef, power of x, power of y, power of ln x).
_BASIS = [
    [(1, 0, 0, 0)],
    [(1, 2, 0, 0)],
    [(1, 0, 2, 0), (-1, 2, 0, 1)],
    [(1, 4, 0, 0), (-4, 2, 2, 0)],
    [(2, 0, 4, 0), (-9, 2, 2, 0), (3, 4, 0, 1), (-12, 2, 2, 1)],
    [(1, 6, 0, 0), (-12, 4, 2, 0), (8, 2, 4, 0)],
    [(8, 0, 6, 0), (-140, 2, 4, 0), (-120, 2, 4, 1), (75, 4, 2, 0), (180, 4, 2, 1), (-15, 6, 0, 1)],
    # up-down antisymmetric ones, needed for the lower X point
    [(1, 0, 1, 0)],
    [(1, 2, 1, 0)],
    [(1, 0, 3, 0), (-3, 2, 1, 1)],
    [(3, 4, 1, 0), (-4, 2, 3, 0)],
    [(8, 0, 5, 0), (-45, 4, 1, 0), (-80, 2, 3, 1), (60, 4, 1, 1)],
]
_BASIS_D = [_derivs(Terms(b)) for b in _BASIS]


def _newton(fun, x0, tol=1e-12, maxit=40):
    """Newton for fun(p) -> (residual (2,), jacobian (2, 2)); raises if it does not converge."""
    p = np.array(x0, float)
    for _ in range(maxit):
        r, j = fun(p)
        step = np.linalg.solve(j, r)
        if np.abs(step).max() > 0.2:                      # keep a wild first step from leaving the domain
            step *= 0.2 / np.abs(step).max()
        p = p - step
        if np.abs(step).max() < tol:
            return p
    raise RuntimeError("Newton did not converge")


class Equilibrium:
    """One Solov'ev equilibrium in physical units. Lengths in m, psi in Wb/rad, B in T, Ip in A.

    config: "limited" or "diverted". Shape inputs (a, kappa, delta) are requests; the attributes
    R_axis, Z_axis, kappa_true, delta_true, X point etc. are measured on the solution.
    """

    def __init__(self, R0p, a, kappa, delta, A, Ip, Zs=0.0, config="limited"):
        self.R0p, self.Zs, self.A, self.config, self.Ip = R0p, Zs, A, config, Ip
        eps, alpha = a / R0p, np.arcsin(delta)
        self._solve_coefficients(eps, kappa, delta, alpha)
        self._measure(eps, kappa, delta)
        self._scale_current()

    # --- construction ---
    def _solve_coefficients(self, eps, kappa, delta, alpha):
        A = self.A
        particular = Terms([((1 - A) / 8, 4, 0, 0), (A / 2, 2, 0, 1)])
        pd = _derivs(particular)
        n1 = -(1 + alpha) ** 2 / (eps * kappa ** 2)
        n2 = (1 - alpha) ** 2 / (eps * kappa ** 2)
        n3 = -kappa / (eps * np.cos(alpha) ** 2)
        outer, inner = (1 + eps, 0.0), (1 - eps, 0.0)
        top = (1 - delta * eps, kappa * eps)
        # each condition is a list of (derivative name, weight) at a point: sum weight * d(psi) = 0
        conds = [([("f", 1)], outer), ([("f", 1)], inner), ([("f", 1)], top), ([("x", 1)], top),
                 ([("yy", 1), ("x", n1)], outer), ([("yy", 1), ("x", n2)], inner), ([("xx", 1), ("y", n3)], top)]
        if self.config == "diverted":
            xpt = (1 - 1.1 * delta * eps, -1.1 * kappa * eps)
            self._x_guess = xpt
            conds = [c for c in conds if c[0] != [("yy", 1), ("x", n1)] and c[0] != [("yy", 1), ("x", n2)]]
            conds += [([("y", 1)], outer), ([("y", 1)], inner), ([("f", 1)], xpt), ([("x", 1)], xpt),
                      ([("y", 1)], xpt), ([("yy", 1), ("x", n1)], outer), ([("yy", 1), ("x", n2)], inner)]
            n = 12
        else:
            n = 7
        M = np.array([[sum(w * _BASIS_D[i][d](*pt) for d, w in ds) for i in range(n)] for ds, pt in conds])
        rhs = -np.array([sum(w * pd[d](*pt) for d, w in ds) for ds, pt in conds])
        if M.shape[0] != n:
            raise RuntimeError(f"{M.shape[0]} conditions for {n} coefficients")
        self.coef = np.linalg.solve(M, rhs)
        total = [(self.coef[i] * c, a, b, k) for i in range(n) for c, a, b, k in _BASIS[i]]
        total += [(c, a, b, k) for c, a, b, k in zip(particular.c, particular.a, particular.b, particular.k)]
        self.d = _derivs(Terms(total))
        self._guess = dict(outer=outer, inner=inner, top=top)

    def _critical(self, p0):
        d = self.d

        def fun(p):
            x, y = p
            return (np.array([d["x"](x, y), d["y"](x, y)]),
                    np.array([[d["xx"](x, y), d["xy"](x, y)], [d["xy"](x, y), d["yy"](x, y)]]))
        return _newton(fun, p0)

    def _on_boundary(self, p0, derivative):
        """Point with psi = 0 and the given first derivative ('x' or 'y') = 0: an extreme of the boundary."""
        d = self.d
        other = "y" if derivative == "x" else "x"   # row 2 of the Jacobian is d(derivative)/d(x, y)
        j2 = {"x": ("xx", "xy"), "y": ("xy", "yy")}[derivative]

        def fun(p):
            x, y = p
            return (np.array([d["f"](x, y), d[derivative](x, y)]),
                    np.array([[d["x"](x, y), d["y"](x, y)], [d[j2[0]](x, y), d[j2[1]](x, y)]]))
        return _newton(fun, p0)

    def _measure(self, eps, kappa, delta):
        g = self._guess
        # magnetic axis: the minimum of psi inside; the coarse scan picks the basin for Newton
        xs, ys = np.meshgrid(np.linspace(1 - eps, 1 + eps, 25), np.linspace(-kappa * eps, kappa * eps, 41))
        v = self.d["f"](xs, ys)
        i = np.unravel_index(np.argmin(v), v.shape)
        self.axis = self._critical((xs[i], ys[i]))
        if self.d["f"](*self.axis) >= 0:
            raise RuntimeError("axis flux is not inside the boundary")
        out = self._on_boundary(g["outer"], "y")
        inn = self._on_boundary(g["inner"], "y")
        top = self._on_boundary(g["top"], "x")
        if self.config == "diverted":
            bot = self._critical(self._x_guess)
            if np.linalg.det(np.array([[self.d["xx"](*bot), self.d["xy"](*bot)],
                                       [self.d["xy"](*bot), self.d["yy"](*bot)]])) >= 0:
                raise RuntimeError("lower critical point is not a saddle")
            self.xpoint = bot
        else:
            bot = self._on_boundary((g["top"][0], -g["top"][1]), "x")
            self.xpoint = None
        self.ext = dict(outer=out, inner=inn, top=top, bottom=bot)
        a = (out[0] - inn[0]) / 2
        Rg = (out[0] + inn[0]) / 2
        self.minor_n = a                                    # in units of R0p
        self.kappa_true = (top[1] - bot[1]) / (2 * a)
        self.delta_up = (Rg - top[0]) / a
        self.delta_low = (Rg - bot[0]) / a
        self.delta_true = 0.5 * (self.delta_up + self.delta_low)

    def _scale_current(self):
        """Fix the amplitude psi0 so that the toroidal current inside the separatrix is Ip.

        j_phi = -Delta* psi / (mu0 R) integrated in polar coordinates about the axis out to the boundary
        (the plasma is star-shaped about the axis; the ray through the X point is a measure-zero miss).
        """
        th = np.linspace(0, 2 * np.pi, 193)[:-1]
        rb = self.boundary_radius(th)
        gl_x, gl_w = np.polynomial.legendre.leggauss(24)
        r = 0.5 * rb[:, None] * (gl_x[None, :] + 1)
        w = 0.5 * rb[:, None] * gl_w[None, :] * r * (2 * np.pi / len(th))
        x = self.axis[0] + r * np.cos(th)[:, None]
        f = (1 - self.A) * x ** 2 + self.A
        S = (f / x * w).sum()
        # Ip = -psi0 / (mu0 R0p^2) * R0p * S
        self.psi0 = -MU0 * self.R0p * self.Ip / S
        self._quad = (th, rb, gl_x, gl_w)

    def boundary_radius(self, th):
        """Distance from the axis to the boundary along each ray (normalised units): the first sign change of psi.

        The diverted plasma is the region psi < 0 above the X point. A ray through the X point meets psi = 0
        only in a sector thinner than any sampling step, so each ray is also capped where it reaches the
        height of the X point.
        """
        r = np.linspace(0, 1.4, 141)[1:]
        x = np.maximum(self.axis[0] + r[None, :] * np.cos(th)[:, None], 1e-3)  # beyond the boundary only
        y = self.axis[1] + r[None, :] * np.sin(th)[:, None]
        pos = self.d["f"](x, y) >= 0
        if self.xpoint is not None:
            cap = np.full(len(th), np.inf)
            down = np.sin(th) < -1e-9
            cap[down] = (self.xpoint[1] - self.axis[1]) / np.sin(th[down])
            pos |= r[None, :] >= cap[:, None]
        first = pos.argmax(1)
        if not pos.any(1).all() or (first == 0).any():
            raise RuntimeError("open or degenerate boundary")
        lo, hi = r[first - 1], r[first]
        for _ in range(32):
            mid = 0.5 * (lo + hi)
            xm = np.maximum(self.axis[0] + mid * np.cos(th), 1e-3)
            vm = self.d["f"](xm, self.axis[1] + mid * np.sin(th))
            if self.xpoint is not None:
                vm = np.where(mid >= cap, 1.0, vm)
            neg = vm < 0
            lo, hi = np.where(neg, mid, lo), np.where(neg, hi, mid)
        return 0.5 * (lo + hi)

    def boundary(self, n=None):
        """Boundary points (R, Z) in m, from rays about the axis (the cusp at an X point is approximate).

        Default: the 192 rays already traced for the current integral."""
        if n is None:
            th, rb = self._quad[:2]
        else:
            th = np.linspace(0, 2 * np.pi, n, endpoint=False)
            rb = self.boundary_radius(th)
        return (self.R0p * (self.axis[0] + rb * np.cos(th)),
                self.Zs + self.R0p * (self.axis[1] + rb * np.sin(th)))

    # --- physical fields ---
    def psi(self, R, Z):
        return self.psi0 * self.d["f"](np.asarray(R) / self.R0p, (np.asarray(Z) - self.Zs) / self.R0p)

    def field(self, R, Z):
        """(B_R, B_Z) in T from B_R = -(1/R) dpsi/dZ, B_Z = (1/R) dpsi/dR."""
        R, Z = np.asarray(R, float), np.asarray(Z, float)
        x, y = R / self.R0p, (Z - self.Zs) / self.R0p
        return (-self.psi0 * self.d["y"](x, y) / (R * self.R0p), self.psi0 * self.d["x"](x, y) / (R * self.R0p))

    def truth(self):
        R0p, Zs = self.R0p, self.Zs
        t = dict(plasma_current=self.Ip, R_mag_axis=R0p * self.axis[0], Z_mag_axis=Zs + R0p * self.axis[1],
                 elongation=self.kappa_true, triangularity=self.delta_true,
                 R_x_point=np.nan, Z_x_point=np.nan, is_limited=float(self.config == "limited"))
        if self.xpoint is not None:
            t["R_x_point"], t["Z_x_point"] = R0p * self.xpoint[0], Zs + R0p * self.xpoint[1]
        return t


# ---------- vessel and probes ----------
def vessel_point(s):
    """Point and unit tangent on the invented vessel contour at angle parameter s (rounded box)."""
    n = VESSEL_POWER
    c, sn = np.cos(s), np.sin(s)
    pw = 2 / n
    with np.errstate(all="ignore"):  # the tangent is singular exactly at the four axis crossings of the box
        return _vessel_point(c, sn, pw)


def _vessel_point(c, sn, pw):
    R = VESSEL_CENTER[0] + VESSEL_HALF[0] * np.sign(c) * np.abs(c) ** pw
    Z = VESSEL_CENTER[1] + VESSEL_HALF[1] * np.sign(sn) * np.abs(sn) ** pw
    dR = -VESSEL_HALF[0] * pw * np.abs(c) ** (pw - 1) * sn
    dZ = VESSEL_HALF[1] * pw * np.abs(sn) ** (pw - 1) * c
    nrm = np.hypot(dR, dZ)
    return R, Z, dR / nrm, dZ / nrm


def probe_layout():
    """Positions of the 16 field probes (equal arc length) and 8 flux loops (equal angle), plus probe tangents."""
    s = np.linspace(0, 2 * np.pi, 20001)
    R, Z, _, _ = vessel_point(s)
    arc = np.r_[0, np.cumsum(np.hypot(np.diff(R), np.diff(Z)))]
    sp = np.interp((np.arange(N_COILS) + 0.5) * arc[-1] / N_COILS, arc, s)
    sf = (np.arange(N_LOOPS) + 0.25) * 2 * np.pi / N_LOOPS
    pr, pz, tr, tz = vessel_point(sp)
    fr, fz, _, _ = vessel_point(sf)
    return dict(coil_R=pr, coil_Z=pz, coil_tR=tr, coil_tZ=tz, loop_R=fr, loop_Z=fz)


_LAYOUT = probe_layout()


def signals(eq):
    """24 signals: tangential poloidal field at the probes (T), then flux 2 pi psi at the loops (Wb)."""
    L = _LAYOUT
    bR, bZ = eq.field(L["coil_R"], L["coil_Z"])
    return np.concatenate([bR * L["coil_tR"] + bZ * L["coil_tZ"], 2 * np.pi * eq.psi(L["loop_R"], L["loop_Z"])])


# ---------- discharges ----------
def _smooth(rng, n):
    """A random smooth curve on n slices with values in about [-1, 1]."""
    t = np.linspace(0, 1, n)
    s = sum(rng.uniform(0.3, 1.0) * np.sin(2 * np.pi * rng.uniform(0.4, 2.0) * t + rng.uniform(0, 2 * np.pi))
            for _ in range(2))
    return s / 2


def make_discharge(rng, config, n_slices=100):
    """Parameter trajectories of one synthetic discharge: a random base shape that drifts smoothly in time."""
    div = config == "diverted"
    base = dict(R0p=rng.uniform(0.545, 0.575), a=rng.uniform(0.185, 0.205),
                kappa=rng.uniform(1.30, 1.55) if div else rng.uniform(1.05, 1.60),
                delta=rng.uniform(0.0, 0.35), A=rng.uniform(-0.25, 0.35), Zs=rng.uniform(-0.02, 0.02))
    swing = dict(R0p=0.012, a=0.008, kappa=0.12 if div else 0.18, delta=0.12, A=0.2, Zs=0.015)
    traj = {k: base[k] + swing[k] * _smooth(rng, n_slices) for k in base}
    ramp = np.clip(np.minimum(np.linspace(0, 1, n_slices) / 0.15, (1 - np.linspace(0, 1, n_slices)) / 0.15), 0, 1)
    traj["Ip"] = rng.uniform(120e3, 260e3) * (0.35 + 0.65 * ramp * ramp * (3 - 2 * ramp))
    traj["kappa"] = np.clip(traj["kappa"], 1.0, 1.7 if div else 1.8)
    traj["delta"] = np.clip(traj["delta"], -0.05, 0.45)
    return traj


def _inside_vessel(eq, margin=0.02):
    bR, bZ = eq.boundary()
    c, h, n = VESSEL_CENTER, VESSEL_HALF, VESSEL_POWER
    # signed superellipse radius: < 1 inside; margin in metres converted with the smaller half-width
    q = (np.abs((bR - c[0]) / h[0]) ** n + np.abs((bZ - c[1]) / h[1]) ** n) ** (1 / n)
    return q.max() < 1 - margin / min(h)


def generate(n_discharges=40, n_slices=100, seed=0, frac_limited=0.45):
    """Return dict(X (N, 24), Y (N, 8) with NaN for non-existing X point, groups, config) of N = n_discharges * n_slices rows.

    A slice is dropped (and the discharge redrawn) if the solve fails or the boundary leaves the vessel,
    so every discharge has exactly n_slices valid rows.
    """
    rng = np.random.default_rng(seed)
    X, Y, G, tt = [], [], [], []
    n_redrawn = 0
    d = 0
    while d < n_discharges:
        config = "limited" if rng.random() < frac_limited else "diverted"
        traj = make_discharge(rng, config, n_slices)
        rows_x, rows_y = [], []
        try:
            for i in range(n_slices):
                eq = Equilibrium(config=config, **{k: v[i] for k, v in traj.items()})
                if not _inside_vessel(eq):
                    raise RuntimeError("boundary too close to the vessel")
                rows_x.append(signals(eq))
                t = eq.truth()
                rows_y.append([t[k] for k in TARGET_NAMES])
        except (RuntimeError, np.linalg.LinAlgError):
            n_redrawn += 1
            continue
        X += rows_x
        Y += rows_y
        G += [d] * n_slices
        tt += list(np.linspace(0, 1, n_slices))
        d += 1
    return dict(X=np.array(X, np.float32), Y=np.array(Y, np.float64), groups=np.array(G),
                time=np.array(tt), n_redrawn=n_redrawn)


def _selfcheck():
    import time
    # 1. every basis function solves the homogeneous equation exactly (analytic derivatives)
    x, y = np.meshgrid(np.linspace(0.5, 1.5, 7), np.linspace(-0.6, 0.6, 7))
    worst = 0.0
    for dd in _BASIS_D:
        res = dd["xx"](x, y) - dd["x"](x, y) / x + dd["yy"](x, y)
        worst = max(worst, np.abs(res).max())
    print(f"homogeneous solutions: max |Delta* phi| = {worst:.2e}")
    # 2. the particular solution and the full solution obey Delta* psi = (1 - A) x^2 + A
    for cfg in ("limited", "diverted"):
        eq = Equilibrium(0.56, 0.2, 1.5, 0.3, 0.1, 200e3, 0.01, cfg)
        d = eq.d
        res = d["xx"](x, y) - d["x"](x, y) / x + d["yy"](x, y) - ((1 - eq.A) * x ** 2 + eq.A)
        print(f"{cfg}: max |Delta* psi - source| = {np.abs(res).max():.2e}; axis (R, Z) = "
              f"({eq.truth()['R_mag_axis']:.4f}, {eq.truth()['Z_mag_axis']:.4f}) m; kappa requested 1.5 measured "
              f"{eq.kappa_true:.4f}; delta requested 0.3 measured {eq.delta_true:.4f}")
        # 3. Ampere check: the loop integral of B_pol along the boundary equals mu0 Ip
        bR, bZ = eq.boundary(2000)
        Bp = np.array(eq.field(bR, bZ))
        dl = np.stack([np.roll(bR, 1) - bR, np.roll(bZ, 1) - bZ])   # clockwise in the (R, Z) plane: the sense of +Ip
        print(f"   Ampere: loop integral of B.dl / (mu0 Ip) = {(Bp * dl).sum() / (MU0 * eq.Ip):.4f} (ray-sampled boundary)")
    t0 = time.time()
    data = generate(4, 100, seed=1)
    print(f"generated {len(data['X'])} rows in {time.time() - t0:.1f} s ({data['n_redrawn']} discharges redrawn)")


if __name__ == "__main__":
    _selfcheck()
