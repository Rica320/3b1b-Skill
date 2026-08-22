# `momentum/` — "The same chart, two opposite bets. What decides which one is right?"

A 6:37 narrated **3D** explainer on momentum, built with the
`3b1b-math-animation` skill. One `ThreeDScene`, seven sections, 42 narration
beats in a synthesised voice the animation is paced to — and a camera move that
is the argument rather than the decoration.

|  |  |
|---|---|
| Runtime | 6:37 (397.0 s), 1920×1080, 30 fps |
| Narration | 42 beats, 334.8 s of speech, **84 %** coverage, 9.4 s longest silence |
| Voice | Kokoro `am_michael` at 0.92 (≈ 2.67 w/s) |
| Mix | −16.5 LUFS, −1.4 dBTP |
| Checks | `verify_render.py` 5/5 · `verify_audio.py` 6/6 · `verify_panel.py` 30/30 · AUDIT 0 overlaps |

```bash
# 0. the market, and the 1152 backtests the video is about
../../env/bin/python panel.py

# 1. the words, and their real durations
../../env/bin/python ../../skills/3b1b-math-animation/scripts/tts.py \
    script.yaml --out audio

# 2. the picture, paced to them
PATH="../../env/bin:$PATH" \
  bash ../../skills/3b1b-math-animation/scripts/render.sh momentum.py Momentum

# 3. the mix
../../env/bin/python ../../skills/3b1b-math-animation/scripts/mux_audio.py \
    videos/Momentum.mp4 --cues narration_cues.json

# 4. all the verifications
../../env/bin/python ../../skills/3b1b-math-animation/scripts/verify_render.py \
    videos/Momentum.mp4 --meta render_meta.json
../../env/bin/python ../../skills/3b1b-math-animation/scripts/verify_audio.py \
    videos/Momentum_narrated.mp4 --cues narration_cues.json
../../env/bin/python verify_panel.py
AUDIT=1 PATH="../../env/bin:$PATH" \
  ../../env/bin/manimgl momentum.py Momentum -w -o -l --video_dir /tmp/audit \
  2>&1 | tr '\r' '\n' | grep OVERLAP
```

## Files

| File | What it is |
|---|---|
| `SPINE.md` | the narrative spine, written and approved **before** any animation code, with a record of what the pixels changed afterwards |
| `panel.py` | the market: 240 stocks × 3000 months, the momentum signal, the deciles, and all 1152 backtests |
| `script.yaml` | every spoken word, one beat per line — the scene contains no prose |
| `momentum.py` | the single `ThreeDScene`, seven section methods |
| `verify_panel.py` | asserts all 30 spoken numbers against `panel.py`, *and* that each phrase is really in the script |
| `audio/` | one wav per beat plus `narration.json` (measured durations) |
| `cache/landscape.npz` | the 1152 backtests, gross and net of costs |
| `narration_cues.json` | the frame each line starts on, written by the render |
| `render_meta.json` | duration and the 16 camera windows, for `verify_render.py` |

## The argument

```
§0  one chart, two opposite bets        -> what decides which is right?
      │  the fair way to settle it is to measure
§1  build the rule and run it: +1.09    -> change k alone, and it is -0.55
      │  so the answer lives in the parameter, and there are two of them
§2  (k, h) is a floor, a strategy is    -> heights applied while the camera is
    a point, 1152 of them                  straight down: nothing happens
      │  the only way to see the direction the view does not have
§3  TILT                                -> a ridge, a basin, a notch: momentum
      │                                     and reversion on one map
      │  a shape you cannot explain is a coincidence
§4  three ingredients, three features   -> one slice IS the whole argument
      │  but the map is gross, and it was drawn from the past
§5  costs sag the fast edge; the map    -> the ridge is real here; here is not
    is an estimate, drawn once             next year
      │  so, the original question
§6  not the chart and not the market: how far back, and how long
```

## Why it is in 3D

`three_d.md` §1 asks for the claim a flat picture cannot make. It is: **what a
strategy pays is a function of two parameters, so it is a surface over the plane
of strategies, and its shape is the argument** — that momentum and mean
reversion are one connected landscape rather than two rival claims, that the
profitable region has a crest rather than a plateau, and that the two camps are
standing on the same slice.

The camera move is built to earn its keep. §2 ends by applying all 1152 heights
**while the camera is still straight down**, so the viewer watches a frame in
which something demonstrably changed and nothing appeared to. §3 is the only
possible response to that, and the focal distance is set to 32 (near
orthographic) precisely so the top-down view really does hide the heights
rather than leaking them as a 16 % perspective bulge.

## Everything on screen is computed

`panel.py` simulates a market with exactly three ingredients — a transient
price error, news priced in over 16 months, and an overshoot handed back with a
27-month half-life — and each one owns a feature of the map. The surface is
`landscape()`, a real backtest at every one of 48 lookbacks × 24 holding
periods; the crest line is `ridge()`; the cost surface is the same 1152
backtests with a turnover charge computed from the portfolios themselves. The
video says out loud that the market is simulated, and says it twice.

## Defects found by rendering, and their fixes

Every one of these was invisible in the source and only appeared in the pixels.

| Defect | Fix |
|---|---|
| The lookback band deleted all 240 price paths inside its own area | ANTI-PATTERN #18: a VMobject fill is drawn by winding number across its render batch. `flat()` did not help and neither did depth order. The wash is a `Square3D`; only the outline is still a VMobject |
| The whole camera-facing slope of the surface rendered black, with a jagged edge that read as a hole | `shading=(0.2, 0.1, 0.15)`; the helper default of 0.5 shadow was the cause |
| Ridge and basin labels overlapped | the viewpoint was chosen by projecting the three features through the camera and sweeping theta; −34 puts them 0.58 apart, −20 puts them 1.4 apart, and the drift is leashed to that range |
| The `k = 1 → +0.22` on screen while the voice said "minus zero point five five" | §1 was paying out `h = 3` while ranking on `k`; the sign flip only exists at `h = 1`. Caught by `verify_panel.py`, not by eye |
| 16.5 s frozen frame in §0, 8–14 s frozen frames in §3 | show the claim instead of holding on it: pulses along the two arrows, and a leashed camera drift with labels that track their markers through it |
| 2.0 s of blank screen before the payoff question | the stage was dimmed to 0.2, below what counts as visible; 0.45 still reads as pushed back |
| "the last 48 months" sat on top of the formula; floor tick numbers sat on the axis title | AUDIT sweep — the band caption is right-aligned to "today" now, and a world gap of 0.9 in y is only 0.39 on screen at φ = 64 |
| The 240-dot ranking column aliased into a dashed line | each stock keeps its own small horizontal offset, so the column is a swarm and a re-sort is visible as motion |
| The band caption garbled mid-`Transform` | different glyph counts; a lagged crossfade takes the old one off before the new one arrives |
| "lookback k (months)" ran off the bottom of the frame for 38 s | the map was 6.0 tall, so pushing the title clear of the tick numbers pushed it off the edge. The map is 5.2 tall now and the two axis titles are fixed HUD text — on the floor they cannot satisfy both views at once, because a world gap in y is foreshortened by cos 64° = 0.44 when the camera tilts |
| The closing spin left the fixed axis titles pointing the wrong way | the axis furniture stays off from the payoff onward; the last frames are the shape and the two corners |
