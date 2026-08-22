"""
The market the video is about — computed, not drawn.

Everything the animation shows and everything the narration claims comes from
this module: the panel of stock prices, the momentum ranking, every backtest,
and the landscape those backtests trace out. Nothing in the scene is a
hand-authored keyframe, so the pictures cannot drift away from the arithmetic
(narrative_template.md §3: "prefer a metaphor that is literally true").

This is a SIMULATED market, not real data. It is simulated because the point of
the video is a mechanism, and a mechanism is only visible if you control what
went in. Three things go in, and each one is a documented effect that momentum
research keeps finding in real returns:

  DIFFUSION   news arrives once but is priced in over J months. A stock that
              rose last month is still absorbing the same news this month, so
              returns are positively autocorrelated at horizons up to J.
              -> continuation at intermediate lookbacks.

  OVERSHOOT   sentiment builds on the same news and decays slowly (AR(1),
              phi=0.975, half-life ~27 months). The price overshoots the
              fundamental and then gives it back over years.
              -> reversal at long lookbacks.

  BOUNCE      an i.i.d. transient error in each month's price (the bid-ask
              bounce and the rest of the microstructure). It is in this month's
              price and gone from next month's, which makes one-month returns
              negatively autocorrelated.
              -> reversal at a one-month lookback.

Every stock has all three. So "momentum" and "mean reversion" are not two
markets: they are the same market read over different horizons, which is the
argument the video makes.

Run it directly for the summary the narration is written against:

    python panel.py
"""

import numpy as np
from pathlib import Path

# ── parameters ───────────────────────────────────────────────────────────
SEED = 7

T = 3000                # months of history (a simulation, so we can afford it)
N = 240                 # stocks in the cross-section
DECILE = 0.10           # long the top 10%, short the bottom 10%

# DIFFUSION: news is priced in over J months with geometrically decaying
# weights. rho < 1 means most of it lands early and the tail is what a
# momentum sort is picking up.
J = 16
RHO = 0.88
SIG_NEWS = 0.055        # monthly, log

# OVERSHOOT: sentiment loads on the same news and unwinds slowly.
PHI = 0.975             # half-life ln(0.5)/ln(PHI) ~= 27 months
C_SENT = 1.10           # how much of each news shock becomes overshoot

# BOUNCE: a transient price error, in this month's price and out of the next.
SIG_BOUNCE = 0.026

# The part of a price that is simply unpredictable: a random walk with no
# autocorrelation at any lag. It contributes nothing to the shape of the
# landscape and everything to its scale -- it is noise in the ranking and noise
# in the payoff, which is why a real decile spread is a fraction of a percent a
# month rather than the several percent a clean simulation would give.
SIG_IDIO = 0.16

# The market factor. Both legs of a long-short ride it, so it cancels -- the
# betas are near-identical on purpose, so that cancellation is exact enough to
# claim on screen.
MKT_DRIFT = 0.006
MKT_VOL = 0.042
BETA_SPREAD = 0.06

# The grid of strategies. Every (k, h) pair is one complete backtest.
K_VALUES = np.arange(1, 49)      # lookback, months
H_VALUES = np.arange(1, 25)      # holding period, months

# The strategies the video names.
K_STAR, H_STAR = 6, 1            # the brief's rule: six-month signal, rebalanced monthly
K_SHORT, H_SHORT = 1, 1          # one month, held one month: reversal
K_LONG, H_LONG = 48, 24          # four years, held two: reversal again

_CACHE = Path(__file__).resolve().parent / "cache" / "landscape.npz"


# ── the panel ────────────────────────────────────────────────────────────

def _weights():
    """Geometric diffusion weights, normalised so all news is eventually in."""
    w = RHO ** np.arange(J)
    return w / w.sum()


def build(seed=SEED):
    """The whole market, as log prices of shape (T, N)."""
    rng = np.random.default_rng(seed)

    # One news process per stock, and three ways the price responds to it.
    news = rng.normal(0.0, SIG_NEWS, size=(T + J, N))

    # DIFFUSION: this month's return is a weighted sum of the last J months of
    # news. Positive autocorrelation out to lag J-1, and nothing beyond it.
    w = _weights()
    r_news = np.zeros((T, N))
    for j, wj in enumerate(w):
        r_news += wj * news[J - 1 - j: J - 1 - j + T]

    # OVERSHOOT: an AR(1) in the same news. It is a level, not a return, so
    # what it does to prices is build up and then hand back.
    sent = np.zeros((T, N))
    n_now = news[J - 1: J - 1 + T]
    for t in range(1, T):
        sent[t] = PHI * sent[t - 1] + C_SENT * n_now[t]

    # BOUNCE: in this month's price, out of next month's.
    bounce = rng.normal(0.0, SIG_BOUNCE, size=(T, N))

    idio = np.cumsum(rng.normal(0.0, SIG_IDIO, size=(T, N)), axis=0)

    market = np.cumsum(rng.normal(MKT_DRIFT, MKT_VOL, size=T))
    beta = 1.0 + rng.normal(0.0, BETA_SPREAD, size=N)

    log_p = (np.cumsum(r_news, axis=0)      # the fundamental, priced in slowly
             + sent                          # the overshoot, given back slowly
             + bounce                        # today's noise, gone tomorrow
             + idio                          # the part nothing can predict
             + np.outer(market, beta))       # the weather

    return {
        "log_p": log_p,
        "price": 40.0 * np.exp(log_p - log_p[0]),
        "market": market,
        "beta": beta,
    }


