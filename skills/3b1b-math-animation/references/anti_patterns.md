# Anti-Patterns

Every entry here is a **defect that actually shipped** in a rendered video, was
confirmed in the pixels, and has a verified fix. When writing scene code, check
against this list before rendering — most of these are invisible in the source
and only appear on screen.

#1–#12 are ordered by how much damage they cause. #13–#18 are the 3D-specific
ones; they only apply to scenes with a tilted camera, and every measurement in
them came from rendering the failing case and counting the pixels. See
`three_d.md` for the positive version of those rules. #19–#22 are the audio
ones, measured on a narrated render; see `narration.md`.

---

## #1 — `color=` is silently ignored by `Dot`, `Arrow` and `Circle`

**Damage: catastrophic.** Killed colour semantics across an entire 213s video.

ManimGL 1.7.x hard-declares colour defaults in these `__init__` signatures:

```python
class Dot(Circle):
    def __init__(self, point=ORIGIN, radius=..., stroke_color=BLACK,
                 stroke_width=0.0, fill_opacity=1.0, fill_color=WHITE, **kwargs):
        super().__init__(..., fill_color=fill_color, **kwargs)   # WHITE wins
```

A `color=ORANGE` argument lands in `**kwargs`; `fill_color=WHITE` is passed
**explicitly** to the parent and overrides it. No warning is emitted.

| Class | Hard-coded default that wins |
|---|---|
| `Dot` | `fill_color=WHITE` |
| `Arrow` | `fill_color=GREY_A` |
| `Circle` | `stroke_color=RED` |

Measured: `Dot(ORIGIN, color=ORANGE)` → RGB(253,255,253). In the shipped video,
**95.9%** of lit pixels in a two-class scatter plot were near-grey — real and
generated points rendered identically, directly under a legend that colour-coded
them.

```python
# WRONG - renders white
d = Dot(pt, radius=0.08, color=ORANGE)
a = Arrow(p, q, color=BLUE_C)

# RIGHT
d = Dot(pt, radius=0.08).set_color(ORANGE)          # or fill_color=ORANGE
a = Arrow(p, q); a.set_fill(BLUE_C, 1); a.set_stroke(BLUE_C, 3)

# BEST - use the helpers
from manim_helpers import dot, arrow
d = dot(pt, ORANGE, radius=0.08)
a = arrow(p, q, BLUE_C)
```

Note the tell: shapes styled with explicit `.set_stroke()` / `fill_color=`
rendered correctly in the same video, while every bare `color=` did not.

---

## #2 — Rendering beats as separate scenes and concatenating them

**Damage: 24.0s (11% of runtime) of blank black frames, 21 windows.**

Eleven `Scene` subclasses, each ending in `FadeOut(everything)` and starting from
an empty frame, concatenated with `ffmpeg`. **Ten of eleven boundaries passed
through black.** No object could possibly persist across a boundary, so no
transition could be a transform.

```python
# WRONG - one Scene per beat, concatenated
class Beat1(Scene): ...
class Beat2(Scene): ...

# RIGHT - one Scene, section methods, persistent state
class MyVideo(Scene):
    def construct(self):
        self.cap = Caption(self)
        self.s0_question()      # sets self.thing
        self.s1_motivation()    # transforms self.thing
```

Also fix the intra-scene version: `FadeOut(VGroup(...everything...))` followed by
building a fresh set. Dim instead, or transform one object through.

---

## #3 — Un-animated `move_to` on a mobject that is already on screen

**Damage: objects teleport.**

```python
self.play(ShowCreation(d_box), Write(d_lbl))    # box appears at ORIGIN
...
d_box.move_to(RIGHT * 1.8)                      # ← teleports on next play()
d_lbl.move_to(d_box)
self.play(ShowCreation(arrow))
```

Verified: the box was at x=960px at t=71.0s and x=1200px at t=72.2s with no
animation between.

```python
# RIGHT
self.play(d_box.animate.move_to(RIGHT * 1.8),
          d_lbl.animate.move_to(RIGHT * 1.8), run_time=0.8)
```

**Related:** do not animate a box and its label as two independent targets and
then "fix" the drift with a `run_time=0.1` correction play — that is a visible
3-frame snap. Group them, or position the label inside the box at construction
and move the group.

---

## #4 — Fading out one caption while writing another at the same position

**Damage: two sentences drawn on top of each other for ~0.9s.**

```python
# WRONG - both occupy the same point simultaneously
self.play(FadeOut(t1_lbl), Write(t2_lbl), run_time=0.9)
```

