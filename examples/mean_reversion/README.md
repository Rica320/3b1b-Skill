# `mean_reversion/` — "When is a gap big enough to bet on?"

A 5:43 narrated explainer on mean reversion and pairs trading, built with the
`3b1b-math-animation` skill. 2D, one `Scene`, six sections, 35 narration beats
in a synthesised voice the animation is paced to.

|  |  |
|---|---|
| Runtime | 5:43 (343.3 s), 1920×1080, 30 fps |
| Narration | 35 beats, 287.1 s of speech, **84 %** coverage, 4.6 s longest silence |
| Voice | Kokoro `am_michael` at 0.92 (≈ 2.74 w/s) |
| Mix | −16.4 LUFS, −1.4 dBTP |
| Checks | `verify_render.py` 5/5 · `verify_audio.py` 6/6 · `verify_market.py` 18/18 |

```bash
# 1. the words, and their real durations
../../env/bin/python ../../skills/3b1b-math-animation/scripts/tts.py \
    script.yaml --out audio

# 2. the picture, paced to them
PATH="../../env/bin:$PATH" \
  bash ../../skills/3b1b-math-animation/scripts/render.sh \
    mean_reversion.py MeanReversion

# 3. the mix
../../env/bin/python ../../skills/3b1b-math-animation/scripts/mux_audio.py \
    videos/MeanReversion.mp4 --cues narration_cues.json

# 4. all three verifications
../../env/bin/python ../../skills/3b1b-math-animation/scripts/verify_render.py \
    videos/MeanReversion.mp4 --meta render_meta.json
../../env/bin/python ../../skills/3b1b-math-animation/scripts/verify_audio.py \
    videos/MeanReversion_narrated.mp4 --cues narration_cues.json
../../env/bin/python verify_market.py
```

## Files

| File | What it is |
|---|---|
| `SPINE.md` | the narrative spine, written and approved **before** any animation code |
| `market.py` | the market: prices, spread, rolling band, z-score, trades, P&L |
| `script.yaml` | every spoken word, one beat per line — the scene contains no prose |
| `mean_reversion.py` | the single `Scene`, six section methods |
| `verify_market.py` | asserts all 18 spoken numbers against `market.py` |
| `audio/` | one wav per beat plus `narration.json` (measured durations) |
| `narration_cues.json` | the frame each line starts on, written by the render |
| `render_meta.json` | duration and camera windows, for `verify_render.py` |

## The argument

```
§0  two paths, one gap        -> "when is a gap big enough to bet on?"
      │  the most obvious meaning of "big" is dollars
§1  a dollar threshold        -> silent for 110 days, then firing on 98 of 130
      │  so the unit has to come from the pair itself
§2  rolling mean and sigma    -> the band breathes -> same curve, new ruler = z
      │  now the rule is testable
§3  |z| > 2, exit at 0        -> 6 winners, $3.75 - and costs eat the quiet ones
      │  but every parameter was fitted to what we just looked at
§4  the held-out stretch      -> the pull ends, z reports nothing, -$9.32
      │  so, the original question
§5  never in dollars; only in sigmas, and only while they measure something
```

## Two things this example is for

**The metaphor is the real object.** `market.py` generates a piecewise
Ornstein–Uhlenbeck spread and computes everything else from it; the scene draws
that computation and never a keyframe. So §4's central claim is not asserted by
an animation, it is a consequence of the arithmetic: as the spread drifts, its
own trailing mean drifts after it, and the z-score — which is all the strategy
can see — reports **−1.41** on the day the gap is **$11.15** from home, and
never passes **−2.47** during the entire collapse. `verify_market.py` asserts
that and seventeen other spoken numbers, so changing a parameter in `market.py`
and forgetting to re-cut the narration is a test failure rather than a wrong
number in a finished render.

**The §2 rescale is a point-for-point morph, not a redraw.** The spread curve,
the mean line and the σ band are all built from the same array of days, so
`ReplacementTransform` maps each to its target vertex by vertex: the wiggly
band straightens into the flat ±2 strip, the mean flattens onto zero, and the
curve deforms with them. That is what makes "we are only measuring it
differently" a thing the viewer watches rather than a thing they are told.

## Defects the review process caught

Ordered by how long they would have survived unnoticed.

| Found by | Defect |
|---|---|
| `assert_in_frame` | `Axes.move_to()` centres the mobject box, which for `x_range=(60, 300)` is anchored at data (0, 0) — every panel was drawn ~2.4 units off. Fixed by shifting on `c2p` of the range midpoint. |
| contact sheet | A `SurroundingRectangle` from §2's equation beat was never removed, and sat in the middle of the chart for the remaining **2 minutes**. Invisible in the source; obvious on the sheet. |
| contact sheet | Stock B was `TEAL_C`, which renders green enough that "buy B" in §3 read as the same colour as the green σ rails it sat on. Now `PURPLE_B`. |
| contact sheet | §1's per-stretch counts and the span brackets under them landed on the same screen row and drew on top of each other. |
| contact sheet | §5's shrunken answer text was placed in the bottom-right corner, on top of the "held out" label. |
| contact sheet | The trade holding-period strips were drawn on top of the band at 0.07 opacity and washed the rails out; now behind, at 0.06. |
| `verify_render` [3] | **Four** frozen holds of 12.6 s, 11.7 s, 11.5 s and 16.0 s — long narration lines sitting over still frames. Fixed the way `anti_patterns.md` #22 says to: by showing the claim, not by trimming the script. The 60-day window slides down the collapse under "the mean is chasing the gap down"; the held position's red span grows a day at a time under "eighty-nine days spent holding it"; the collapse is traced under "it never once passes minus two and a half". |
| `verify_render` [3], **full quality only** | The fix above used `ShowCreation` to trace the collapse — which extends a thin line by a pixel or two per frame, well under the checker's motion threshold. It read as a 15 s frozen hold *and the draft render had passed*, because low-quality encoding noise inflated the frame deltas enough to hide it. Replaced with a playhead that sweeps from the entry day to the low, which moves. |
| `verify_audio` [5] | The first cut was **89.8 %** speech. Nine wordless beats brought it to 84 %. |

Two of those are worth generalising. **A draft render can pass a check the
final render fails** — the encoder's own noise is motion as far as a
frame-delta test is concerned, which is the same trap `anti_patterns.md` #18
describes from the other direction. And **growing an object is not moving one**:
if a beat needs to register as motion, animate a position, not a `ShowCreation`.

The text-overlap audit reports zero — and the detector was validated against a
deliberately overlapping pair first, because a silent zero is its failure mode.

## Known, and left alone

`verify_audio`'s advisory pacing report flags six lines above 3.3 w/s, of which
the two that matter are the driving question and its restatement. Both are
short sentences that Kokoro delivers briskly, and both are followed by a
deliberate wordless beat (3.2 s and 3.0 s) that gives them the room the
delivery does not. Slowing them would mean re-cutting at a lower global speed,
which re-times every one of the 35 beats. Overall delivery is 2.74 w/s, inside
the 2.2–3.0 the style wants.
