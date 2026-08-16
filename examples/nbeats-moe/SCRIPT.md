# N-BEATS-MoE — narrative spine

Source: *N-BEATS-MOE: N-BEATS with a Mixture-of-Experts Layer for Heterogeneous
Time Series Forecasting* — Matos, Roque, Cerqueira (arXiv:2508.07490).

Target runtime **≈ 4:40**; the built render came in at **5:19** (787 narration
words at 2.46 w/s) after the narration was enriched to bring every section
inside the pacing band. Silent render, so audio can be layered afterwards.

---

## The spine in one paragraph

N-BEATS forecasts by decomposing: a level piece, a trend piece, a seasonal
piece, added together. That addition hides a decision — every piece is added
with a coefficient of exactly one, and the same coefficient is used for every
series in the dataset. The obvious defence is that the blocks will learn to
output small values when a piece doesn't matter, but they can't: the blocks are
*global*, one set of weights serving thousands of series, so their amplitude is
a dataset-wide compromise that is wrong for any individual series. The fix is to
put a real number back in front of each piece and let that number be read off
the input window by a small gating network. That number is what N-BEATS-MoE
adds. The gains show up on datasets built from many different domains, and not
on the one dataset built from a single domain, where the gate opens to nearly
the same numbers every time. And because those numbers are visible, they double
as an explanation of what the model thinks each series is.

## Driving question

> **"Who decides how much each piece counts?"**

Lands at **0:22**, anchored to three literal `1` coefficients written into the
sum on screen. Restated verbatim at **4:12**.

## The carried metaphor

**Three bars in front of three curves.** Three stacked lanes, one per stack,
each showing that stack's output curve; to the right of each lane, a horizontal
bar whose length *is* that stack's coefficient. On screen from 0:22 to the end.

| Concept | Same object, later |
|---|---|
| the three N-BEATS stacks | the three lanes |
| the plain sum `ŷ = Σ ŷℓ` | three bars pinned at equal length, grey |
| `Ĝℓ = softmax(Linear(x₀))` | the bars, released, set by the input window |
| softmax normalisation | the three bars always totalling one |
| plain N-BEATS as a special case | the gate frozen at ⅓, ⅓, ⅓ |
| a heterogeneous dataset | the bars swinging from series to series |
| a homogeneous dataset (Tourism) | the bars barely moving — little to route |
| interpretability | reading the bars tells you what the model sees |
| expert specialisation | which bar is tallest, per STL component |
| mode collapse (why LayerNorm) | one bar takes everything, two starve |

**It is literally the real object.** The bars are a genuine softmax computed
from the series on screen, and the forecast drawn is the actual weighted sum of
the three lane curves. Setting the gate to uniform reproduces the plain-sum
forecast exactly, so the comparison animated in §1 is computed, not authored.

## Colour mapping

| Colour | Means | Where |
|---|---|---|
| `BLUE_C` | the given data — observed history, true future | input window, truth curve |
| `ORANGE` | the model's own output | the three lane curves, the N-BEATS-MoE forecast |
| `TEAL_C` | the gate — the second actor, the learned function | gate box, the bars once released |
| `GREEN` | improvement / a win | SMAPE drop, aligned expert cells |
| `YELLOW` | **transient** emphasis only | the three coefficients at 0:22, the question |
| `GREY_B` | neutral scaffolding | axes, lane labels, the pinned bars, baseline N-BEATS curve |

Note: the three stacks are deliberately *not* colour-coded against each other —
they are all the model's own output, so they share `ORANGE`, and lane identity
comes from position and label. This keeps `TEAL_C` unambiguously "the gate."
The baseline N-BEATS forecast is `GREY_B` because it is the neutral "before."

---

## §0 — The question (0:00 – 0:35)

**Narration.** "Here is a monthly time series, and here is how N-BEATS forecasts
it. It doesn't predict the curve directly. It predicts pieces of it — a flat
level, a slow trend, a repeating seasonal shape — and then adds them up. That
addition is the part worth looking at. Because written out in full, every piece
is added with a coefficient of exactly one. Nobody chose those ones. And the
same ones are used for every single series in the dataset. So: who decides how
much each piece counts?"

