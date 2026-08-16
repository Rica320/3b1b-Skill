# "When is a gap big enough to bet on?"

The narrative spine, written before any animation code exists
(`narrative_template.md`). Every number quoted below is computed by
`market.py`, not estimated — run `python market.py` to reproduce them.

---

## The spine in one paragraph

Two stocks in the same industry move together, so the interesting quantity is
not either price but the gap between them. The obvious way to say the gap is
"too big" is to put a dollar threshold on it — and that fails, visibly, because
the same pair is quiet for half the year and noisy for the other half: two
dollars is silent for 110 days and forty cents is shouting on 98 of the next
130. What the threshold is missing is a unit, and the only place a unit can
come from is the gap's own recent past. That is the rolling mean and rolling
standard deviation, and measuring the gap in those units is the z-score — not a
new object, the *same curve on a new ruler*. Now the rule is testable: enter at
two sigma, exit at zero. Six such trades on the part of the data we designed
the rule against made $3.75, of which the quiet-stretch trades kept seven cents
and four cents after costs — because a two-sigma move is only worth thirty
cents when sigma is fifteen. Then the held-out data arrives, the pull
disappears, and the gap walks eleven dollars away and never returns. The
z-score never reports an emergency, because the mean it is measured against
falls with it. One trade gives back $9.32. The ruler was never measuring the
gap; it was measuring the gap against an assumption, and the assumption expired.

## The driving question

> **"When is a gap big enough to bet on?"**

Stated at **0:26**, over a visibly stretched vertical gap between two price
paths, with a `?` on the gap itself. Restated verbatim at **4:15** and answered
in one line:

> **"Never in dollars. Only in sigmas — and only while the sigmas are still
> measuring something that is there."**

## The carried metaphor: THE GAP

One object, introduced at 0:20, still on screen at the end. It is literally the
real object throughout — `market.py` computes it and everything drawn is that
computation.

| Concept | The gap, later |
|---|---|
| two stocks that move together | two paths, and the vertical distance between them |
| β | the number that stretches B until the gap is all that is left |
| `Spread_t = P_A − βP_B` | the gap, lifted off the prices and drawn as its own curve |
| "unusually far" | the curve leaving a band built from its own recent past |
| `z_t` | the same curve remeasured, so the band becomes flat rails |
| the trade | grab the curve outside the rails, let go when it is home |
| transaction cost | a strip around the middle the curve has to clear |
| a broken relationship | the band drifting after the curve, reporting nothing wrong |
| the drawdown | the curve leaving, and the rails following it down |

## Colour mapping (fixed for the whole video)

| Colour | Means | Appears |
|---|---|---|
| `BLUE_C` | stock A's price | §0, §1, §5 |
| `PURPLE_B` | stock B's price | §0, §1, §3 |
| `ORANGE` | **the gap** — the carried object | §1 → end |
| `GREEN_C` | the ruler: rolling mean, ±1σ/±2σ band, the ±2 rails | §2 → end |
| `RED_C` | what it costs you: the cost strip, and the loss | §3, §4 |
| `YELLOW` | transient emphasis only — the driving question, the current focus | throughout |
| `GREY_B` | scaffolding: axes, ticks, connective labels | throughout |

Yellow is never an object's identity. Green never means "profit" — it means
"what normal is assumed to be", which is exactly the thing that fails at the
end. Red only ever means a cost.

Stock B was `TEAL_C` until the first contact sheet, where teal rendered green
enough that the "buy B" label in §3 read as the same colour as the sigma rails
it was sitting on. Violet collides with nothing else on the palette.

---

## Section by section

### §0 — The question (0:00 – 0:35)

**Narration.** Two companies in the same industry. When the market goes up
they both go up; when it falls they both fall. So the fact that one of them
rose tells you almost nothing — you are mostly looking at the weather. But
look at the distance between them. Most of the year it holds. And then, here,
it stretches. **When is a gap big enough to bet on?**

**Visuals.** `p_a` in blue and `p_b` in teal, drawn together over 420 days;
they visibly ride the same $20 market swing. Both dim; a vertical yellow
segment marks the widest stretch, with a `?` on it. The question is written
under the chart in yellow.

**Follows from.** Nothing — this is the opening. The question is anchored to
one visible object: that segment.

### §1 — The obvious answer, and the way it fails (0:35 – 1:45)

**Narration.** First, make the gap a real number. Scale B until it sits on top
of A — that is all β does — and what is left over is the gap. Now the obvious
rule: pick a number of dollars and call anything past it unusual. Two dollars,
say. And for the first hundred and ten days it never fires once. Fine — lower
it. Forty cents. Now it fires on ninety-eight days out of the next hundred and
thirty. There is no dollar number that works, because the pair is not one
thing: it is quiet here and loud there, and "two dollars" is a fact about
dollars, not about this pair.

**Visuals.** `b_scaled` stretches onto `p_a` (a genuine transform of the teal
path). The two paths collapse: the vertical gaps lift off and trace out the
orange spread curve on its own axes. A red-ish $2 line: silent across the calm
stretch, 20 crossings in the wild one. The line drops to $0.40 and 98 days
light up. Counters, drawn from the data.

**Follows from.** The question asked "big enough" — this is the most obvious
possible meaning of "big", tried fairly, and its specific failure (no knowledge
of what is normal *here*) is what forces §2.

### §2 — A unit the pair supplies itself (1:45 – 2:50)

