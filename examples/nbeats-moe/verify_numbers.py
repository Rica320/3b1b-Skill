"""Check everything the video asserts numerically, before rendering it.

    python verify_numbers.py

Run this whenever nbeats_data.py changes. It is the guard against animating a
claim the data does not support.
"""

import numpy as np
import nbeats_data as D

FAIL = []


def check(name, ok, detail):
    print(f"  [{'ok ' if ok else 'FAIL'}] {name}: {detail}")
    if not ok:
        FAIL.append(name)


def span(f, lo=1, hi=D.H, n=80):
    v = f(np.linspace(lo, hi, n))
    return float(v.min()), float(v.max())


print("Figure 5, ID1 — component magnitudes over the horizon")
a, b = span(D.HERO.identity)
check("identity ~ [122,127]", 121.0 <= a and b <= 128.0, f"[{a:.1f}, {b:.1f}]")
a, b = span(D.HERO.trend)
check("gated trend ~ [0.4,0.9]", 0.3 <= a and b <= 1.0, f"[{a:.2f}, {b:.2f}]")
a, b = span(D.nbeats_trend)
check("plain trend ~ [1,3]", 0.9 <= a and b <= 3.1, f"[{a:.2f}, {b:.2f}]")
a, b = span(D.HERO.seasonal)
check("seasonality ~ [0,15]", a <= 2.0 and 14.0 <= b <= 17.0, f"[{a:.2f}, {b:.2f}]")

print("\nGate — softmax(Linear(LayerNorm(x0))), paper Eq. 3")
g = D.gate(D.HERO.window())
check("hero == published (0.275, 0.169, 0.556)",
      np.allclose(g, D.HERO_GATE, atol=5e-4),
      f"{np.round(g, 3).tolist()}")
check("weights sum to 1", abs(g.sum() - 1.0) < 1e-9, f"{g.sum():.6f}")

print("\nForecast error on the hero series")
t = D.HERO.horizon_idx()
truth = D.HERO.truth()
s_nb = D.smape(truth, D.nbeats_forecast(t))
s_moe = D.smape(truth, D.moe_forecast(t))
check("baseline is the worse of the two", s_nb > s_moe,
      f"reconstruction: N-BEATS {s_nb:.2f}%  vs  MoE {s_moe:.2f}%")
ratio, paper_ratio = s_nb / s_moe, D.HERO_SMAPE_NBEATS / D.HERO_SMAPE_MOE
check("error ratio tracks the paper's", abs(ratio - paper_ratio) < 0.35,
      f"{ratio:.2f} vs {paper_ratio:.2f} reported "
      f"({D.HERO_SMAPE_NBEATS}/{D.HERO_SMAPE_MOE})")

print("\nGate behaviour across ensembles (the §3 claim)")
res = {}
for nm, fn in [("mixed-domain (M1-like)", D.m1_like),
               ("single-domain (Tourism-like)", D.tourism_like)]:
    G = np.array([D.gate(s.window()) for s in fn()])
    swing = float(np.abs(np.diff(G, axis=0)).mean())
    res[nm] = swing
    print(f"    {nm:30s} mean series-to-series swing {swing:.3f}"
          f"   max weight {G.max():.2f}")
check("mixed-domain bars swing much more",
      res["mixed-domain (M1-like)"] > 4 * res["single-domain (Tourism-like)"],
      f"{res['mixed-domain (M1-like)']:.3f} vs "
      f"{res['single-domain (Tourism-like)']:.3f}")
Gm = np.array([D.gate(s.window()) for s in D.m1_like()])
check("no bar saturates to one-hot", Gm.max() < 0.93, f"max {Gm.max():.3f}")

print("\nPaper tables")
for ds, rows in D.TABLE4.items():
    for comp, v in rows.items():
        check(f"Table 4 {ds}/{comp} sums to 1", abs(sum(v) - 1.0) < 0.011,
              f"{v} -> {sum(v):.2f}")
wins = sum(w for _, _, w in D.RECORD_MIXED)
check("Table 3 mixed-domain record is 6/9", wins == 6, f"{wins}/9")
check("Table 3 Tourism record is 0/3",
      sum(w for _, _, w in D.RECORD_TOURISM) == 0, "0/3")

print("\nRanges the scene has to plot inside")
obs = D.HERO.observed(np.arange(-D.N_HIST, D.H + 1))
print(f"    observed series   [{obs.min():.1f}, {obs.max():.1f}]")
print(f"    horizon truth     [{truth.min():.1f}, {truth.max():.1f}]")
print(f"    nbeats forecast   [{D.nbeats_forecast(t).min():.1f}, "
      f"{D.nbeats_forecast(t).max():.1f}]")
print(f"    moe forecast      [{D.moe_forecast(t).min():.1f}, "
      f"{D.moe_forecast(t).max():.1f}]")

print("\n" + ("ALL CHECKS PASSED" if not FAIL
              else f"{len(FAIL)} FAILED: {', '.join(FAIL)}"))
raise SystemExit(1 if FAIL else 0)
