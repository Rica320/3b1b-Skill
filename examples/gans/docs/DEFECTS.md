# Phase 1 — Defect List: `GANs_Explained_Full.mp4`

> **This documents the first build of the video, which no longer exists in this
> repository.** It was eleven separate `Scene`s (`scene00_cold_open.py` …
> `scene10_final_synthesis.py`) rendered individually and concatenated. The
> rebuild that replaced it is [`../gans.py`](../gans.py); the two are unrelated
> code. The `file.py:line` citations below are the record of what was measured,
> and no longer resolve to files you can open — the flawed sources were removed
> rather than shipped alongside a skill that exists to prevent exactly these
> defects. [`VERIFICATION.md`](VERIFICATION.md) answers this list item by item.
>
> Most of what follows is invisible when reading the source. That is the point:
> these are the failure modes that only appear once you measure the pixels, and
> they are what the skill's rules and `verify_render.py` checks were derived
> from.

**Source analysed:** `output/GANs_Explained_Full.mp4` — 213.1s, 1920×1080, 30fps, 11 scenes.
Timestamps below are **absolute, in the concatenated full video**. Scene-relative offsets in `[brackets]`.

Method: contact sheets at 0.5fps, full-res frame extraction at suspect moments,
plus three programmatic passes (edge-content detector, dead-air/cut/hold detector,
pixel-hue sampler). Nothing below is inferred from reading code alone — every
item is confirmed in the rendered pixels.

## Scene map (absolute start times)

| # | Scene | Start | Dur |
|---|---|---|---|
| 0 | ColdOpen | 0.0 | 21.6 |
| 1 | GeneratingMeaning | 21.6 | 26.0 |
| 2 | GeneratorScene | 47.6 | 18.5 |
| 3 | DiscriminatorIntro | 66.1 | 12.5 |
| 4 | DiscriminatorLearns | 78.6 | 21.5 |
| 5 | TheGame | 100.1 | 22.0 |
| 6 | DistributionsChase | 122.1 | 20.2 |
| 7 | GradientScene | 142.3 | 18.5 |
| 8 | ModeCollapse | 160.8 | 17.4 |
| 9 | LatentInterpolation | 178.2 | 16.7 |
| 10 | FinalSynthesis | 194.9 | 18.2 |

---

## A. Critical — colour semantics are dead across the whole video

### A1. Every `Dot` in the video renders WHITE, regardless of the colour asked for
**Severity: critical. Affects 7 of 11 scenes.**

Measured by sampling lit pixels (>90 max channel) at full resolution:

| Frame | What it should show | % of lit pixels that are near-grey (sat<0.15) |
|---|---|---|
| 18.0s ColdOpen point cloud | blue "real" + orange "fake" dots | **100.0%** |
| 44.0s GeneratingMeaning latent dots | orange z-samples | 75.8% (rest is text) |
| 97.0s DiscriminatorLearns scatter | 25 blue "real" + 25 orange "generated" | **95.9%** |
| 170.0s ModeCollapse latent dots | orange z-samples | **100.0%** |

At 97.0s the scatter plot's entire pedagogical point is that real and generated
points are two separable clouds — and both clouds render identical white. The
legend directly below says "real" / "generated" in blue and orange text next to
two white dots.

**Root cause (verified in `manimlib/mobject/geometry.py:321`):** ManimGL 1.7.2 declares
```python
class Dot(Circle):
    def __init__(self, point=ORIGIN, radius=..., stroke_color=BLACK,
                 stroke_width=0.0, fill_opacity=1.0, fill_color=WHITE, **kwargs):
        super().__init__(..., fill_color=fill_color, **kwargs)
```
A `color=ORANGE` argument falls into `**kwargs`, but `fill_color=WHITE` is passed
**explicitly** to the parent and wins. The colour argument is silently discarded.

**Same trap in two sibling classes:**
- `Arrow` (`geometry.py:731`) hard-declares `fill_color=GREY_A` → every `Arrow(color=ORANGE)`
  in scenes 2/3/10 renders grey. Confirmed: the orange fake-data path and blue real-data
  path in FinalSynthesis are both grey.
- `Circle` (`geometry.py:286`) hard-declares `stroke_color=RED`.

**Natural experiment confirming it:** `scene06_distributions.py` is the *only* scene that
sets colour via `fill_color=`/`get_graph(color=)` rather than a bare `color=` on a Dot —
and it is the only scene whose colours render correctly (see the clean blue/orange
distribution curves at 122–142s).