```python
# RIGHT - use Caption, which clears before writing
cap = Caption(self)
cap.show("first line", narration="...")
cap.show("second line", narration="...")     # fades the first out first
```

Only overlap two texts when you are genuinely `ReplacementTransform`-ing one into
the other (`morph_from_prev=True`), where the glyphs interpolate rather than
stack.

---

## #5 — Indexing a `Tex` glyph array to highlight part of an equation

**Damage: the highlight box lands on nothing; the "explain the formula" beat has
no working visual.**

```python
# WRONG - len() of the LaTeX SOURCE has nothing to do with glyph positions
term = full_obj[0][len(r"\min_G \max_D \,"):len(r"\min_G \max_D \,") + 30]
box = SurroundingRectangle(term)        # collapsed to a 4px dot in empty space

# ALSO WRONG - the "fallback" that boxes everything
box2 = SurroundingRectangle(full_obj)   # highlights the entire equation
```

Both shipped in v1, in the beat explaining the GAN objective — the mathematical
core of the video.

```python
# RIGHT - build the equation from separately addressable Tex objects
t_real = Tex(r"\mathbb{E}_{x\sim p_{\text{data}}}\big[\log D(x)\big]")
t_fake = Tex(r"\mathbb{E}_{z\sim p_z}\big[\log(1 - D(G(z)))\big]")
obj = equation(t_real, "+", t_fake, scale=0.78)

self.play(ShowCreation(box_around(t_real, C_REAL)))   # a real mobject
```

If you must address sub-parts of a single `Tex`, use `TransformMatchingTex` or
`set_color_by_tex` — both match on substrings, never on integer offsets.

**Corollary:** don't fly equation terms onto a busy region to "label" it. Dense
LaTeX over a dot cloud destroys both. Box the term where it sits and
`FlashAround` the region at the same moment — colour already links them.

---

## #6 — `Group.set_opacity()` to dim and restore

**Damage: outlines return as solid blocks; per-element alpha is flattened.**

`set_opacity` drives **fill and stroke to the same value**. Anything drawn as an
outline (`fill_opacity=0`) — a plot frame, an empty box — comes back as a filled
rectangle. In v1's successor this turned the image-space plane into a solid grey
slab.

The same bug in reveal form: setting a group to opacity 0 and animating to 1
overwrites every element's individually computed opacity with a flat 1.0, turning
a soft height map into a hard two-tone poster (and re-enabling stroke, which adds
seams).

```python
# WRONG
self.play(stage.animate.set_opacity(0.16))
self.play(stage.animate.set_opacity(1.0))     # outlines now solid

# RIGHT - snapshot each leaf's own opacities and scale them
stage = Dimmer(field, dots, frame_rect, axes, profile)
self.play(*stage.to(0.16), run_time=0.9)
...
self.play(*stage.restore(), run_time=1.1)
```

Two traps inside any such helper:
- `get_family()` yields point-less group containers; `set_fill()` raises on them.
  Filter with `m.has_points()`.
- `get_fill_opacity()` returns **`np.float32`, which is not a subclass of Python
  `float`** (`np.float64` is). ManimGL's `set_fill` tests
  `isinstance(opacity, (float, int))` to choose scalar vs per-point array, so an
  `np.float32` takes the array branch and dies on `len()` of a 0-d value. Cast
  with `float()`.

---

## #7 — Drawing a scalar field as a grid of translucent rectangles

**Damage: a smooth height map renders as a bar chart.**

Translucent rectangles cannot tile cleanly:
- **overlapping** them (`width * 1.2`) double-blends the seams → a *bright* grid
- **abutting** them exactly leaves antialiasing hairlines → a *dark* grid

Both were rendered and rejected. Rasterise instead — one `ImageMobject`, no
seams, crisp at any zoom, and far cheaper than 1000+ mobjects:

```python
field = raster_field(lambda X, Y: D(X, Y), x_range, y_range,
                     width, height, center, cache_path)
```

`ImageMobject` needs a **file path** (it does not accept a numpy array), so write
the PNG to a cache directory first — `raster_field` does this.

To change the field, cross-dissolve with `swap_raster(...)` and pass a genuine
`Transform` of a derived curve as `extra=` so identity is carried by the thing
that truly morphs.

---

## #8 — Content positioned relative to something already at the frame edge

**Damage: an element rendered entirely off-screen for 3.2s.**

```python
# WRONG
img1.to_corner(DR, buff=0.8)
img2.next_to(img1, RIGHT, buff=0.5)      # img1 is already at the right edge
```

The beat was "two nearby seeds give two similar images" — the second image was
not visible.

```python
# RIGHT - assert it, and let the build fail loudly
img2.next_to(img1, RIGHT, buff=0.5)
assert_in_frame(img1=img1, img2=img2)
```

