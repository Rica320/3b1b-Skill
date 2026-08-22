# "The same chart, two opposite bets. What decides which one is right?"

The narrative spine, written before any animation code exists
(`narrative_template.md`). Every number quoted below is computed by `panel.py`,
not estimated — run `python panel.py` to reproduce them.

---

## The spine in one paragraph

Momentum and mean reversion look at the same chart and say opposite things, and
both are real strategies that have made real money. The obvious way to settle it
is to stop arguing and measure: build the momentum rule exactly as it is
described — rank the cross-section on its six-month return, buy the strongest
tenth, short the weakest tenth, rebalance monthly — and run it. It makes 1.09% a
month. Momentum wins. Except that changing *one number* in that rule, the lookback,
from six months to one month, turns +1.09 into −0.55, and stretching it to four
years turns it into −0.10. Nothing about the market changed and nothing about
the rule changed. So "does momentum work" was never a question about the market;
it is a question about a number you chose. And there are two such numbers — how
far back you look, `k`, and how long you hold, `h` — so a strategy is not a rule,
it is a **point on a floor**. Run all 1152 of them, give each point the height of
what it pays, and from directly above nothing happens: the heights are in the one
direction the flat view cannot show. Tilt the camera and it is a landscape — a
ridge at intermediate horizons where momentum pays, a basin in the far corner
where it loses, and a notch at the very corner where it loses worst. That basin
is mean reversion, on the same map, computed by the same code, from the same
market. The shape is not a coincidence: the simulated market has exactly three
ingredients — a transient price error, news that takes sixteen months to be
priced in, and an overshoot with a twenty-seven-month half-life — and each one
owns a feature of the map. So the two camps were never disagreeing about the
market. They were standing at opposite ends of one slice through one surface, and
each was reporting the ground under their own feet.

## The driving question

> **"The same chart, two opposite bets. What decides which one is right?"**

Stated at **0:30**, over a single price path with two arrows forking off its
right-hand end — orange continuing up, blue turning back down — and a `?` at the
fork. Restated verbatim at **6:12** and answered in one line:

> **"Not the chart, and not the market. Two numbers: how far back you look, and
> how long you hold."**

## The carried metaphor: THE MAP OF STRATEGIES

One object, and the first two minutes are its construction. Everything before the
floor appears is a single point on it — which is the hinge of the video: the
whole strategy we spend two minutes building turns out to be **one dot**.

It is literally the real object throughout. `panel.py` runs 1152 backtests and
the surface is those numbers; the ridge is where they are largest; the slice
curve is a row of them; the cost surface is the same 1152 backtests with a
computed turnover charge. Nothing on screen is a hand-drawn shape.

| Concept | The map, later |
|---|---|
| one stock's six-month return | the ranking that picks the two ends of the cross-section |
| one complete strategy (rank, buy, short, rebalance) | **one dot on the floor** |
| the lookback `k` | the east–west axis; one step doubles the months |
| the holding period `h` | the north–south axis |
| what a strategy pays | the height of the floor under that dot |
| "momentum works" | the ridge |
| "mean reversion works" | the basin in the far corner, and the notch at (1,1) |
| the argument between the two camps | two people standing at opposite ends of one slice |
| the bid-ask bounce | the notch at a one-month lookback |
| news priced in over 16 months | the ridge itself |
| a 27-month overshoot, handed back | the basin |
| transaction costs | the left edge of the map sagging, where you rebalance most |
| everything you don't know about the future | the map is drawn from the past, and it is drawn once |

## Colour mapping (fixed for the whole video)

| Colour | Means | Appears |
|---|---|---|
| `ORANGE` | **continuation**: the winners, buying them, and every part of the map where momentum pays | §0 → end |
| `BLUE_C` | **reversal**: the losers, buying them, and every part of the map where reversion pays | §0 → end |
| `GREY_B` | scaffolding: the price panel, the axes, the mesh, connective labels | throughout |
| `YELLOW` | transient emphasis only: the driving question, the strategy currently being read, the slice being walked | throughout |
| `RED_C` | cost, and nothing else | §5 |