**Correct alternative:** never pass bare `color=` to `Dot`/`Arrow`/`Circle`. Use
`Dot(pt, radius=r).set_color(C)`, or `Dot(pt, radius=r, fill_color=C)`.

### A2. Colour mapping is not consistent even where it does render
- BLUE = "real data" in scenes 0, 3, 4, 6, 10.
- BLUE is reused for **"the generated image x̂"** in scene 2 (`layer_colors[3] = BLUE_C`,
  label "image (x̂)") — the exact opposite meaning, 20s later.
- BLUE is reused again for **"generator loss L"** in scene 7 (144–160s).
- ModeCollapse (164.5s) draws *generated* faces with **blue** borders under the label
  "Good training: diverse faces", then the same faces with orange borders at 166.5s.
  Blue was established as "real" in the cold open.
- YELLOW means "the generator" (scenes 2, 5, 10), "emphasis text" (scenes 0, 1, 8),
  "the needle" (scene 4), and "z₂" (scene 9).

---

## B. Transitions that cut rather than transform

### B1. 24.0 seconds — 11% of the video — is a fully blank black frame
Programmatic detection (frames where <0.4% of the frame is lit, runs ≥0.4s). **21 windows:**

```
  0.0– 0.7 (0.7s)   21.0– 22.2 (1.2s)   30.6– 31.6 (1.0s)   37.2– 38.1 (0.9s)
 47.2– 49.1 (1.9s)  52.9– 55.3 (2.4s)   65.6– 66.8 (1.2s)   69.9– 70.6 (0.7s)
 78.1– 79.3 (1.2s)  87.3– 88.0 (0.7s)   91.2– 92.5 (1.3s)   99.7–100.5 (0.8s)
108.9–110.9 (2.0s) 113.5–113.9 (0.4s)  121.6–122.3 (0.7s)  141.9–142.8 (0.9s)
154.3–154.9 (0.6s) 160.4–161.3 (0.9s)  177.7–180.6 (2.9s)  194.5–195.2 (0.7s)
212.2–213.1 (0.9s)
```

**10 of the 11 scene boundaries pass through black.** The three worst are internal:
- **52.9–55.3s (2.4s blank)** — GeneratorScene, between the `z→[G]→x̂` block diagram
  and the layered network. These are the *same object* at two zoom levels; the code
  fades the whole diagram out and builds a new one (`scene02_generator.py:77-81`).
- **108.9–110.9s (2.0s blank)** — TheGame, between the training-loop diagram and the
  minimax objective.
- **177.7–180.6s (2.9s blank)** — the ModeCollapse→LatentInterpolation boundary. Nearly
  three seconds of nothing.

Every one of these is a `FadeOut(VGroup(everything))` followed by construction of a fresh
mobject set. There is not a single `Transform` across a scene boundary in the entire video.

### B2. Objects teleport instead of moving — DiscriminatorIntro, ~71.5s [+5.4s]
`scene03_discriminator_intro.py:87-89` calls `d_box.move_to(RIGHT*1.8)` **un-animated**,
after the box is already on screen at ORIGIN.

Verified frame-by-frame: at **71.0s** the DISCRIMINATOR box is centred at x=960px;
at **72.2s** it is at x=1200px. No intervening animation — it jumps. Same for its
label and the "Real or Fake?" caption.

### B3. Visible 3-frame snap hack — TheGame, ~104.5s [+4.4s]
`scene05_game.py:44-57` animates `g_box` and `g_lbl` to new positions as two independent
targets, which desynchronises them, then "fixes" it with a `run_time=0.1` play call that
snaps the labels back into their boxes. That is a 3-frame visual jitter.

### B4. Edges drawn before the nodes they connect — GeneratorScene, ~55.5s [+7.9s]
`scene02_generator.py:109-117` plays all `edge_groups` first, then the `layers`. For ~1.8s
the screen shows a lattice of lines connecting nothing, then circles pop in on top of the
line endpoints. The build order inverts the dependency.

---

## C. Orphaned objects and element collisions

### C1. `img2` is rendered off-frame — GeneratorScene, 62.2–65.4s [+14.6s]
**Detected programmatically** (content in the outer 8px of the right edge, 62.2→65.4s).