# ── the strategy ─────────────────────────────────────────────────────────

def signal(log_p, t, k):
    """M_t = P_t / P_{t-k} - 1, for every stock, as of month t.

    Returned as a simple return so it is the quantity in the video's formula;
    the ranking is identical either way.
    """
    return np.exp(log_p[t] - log_p[t - k]) - 1.0


def legs(m, decile=DECILE):
    """Indices of the strongest and the weakest `decile` of the cross-section."""
    n_side = max(1, int(round(decile * len(m))))
    order = np.argsort(m)
    return order[-n_side:][::-1], order[:n_side]


def _sides(log_p, k, decile=DECILE):
    """Long/short membership at every month, from the k-month ranking.

    Split out because the ranking depends only on k: computing it once per
    lookback rather than once per (k, h) pair is what makes the whole 1152-cell
    landscape a few seconds instead of a few minutes.
    """
    T_, N_ = log_p.shape
    n_side = max(1, int(round(decile * N_)))
    past = log_p[k:] - log_p[:-k]                        # (T-k, N)
    rank = np.argsort(np.argsort(past, axis=1), axis=1)
    return (rank >= N_ - n_side).astype(float) - (rank < n_side), n_side


def backtest(log_p, k, h, decile=DECILE, sides=None):
    """Average monthly return of the long-short portfolio, in percent.

    Rebalanced every month (overlapping holding periods, which is the standard
    way to use every observation), long the top decile of the k-month return,
    short the bottom decile, held h months. The market cancels between the legs.
    """
    T_ = log_p.shape[0]
    if sides is None:
        sides, n_side = _sides(log_p, k, decile)
    else:
        n_side = max(1, int(round(decile * log_p.shape[1])))

    w = sides[:T_ - k - h]                               # aligned at t = k..T-h
    fut = log_p[k + h:] - log_p[k:T_ - h]                # what it pays
    return 100.0 * float((w * fut).sum(1).mean()) / (n_side * h)


def turnover(sides, h, decile=DECILE):
    """Units traded per unit of capital at each rebalance.

    Computed, not assumed: it compares the decile you would hold now with the
    one you held h months ago, and counts every name that has to be bought or
    sold to get from one to the other. A book that is replaced completely
    trades 4.0 -- sell the old longs, buy the new ones, cover the old shorts,
    short the new ones -- against a 1-long-1-short unit of capital.

    A six-month signal rebalanced monthly churns most of the book every month;
    a four-year signal held two years barely moves. That difference is the
    whole reason the cost surface tilts rather than just dropping.
    """
    n_side = max(1, int(round(decile * sides.shape[1])))
    traded = np.abs(sides[h:] - sides[:-h]).sum(1)
    return float(traded.mean() / n_side)


def landscape(log_p=None, ks=K_VALUES, hs=H_VALUES, use_cache=True, cost=0.0):
    """backtest() at every (k, h): the surface the video is about.

    Shape (len(ks), len(hs)), in percent per month. `cost` is charged in
    percent of the traded amount, one way, on the fraction of the book that
    actually turns over -- so it lands as `cost * turnover / h` percent a
    month and falls hardest on the left edge of the map, where you rebalance
    most often. Cached because the scene builds it at import time and a
    re-render should not pay for it again.
    """
    key = f"grid_{cost:.3f}"
    if use_cache and _CACHE.exists():
        z = np.load(_CACHE)
        if (key in z and len(z["ks"]) == len(ks) and (z["ks"] == ks).all()
                and len(z["hs"]) == len(hs) and (z["hs"] == hs).all()):
            return z[key]

    log_p = build()["log_p"] if log_p is None else log_p
    grid = np.empty((len(ks), len(hs)))
    for i, k in enumerate(ks):
        sides, _ = _sides(log_p, int(k))
        for j, h in enumerate(hs):
            gross = backtest(log_p, int(k), int(h), sides=sides)
            drag = cost * turnover(sides, int(h)) / h if cost else 0.0
            grid[i, j] = gross - drag

    _CACHE.parent.mkdir(parents=True, exist_ok=True)
    old = dict(np.load(_CACHE)) if _CACHE.exists() else {}
    old.update({key: grid, "ks": np.asarray(ks), "hs": np.asarray(hs)})
    np.savez(_CACHE, **old)
    return grid


# ── reading the landscape ────────────────────────────────────────────────

