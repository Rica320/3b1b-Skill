"""
The market the video is about — computed, not drawn.

Everything the animation shows and everything the narration claims comes from
this module: the two price paths, the spread, the rolling band, the z-score,
the trades and their P&L. Nothing in the scene is a hand-authored keyframe, so
the pictures cannot drift away from the arithmetic (narrative_template.md §3:
"prefer a metaphor that is literally true").

The spread is a piecewise Ornstein-Uhlenbeck process, which is the standard
continuous-time model of a mean-reverting series:

    ds = theta * (mu - s) dt + sigma dW

Three regimes, and each one exists to force a section of the argument:

  CALM  (day   0-170)  strong pull, small shocks -> the gap swings a few tens
                       of cents. A fixed dollar threshold never fires here.
  WILD  (day 170-300)  same pull, shocks five times bigger -> the gap swings
                       a few dollars. The same fixed threshold now fires
                       constantly. This is what kills the dollar threshold and
                       forces a unit that comes from the pair's own history.
  BREAK (day 300-420)  theta = 0. The pull is gone: what is left is a random
                       walk with a downward drift. The relationship has not
                       stretched, it has ended -- and the rolling mean, which
                       is all the z-score knows about "normal", follows the
                       spread down and reports that everything is fine.

Run it directly for the summary the narration is written against:

    python market.py
"""

import numpy as np

# ── parameters ───────────────────────────────────────────────────────────
SEED = 11

DAYS = 420
WINDOW = 60             # trailing days in the rolling mean and rolling sd
BETA = 1.12             # shares of B that match one share of A
COST = 0.20             # dollars of spread per round trip (both legs)

Z_ENTRY = 2.0
Z_EXIT = 0.5

# (first_day, last_day, theta, sigma, drift)  — theta = 0 is a random walk
REGIMES = [
    ("calm",  0,   170, 0.060, 0.100,  0.0),
    ("wild",  170, 300, 0.060, 0.550,  0.0),
    ("break", 300, 420, 0.000, 0.350, -0.075),
]

# The day the regime break begins; §4 of the video is everything after it.
BREAK_DAY = 300

# The dollar threshold §1 tries and abandons.
DOLLAR_THRESHOLD = 2.0


# ── the series ───────────────────────────────────────────────────────────

def _spread(rng):
    """Piecewise OU. Continuous at the joins: each regime starts where the
    last one ended, so the break is a change in behaviour, not a jump."""
    s = np.zeros(DAYS)
    for _, lo, hi, theta, sigma, drift in REGIMES:
        for t in range(max(lo, 1), hi):
            s[t] = (s[t - 1] + theta * (0.0 - s[t - 1]) + drift
                    + sigma * rng.standard_normal())
    return s


def build():
    """The whole market, as one dict of arrays indexed by trading day."""
    rng = np.random.default_rng(SEED)

    # A common factor both stocks ride: this is the part a pairs trade is
    # built to ignore, and it has to be big enough on screen that ignoring it
    # is visibly the point (sd of the walk is ~9 dollars over the year, while
    # the spread swings a couple of dollars at most).
    market = np.cumsum(rng.normal(0.02, 0.45, DAYS))

    spread = _spread(rng)
    p_b = 44.0 + market + rng.normal(0.0, 0.09, DAYS).cumsum() * 0.35
    p_a = BETA * p_b + spread

    mu, sd = _rolling(spread, WINDOW)
    with np.errstate(invalid="ignore", divide="ignore"):
        z = (spread - mu) / sd

    return {
        "day": np.arange(DAYS),
        "p_a": p_a,
        "p_b": p_b,
        "b_scaled": BETA * p_b,       # what the eye compares P_A against
        "spread": spread,
        "mu": mu,
        "sd": sd,
        "z": z,
        "trades": trades(spread, z),
    }


def _rolling(x, window):
    """Trailing mean and (population) sd. NaN until the window is full."""
    mu = np.full_like(x, np.nan)
    sd = np.full_like(x, np.nan)
    for t in range(window - 1, len(x)):
        w = x[t - window + 1:t + 1]
        mu[t] = w.mean()
        sd[t] = w.std()
    return mu, sd


# ── the strategy ─────────────────────────────────────────────────────────