`scene02_generator.py:163-164`:
```python
img1.to_corner(DR, buff=0.8).shift(UP * 1.0)
img2.next_to(img1, RIGHT, buff=0.5)   # ← img1 is already at the right corner
```
`img2` and its label `x̂₂` are pushed past the right edge. The frame shows `x̂₁` hard
against the border and a sliver of `img2` bleeding off-screen. The beat is
"two nearby z's give two similar images" — the second image is not visible.

### C2. The loss parabola is clipped by the top edge — GradientScene, 144.2–154.0s [+1.9s]
**Detected programmatically** (top-edge content for 9.8 continuous seconds).
`axes.get_graph(0.4x² + 0.3sin2x + 1.5)` over `x_range=(-3.5, 3.5)` reaches y≈6.4 while
`y_range` tops out at 3.2. Both arms of the bowl run off the top of the frame for the
entire beat.

### C3. Latent-space inset overlaps the neural network — GeneratorScene, ~59–65s
`lat_axes.to_corner(DL)` (`scene02_generator.py:138`) lands on top of the network's first
layer, which spans x=-4.5. The axes cross through the orange input nodes and the
"Latent space" title is partially occluded by the "noise (z)" label.

### C4. Two captions drawn on top of each other — TheGame, 114–117s [+14s]
`scene05_game.py:155-165` writes `t2_lbl` at `to_edge(DOWN, buff=0.8)` while fading out
`t1_lbl` at the identical position, in the same `self.play`. For ~0.9s the frame reads
`G minimises D'…robability to real images` — two sentences superimposed.

### C5. Closing text drawn through the diagram — FinalSynthesis, 205–211s
`scene10_final_synthesis.py:148-155` places `closing2` below `closing`, which puts it
directly over `g_box` (still on screen at `UP*1.8`). The line "is constantly trying to
prove" runs straight through the rectangle.

### C6. Empty grey rectangles left on screen — FinalSynthesis, 202–212s [+7s]
`scene10_final_synthesis.py:126-131` fades out `g_lbl`/`d_lbl` and greys the boxes, then
strips the arrows. What remains for the final 10 seconds — under the closing statement —
is two unlabelled grey rectangles and a green polyline. The diagram is not resolved into
anything; it is disassembled into debris.

### C7. "Decision boundary" label collides with plot and legend — DiscriminatorLearns, ~96–99s
`scene04:153` anchors the label `RIGHT` of the top of the boundary line, putting it inside
the plot area and adjacent to the UR legend.

### C8. `D(x) = ½` sits on the axis line — DistributionsChase, ~138–141s
The equation is placed at the bottom where the x-axis and the converged curve's baseline
run through it.

---

## D. Broken reveals

### D1. Highlight boxes land on nothing / on everything — TheGame, 113–121s
`scene05_game.py:138-141` indexes a Tex glyph array using **the character length of the
LaTeX source string**:
```python
full_obj[0][len(r"\min_G \max_D \,"):len(r"\min_G \max_D \,") + 30]
```
`len(...)` is 17 — a count of source characters, unrelated to glyph positions. The
resulting `SurroundingRectangle` collapses to a ~4px dot floating in empty space below
the equation (visible at 114.5s).

Then `term2_box` (line 151-153) is a `SurroundingRectangle(full_obj)` — the comment in the
source says `# approximate — whole eq as fallback`. The "highlight term 2" beat draws a
box around the **entire equation**, highlighting nothing.

Net effect: the two-term breakdown of the GAN objective — the mathematical core of the
video — has no working visual.

### D2. `min_G max_D` is duplicated on screen — TheGame, 111–121s
`min_max` is written at `UP*2.8` and left there; `full_obj` (which *contains*
`\min_G \max_D`) is then written at `UP*1.0`. Both are on screen simultaneously for 10s.
The standalone term was never transformed into the full objective — it is an orphan.

### D3. Digits stack on top of each other — LatentInterpolation, 180–194s
`scene09:101` calls `Transform(cur_t, t_lbl)` repeatedly on the same mobject with `Tex`
strings of differing glyph counts. Verified at 186.4s: the label reads `t = 0.5` with the
final digit rendered as **`0` and `8` superimposed**. Every t-value in the 9-step walk is
garbled this way.

### D4. Dead code — `scene04:132-135` defines `boundary(t)`, never called.

---

## E. Timing

### E1. Reveals that land too fast to read
| Time | Element | Budget | Words |
|---|---|---|---|
| 100.7s | "GENERATOR" + box | 0.7s | — |
| 112.5s | full minimax objective, `Write(run_time=2.5)` | 2.5s | a 40-glyph equation with 2 expectations |
| 80.1s | `ShowCreation(dial_group)` — line, 2 ticks, 3 labels | 1.0s | 6 elements at once |
| 158.6s | 5-item backprop chain via LaggedStart | 1.5s | 5 multi-word labels |

