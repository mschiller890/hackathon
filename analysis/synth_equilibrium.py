"""Syntetické tokamakové rovnováhy se ZNÁMÝM plazmatem pro uzavřený test převodu signálů sond na tvar plazmatu.

SIMULOVANÁ DATA, NE DATA Z COMPASSU. Nic tu nečte ani nekopíruje žádný soubor ÚFP; obrys komory, polohy sond
a rozsahy parametrů jsou vymyšlené a jen velikostí odpovídají COMPASSu (R0 kolem 0,56 m, a kolem 0,2 m).

Model: Solovjovova řešení Grad-Šafranovovy rovnice (konstantní p' a F F'), sestavená podle Cerfon a Freidberg,
Phys. Plasmas 17, 032502 (2010). V jednotkách hlavního poloměru plazmatu R0p, x = R / R0p, y = (Z - Zs) / R0p,

    psi = x^4/8 + A (x^2 ln x / 2 - x^4/8) + součet_i c_i phi_i(x, y),     Delta* psi = (1 - A) x^2 + A,

kde phi_i jsou homogenní řešení. Koeficienty c_i jsou dané tím, že hranice psi = 0 prochází vnějším, vnitřním
a horním bodem požadovaného tvaru (a, kappa, delta) a má tam odpovídající křivosti. Dvě konfigurace: "limited"
(souměrná podle roviny z = 0, 7 koeficientů) a "diverted" (dolní X bod, 12 koeficientů). Pravda (osa, X bod,
krajní body hranice) se pak MĚŘÍ na hotovém řešení Newtonovými iteracemi na analytických derivacích, nekopíruje se
z požadovaných parametrů.

Signály sond (16 tangenciálních sond pole, 8 magnetických smyček na vymyšleném obrysu komory) se počítají přesně
ze stejného analytického psi v polohách sond. Protože Solovjovovo řešení je analytické všude, nese proud i mimo
separatrix; viz results/synthetic-validation.md.

Použití: python -I analysis/synth_equilibrium.py   (samokontroly a řádek s časem)
"""
import numpy as np

MU0 = 4e-7 * np.pi
VESSEL_CENTER = (0.56, 0.0)
VESSEL_HALF = (0.30, 0.55)   # vymyšlený obecný obrys: zaoblená krabice (superelipsa), ne komora COMPASSu
VESSEL_POWER = 3.0
N_COILS, N_LOOPS = 16, 8
SIGNAL_NAMES = [f"IPR{i + 1:02d}" for i in range(N_COILS)] + [f"FL{i + 1:02d}" for i in range(N_LOOPS)]
TARGET_NAMES = ["plasma_current", "R_mag_axis", "Z_mag_axis", "elongation", "triangularity",
                "R_x_point", "Z_x_point", "is_limited"]


