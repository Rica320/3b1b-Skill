"""Data layer for the N-BEATS-MoE explainer.

Everything the video draws is computed here, so the animation cannot drift
from the claim it is making (style_guide.md: "prefer a metaphor that IS the
real object").

Three things are genuinely computed rather than keyframed:

  1. The stack outputs are the actual N-BEATS bases — a polynomial B(t) for
     the trend stack and a harmonic Fourier F(t) for the seasonal stack, over
     normalised time t = tau/H, exactly as in Oreshkin et al. §3.3.
  2. The gate is a real `softmax(Linear(LayerNorm(x0)))`: a 3x3 affine map
     over three features of the layer-normalised input window. The weights are
     set by hand rather than trained, but the computation is the paper's
     Equation 3, so the bars in the video move because the series changed.
  3. SMAPE is computed from the drawn curves.

The hero series reconstructs the ID1 panel of Figure 5. Its component
magnitudes (identity 122-127, trend [0.4,0.9] gated vs [1,3] plain,
seasonality 0-15) and its gate weights (0.275 / 0.169 / 0.556) are the paper's,
and the gate weights are reproduced exactly by the calibration at the bottom of
this file.

The two SMAPE figures shown on screen — 7.34% and 2.68% — are the paper's
measured results for the real ID1 series, not outputs of this reconstruction.
A clean additive reconstruction cannot match both those absolute values and the
published component magnitudes at once: an irreducible residual large enough to
give 2.68% would be sigma ~= 6.6, which swamps a seasonal component of
amplitude 7.5. The component magnitudes are the ones the video makes explicit
claims about, so those are matched exactly, and the baseline's error is tuned
to preserve the published *ratio* instead (2.70 here against 2.74 reported).
`verify_numbers.py` prints both so the gap stays visible.
"""

import numpy as np

H = 8                # M1 monthly forecast horizon (Table 3)
N_HIST = 36          # input window: 4.5 * H, inside the 1-5x multiplier range
SEASON = 12          # monthly data


# ─────────────────────────────────────────────────────────────────────────
# The N-BEATS bases.  tau is in months; u = tau / H is normalised time.
# ─────────────────────────────────────────────────────────────────────────

def trend_basis(tau, coefs):
    """Polynomial basis B(t) = [1, t, t^2, ...] — the N-BEATS trend stack."""
    u = np.asarray(tau, dtype=float) / H
    return sum(c * u ** i for i, c in enumerate(coefs))


def seasonal_basis(tau, const, cos_c, sin_c):
    """Harmonic Fourier basis F(t) — the N-BEATS seasonality stack."""
    tau = np.asarray(tau, dtype=float)
    out = np.full(tau.shape, float(const))
    for k, c in enumerate(cos_c, start=1):
        out = out + c * np.cos(2 * np.pi * k * tau / SEASON)
    for k, c in enumerate(sin_c, start=1):
        out = out + c * np.sin(2 * np.pi * k * tau / SEASON)
    return out


def identity_basis(tau, level, drift, wobble, phase, freq=1.9):
    """The generic (unconstrained) stack: level plus slow local movement."""
    u = np.asarray(tau, dtype=float) / H
    return level + drift * u + wobble * np.sin(freq * u + phase)


class Series:
    """One time series, decomposed into the three stacks that generate it."""

    def __init__(self, level=124.5, drift=-0.9, wobble=2.3, phase=0.55,
                 freq=1.9, trend=(0.45, 0.62, -0.15),
                 seas_const=7.5, seas_cos=(-5.4,), seas_sin=(5.2, 1.9),
                 resid=0.0, seed=0):
        self.p = dict(level=level, drift=drift, wobble=wobble, phase=phase,
                      freq=freq, trend=trend, seas_const=seas_const,
                      seas_cos=seas_cos, seas_sin=seas_sin, resid=resid)
        self.rng = np.random.default_rng(seed)
        self._noise = self.rng.normal(0.0, 1.0, N_HIST + H + 1)

    # ── components, evaluable at any (possibly fractional) tau ──────────
    def identity(self, tau):
        p = self.p
        return identity_basis(tau, p["level"], p["drift"], p["wobble"],
                              p["phase"], p["freq"])

    def trend(self, tau):
        return trend_basis(tau, self.p["trend"])

    def seasonal(self, tau):
        p = self.p
        return seasonal_basis(tau, p["seas_const"], p["seas_cos"],
                              p["seas_sin"])

    def clean(self, tau):
        return self.identity(tau) + self.trend(tau) + self.seasonal(tau)

    # ── the observed series: clean signal plus an irreducible residual ──
    def observed(self, idx):
        """idx: integer month offsets, -N_HIST .. H."""
        idx = np.asarray(idx, dtype=int)
        return self.clean(idx) + self.p["resid"] * self._noise[idx + N_HIST]

    def window(self):
        """x0 — the input window the gate reads."""
        return self.observed(np.arange(-N_HIST, 0))

    def horizon_idx(self):
        return np.arange(1, H + 1)

    def truth(self):
        return self.observed(self.horizon_idx())