This guard caught two real off-frame errors during the rebuild (a label at
x=-6.93 and a closing image at y=-3.75) before either reached a render.

**Same family:** plotting a function whose range exceeds the axes' `y_range`.
`0.4x² + 0.3sin(2x) + 1.5` over `x ∈ [-3.5, 3.5]` reaches y≈6.4 against a
`y_range` topping out at 3.2 — both arms ran off the top of the frame for 9.8
continuous seconds. Evaluate the function at the x-range endpoints and check.

---

## #9 — Drawing connectors before the things they connect

**Damage: ~1.8s of lines joining nothing, then circles popping in on top.**

```python
# WRONG
for eg in edge_groups: self.play(ShowCreation(eg))   # edges first
for lay in layers:     self.play(GrowFromCenter(lay))
```

Build in dependency order: nodes, then edges; axes, then curve; surface, then
the symbol naming it.

---

## #10 — Repeated `Transform` on a `Tex` whose glyph count changes

**Damage: digits stack on top of each other.**

```python
# WRONG - "t = 0.50" rendered with 0 and 8 superimposed
t_lbl = Tex(f"t = {t:.2f}")
self.play(Transform(cur_t, t_lbl))      # called 9 times on the same mobject
```

Use a `DecimalNumber` with a `ValueTracker`, or `ReplacementTransform` to a fresh
mobject and rebind the reference each step.

---

## #11 — Uniform `self.wait(2.0)` after every beat

**Damage: 12 holds ≥2s totalling 27.8s; drags on trivial frames, rushes dense
ones.**

Holds must vary with content. Derive them from the narration line:
`Caption.show(text, narration="the actual spoken sentence")`. Use `hold()` for
post-reveal landings only.

When a section comes out rushed, add holds **at natural landing points in that
section** — never scale every hold in the video uniformly.

---

## #12 — Dead code and vestigial helpers

`scene04` defined a `boundary(t)` function that was never called. Harmless at
runtime, but it signals that the scene was edited without being re-read, and it
misleads the next person. Delete it.

---

## #13 — Flat 2D mobjects used inside a 3D scene

**Damage: captions render at a 70° slant and half-buried in the geometry; dots
render as ellipses.**

A `Text` that is not fixed in frame is a sheet of glyphs lying in the world's
xy-plane, and a `Dot` is a flat disc in that same plane. Rendered at the default
`ThreeDScene` viewpoint:

| | Result |
|---|---|
| unfixed caption | skewed and occluded by the surface — measured unreadable |
| `Dot` | ellipse, **19×6 px, aspect 3.2** (it is `cos(phi)` squashed) |
| `TrueDot` | circular at every depth: 24, 20, 18 px across at three distances |

```python
# WRONG
cap = Text("...").move_to(UP * 3.4)
d = Dot(axes.c2p(0, 0, 0)).set_color(YELLOW)

# RIGHT
cap = fix(Text("...").move_to(np.array([0, 3.42, 0])))   # fix_in_frame + no depth test
d = dot3d(axes.c2p(0, 0, 0.08), YELLOW)                  # TrueDot, lifted clear
```

`Caption(scene)` fixes itself automatically inside a `ThreeDScene`.

---

## #14 — `fix_in_frame()` after `self.add()`, and flat fills that swallow layers

**Damage: a caption rendered with its first four characters missing.**

`ThreeDScene.add()` switches depth testing on for everything it adds. Fixing a
mobject in frame afterwards pins it to the screen but leaves the depth test on,
so the surface in front of it still wins:

| | Rendered |
|---|---|
| `fix_in_frame()` **before** `add()` | full text, 3723 px |
| `fix_in_frame()` **after** `add()` | 989 px — the left half eaten by the surface |
| after `add()`, plus `deactivate_depth_test()` | full text |

The general form of this is worse than it sounds. Under depth testing, an opaque
VMobject fill hides anything drawn over it **regardless of distance**:

```python
rect = Rectangle(...).set_fill(BLUE_E, 1)
lbl = Text("label").move_to(rect).shift(OUT * 1.0)   # 1.0 units toward camera
self.add(rect, lbl)                                  # -> zero pixels of label
```

Measured: text nudged 0.1 and 0.5 toward the camera — invisible. A filled circle
nudged **1.0** — invisible, in both draw orders. The same label over an
*unfilled* rectangle renders fine. Nudging is not a fix; turning the depth test
off for the top layer is:

```python
lbl = flat(Text("label").move_to(rect))      # deactivate_depth_test()
# or, for anything that belongs to the HUD rather than the world:
lbl = fix(Text("label"))
```