# ===================================================================================================================
# Derivace bez symbolického počtu: členy tvaru koeficient * x^a * y^b * (ln x)^k
# ===================================================================================================================
class Terms:
    """Součet členů coefficient * x^x_power * y^y_power * (ln x)^log_power s celými mocninami; přesné derivace a
    vektorizované vyhodnocení."""

    def __init__(self, terms):
        """terms: seznam čtveřic (koeficient, mocnina x, mocnina y, mocnina ln x); nulové členy se zahodí."""
        nonzero = np.array([term for term in terms if term[0] != 0], dtype=float).reshape(-1, 4)
        self.coefficient = nonzero[:, 0]
        self.x_power, self.y_power, self.log_power = nonzero[:, 1].astype(int), nonzero[:, 2].astype(int), nonzero[:, 3].astype(int)

    def _terms(self):
        return list(zip(self.coefficient, self.x_power, self.y_power, self.log_power))

    def dx(self):
        """Derivace podle x (člen s ln x dá dva členy)."""
        derivative = []
        for coefficient, x_power, y_power, log_power in self._terms():
            if x_power:
                derivative.append((coefficient * x_power, x_power - 1, y_power, log_power))
            if log_power:
                derivative.append((coefficient * log_power, x_power - 1, y_power, log_power - 1))
        return Terms(derivative)

    def dy(self):
        """Derivace podle y."""
        return Terms([(coefficient * y_power, x_power, y_power - 1, log_power)
                      for coefficient, x_power, y_power, log_power in self._terms() if y_power])

    def __call__(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        if not len(self.coefficient):
            return np.zeros(x.shape)
        # Tabulka několika různých mocnin a pak výběr z ní: o několikanásobek rychlejší než mocnina pro každý člen.
        log_x = np.log(x)
        x_powers = {power: x ** power for power in set(self.x_power)}
        y_powers = {power: y ** power for power in set(self.y_power)}
        log_powers = {power: log_x ** power for power in set(self.log_power)}
        total = np.zeros(x.shape)
        for coefficient, x_power, y_power, log_power in zip(self.coefficient, self.x_power, self.y_power, self.log_power):
            total += coefficient * x_powers[x_power] * y_powers[y_power] * log_powers[log_power]
        return total


def derivatives_of(terms):
    """Slovník funkce a jejích derivací: f, x, y, xx, xy, yy."""
    d_dx, d_dy = terms.dx(), terms.dy()
    return {"f": terms, "x": d_dx, "y": d_dy, "xx": d_dx.dx(), "xy": d_dx.dy(), "yy": d_dy.dy()}


# Homogenní řešení rovnice Delta* psi = 0 (Cerfon a Freidberg 2010): (koeficient, mocnina x, mocnina y, mocnina ln x).
BASIS = [
    [(1, 0, 0, 0)],
    [(1, 2, 0, 0)],
    [(1, 0, 2, 0), (-1, 2, 0, 1)],
    [(1, 4, 0, 0), (-4, 2, 2, 0)],
    [(2, 0, 4, 0), (-9, 2, 2, 0), (3, 4, 0, 1), (-12, 2, 2, 1)],
    [(1, 6, 0, 0), (-12, 4, 2, 0), (8, 2, 4, 0)],
    [(8, 0, 6, 0), (-140, 2, 4, 0), (-120, 2, 4, 1), (75, 4, 2, 0), (180, 4, 2, 1), (-15, 6, 0, 1)],
    # antisymetrická podle z = 0, potřebná pro dolní X bod
    [(1, 0, 1, 0)],
    [(1, 2, 1, 0)],
    [(1, 0, 3, 0), (-3, 2, 1, 1)],
    [(3, 4, 1, 0), (-4, 2, 3, 0)],
    [(8, 0, 5, 0), (-45, 4, 1, 0), (-80, 2, 3, 1), (60, 4, 1, 1)],
]
BASIS_DERIVATIVES = [derivatives_of(Terms(function)) for function in BASIS]


def newton(residual_and_jacobian, start, tolerance=1e-12, max_iterations=40):
    """Newtonova metoda pro funkci p -> (reziduum (2,), jakobián (2, 2)); když nekonverguje, vyhodí chybu."""
    point = np.array(start, float)
    for _ in range(max_iterations):
        residual, jacobian = residual_and_jacobian(point)
        step = np.linalg.solve(jacobian, residual)
        if np.abs(step).max() > 0.2:                      # divoký první krok nesmí vyjet z oblasti
            step *= 0.2 / np.abs(step).max()
        point = point - step
        if np.abs(step).max() < tolerance:
            return point
    raise RuntimeError("Newton did not converge")


# ===================================================================================================================
# Jedna rovnováha
# ===================================================================================================================
class Equilibrium:
    """Jedna Solovjovova rovnováha ve fyzikálních jednotkách. Délky v m, psi ve Wb/rad, B v T, Ip v A.

    config: "limited" nebo "diverted". Parametry tvaru (a, kappa, delta) jsou požadavky; atributy axis, kappa_true,
    delta_true, xpoint atd. se měří na hotovém řešení.
    """

    def __init__(self, R0p, a, kappa, delta, A, Ip, Zs=0.0, config="limited"):
        self.R0p, self.Zs, self.A, self.config, self.Ip = R0p, Zs, A, config, Ip
        epsilon, alpha = a / R0p, np.arcsin(delta)
        self._solve_coefficients(epsilon, kappa, delta, alpha)
        self._measure(epsilon, kappa, delta)
        self._scale_current()

    # --- stavba ---
    def _solve_coefficients(self, epsilon, kappa, delta, alpha):
        """Koeficienty homogenních řešení z podmínek, že hranice psi = 0 prochází vnějším, vnitřním a horním bodem
        s předepsanými křivostmi (u divertorové konfigurace i dolním X bodem)."""
        A = self.A
        particular = Terms([((1 - A) / 8, 4, 0, 0), (A / 2, 2, 0, 1)])
        particular_derivatives = derivatives_of(particular)
        outer_curvature = -(1 + alpha) ** 2 / (epsilon * kappa ** 2)
        inner_curvature = (1 - alpha) ** 2 / (epsilon * kappa ** 2)
        top_curvature = -kappa / (epsilon * np.cos(alpha) ** 2)
        outer, inner = (1 + epsilon, 0.0), (1 - epsilon, 0.0)
        top = (1 - delta * epsilon, kappa * epsilon)
        # Každá podmínka je seznam (jméno derivace, váha) v bodě: součet váha * d(psi) = 0.
        conditions = [([("f", 1)], outer), ([("f", 1)], inner), ([("f", 1)], top), ([("x", 1)], top),
                      ([("yy", 1), ("x", outer_curvature)], outer), ([("yy", 1), ("x", inner_curvature)], inner),
                      ([("xx", 1), ("y", top_curvature)], top)]
        if self.config == "diverted":
            xpoint = (1 - 1.1 * delta * epsilon, -1.1 * kappa * epsilon)
            self._xpoint_guess = xpoint
            conditions = [c for c in conditions
                          if c[0] != [("yy", 1), ("x", outer_curvature)] and c[0] != [("yy", 1), ("x", inner_curvature)]]
            conditions += [([("y", 1)], outer), ([("y", 1)], inner), ([("f", 1)], xpoint), ([("x", 1)], xpoint),
                           ([("y", 1)], xpoint), ([("yy", 1), ("x", outer_curvature)], outer),
                           ([("yy", 1), ("x", inner_curvature)], inner)]
            n_coefficients = 12
        else:
            n_coefficients = 7
        matrix = np.array([[sum(weight * BASIS_DERIVATIVES[i][name](*point) for name, weight in terms)
                            for i in range(n_coefficients)] for terms, point in conditions])
        right_side = -np.array([sum(weight * particular_derivatives[name](*point) for name, weight in terms)
                                for terms, point in conditions])
        if matrix.shape[0] != n_coefficients:
            raise RuntimeError(f"{matrix.shape[0]} conditions for {n_coefficients} coefficients")
        self.coefficients = np.linalg.solve(matrix, right_side)
        all_terms = [(self.coefficients[i] * c, x_power, y_power, log_power)
                     for i in range(n_coefficients) for c, x_power, y_power, log_power in BASIS[i]]
        all_terms += [(c, x_power, y_power, log_power) for c, x_power, y_power, log_power
                      in zip(particular.coefficient, particular.x_power, particular.y_power, particular.log_power)]
        self.derivatives = derivatives_of(Terms(all_terms))
        self._boundary_guesses = dict(outer=outer, inner=inner, top=top)

    def _critical_point(self, start):
        """Bod, kde se gradient psi rovná nule (osa nebo X bod), Newtonovou metodou od `start`."""
        d = self.derivatives

        def residual_and_jacobian(point):
            x, y = point
            return (np.array([d["x"](x, y), d["y"](x, y)]),
                    np.array([[d["xx"](x, y), d["xy"](x, y)], [d["xy"](x, y), d["yy"](x, y)]]))
        return newton(residual_and_jacobian, start)

    def _boundary_extreme(self, start, derivative):
        """Bod, kde psi = 0 a daná první derivace ('x' nebo 'y') je nula: krajní bod hranice."""
        d = self.derivatives
        second_derivatives = {"x": ("xx", "xy"), "y": ("xy", "yy")}[derivative]   # druhý řádek jakobiánu je d(derivace)/d(x, y)

        def residual_and_jacobian(point):
            x, y = point
            return (np.array([d["f"](x, y), d[derivative](x, y)]),
                    np.array([[d["x"](x, y), d["y"](x, y)],
                              [d[second_derivatives[0]](x, y), d[second_derivatives[1]](x, y)]]))
        return newton(residual_and_jacobian, start)

    def _measure(self, epsilon, kappa, delta):
        """Změří na hotovém řešení osu, krajní body hranice, X bod a z nich skutečné kappa a delta."""
        guesses = self._boundary_guesses
        # Magnetická osa je minimum psi uvnitř; hrubé prohledání vybere údolí pro Newtonovu metodu.
        x_grid, y_grid = np.meshgrid(np.linspace(1 - epsilon, 1 + epsilon, 25), np.linspace(-kappa * epsilon, kappa * epsilon, 41))
        flux = self.derivatives["f"](x_grid, y_grid)
        best = np.unravel_index(np.argmin(flux), flux.shape)
        self.axis = self._critical_point((x_grid[best], y_grid[best]))
        if self.derivatives["f"](*self.axis) >= 0:
            raise RuntimeError("axis flux is not inside the boundary")
        outer = self._boundary_extreme(guesses["outer"], "y")
        inner = self._boundary_extreme(guesses["inner"], "y")
        top = self._boundary_extreme(guesses["top"], "x")
        d = self.derivatives
        if self.config == "diverted":
            bottom = self._critical_point(self._xpoint_guess)
            if np.linalg.det(np.array([[d["xx"](*bottom), d["xy"](*bottom)],
                                       [d["xy"](*bottom), d["yy"](*bottom)]])) >= 0:
                raise RuntimeError("lower critical point is not a saddle")
            self.xpoint = bottom
        else:
            bottom = self._boundary_extreme((guesses["top"][0], -guesses["top"][1]), "x")
            self.xpoint = None
        self.extremes = dict(outer=outer, inner=inner, top=top, bottom=bottom)
        minor_radius = (outer[0] - inner[0]) / 2
        geometric_center = (outer[0] + inner[0]) / 2
        self.minor_n = minor_radius                         # v jednotkách R0p
        self.kappa_true = (top[1] - bottom[1]) / (2 * minor_radius)
        self.delta_up = (geometric_center - top[0]) / minor_radius
        self.delta_low = (geometric_center - bottom[0]) / minor_radius
        self.delta_true = 0.5 * (self.delta_up + self.delta_low)

    def _scale_current(self):
        """Nastaví amplitudu psi0 tak, aby toroidální proud uvnitř separatrix byl Ip.

        j_phi = -Delta* psi / (mu0 R) se integruje v polárních souřadnicích kolem osy až po hranici (plazma je
        hvězdicovité kolem osy; paprsek přesně přes X bod je zanedbatelná miss množina míry nula).
        """
        angles = np.linspace(0, 2 * np.pi, 193)[:-1]
        boundary_radii = self.boundary_radius(angles)
        nodes, node_weights = np.polynomial.legendre.leggauss(24)
        radius = 0.5 * boundary_radii[:, None] * (nodes[None, :] + 1)
        weights = 0.5 * boundary_radii[:, None] * node_weights[None, :] * radius * (2 * np.pi / len(angles))
        x = self.axis[0] + radius * np.cos(angles)[:, None]
        source = (1 - self.A) * x ** 2 + self.A
        integral = (source / x * weights).sum()
        # Ip = -psi0 / (mu0 R0p^2) * R0p * integral
        self.psi0 = -MU0 * self.R0p * self.Ip / integral
        self._quadrature = (angles, boundary_radii, nodes, node_weights)

    def boundary_radius(self, angles):
        """Vzdálenost osy od hranice podél každého paprsku (normované jednotky): první změna znaménka psi.

        Divertorové plazma je oblast psi < 0 nad X bodem. Paprsek přes X bod protne psi = 0 jen v sektoru užším
        než jakýkoli krok vzorkování, proto je každý paprsek navíc omezen ve výšce X bodu.
        """
        radius = np.linspace(0, 1.4, 141)[1:]
        x = np.maximum(self.axis[0] + radius[None, :] * np.cos(angles)[:, None], 1e-3)  # jen za hranicí
        y = self.axis[1] + radius[None, :] * np.sin(angles)[:, None]
        outside = self.derivatives["f"](x, y) >= 0
        if self.xpoint is not None:
            cap = np.full(len(angles), np.inf)
            downward = np.sin(angles) < -1e-9
            cap[downward] = (self.xpoint[1] - self.axis[1]) / np.sin(angles[downward])
            outside |= radius[None, :] >= cap[:, None]
        first_outside = outside.argmax(1)
        if not outside.any(1).all() or (first_outside == 0).any():
            raise RuntimeError("open or degenerate boundary")
        low, high = radius[first_outside - 1], radius[first_outside]
        for _ in range(32):                                    # půlení intervalu
            middle = 0.5 * (low + high)
            x_middle = np.maximum(self.axis[0] + middle * np.cos(angles), 1e-3)
            flux_middle = self.derivatives["f"](x_middle, self.axis[1] + middle * np.sin(angles))
            if self.xpoint is not None:
                flux_middle = np.where(middle >= cap, 1.0, flux_middle)
            inside = flux_middle < 0
            low, high = np.where(inside, middle, low), np.where(inside, high, middle)
        return 0.5 * (low + high)

    def boundary(self, n=None):
        """Body hranice (R, Z) v m z paprsků kolem osy (hrot u X bodu je přibližný).

        Výchozí: 192 paprsků, které se už vedly pro integrál proudu."""
        if n is None:
            angles, boundary_radii = self._quadrature[:2]
        else:
            angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
            boundary_radii = self.boundary_radius(angles)
        return (self.R0p * (self.axis[0] + boundary_radii * np.cos(angles)),
                self.Zs + self.R0p * (self.axis[1] + boundary_radii * np.sin(angles)))

    # --- fyzikální pole ---
    def psi(self, R, Z):
        """Poloidální tok psi (Wb/rad) v bodech (R, Z)."""
        return self.psi0 * self.derivatives["f"](np.asarray(R) / self.R0p, (np.asarray(Z) - self.Zs) / self.R0p)

    def field(self, R, Z):
        """(B_R, B_Z) v T z B_R = -(1/R) dpsi/dZ, B_Z = (1/R) dpsi/dR."""
        R, Z = np.asarray(R, float), np.asarray(Z, float)
        x, y = R / self.R0p, (Z - self.Zs) / self.R0p
        return (-self.psi0 * self.derivatives["y"](x, y) / (R * self.R0p),
                self.psi0 * self.derivatives["x"](x, y) / (R * self.R0p))

    def truth(self):
        """Skutečné hodnoty cílů této rovnováhy (X bod je NaN u limiterové konfigurace)."""
        R0p, Zs = self.R0p, self.Zs
        values = dict(plasma_current=self.Ip, R_mag_axis=R0p * self.axis[0], Z_mag_axis=Zs + R0p * self.axis[1],
                      elongation=self.kappa_true, triangularity=self.delta_true,
                      R_x_point=np.nan, Z_x_point=np.nan, is_limited=float(self.config == "limited"))
        if self.xpoint is not None:
            values["R_x_point"], values["Z_x_point"] = R0p * self.xpoint[0], Zs + R0p * self.xpoint[1]
        return values


# ===================================================================================================================
# Komora a sondy
# ===================================================================================================================
def vessel_point(parameter):
    """Bod a jednotková tečna na vymyšleném obrysu komory (zaoblená krabice) pro úhlový parametr `parameter`."""
    cosine, sine = np.cos(parameter), np.sin(parameter)
    exponent = 2 / VESSEL_POWER
    with np.errstate(all="ignore"):  # tečna je singulární přesně ve čtyřech průsečících krabice s osami
        return _vessel_point(cosine, sine, exponent)


def _vessel_point(cosine, sine, exponent):
    R = VESSEL_CENTER[0] + VESSEL_HALF[0] * np.sign(cosine) * np.abs(cosine) ** exponent
    Z = VESSEL_CENTER[1] + VESSEL_HALF[1] * np.sign(sine) * np.abs(sine) ** exponent
    dR = -VESSEL_HALF[0] * exponent * np.abs(cosine) ** (exponent - 1) * sine
    dZ = VESSEL_HALF[1] * exponent * np.abs(sine) ** (exponent - 1) * cosine
    length = np.hypot(dR, dZ)
    return R, Z, dR / length, dZ / length


def probe_layout():
    """Polohy 16 sond pole (stejná délka oblouku) a 8 smyček toku (stejný úhel) a tečny v místech sond."""
    parameter = np.linspace(0, 2 * np.pi, 20001)
    R, Z, _, _ = vessel_point(parameter)
    arc_length = np.r_[0, np.cumsum(np.hypot(np.diff(R), np.diff(Z)))]
    coil_parameter = np.interp((np.arange(N_COILS) + 0.5) * arc_length[-1] / N_COILS, arc_length, parameter)
    loop_parameter = (np.arange(N_LOOPS) + 0.25) * 2 * np.pi / N_LOOPS
    coil_R, coil_Z, coil_tangent_R, coil_tangent_Z = vessel_point(coil_parameter)
    loop_R, loop_Z, _, _ = vessel_point(loop_parameter)
    return dict(coil_R=coil_R, coil_Z=coil_Z, coil_tR=coil_tangent_R, coil_tZ=coil_tangent_Z, loop_R=loop_R, loop_Z=loop_Z)


PROBE_LAYOUT = probe_layout()


def signals(equilibrium):
    """24 signálů: tangenciální poloidální pole na sondách (T), pak tok 2 pi psi na smyčkách (Wb)."""
    layout = PROBE_LAYOUT
    field_R, field_Z = equilibrium.field(layout["coil_R"], layout["coil_Z"])
    return np.concatenate([field_R * layout["coil_tR"] + field_Z * layout["coil_tZ"],
                           2 * np.pi * equilibrium.psi(layout["loop_R"], layout["loop_Z"])])


# ===================================================================================================================
# Výboje
# ===================================================================================================================
def smooth_curve(rng, n_slices):
    """Náhodná hladká křivka na n řezech s hodnotami zhruba v [-1, 1]."""
    t = np.linspace(0, 1, n_slices)
    total = sum(rng.uniform(0.3, 1.0) * np.sin(2 * np.pi * rng.uniform(0.4, 2.0) * t + rng.uniform(0, 2 * np.pi))
                for _ in range(2))
    return total / 2


def make_discharge(rng, config, n_slices=100):
    """Průběhy parametrů jednoho syntetického výboje: náhodný základní tvar, který se v čase hladce mění."""
    diverted = config == "diverted"
    base = dict(R0p=rng.uniform(0.545, 0.575), a=rng.uniform(0.185, 0.205),
                kappa=rng.uniform(1.30, 1.55) if diverted else rng.uniform(1.05, 1.60),
                delta=rng.uniform(0.0, 0.35), A=rng.uniform(-0.25, 0.35), Zs=rng.uniform(-0.02, 0.02))
    swing = dict(R0p=0.012, a=0.008, kappa=0.12 if diverted else 0.18, delta=0.12, A=0.2, Zs=0.015)
    trajectory = {name: base[name] + swing[name] * smooth_curve(rng, n_slices) for name in base}
    ramp = np.clip(np.minimum(np.linspace(0, 1, n_slices) / 0.15, (1 - np.linspace(0, 1, n_slices)) / 0.15), 0, 1)
    trajectory["Ip"] = rng.uniform(120e3, 260e3) * (0.35 + 0.65 * ramp * ramp * (3 - 2 * ramp))
    trajectory["kappa"] = np.clip(trajectory["kappa"], 1.0, 1.7 if diverted else 1.8)
    trajectory["delta"] = np.clip(trajectory["delta"], -0.05, 0.45)
    return trajectory


def is_inside_vessel(equilibrium, margin=0.02):
    """Leží celá hranice plazmatu uvnitř komory s odstupem `margin` (m)?"""
    boundary_R, boundary_Z = equilibrium.boundary()
    center, half, power = VESSEL_CENTER, VESSEL_HALF, VESSEL_POWER
    # Poloměr superelipsy: < 1 uvnitř; odstup v metrech se převádí menší poloosou.
    radius = (np.abs((boundary_R - center[0]) / half[0]) ** power + np.abs((boundary_Z - center[1]) / half[1]) ** power) ** (1 / power)
    return radius.max() < 1 - margin / min(half)


def generate(n_discharges=40, n_slices=100, seed=0, frac_limited=0.45):
    """Vrátí slovník X (N, 24), Y (N, 8; NaN pro neexistující X bod), groups, time, n_redrawn; N = n_discharges * n_slices řádků.

    Řez se zahodí (a výboj se vylosuje znovu), když řešení selže nebo hranice vyjede z komory, takže každý výboj
    má právě n_slices platných řádků.
    """
    rng = np.random.default_rng(seed)
    signal_rows, target_rows, group_ids, times = [], [], [], []
    n_redrawn = 0
    discharge = 0
    while discharge < n_discharges:
        config = "limited" if rng.random() < frac_limited else "diverted"
        trajectory = make_discharge(rng, config, n_slices)
        discharge_signals, discharge_targets = [], []
        try:
            for i in range(n_slices):
                equilibrium = Equilibrium(config=config, **{name: values[i] for name, values in trajectory.items()})
                if not is_inside_vessel(equilibrium):
                    raise RuntimeError("boundary too close to the vessel")
                discharge_signals.append(signals(equilibrium))
                truth = equilibrium.truth()
                discharge_targets.append([truth[name] for name in TARGET_NAMES])
        except (RuntimeError, np.linalg.LinAlgError):
            n_redrawn += 1
            continue
        signal_rows += discharge_signals
        target_rows += discharge_targets
        group_ids += [discharge] * n_slices
        times += list(np.linspace(0, 1, n_slices))
        discharge += 1
    return dict(X=np.array(signal_rows, np.float32), Y=np.array(target_rows, np.float64), groups=np.array(group_ids),
                time=np.array(times), n_redrawn=n_redrawn)


def self_check():
    """Samokontroly generátoru: homogenní řešení, rovnice pro psi, Ampérův zákon a doba generování."""
    import time
    # 1. Každá bázová funkce řeší homogenní rovnici přesně (analytické derivace).
    x, y = np.meshgrid(np.linspace(0.5, 1.5, 7), np.linspace(-0.6, 0.6, 7))
    worst = 0.0
    for derivatives in BASIS_DERIVATIVES:
        residual = derivatives["xx"](x, y) - derivatives["x"](x, y) / x + derivatives["yy"](x, y)
        worst = max(worst, np.abs(residual).max())
    print(f"homogeneous solutions: max |Delta* phi| = {worst:.2e}")
    # 2. Partikulární i úplné řešení splňuje Delta* psi = (1 - A) x^2 + A.
    for config in ("limited", "diverted"):
        equilibrium = Equilibrium(0.56, 0.2, 1.5, 0.3, 0.1, 200e3, 0.01, config)
        d = equilibrium.derivatives
        residual = d["xx"](x, y) - d["x"](x, y) / x + d["yy"](x, y) - ((1 - equilibrium.A) * x ** 2 + equilibrium.A)
        print(f"{config}: max |Delta* psi - source| = {np.abs(residual).max():.2e}; axis (R, Z) = "
              f"({equilibrium.truth()['R_mag_axis']:.4f}, {equilibrium.truth()['Z_mag_axis']:.4f}) m; kappa requested 1.5 measured "
              f"{equilibrium.kappa_true:.4f}; delta requested 0.3 measured {equilibrium.delta_true:.4f}")
        # 3. Ampérova kontrola: křivkový integrál B_pol podél hranice se rovná mu0 Ip.
        boundary_R, boundary_Z = equilibrium.boundary(2000)
        poloidal_field = np.array(equilibrium.field(boundary_R, boundary_Z))
        segments = np.stack([np.roll(boundary_R, 1) - boundary_R, np.roll(boundary_Z, 1) - boundary_Z])   # po směru hodin v rovině (R, Z): smysl +Ip
        print(f"   Ampere: loop integral of B.dl / (mu0 Ip) = {(poloidal_field * segments).sum() / (MU0 * equilibrium.Ip):.4f} (ray-sampled boundary)")
    started = time.time()
    data = generate(4, 100, seed=1)
    print(f"generated {len(data['X'])} rows in {time.time() - started:.1f} s ({data['n_redrawn']} discharges redrawn)")


if __name__ == "__main__":
    self_check()