def trades(spread, z, z_entry=Z_ENTRY, z_exit=Z_EXIT, cost=COST):
    """Enter when |z| > z_entry, close when |z| falls back under z_exit.

    Short the spread when it is stretched high, long it when stretched low;
    the P&L of one round trip is how far the spread travelled back toward the
    mean, less the cost of getting in and out. An open position at the end of
    the data is closed on the last day.
    """
    out, side, i_in = [], 0, 0
    for t in range(len(z)):
        if np.isnan(z[t]):
            continue
        if side == 0:
            if z[t] > z_entry:
                side, i_in = -1, t
            elif z[t] < -z_entry:
                side, i_in = +1, t
        elif abs(z[t]) < z_exit or t == len(z) - 1:
            gross = side * (spread[t] - spread[i_in])
            out.append({
                "entry": i_in, "exit": t, "side": side,
                "z_in": float(z[i_in]), "z_out": float(z[t]),
                "s_in": float(spread[i_in]), "s_out": float(spread[t]),
                "gross": float(gross), "net": float(gross - cost),
            })
            side = 0
    return out


def split(trs, day=BREAK_DAY):
    """Trades entered before the relationship broke, and after."""
    return ([t for t in trs if t["entry"] < day],
            [t for t in trs if t["entry"] >= day])


# ── the numbers the narration quotes ──────────────────────────────────────

def facts(m=None):
    m = m or build()
    s, z, mu, sd = m["spread"], m["z"], m["mu"], m["sd"]
    before, after = split(m["trades"])

    calm = slice(WINDOW, 170)
    wild = slice(170, 300)
    brk = slice(BREAK_DAY, DAYS)

    # Where the spread is furthest from where it started, after the break.
    t_low = int(BREAK_DAY + np.argmin(s[brk]))

    return {
        "calm_sd": float(np.nanmean(sd[calm])),
        "wild_sd": float(np.nanmean(sd[wild])),
        "calm_max_abs": float(np.abs(s[calm]).max()),
        "wild_max_abs": float(np.abs(s[wild]).max()),
        "dollar_fires_calm": int((np.abs(s[calm]) > DOLLAR_THRESHOLD).sum()),
        "dollar_fires_wild": int((np.abs(s[wild]) > DOLLAR_THRESHOLD).sum()),
        "n_trades": len(m["trades"]),
        "n_before": len(before),
        "n_after": len(after),
        "pnl_before": float(sum(t["net"] for t in before)),
        "pnl_after": float(sum(t["net"] for t in after)),
        "win_rate_before": (sum(t["net"] > 0 for t in before) / len(before)
                            if before else float("nan")),
        "cost_frac_calm": COST / (2 * float(np.nanmean(sd[calm]))),
        "cost_frac_wild": COST / (2 * float(np.nanmean(sd[wild]))),
        "spread_at_low": float(s[t_low]),
        "z_at_low": float(z[t_low]),
        "mu_at_low": float(mu[t_low]),
        "day_at_low": t_low,
        "market_range": float(m["p_b"].max() - m["p_b"].min()),
        "spread_range_all": float(s.max() - s.min()),
    }


if __name__ == "__main__":
    m = build()
    f = facts(m)
    print(f"{DAYS} days, window {WINDOW}, beta {BETA}, cost ${COST:.2f}/trip\n")
    print("  the gap's own size")
    print(f"    calm  sd ${f['calm_sd']:.2f}   largest gap ${f['calm_max_abs']:.2f}")
    print(f"    wild  sd ${f['wild_sd']:.2f}   largest gap ${f['wild_max_abs']:.2f}")
    print(f"    a ${DOLLAR_THRESHOLD:.0f} line fires on {f['dollar_fires_calm']} "
          f"calm days and {f['dollar_fires_wild']} wild days")
    print("\n  cost as a share of a two-sigma move")
    print(f"    calm {100 * f['cost_frac_calm']:.0f}%    "
          f"wild {100 * f['cost_frac_wild']:.0f}%")
    print("\n  trades")
    print(f"    before the break: {f['n_before']}  net ${f['pnl_before']:+.2f}  "
          f"win rate {100 * f['win_rate_before']:.0f}%")
    print(f"    after  the break: {f['n_after']}  net ${f['pnl_after']:+.2f}")
    print("\n  the break")
    print(f"    day {f['day_at_low']}: spread ${f['spread_at_low']:.2f}, "
          f"rolling mean ${f['mu_at_low']:.2f}, z = {f['z_at_low']:+.2f}")
    print(f"    the market moved ${f['market_range']:.0f} over the year; "
          f"the gap moved ${f['spread_range_all']:.2f}")
    print("\n  every trade")
    for t in m["trades"]:
        print(f"    d{t['entry']:>3}->{t['exit']:>3}  "
              f"{'short' if t['side'] < 0 else 'long ':<5} "
              f"z {t['z_in']:+.2f} -> {t['z_out']:+.2f}   "
              f"spread ${t['s_in']:+.2f} -> ${t['s_out']:+.2f}   "
              f"net ${t['net']:+.2f}")