The surface has **no colour of its own**: it is coloured by its own sign, orange
above zero and blue below. That is not decoration — it is the argument. Orange is
the winners *and* the people who bet on them; blue is the losers *and* the people
who bet on them; the two camps disagree about which end of the ranking to buy,
and the colour of the ground tells you which of them was right at that point.

Yellow is never an object's identity, and green is not used at all — in a video
about a strategy's return, a green/red profit-and-loss palette would collide with
the orange/blue one and quietly turn "momentum pays" into "momentum good".

---

## Section by section

### §0 — The question (0:00 – 0:40)

**Narration.** Here is a stock that has gone up a lot over the last six months.
Two people look at exactly this chart. One says: it has run too far, it will come
back. The other says: it is moving, it will keep moving. These are not moods,
they are both real strategies with real money in them. And they are opposite.
**The same chart, two opposite bets. What decides which one is right?**

**Visuals.** One price path from `panel.py`, drawn in grey, rising. Two arrows
fork from its right end: orange continuing up, blue bending back to the mean. A
yellow `?` at the fork. The question is written in yellow beneath.

**Follows from.** Nothing — this is the opening. The question is anchored to one
visible object: that fork.

### §1 — Stop arguing, measure (0:40 – 2:05)

**Narration.** The obvious answer is to stop arguing and measure. One chart
proves nothing, so take the whole market — two hundred and forty stocks. For each
one, the six-month return: today's price over the price six months ago, minus
one. Now sort them. Buy the strongest tenth. Short the weakest tenth. Wait, and
do it again. That is the whole rule, and over two hundred and fifty years of this
market it makes **one point zero nine percent a month**. Momentum wins; the
argument is over. Except — change one number. Not the market, not the rule: the
six. Rank on the *last month* instead, and the same code, on the same market,
makes **minus zero point five five**. Rank on the last four years: **minus zero
point one zero**. So "does momentum work" was never a question about the market.
It is a question about a number we picked without thinking.

**Visuals.** The single path is joined by 239 more (staggered, faint grey) — the
cross-section. A six-month window slides back from today on all of them. Each
path collapses to a dot on a vertical ranking column, sorted; the top tenth
lights orange, the bottom tenth blue. Only now does the formula appear,
`M_t = P_t / P_{t-k} - 1`, built from separately addressable `Tex` parts with a
yellow note naming `k`. The answer +1.09 is written. Then `k` alone is changed —
6 → 1 → 48 — the answer is recomputed each time from `panel.py`, and all three
are kept on screen so they can be read together. Only `k` is ever shown as a
parameter here; `h` does not exist yet, which is what §2 is for.

**Follows from.** §0 asked which camp is right; this is the fairest way to find
out, tried honestly, and its specific failure — the answer flips when a
parameter moves — is what forces §2.

### §2 — A strategy is a point, not a rule (2:05 – 3:00)

**Narration.** There is a second number hiding in "and do it again": how long you
hold before you re-sort. Hold that same six-month signal for a month and it pays
one point zero nine; hold it for two years and it pays six hundredths. So a
strategy is not a rule. It is a *pair* of numbers, and every pair is a different
strategy. Put lookback on one axis and holding period on the other — each step
doubles the months — and everything we just built is one dot on this floor. So
let us run all of them. Forty-eight lookbacks, twenty-four holding periods:
eleven hundred and fifty-two backtests. And each one has a number attached: what
it pays. Give every dot that height. [wordless beat] Nothing happened. Because
from straight above, height is the one thing you cannot see.

**Visuals.** The ranking column — all 240 dots of it — collapses into a single
yellow dot, which is the transform that carries §1 into §2; the floor grid
(`ThreeDAxes`, `phi = 0`, ticks 1, 2, 4, 8, 16, 32 months) is drawn under it.
Dots fill the lattice, staggered. Then every dot moves to its true height — while
the camera is still straight down, so almost nothing changes on screen. Two or
three seconds of silence on that frame.

**Follows from.** §1 showed the answer depends on `k`; the moment there are two
such numbers, the set of strategies is a plane, and the thing we want to know is
a function on it. The last beat is what earns the camera move.

### §3 — The tilt (3:00 – 3:50)

**Narration.** So move.

[the orbit, wordless]