**Visuals.** A blue series fills the frame. It shrinks to a small panel top-left
as three lanes build below it in dependency order — axes, then each stack's
output curve in orange, then the labels Identity / Trend / Seasonality. The sum
`ŷ = ŷ₁ + ŷ₂ + ŷ₃` writes itself at the right, then rewrites to
`ŷ = 1·ŷ₁ + 1·ŷ₂ + 1·ŷ₃` with the three ones in yellow. Those three ones fly
out to become three grey bars of equal length, one beside each lane — the
carried object enters by transformation. The question lands beneath them.

**Why this follows:** — (opening).

## §1 — The obvious answer, and why it fails (0:35 – 1:35)

**Narration.** "The obvious answer is that nobody has to. These blocks are
trained. If the trend doesn't matter for a series, the trend block will just
learn to output something small. That would be fine, except for one thing:
these blocks are global. There is one trend block, with one set of weights,
serving all six hundred and seventeen series in this dataset. It sees a
different input window each time, but the scale it learned is a compromise
across all of them. Watch what that costs. On this series the true trend is
almost flat — it barely moves between zero point four and zero point nine. But
the global trend block, generalising across the whole dataset, sweeps from one
to three. Add that in with a coefficient of one, and it drags the forecast off
the truth. Seven point three percent error, on a series that didn't need a
trend at all."

**Visuals.** The forecast panel appears on the right: blue truth, grey N-BEATS
prediction diverging from it. The trend lane's curve is pushed to its
dataset-average amplitude and the three bars stay pinned. `push_in` on the trend
lane to show the over-scaled sweep, then `pull_back`; the mis-scaled trend is
carried visibly into the forecast panel and the gap opens. SMAPE 7.34% written
in grey.

**Why this follows:** the ones are indefensible only once the "the block will
handle it" defence has been given its strongest form and broken.

## §2 — Put the number back (1:35 – 2:40)

**Narration.** "So the contribution has to be adjustable per series, without
retraining the block. Which means putting a real number back in front of each
piece. Where does that number come from? From the one thing that is already
different for every series: the input window. Run it through a single linear
layer, take a softmax, and you get three numbers — positive, and summing to one.
That is the whole modification. The sum becomes a weighted sum, and the weights
are read off the input. Notice what happens when all three weights are equal:
you get the original N-BEATS back, exactly. Plain N-BEATS is this model with the
gate frozen. One detail matters here — the input is normalised before the linear
layer. Without that, the gate collapses: one weight takes everything and the
other two never get trained. And now, on this series, the gate pulls the trend
down to seventeen percent. The forecast follows the truth. Two point seven."

**Visuals.** A teal gate box appears beside the input panel, fed by an arrow
from it. Three arrows fan down to the bars, which turn from grey to teal and
release. Formalism arrives now, after the picture: `Ĝℓ = softmaxℓ(Linearℓ(x₀))`
then `ŷ = Σ Ĝℓ · ŷℓ`, built from separately addressable Tex terms so the
`Ĝℓ` can be boxed. Bars slide to uniform ⅓ and the forecast snaps back onto the
grey baseline curve — the "special case" claim, computed. Brief collapse demo:
bars slam to (1,0,0) then recover when LayerNorm is named. Then the real gate
runs: bars settle at 0.275 / 0.169 / 0.556, the trend lane rescales, the orange
forecast converges on the blue truth, SMAPE reads 2.68% in green.

**Why this follows:** §1 established that the block can't fix its own scale, so
something outside the block has to.

## §3 — Where it wins, and where it doesn't (2:40 – 3:30)

**Narration.** "Twelve datasets, a hundred thousand series. On M1, M3 and M4 —
each built from many different domains — the gated model beats N-BEATS in six of
nine cases. On Tourism it doesn't: it loses all three. Tourism is a single
domain, so its series look broadly alike, and the gate opens to nearly the same
three numbers every time. Where that happens the extra weights buy very little,
and here they cost a little accuracy. So the gains are real, but they are not
uniform, and they are concentrated where the data is mixed."