**Narration.** The threshold needs to know what normal looks like around here,
and the only honest source for that is the gap's own recent past. Take the last
sixty days: their average is where the gap has been sitting, and their spread
is how far it usually wanders. Draw that as a band, and it breathes — narrow
where the pair is quiet, wide where it is loud. Now ask the same question in
units of the band. Nothing moves; only the ruler changes. That number has a
name: the z-score.

**Visuals.** A 60-day window slides along the curve; the green rolling mean is
drawn as it goes, then the ±1σ / ±2σ band fills in and visibly breathes. Then
the whole picture is remeasured: the orange curve morphs into the z-curve while
the wiggly band straightens into flat green rails at 0, ±1, ±2. Only *after*
that lands does the formula appear:
`z_t = (Spread_t − μ_t) / σ_t`, each term built as its own `Tex` so it can be
boxed against the picture.

**Follows from.** §1 needed a unit; this is where the unit comes from, and the
z-score is introduced as a *consequence* of the picture, not as a definition.

### §3 — The rule, and what it actually pays (2:50 – 4:00)

**Narration.** Now the rule is something you can test. Outside the rails, bet
the gap closes: sell the expensive one, buy the cheap one. Back at zero, close.
Nothing here is a forecast of the market — both legs move with it and it
cancels. Six trades, six winners, three dollars seventy-five. But look at the
first two. The gap came back twenty-seven cents, and twenty-four. Getting in
and out costs twenty. So those trades kept seven cents and four cents, while
the same rule in the noisy stretch kept a dollar fifty-eight. Cost is a fixed
number of dollars, and sigma is not: a two-sigma signal is worth thirty cents
when sigma is fifteen.

**Visuals.** Entry and exit markers on the z-curve; the position drawn as the
distance from the rail back to zero. The two price paths return, dimmed,
underneath — you see both legs rise together and the gap close anyway. Then a
red cost strip at ±`cost/σ_t`, which is a *breathing* curve: ±1.33 in the quiet
stretch, ±0.19 in the loud one. Per-trade P&L printed from the data.

**Follows from.** §2 produced a testable rule; a rule you can test is a rule
you can price. The cost strip is drawn on the same axes as the rails, so the
comparison is geometric, not asserted.

### §4 — The part of the data we did not look at (4:00 – 5:05)

**Narration.** Sixty days, two sigma, forty cents — every one of those numbers
was chosen by looking at this picture. So the only honest test is the part of
the picture we have not looked at. Here it is. The gap goes low, the rule buys,
and then the gap keeps going: nine dollars, eleven, and it never comes back.
The relationship did not stretch, it ended. And watch what the z-score does
while that happens — it stays between minus one and minus two and a half the
whole way down, because the mean it is measured against is falling with it. It
is not lying. It is answering the question it was asked: *unusual compared to
the last sixty days*. Six winners, three seventy-five. One trade back: nine
dollars thirty-two.

**Visuals.** The axes extend into unseen territory (a real rescale of both the
curve and the y-range — the same object, zoomed out). The orange curve walks
off the bottom; the green band follows it down like a tow-rope; the z-curve
underneath stays unremarkable. The open position is a red area that grows for
89 days. Then the tally: `+3.75` against `−9.32`.

**Follows from.** §3 fitted a rule to data it had already seen. This is the
only thing that can falsify it, and the failure is a computed consequence of a
regime change in `market.py`, not a hand-drawn scare.

### §5 — Payoff (5:05 – 5:35)

**Narration.** So: **when is a gap big enough to bet on?** Never in dollars.
Only in sigmas — and only while the sigmas are still measuring something that
is there. What we built was not a prediction. It was a ruler, made out of the
recent past, and handed the assumption that the recent past still applies. That
is why the real work in this is not finding the signal. It is out-of-sample
testing, costs, and position sizing: the machinery for finding out how much of
your edge was ever there.

**Visuals.** Everything dims; the question returns in yellow, in its opening
styling, centred. The answer replaces it. Then the stage restores and we close
on the frame we opened with — the two price paths and the gap between them —
with the gap flashing once.

**Follows from.** It restates the opening question verbatim and answers it with
the object the viewer has watched for five minutes.

---

## Dependency chain

```
§0  two paths, one gap        -> "when is a gap big enough to bet on?"
      │  the most obvious meaning of "big" is dollars
§1  a dollar threshold        -> silent for 110 days, screaming for 98
      │  so the unit has to come from the pair itself
§2  rolling mean and sigma    -> the band breathes -> same curve, new ruler = z
      │  now the rule is testable
§3  |z| > 2, exit at 0        -> 6 winners, $3.75 - and costs eat the quiet ones
      │  but every parameter was fitted to what we just looked at
§4  the held-out stretch      -> the pull ends, z reports nothing, -$9.32
      │  so, the original question
§5  never in dollars; only in sigmas, and only while they measure something
```

Every arrow is a *because*, and each one is spoken aloud as the first sentence
of its section.

---

## Open choices, flagged

1. **Runtime** — the plan above is about 5:30. It can be cut to ~4:30 by
   compressing §3 (drop the per-trade P&L walk and keep only the cost strip).
2. **Voice** — Kokoro `am_michael` at 0.92 (the skill's default explainer
   voice, ~2.9 w/s). `bm_george` is the British alternative; `af_heart` the
   warmest female one.
3. **§4's second half** — position sizing and drawdown are named in one
   sentence rather than given their own beats, because the picture already
   shows a drawdown (89 days in an open loss) and a bullet list is not a
   visualisation.