Every dot was already at its own height. It is a landscape. Up here, where you
rank on something between three months and a year and hold it for a month or
three, the ground is orange: buying winners pays, and the peak is **one point
two two percent a month at a six-month lookback held two**. Down in the far
corner — rank on four years, hold for two — the ground is blue and the same
strategy loses half a percent a month. That corner is not a different market and
it is not a different theory. It is mean reversion, on the same map, from the
same code. And here is the thing I did not expect: the two lowest points on this
entire map are minus zero point five five, and minus zero point five five. They
are at opposite corners. Reversion at one month, reversion at four years, and
between them a ridge.

**Visuals.** `orbit(theta=-35, phi=64)` over 3.6s with nothing else changing;
the surface knits between the dots as they lift into view. Surface coloured by
its own sign (orange above zero, blue below) with a faint grey zero-plane. Named
points marked with `dot3d` + fixed labels. A slow `spin` under the payoff.

**Follows from.** §2's last frame is a claim that something is there and cannot
be seen; this is the only move that can test it. The camera move *is* the
argument.

### §4 — Why the map has that shape (3:50 – 4:45)

**Narration.** And the shape is not an accident, because I know what is in this
market: three things, and each one owns a feature of the map. Every price carries
a small error that is in today's number and gone from tomorrow's — a spread, a
bounce. Rank on one month and that is most of what you are ranking on, so you buy
noise and it reverses: that is the notch. Second, news is priced in slowly —
sixteen months, in this market — so a stock that moved on news last quarter is
still moving on it now: that is the ridge. Third, the move overshoots, and the
overshoot is handed back with a twenty-seven-month half-life: that is the basin.
Take one straight line across the map — hold for a month, and walk the lookback
from one month out to four years — and you get the whole argument in a single
curve. Minus zero five five. Up over the ridge, plus one point zero nine. And
back under water at the far end. Momentum people stood here. Reversion people
stood here. Neither of them was wrong.

**Visuals.** Three labels attach to three features of the surface as each is
named (`fix`ed, with a `dot3d` marker on the feature). Then a real `slice_curve`
at h = 1 is drawn on the surface in yellow — the row that crosses zero twice,
at k ≈ 2 and k ≈ 39 — and two markers walk to its two ends as the camps are
named: orange at the ridge, blue at the far end.

**Follows from.** §3 showed *that* the landscape has this shape; a shape you
cannot explain is a coincidence. This is the mechanism, and it arrives after the
picture it explains, never before.

### §5 — What the map does not know (4:45 – 5:25)

**Narration.** Two things this picture is not telling you. First, it is gross.
Every rebalance trades, and the fast corner of the map trades most — the
one-month rule replaces its whole book every month. Charge ten basis points a
trade on the turnover this thing actually generates, and the left edge sags: the
peak gives up a tenth of a percent, and the notch goes from minus fifty-five to
minus ninety-two. Second, and much worse: I drew this map from two hundred and
fifty years of a market whose rules never changed, and I knew what they were. You
get one path, once, and you have to estimate every height on this map from the
part of it you have already lived through. The ridge is real here. Whether it is
still there next year is not a question this picture can answer.

**Visuals.** The surface cross-dissolves to the net-of-cost surface (a genuine
second computation) while a red cost figure is written; the left edge visibly
drops and the notch deepens. Then the whole map dims and only the ridge line
stays lit, flickering — the honest limit stated over a still frame.

**Follows from.** §4 explained the shape; §5 is what you still cannot do with
it. Both facts are computed, not asserted: the cost surface is `landscape(cost=0.10)`
and the sag is where the turnover is.

### §6 — Payoff (5:25 – 5:55)

**Narration.** So. **The same chart, two opposite bets. What decides which one is
right?** Not the chart, and not the market. Two numbers: how far back you look,
and how long you hold. Mean reversion says it moved too far and it will come
back. Momentum says it has been moving and it will keep moving. They are the same
sentence, read at two different horizons — and the horizon is the whole
strategy.

**Visuals.** The map dims; the opening question returns in yellow in its opening
styling; the answer replaces it. The two named points glow, orange on the ridge
and blue in the basin, and the camera spins slowly through the final frame.

**Follows from.** It restates the opening question verbatim and answers it with
the object the viewer has watched being built.