def height(grid, k, h, ks=K_VALUES, hs=H_VALUES):
    """Bilinear interpolation of the grid at real-valued (k, h).

    The surface mobject samples this thousands of times, so it stays cheap and
    it is the same array the numbers in the narration come from.
    """
    ki = np.clip(np.interp(k, ks, np.arange(len(ks))), 0, len(ks) - 1)
    hi = np.clip(np.interp(h, hs, np.arange(len(hs))), 0, len(hs) - 1)
    k0, h0 = int(np.floor(ki)), int(np.floor(hi))
    k1, h1 = min(k0 + 1, len(ks) - 1), min(h0 + 1, len(hs) - 1)
    fk, fh = ki - k0, hi - h0
    return float(
        grid[k0, h0] * (1 - fk) * (1 - fh) + grid[k1, h0] * fk * (1 - fh)
        + grid[k0, h1] * (1 - fk) * fh + grid[k1, h1] * fk * fh
    )


def ridge(grid, hs=H_VALUES, ks=K_VALUES):
    """For each holding period, the lookback that pays most: the ridge line."""
    return ks[grid.argmax(axis=0)]


# ── the numbers the narration quotes ──────────────────────────────────────

def facts(m=None, grid=None):
    m = m or build()
    log_p = m["log_p"]
    grid = landscape(log_p) if grid is None else grid

    i_star = list(K_VALUES).index(K_STAR), list(H_VALUES).index(H_STAR)
    peak = np.unravel_index(grid.argmax(), grid.shape)

    # Autocorrelation of monthly returns, which is where the whole shape comes
    # from: negative at lag 1 (bounce), positive out to J (diffusion).
    r = np.diff(log_p, axis=0)
    r = r - r.mean(axis=0)
    ac = [float((r[:-l] * r[l:]).mean() / r.var()) for l in range(1, 7)]

    # How much of the strategy's return is the market? The long-short beta.
    mkt_r = np.diff(m["market"])

    return {
        "T": T, "N": N,
        "one_month": backtest(log_p, 1, 1),
        "six_one": grid[i_star],
        "twelve_one": backtest(log_p, 12, 1),
        "four_year": backtest(log_p, 48, 24),
        "peak_k": int(K_VALUES[peak[0]]), "peak_h": int(H_VALUES[peak[1]]),
        "peak": float(grid[peak]),
        "worst": float(grid.min()),
        "worst_k": int(K_VALUES[np.unravel_index(grid.argmin(), grid.shape)[0]]),
        "worst_h": int(H_VALUES[np.unravel_index(grid.argmin(), grid.shape)[1]]),
        "frac_positive": float((grid > 0).mean()),
        "autocorr": ac,
        "market_move": float(np.exp(m["market"][-1] - m["market"][0])),
        "mkt_vol_annual": float(mkt_r.std() * np.sqrt(12) * 100),
        "diffusion_months": J,
        "overshoot_halflife": float(np.log(0.5) / np.log(PHI)),
    }


if __name__ == "__main__":
    m = build()
    grid = landscape(m["log_p"])
    f = facts(m, grid)

    print(f"{f['N']} stocks, {f['T']} months, deciles at {DECILE:.0%}\n")
    print("  monthly return autocorrelation (lags 1-6)")
    print("   ", "  ".join(f"{a:+.3f}" for a in f["autocorr"]))
    print(f"    news is priced in over {f['diffusion_months']} months; "
          f"the overshoot half-life is {f['overshoot_halflife']:.0f} months\n")

    print("  the long-short strategy, percent per month")
    print(f"    k= 1  h= 1   {f['one_month']:+.2f}   one-month reversal")
    print(f"    k= 6  h= 1   {f['six_one']:+.2f}   the brief's rule")
    print(f"    k=12  h= 1   {f['twelve_one']:+.2f}")
    print(f"    k=48  h=24   {f['four_year']:+.2f}   long-horizon reversal")
    print(f"    best  k={f['peak_k']:>2}  h={f['peak_h']:>2}   {f['peak']:+.2f}")
    print(f"    worst k={f['worst_k']:>2}  h={f['worst_h']:>2}   {f['worst']:+.2f}")
    print(f"    {f['frac_positive']:.0%} of the {grid.size} strategies "
          f"on the grid make money\n")

    print("  the ridge: best lookback for each holding period")
    rk = ridge(grid)
    for i, h in enumerate(H_VALUES):
        if h in (1, 2, 3, 6, 12, 18, 24):
            print(f"    h={h:>2}  ->  k={rk[i]:>2}   {grid[:, i].max():+.2f}")

    print("\n  the k-slice at h=3 (what the flat argument is about)")
    hi = list(H_VALUES).index(3)
    for k in (1, 2, 3, 6, 9, 12, 18, 24, 36, 48):
        ki = list(K_VALUES).index(k)
        print(f"    k={k:>2}  {grid[ki, hi]:+.2f}")
