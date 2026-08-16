# Who decides how much each piece counts?

A 5:19 explainer of **N-BEATS-MoE** — Matos, Roque & Cerqueira,
*N-BEATS-MOE: N-BEATS with a Mixture-of-Experts Layer for Heterogeneous Time
Series Forecasting* ([arXiv:2508.07490](https://arxiv.org/abs/2508.07490)).

N-BEATS forecasts by decomposition: a level piece, a trend piece, a seasonal
piece, added together. That addition hides a decision — every piece is added
with a coefficient of exactly one, and the same coefficient serves every series
in the dataset. This video is about putting a real number back in front of each
piece and letting the input window choose it.

Silent render, paced to the narration in `SCRIPT.md`, so audio can be layered
on afterwards.

## Run it

```bash
cd examples/nbeats-moe

python verify_numbers.py                                                     # data first

bash ../../skills/3b1b-math-animation/scripts/render.sh nbeats_moe.py NBeatsMoE -l   # draft
bash ../../skills/3b1b-math-animation/scripts/render.sh nbeats_moe.py NBeatsMoE      # 1080p

python ../../skills/3b1b-math-animation/scripts/verify_render.py \
    videos/NBeatsMoE.mp4 --meta render_meta.json

AUDIT=1 manimgl nbeats_moe.py NBeatsMoE -w -o -l    # report texts sharing screen space
```

Run from this directory — `custom_config.yml` is read from the working
directory. No asset preparation is needed.

## The spine

| | |
|---|---|
| **Question** | A forecast is a sum of pieces. Who decides how much each piece counts? |
| **Motivation** | The obvious defence is that the blocks will learn to output something small when a piece doesn't matter. They can't: the blocks are *global*, one set of weights serving 617 series, so their scale is a dataset-wide compromise that is wrong for any individual series. |
| **Build** | Put a real number back in front of each piece and read it off the input window: `Ĝℓ = softmax(Linear(LayerNorm(x₀)))`. A uniform gate reproduces plain N-BEATS exactly, so N-BEATS is this model with the gate frozen at ⅓. |
| **Payoff** | The series does. |

Carried metaphor: **three bars in front of three curves**, on screen from 0:35
to the end. Full meaning table, colour mapping and per-section narration are in
`SCRIPT.md`.

## Everything numeric is computed

`nbeats_data.py` is the data layer; `verify_numbers.py` checks it before a
render is worth starting. Three things are genuinely computed rather than
keyframed:

- **The stack outputs are the real N-BEATS bases** — a polynomial `B(t)` for
  the trend stack and a harmonic Fourier `F(t)` for the seasonal stack, over
  normalised time `t = τ/H`.
- **The gate is a real softmax over a real linear layer** applied to three
  features of the layer-normalised input window. The bars move because the
  series changed, not because a keyframe said so. Calibration makes the hero
  series reproduce the paper's published ID1 weights **exactly**
  (0.275 / 0.169 / 0.556).
- **The §3 spread contrast is measured, not staged.** Mean series-to-series
  weight swing: **0.351** on the mixed-domain ensemble against **0.021** on the
  single-domain one.

### The one number that is quoted rather than computed

The two SMAPE figures on screen — **7.34%** and **2.68%** — are the paper's
measured results for the real ID1 series, not outputs of the reconstruction.

A clean additive reconstruction cannot match both those absolute values and the
published component magnitudes at once: the irreducible residual needed to
produce 2.68% is σ ≈ 6.6, which swamps a seasonal component of amplitude 7.5.
The component magnitudes are what the video makes explicit claims about
(*"[1, 3] versus [0.4, 0.9]"* is quoted from §4.5), so those are matched
exactly, and the baseline's error is tuned to preserve the published **ratio**
instead — 2.69 here against 2.74 reported. `verify_numbers.py` prints both so
the gap stays visible.

## Verification

```
[1] off-frame content ......... pass (0 frames)
[2] blank-frame windows ....... pass (0 windows, 0.0s)
[3] over-long frozen holds .... pass (0)
[4] hard cuts ................. pass (0)
[5] colour reaching screen .... pass (56% of lit pixels saturated)
```

Text-overlap audit: **0 overlaps**, against a detector validated on a
deliberately overlapping nested pair first (a silent zero is that check's
failure mode).

Section boundaries were inspected frame by frame at 51.0s, 106.2s, 169.1s,
235.7s and 287.2s. The three lanes and the three bars persist across all five —
the whole video is one `Scene`, so nothing passes through black.

Narration pacing (words ÷ duration, target ≈ 2.6 w/s):

| Section | Words | Duration | w/s |
|---|---|---|---|
| §0 question | 115 | 51.0s | 2.25 |
| §1 global | 130 | 55.2s | 2.36 |
| §2 gate | 162 | 62.9s | 2.58 |
| §3 evidence | 184 | 66.6s | 2.76 |
| §4 readout | 128 | 51.5s | 2.49 |
| §5 payoff | 68 | 32.1s | 2.12 |
| **total** | **787** | **319.2s** | **2.46** |

## Defects found and fixed during the build

Each was found in the pixels, not in the source:

| Defect | Fix |
|---|---|
| ManimGL's `Axes` crosses at the **data** origin, so a series at 123–140 produced a mobject ~35 units tall | replaced with `Panel`, which maps coordinates directly |
| Lane names rendered *on* the baselines — `next_to(panel, UP)` uses the bounding box, which for a baseline-only panel **is** the baseline | position from the lane's logical top instead |
| Gate readouts frozen at `0.33` for 3 minutes — `ValueTracker`s were created but never bound | `DecimalNumber` with an updater reading the tracker |
| `Ĝℓ` coefficients overlapped their neighbours — transformed in place, so the wider glyphs had no room | rebuild the equation and morph the whole group so layout is recomputed |
| §3 ensemble series (levels 40–900) drawn against the hero's fixed y-range left the panel entirely | `fit_to_panel` — honest, since the gate layer-norms its input anyway |
| The close-up annotation collided with the "617 series, one block" label | retire the label before the crop; push the rest back to 0.05 |
| The payoff text sat on top of the lane-1 readout | moved to the exact slot the opening question used — which also makes the verbatim restatement land in the same place |
| Two enriched narration lines froze the frame past the 11s ceiling | split each in two, with motion in between |