---

## Dependency chain

```
§0  one chart, two opposite bets        -> what decides which is right?
      │  the fair way to settle it is to measure
§1  build the rule and run it: +1.09    -> change k, and it is -0.55
      │  so the answer lives in the parameter, and there are two of them
§2  (k, h) is a floor; a strategy is    -> heights added, and from above
    a point; 1152 of them                  nothing happens
      │  the only way to see the missing direction
§3  TILT                                -> a ridge, a basin, a notch:
      │                                     momentum and reversion, one map
      │  a shape you cannot explain is a coincidence
§4  three ingredients, three features   -> one slice IS the whole argument
      │  but the map is gross, and it was drawn from the past
§5  costs sag the fast edge; the map    -> the ridge is real here; here is
    is an estimate, drawn once             not next year
      │  so, the original question
§6  not the chart and not the market: how far back, and how long
```

Every arrow is a *because*, and each one is spoken aloud as the first sentence of
its section.

---

## Why this is in 3D at all

`three_d.md` §1 requires naming the claim a flat picture cannot make. It is:

> The thing you want to know — what a strategy pays — is a function of two
> parameters, so it is a surface over the plane of strategies. Its **shape** is
> the argument: that momentum and reversion are one connected landscape rather
> than two rival claims, that the profitable region is a ridge with a crest and
> not a plateau, and that the two camps are standing on the same slice.

A flat heat map can show the *sign* at each point and nothing else — no crest, no
steepness, no sense of how far you are from the water. And the video is built so
that the camera move earns its keep: §2 ends with all 1152 heights being applied
while the camera is straight down, so the viewer watches a frame in which
something demonstrably changed and nothing appeared to. §3 is the only possible
response to that.

---

## Open choices, flagged

1. **Runtime** — the plan above is about 5:55. It can be cut to ~5:05 by dropping
   §5's cost surface (keeping only the one-sentence "it is gross" caveat), which
   is the least load-bearing beat.
2. **Voice** — Kokoro `am_michael` at 0.92, matching `examples/mean_reversion`
   so the two sit together as a pair.
3. **The market is simulated, and the video says so out loud in §4.** The three
   ingredients are real documented effects, but the numbers on screen are this
   simulation's, not measurements of any real market. The alternative — real
   price data — cannot be shipped in this repository and would make the
   mechanism section impossible, because with real data you do not get to know
   what went in.


---

## What changed between this document and the build

The spine was approved first and then the pixels argued back. Recorded here
because the reasons are the useful part:

- **§1 runs the rule at a one-month hold, not a quarterly one.** The first cut
  ranked on `k` but paid out `h = 3`, so the screen read `k = 1  →  +0.22`
  while the voice said "minus zero point five five" — the k = 1 sign flip only
  exists at `h = 1`. `verify_panel.py` caught it. The section now quotes
  +1.09 / −0.55 / −0.10, all from the `h = 1` column, and `h` is not shown as a
  parameter at all until §2 needs it, which makes §2's reveal land harder.
- **The camera sits at theta = −20, not −34.** At −34 the ridge and the basin
  project 0.58 units apart on screen and their labels overlap. The angle was
  chosen by projecting the three labelled points through the camera and
  sweeping theta, and the §3–§5 drift is leashed to the range where the
  separation holds.
- **The lookback window is a `Square3D` wash inside a stroke-only outline.**
  As a filled `Rectangle` it deleted all 240 price paths inside its own area —
  ANTI-PATTERN #18's winding-number mechanism, not a depth-test problem, and
  `flat()` did not fix it.
- **Surface shading is (0.2, 0.1, 0.15).** At the helper's default 0.5 shadow
  the whole camera-facing slope rendered black, with a jagged edge that read
  as a hole in the geometry rather than as lighting.
- **The three long §3 lines play over a slow camera drift**, with labels that
  track their markers through it. Held still they were 8–14s frozen frames,
  which fails `verify_render.py` check [3] and is ANTI-PATTERN #22 besides.
- **Runtime is 6:37, not 5:55.** The first synthesis came back at 382s of
  speech against a ~340s budget; ~250 words were cut from the longest beats
  rather than trimming every line evenly.