# ─────────────────────────────────────────────────────────────────────────
# The gate:  G = softmax(Linear(LayerNorm(x0)))          — paper Eq. (3)
# ─────────────────────────────────────────────────────────────────────────

def layer_norm(x, eps=1e-5):
    x = np.asarray(x, dtype=float)
    return (x - x.mean()) / (x.std() + eps)


def gate_features(window):
    """Three summaries a linear layer can read off a normalised window.

    A learned Linear(36 -> 3) is free to compute any linear functional of x0;
    these are the three that matter for choosing between a level, a trend and
    a seasonal expert, written explicitly so the routing is legible.
    """
    xn = layer_norm(window)
    n = len(xn)
    tt = np.linspace(-1.0, 1.0, n)

    slope, icept = np.polyfit(tt, xn, 1)
    detr = xn - (slope * tt + icept)

    k = np.arange(n)
    c = np.mean(detr * np.cos(2 * np.pi * k / SEASON))
    s = np.mean(detr * np.sin(2 * np.pi * k / SEASON))
    seas = 2.0 * float(np.hypot(c, s))

    return np.array([1.0, abs(float(slope)), seas])


# Affine map from features to logits. Row 0 = identity expert, 1 = trend,
# 2 = seasonal. The bias column is calibrated below so the hero series
# reproduces the paper's published ID1 gate weights exactly.
GATE_W = np.array([
    [0.0, -0.80, -0.75],
    [0.0,  1.55, -0.30],
    [0.0, -0.40,  1.90],
])
GATE_B = np.zeros(3)          # replaced at import time by _calibrate()


def gate(window, bias=None):
    f = gate_features(window)
    logits = GATE_W @ f + (GATE_B if bias is None else bias)
    z = logits - logits.max()
    e = np.exp(z)
    return e / e.sum()


# ─────────────────────────────────────────────────────────────────────────
# The hero series — Figure 5, panel ID1
# ─────────────────────────────────────────────────────────────────────────

# Component magnitudes read off Figure 5's ID1 column: identity 122-127,
# trend 0.4-0.9 (N-BEATS-MoE), seasonality 0-15. The seasonal coefficients are
# the Fourier form of a 7.5-amplitude annual cycle troughing at the start of
# the horizon and peaking near its end, which is the shape the ID1 panel shows.
HERO = Series(level=124.6, drift=-0.4, wobble=2.35, phase=0.60, freq=4.0,
              trend=(0.45, 0.62, -0.15),
              seas_const=7.5, seas_cos=(-7.244,), seas_sin=(-1.941, 0.9),
              resid=2.6, seed=7)

# Published for ID1 (Figure 5 caption).
HERO_GATE = np.array([0.275, 0.169, 0.556])
HERO_SMAPE_NBEATS = 7.34
HERO_SMAPE_MOE = 2.68

# What plain N-BEATS gets wrong on this series, per §4.5 of the paper: it
# "overestimates this component's importance, exaggerating its scale to around
# [1, 3]", and it models the seasonal swings less sharply.
TREND_OVERSCALED = (1.05, 2.10, -0.20)
SEAS_DAMPING = 0.35
SEAS_PHASE_ERR = 1.6


def nbeats_trend(tau):
    return trend_basis(tau, TREND_OVERSCALED)


def nbeats_seasonal(tau):
    """The baseline's seasonal stack: damped, and slightly out of phase."""
    tau = np.asarray(tau, dtype=float) + SEAS_PHASE_ERR
    p = HERO.p
    base = seasonal_basis(tau, 0.0, p["seas_cos"], p["seas_sin"])
    return p["seas_const"] + SEAS_DAMPING * base


def nbeats_forecast(tau):
    return HERO.identity(tau) + nbeats_trend(tau) + nbeats_seasonal(tau)


