"""
Check every number the narration says out loud against panel.py.

script.yaml is the only place the spoken words exist, and panel.py is the only
place the arithmetic exists. This file is the join: it re-derives each quoted
figure from the market and fails if the script and the data have drifted apart.
It reads the numbers out of script.yaml itself where it can, so editing a line
without re-checking the maths is caught here rather than in a render.

    ../../env/bin/python verify_panel.py
"""

import re
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel as pn

COST = 0.10                      # what momentum.py charges, one way
SCRIPT = Path(__file__).resolve().parent / "script.yaml"

_LOGP = pn.build()["log_p"]
_GROSS = pn.landscape(_LOGP)
_NET = pn.landscape(_LOGP, cost=COST)


def g(k, h, grid=None):
    grid = _GROSS if grid is None else grid
    return float(grid[pn.K_VALUES.tolist().index(k),
                      pn.H_VALUES.tolist().index(h)])


def spoken(beat_id):
    """The words of one beat, as they will be said."""
    doc = yaml.safe_load(SCRIPT.read_text())
    for b in doc["beats"]:
        if b["id"] == beat_id:
            return re.sub(r"\[\[[0-9.]+\]\]", " ", " ".join(b["text"].split()))
    raise KeyError(beat_id)


CHECKS = []


def check(name, claim, value, expect, tol=0.005, beat=None, phrase=None):
    """One spoken claim against one computed number."""
    if isinstance(value, (bool, np.bool_)) or isinstance(expect, bool):
        ok = bool(value) == bool(expect)
    else:
        ok = abs(float(value) - float(expect)) <= tol
    if beat is not None and phrase is not None:
        said = phrase.lower() in spoken(beat).lower()
        if not said:
            ok = False
            claim += f"   [NOT IN {beat}: {phrase!r}]"
    CHECKS.append((ok, name, claim, value, expect))


# ── §1  the rule, and the number that breaks it ──────────────────────────
# §1 runs the rule at h = 1 throughout -- rebalanced monthly -- so every
# number the section says out loud has to come from the h = 1 column.
check("6-month rule", "+1.09% a month", g(6, 1), 1.09,
      beat="s1.result", phrase="one point zero nine percent a month")
check("1-month lookback", "-0.55, the sign flips", g(1, 1), -0.55,
      beat="s1.one", phrase="minus zero point five five")
check("4-year lookback", "-0.10, and it flips again", g(48, 1), -0.10,
      beat="s1.four", phrase="minus zero point one zero")

# ── §2  the second parameter ─────────────────────────────────────────────
check("held one month", "+1.09", g(6, 1), 1.09,
      beat="s2.hold", phrase="one point zero nine")
check("six-month peak beats k=1", "the same rule, opposite signs",
      g(6, 1) > 0 > g(1, 1), True, tol=0)
check("held two years", "+0.06", g(6, 24), 0.06,
      beat="s2.hold", phrase="six hundredths")
check("grid size", "1152 backtests", _GROSS.size, 1152, tol=0,
      beat="s2.all", phrase="eleven hundred and fifty-two")
check("lookbacks", "48 of them", len(pn.K_VALUES), 48, tol=0,
      beat="s2.all", phrase="forty-eight lookbacks")
check("holding periods", "24 of them", len(pn.H_VALUES), 24, tol=0,
      beat="s2.all", phrase="twenty-four holding periods")

# ── §3  what the map says ────────────────────────────────────────────────
peak = np.unravel_index(_GROSS.argmax(), _GROSS.shape)
check("the peak", "+1.22 a month", _GROSS.max(), 1.22,
      beat="s3.ridge", phrase="one point two two percent a month")
check("peak location", "k=6, h=2", (int(pn.K_VALUES[peak[0]]),
                                    int(pn.H_VALUES[peak[1]])) == (6, 2), True,
      tol=0)
check("the far corner", "loses half a percent", g(48, 24), -0.54,
      beat="s3.corner", phrase="half a percent a month")

# The claim that carries the whole video: the two lowest points on the map are
# the same number, at opposite corners.
lo = np.sort(_GROSS.flatten())[:2]
worst = np.unravel_index(_GROSS.argmin(), _GROSS.shape)
check("two lowest, tied", "both -0.55", abs(lo[0] - lo[1]) < 0.005, True, tol=0,
      beat="s3.tie", phrase="minus zero point five five")
check("lowest is -0.55", "rounds to -0.55", round(float(lo[0]), 2), -0.55, tol=0)
check("second is -0.55", "rounds to -0.55", round(float(lo[1]), 2), -0.55, tol=0)
check("opposite corners", "(1,1) and the far end",
      g(1, 1) - float(lo[1]) < 0.005
      and int(pn.K_VALUES[worst[0]]) >= 40
      and int(pn.H_VALUES[worst[1]]) >= 20, True, tol=0)

# ── §4  the three ingredients, and the slice ─────────────────────────────
check("diffusion horizon", "16 months", pn.J, 16, tol=0,
      beat="s4.diffusion", phrase="sixteen months")
check("overshoot half-life", "years, not months",
      np.log(0.5) / np.log(pn.PHI) > 24, True, tol=0)

# The h = 1 row is the line §4 walks: below zero, over the ridge, below again.
row = _GROSS[:, 0]
crossings = [int(pn.K_VALUES[i]) for i in range(1, len(row))
             if row[i - 1] * row[i] < 0]
check("the slice crosses twice", "under, over, under", len(crossings), 2, tol=0)
check("first crossing", "just past one month", crossings[0] <= 3, True, tol=0)
check("second crossing", "before four years", crossings[-1] >= 30, True, tol=0)
check("slice starts under", "-0.55 at one month", row[0], -0.55)
check("slice peaks over", "+1.09 at six months", g(6, 1), 1.09)
check("slice ends under", "below zero at four years", row[-1] < 0, True, tol=0)

# ── §5  costs ────────────────────────────────────────────────────────────
sides1, _ = pn._sides(_LOGP, 1)
turn = pn.turnover(sides1, 1)
check("one-month turnover", "about 90% of the book replaced",
      round(100 * turn / 4.0), 90, tol=1,
      beat="s5.cost", phrase="ninety percent")
check("notch after costs", "-0.92", g(1, 1, _NET), -0.92,
      beat="s5.sag", phrase="minus ninety-two")
check("peak after costs", "gives up about a tenth",
      _GROSS.max() - _NET.max(), 0.11, tol=0.02)
check("cost rate", "ten basis points", COST, 0.10, tol=0,
      beat="s5.sag", phrase="ten basis points")

# ── the market itself ────────────────────────────────────────────────────
check("stocks", "two hundred and forty", pn.N, 240, tol=0,
      beat="s1.cross", phrase="two hundred and forty stocks")
check("years", "two hundred and fifty", pn.T / 12, 250, tol=0,
      beat="s1.cross", phrase="two hundred and fifty years")


# ── report ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bad = 0
    for ok, name, claim, value, expect in CHECKS:
        v = f"{value:.4g}" if isinstance(value, (int, float)) else str(value)
        e = f"{expect:.4g}" if isinstance(expect, (int, float)) else str(expect)
        print(f"  {'pass' if ok else 'FAIL'}  {name:<24} {claim:<44} "
              f"computed {v:>8}   expected {e}")
        bad += not ok
    print(f"\n{len(CHECKS) - bad}/{len(CHECKS)} checks pass")
    sys.exit(1 if bad else 0)