**Visuals.** The stage dims; the three bars survive and stay lit. Series cycle
through them: on M1 the bars swing hard from series to series; on Tourism they
barely twitch. Beside each, the win/loss record as a compact strip of small
markers — green for a win, grey for a loss — 6/9 against 0/3.

**Why this follows:** having built the mechanism, the honest next question is
whether it does anything.

## §4 — The bars as a readout (3:30 – 4:10)

**Narration.** "There is a second thing you get for free. The weights are
visible, so you can ask what the model thinks a series is. Decompose the series
with STL, then check which expert the gate favours. On M3 it lines up: trend
components go to the trend expert, seasonal components to the seasonal expert.
On M1 it doesn't line up at all — trend components get routed to the seasonal
expert, more than two-thirds of the time. And M1 is where the model wins by the
largest margin. So the gate is not a component detector. A large weight doesn't
mean a large output. It means that piece contributes more to getting the answer
right."

**Visuals.** The same three bars, now used as a readout: three rows (Trend,
Seasonal, Residual components) × the three experts, filled from Table 4 —
M3 shown first with the diagonal in green, then morphing to M1 where the green
lands off-diagonal. One line lands the caveat, boxed.

**Why this follows:** if the bars really track the series, they can be read.

## §5 — Payoff (4:10 – 4:40)

**Narration.** "So — who decides how much each piece counts? The series does.
Not the architecture, and not the dataset average. Every forecast N-BEATS makes
is a sum, and every sum has coefficients, whether or not anyone chose them. This
just makes them something the model looks up, instead of something it assumes."

**Visuals.** Stage dims to 0.15, the question returns verbatim in yellow at the
same size and position it had at 0:35. Beat. It fades as the stage comes back up
and the answer writes: "The series does." The stage restores fully, and the
three bars are indicated in sequence — they were the answer all along. Close on
the opening series with its three lanes and the bars moving.

---

## Dependency chain

```
§0  a forecast is a sum of pieces → every piece has coefficient 1
      │  the defence is that the block will shrink itself
§1  blocks are GLOBAL → their scale is a dataset compromise → wrong per series
      │  so the fix must live outside the block
§2  a number in front, read from x₀ → softmax gate → uniform gate == N-BEATS
      │  does it actually do anything?
§3  wins on heterogeneous (6/9), loses on homogeneous (0/3) → gains are uneven
      │  if the bars track the series, read them
§4  gate as readout → aligns on M3, not on M1 → contribution, not detection
      │  so, the original question
§5  the series decides
```

## Numbers used (all from the paper)

| Where | Value |
|---|---|
| M1 monthly series count | 617 |
| Total series across 12 datasets | 100,141 |
| ID1 gate weights | 0.275 / 0.169 / 0.556 |
| ID1 SMAPE | N-BEATS 7.34% → N-BEATS-MoE 2.68% |
| ID1 trend stack range | N-BEATS ≈ [1, 3]; N-BEATS-MoE ≈ [0.4, 0.9] |
| Heterogeneous record (M1, M3, M4) | N-BEATS-MoE wins 6 of 9 |
| Tourism record | N-BEATS-MoE wins 0 of 3 |
| Table 4, M3 | Trend→Trend 0.55, Seasonal→Seasonal 0.45 |
| Table 4, M1 | Trend→Seasonal 0.68 |

## Open choices flagged

1. **Runtime.** Built at 5:19 rather than the 4:40 target — the extra time is
   narration, not new content. §3 and §4 remain the compressible pair if a
   shorter cut is wanted; §0–§2 carry the mechanism and shouldn't be trimmed.
2. **Title card.** None currently — it opens cold on the series, which is the
   3b1b habit. Say if you want the paper title and authors on screen.
3. **The Tourism loss.** *Resolved 2026-08-14:* presented as a limitation —
   the gains are real but uneven and concentrated where the data is mixed —
   rather than as confirming evidence for the mechanism.