def moe_forecast(tau):
    """The gated model recovers the clean components; only the residual is
    left over, which is what its 2.68% SMAPE measures."""
    return HERO.clean(tau)


def smape(y, yhat):
    """SMAPE in percent, M4-competition convention (paper Eq. 4)."""
    y, yhat = np.asarray(y, float), np.asarray(yhat, float)
    return 200.0 * np.mean(np.abs(y - yhat) / (np.abs(y) + np.abs(yhat)))


# ─────────────────────────────────────────────────────────────────────────
# Ensembles for §3: mixed-domain vs single-domain
# ─────────────────────────────────────────────────────────────────────────

def m1_like(n=7, seed=11):
    """Heterogeneous: mixed domains, so scale, trend and seasonality all vary
    widely from series to series (M1/M3/M4 are drawn from many domains)."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        kind = i % 3
        if kind == 0:            # strongly trending, weak season
            tr = (0.5, rng.uniform(9.0, 16.0), rng.uniform(-1.5, 1.5))
            amp = rng.uniform(0.3, 1.2)
        elif kind == 1:          # strongly seasonal, flat
            tr = (0.4, rng.uniform(-0.6, 0.6), 0.1)
            amp = rng.uniform(9.0, 15.0)
        else:                    # mostly level, little of either
            tr = (0.4, rng.uniform(-1.2, 1.2), 0.1)
            amp = rng.uniform(1.5, 3.5)
        out.append(Series(
            level=float(rng.uniform(40.0, 900.0)),
            drift=float(rng.uniform(-1.5, 1.5)),
            wobble=float(rng.uniform(1.0, 3.0)),
            phase=float(rng.uniform(0, 2 * np.pi)),
            trend=tr,
            seas_const=amp * 0.5,
            seas_cos=(-amp * 0.75,),
            seas_sin=(amp * 0.7, amp * 0.25),
            resid=float(rng.uniform(0.6, 1.8)), seed=100 + i))
    return out


def tourism_like(n=7, seed=23):
    """Homogeneous: one domain. Every series has the same broad shape — a
    mild trend under a strong annual cycle — so the gate sees nearly the same
    features every time."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(n):
        amp = float(rng.uniform(9.5, 11.5))
        out.append(Series(
            level=float(rng.uniform(180.0, 260.0)),
            drift=float(rng.uniform(-0.8, 0.8)),
            wobble=float(rng.uniform(1.6, 2.4)),
            phase=float(rng.uniform(0, 2 * np.pi)),
            trend=(0.5, float(rng.uniform(2.0, 3.2)), 0.2),
            seas_const=amp * 0.5,
            seas_cos=(-amp * 0.72,),
            seas_sin=(amp * 0.68, amp * 0.22),
            resid=float(rng.uniform(0.8, 1.3)), seed=200 + i))
    return out


# ─────────────────────────────────────────────────────────────────────────
# Table 4 — expert selection ratios by STL component (monthly frequency)
# ─────────────────────────────────────────────────────────────────────────

TABLE4 = {
    "M3": {"Trend":    (0.19, 0.55, 0.26),
           "Seasonal": (0.18, 0.37, 0.45),
           "Residual": (0.23, 0.52, 0.25)},
    "M1": {"Trend":    (0.31, 0.01, 0.68),
           "Seasonal": (0.44, 0.25, 0.31),
           "Residual": (0.48, 0.24, 0.28)},
}

# Table 3 — N-BEATS-MoE vs N-BEATS, per dataset/frequency. True = MoE wins.
RECORD_MIXED = [("M1", "Yearly", True), ("M1", "Quarterly", True),
                ("M1", "Monthly", True), ("M3", "Yearly", False),
                ("M3", "Quarterly", False), ("M3", "Monthly", True),
                ("M4", "Yearly", True), ("M4", "Quarterly", True),
                ("M4", "Monthly", False)]
RECORD_TOURISM = [("Tourism", "Yearly", False),
                  ("Tourism", "Quarterly", False),
                  ("Tourism", "Monthly", False)]


# ─────────────────────────────────────────────────────────────────────────
# Calibration: shift the gate bias so the hero series lands on the paper's
# published weights. softmax(l + d) = target  <=>  d = log(target) - l + c,
# so this is exact and leaves the linear part of the layer untouched.
# ─────────────────────────────────────────────────────────────────────────

def _calibrate():
    global GATE_B
    logits = GATE_W @ gate_features(HERO.window())
    d = np.log(HERO_GATE) - logits
    GATE_B = d - d.mean()


_calibrate()