The minimax objective at 112.5s is the hardest single frame in the video and gets 2.5s to
draw plus 0.6s to hold before the first (broken) highlight begins.

### E2. Holds that drag
12 static holds ≥2.0s where nothing changes at all:
```
  3.6– 6.0 (2.4s)   18.1– 20.3 (2.2s)   39.2– 41.3 (2.1s)   44.4– 46.6 (2.2s)
 59.5– 61.9 (2.4s)  75.4– 77.6 (2.2s)   96.9– 99.1 (2.2s)  138.8–141.3 (2.5s)
157.7–159.9 (2.2s) 175.0–177.2 (2.2s)  191.7–193.9 (2.2s)  208.1–211.5 (3.4s)
```
These are uniform `self.wait(2.0)` calls, not pacing decisions — the same 2.2s hold lands
on a trivial frame (18.1s, six photos already seen) and on a dense one. Combined with §B1,
**roughly 50 of 213 seconds are either blank or frozen.**

### E3. The video ends on 0.9s of black with no closing card (212.2–213.1s).

---

## F. Narrative — where the thread is lost

### F1. There is no driving question
The cold open asks at 0:10, *"If you had a million examples, could a machine learn to make
new ones?"* — then at 0:18 **replaces** it with a different framing, *"The goal: learn the
distribution, not memorise examples."* The first question is faded out (`scene00:124`) and
never returned to. Nothing in the remaining 195 seconds refers back to either line.
The video ends on a statement about feedback loops that answers neither.

### F2. Formalism arrives before motivation, repeatedly
- **z ~ N(0, I) at 38s**, before the viewer has been told why a random seed is needed.
  The notation lands 4 seconds after the "image space" blob picture, with no bridge.
- **The minimax objective at 112.5s** arrives immediately after a bullet-list of the
  training loop. Nothing has motivated *why* the objective takes the log-expectation form.
  The two annotations ("D tries to distinguish", "G tries to fool D") are asserted, then
  faded out before the equation appears — so the equation is unlabelled when it lands.
- **The gradient-descent beat (142s)** introduces a loss landscape for the generator
  without ever establishing what the generator's loss *is*.

### F3. No carried visual metaphor
Each scene invents new imagery and abandons it:
photos → 1-D curve → 2-D blobs → latent square → block diagram → node graph → number line
→ scatter plot → two boxes → text list → equation → two curves → parabola → thumbnails →
latent square → block diagram. **Fifteen distinct visual systems in eleven scenes.** The
"latent square" and "block diagram" recur but are rebuilt from scratch each time rather
than persisting.

### F4. Claims that arrive unearned
- **95s: "It only needs a boundary separating real from fake."** Asserted as text. The
  scatter plot that would justify it appears *after* the claim, and its two classes render
  in the same colour (§A1), so it cannot justify anything.
- **122–142s: the distributions converge.** The p_G curve slides onto p_data and the label
  says "Curves converge: real = generated". *Why* the chase converges is never shown — it
  is asserted by animating the answer.
- **142s: "Loss landscape of the Generator."** A parabola with a ball rolling to the
  bottom. This is a generic gradient-descent stock image; nothing ties its x-axis to
  anything the viewer has seen, and the actual interesting fact (that G's gradient arrives
  *through* D) is relegated to a text list at 155s.
- **160.8s: mode collapse.** Introduced as "A subtle problem" with no setup for why the
  generator would do this. The positive-feedback explanation is one line of yellow text.

### F5. The payoff does not resolve anything
FinalSynthesis (194.9s) ends on *"Nobody ever tells the generator what a good image looks
like. It learns because another network is constantly trying to prove that its images are
fake."* That is a decent closing line — but it answers a question the video never asked,
delivered over two unlabelled grey rectangles (§C6), followed by black.

---

## Summary of what has to change

| | Count |
|---|---|
| Confirmed rendering bugs (wrong colour, off-frame, garbled, teleport) | 12 |
| Element collisions | 6 |
| Blank-frame windows | 21 (24.0s) |
| Frozen holds ≥2s | 12 (27.8s) |
| Distinct visual systems for one topic | 15 |
| Transforms carrying an idea across a scene boundary | **0** |