---

## #15 — `assert_in_frame()` on a scene whose camera is tilted

**Damage: a false pass. The guard reports nothing while a label sits off the
edge.**

`assert_in_frame()` compares **world** coordinates against the frame rectangle.
Once the camera has been reoriented, world coordinates and screen position are
unrelated: a label at world x = 6.5 can be dead centre on screen, and a label at
the world origin can be outside the frame.

```python
# WRONG in 3D
assert_in_frame(label=lbl)

# RIGHT - projects through the view matrix and the perspective divide
assert_in_frame_3d(self, label=lbl)
```

The projection was checked against rendered pixels: four probe points landed
within 1 px of prediction. Call it **at the orientation the label is meant to be
read at** — a label that is perfectly placed at `theta = −30` can be off the
edge at `theta = +40`, and only the projection at that angle knows.

The same correction applies to `audit_text_overlaps`, which now compares
projected boxes for anything not fixed in frame.

---

## #16 — Dimming a 3D stage with a VMobject-only helper

**Damage: the surface stays at full brightness while everything else dims.**

A `Surface` is **not** a `VMobject` (verified: `isinstance(surf, VMobject)` is
`False`), and neither are `TrueDot`, `GlowDot` or `DotCloud`. They have no
fill/stroke split — one opacity each. Any helper that walks `get_family()`
looking for `VMobject` leaves them untouched and reports no error.

`Dimmer` handles all of them. Do not reach for `Group.set_opacity()` instead —
that is ANTI-PATTERN #6, and in 3D it also flattens the surface's shading.

---

## #17 — A curve drawn exactly on the surface it slices

**Damage: one of two slice curves rendered zero pixels for a whole section.**

A slice curve shares every point with the surface, so the two fight for each
pixel and the curve renders in patches or not at all — and which one wins
changes with the camera angle, so it can look fine in one still and vanish in
the next.

```python
# WRONG - coincident with the surface
cut = path3d(lambda t: axes.c2p(t, 0, f(t, 0)), (-R, R), BLUE_C)

# RIGHT - lifted clear (slice_curve does this by default, lift=0.05)
cut = slice_curve(axes, f, (-R, R), direction="x", color=BLUE_C)
```

Lifting in +z always clears a graph surface, because such a surface has exactly
one height per (x, y). Markers sitting on a surface need the same treatment.

**Related, same section:** an *undeclared* camera rotation fails
`verify_render.py` checks [1] and [4] — a rotating frame produces the same pixel
signature as content falling off the edge and as a hard cut. `orbit()` and
`spin()` record the window; a hand-written `frame.animate.reorient(...)` does
not.

---

## #18 — Building a 3D solid out of `Square`, `Polygon` or any other VMobject

**Damage: catastrophic, and it does not look like a bug.** A Rubik's cube built
from `Square`s rendered *inside out*: every face turned toward the camera was
missing, and the interior of the far side showed through the gap.

A VMobject's fill is not a filled polygon. ManimGL draws it by winding number
in screen space, and a polygon seen from behind winds the other way, so the
fill cancels to nothing. In 2D this never comes up — everything faces the
camera. In 3D exactly half of any closed object faces away.

The give-away is that the *far* geometry renders and the *near* geometry does
not, which reads as a depth-test bug and is not one. Turning the depth test
off does not help; nor does draw order.

```python
face = Square(side_length=1).set_fill(GREEN, 1)      # a hole, from one side
face = Square3D(side_length=1, color=GREEN, opacity=1)   # a face, from both
```

`Square3D`, `Disk3D`, `Cube`, `Prism` and `Sphere` are `Surface` subclasses and
have no winding problem. They also take `shading`, which is what makes six
identically-coloured faces distinguishable. Strokes are fine either way — a
stroke has no fill to wind — so an outline drawn over a solid can stay a
VMobject, and should, since `Surface` has no stroke.

Two consequences worth knowing before you hit them:

- A `Surface` cannot go in a `VGroup`. Use `Group`.
- **Two coincident faces z-fight, and the fix is a gap, not a bigger offset.**
  This is #17 again in a different costume, and it took two passes to get
  right, so both passes are worth writing down.

  On the cube, each cubie's outer face sits at 0.5 of a cubie from its centre
  and its neighbour's inner face sits at 0.5 from *its* centre — the same
  plane. Both are black, which is why it looks harmless, but they carry
  opposite normals and therefore different shading, so the depth test hands a
  thin strip to one and the rest to the other. Measured, magnified 3×: **a
  grey hairline down the middle of every black channel on the cube**, crawling
  as the camera moves.

  Pushing the *stickers* further forward does not touch that — they were never
  the pair that was fighting. Shrinking the cubie body to 0.97 so neighbours
  are 0.03 apart does, and the channels go solid black.

  The stickers then want the opposite treatment. At 0.03 proud of the body
  they stand off it: the far side's stickers poke past the silhouette as
  coloured hairlines, and up close the tiles look like they are hovering.
  0.008 of a cubie is 0.0096 world units at this scale — still four times what
  the depth buffer needed, and sub-pixel at 1080p.

  **A seam artifact can hide a pacing defect.** After the seams were fixed,
  `verify_render.py` check [3] reported a 12.6 s frozen hold that had passed
  every earlier run. It had always been there; the z-fighting was churning
  enough pixels on its own to keep the frame-to-frame delta above the freeze
  threshold. Any check that measures "did anything change" can be fooled by
  something changing for the wrong reason, so re-run the full suite after
  fixing a rendering artifact — not just the check that was failing.

---

## #19 — Fitting the narration to the animation

**Damage: structural.** It forces every later choice.

A spoken line has one correct duration. Speed it up and it gabbles; stretch it
and it drags. A hold is any length you like. So the audio is the rigid thing
and it has to be cut first — synthesise the script, measure each line, and let
the scene wait for real durations. Fitting words to a finished render leaves
only two options at every beat, both bad: overlap the next line, or cut the
sentence.

The scene then records the frame each line starts on and the mux lays each file
down there. **If the result is out of sync, do not adjust the mux** — the scene
and the audio were built from different versions of the script.

Related: cue the line *before* writing the caption, not after. The voice starts
as the words appear. Cueing after the `Write` puts every line ~1.3s late and
the error accumulates.

---

## #20 — Keeping the spoken words in the scene file

**Damage: moderate, and it compounds.** Two copies of a sentence means the one
that gets edited is not the one that gets spoken.

Put every line in `script.yaml` under a beat id and refer to it by id. The
narration can then be read as prose — the only way to hear whether it is an
argument or a list — and the voice can be recast without touching animation
code. `Narrator.dump()` reports beats no cue used; a beat you wrote and forgot
to place is silent in the render and invisible in review.

---

## #21 — Asking the TTS engine for the pauses

**Damage: silent desync that grows.** The duration the scene waited for has to
be the duration the file actually is.

Engine break tags drift or are ignored, and engines pad their output
unpredictably: measured on Kokoro, the same sentence returned with between
30 ms and 210 ms of lead-in depending on the first phoneme. That padding lands
inside the gap the scene reserved for the line, and the next line starts a
little later, and the one after that a little later still.

`tts.py` writes `[[0.4]]` as a real 0.4 s of digital silence: each side is
synthesised separately, trimmed, and rejoined. Identical on every engine, and
exactly as long as it says.

---

## #22 — Narration with no gaps in it

**Damage: measured.** A first cut of the Rubik's video was **92% speech**, and
the same cut had frozen holds of **14.2 s** and **12.7 s**.

Those are one defect seen from two sides: the words were doing all the work,
and the picture was doing none. `verify_audio.py` fails above 88% coverage and
`verify_render.py` check [3] fails a still frame that outlasts any plausible
line, so a video like this fails both.

The fix is never to trim the script uniformly. It is:

- where a long line sits over a still frame, **show the claim** — "every turn
  moves nine cubies at once" became one layer lit, turned, and turned back;
- where the video needs air, spend a **wordless beat** with slow motion under
  it — `spin(self, 3.5, speed=-5.0)`, nothing said — after the driving
  question, after the payoff, and on the one image the section was built to
  reach.

Target 75–85% coverage. Passing the checks is a side effect of the picture
carrying its share.


---

## Narrative anti-patterns

| Anti-pattern | Correct alternative |
|---|---|
| Opening question replaced by a different framing 8s later and never revisited | One question, stated by 0:20, restated verbatim in the payoff |
| A new visual system per section (v1: **15 across 11 sections**) | One carried metaphor, introduced early, on screen at the end |
| Notation before the picture it names (`z ~ N(0,I)` at 0:38 with no motivation) | Picture → words → symbol, always in that order |
| Asserting a result by animating it ("Curves converge: real = generated") | Make the metaphor literally the real object, so the result is computed |
| Bullet lists of text as a "visualisation" (a 5-item backprop chain) | Show the mechanism, or cut the beat |
| Closing on a statement that answers a question the video never asked | Payoff resolves the opening question explicitly |
| Diagram disassembled into unlabelled grey rectangles at the end | Resolve the visual, then clear it deliberately |
