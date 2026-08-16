# 3D Scenes and Presentations

Everything here was verified by rendering it in ManimGL 1.7.2 and measuring the
resulting pixels. Where a number appears — a pixel count, an aspect ratio, a
render time — it was measured, not estimated. The defects this file prevents are
listed as ANTI-PATTERNS #13–#17 in `anti_patterns.md`; the helpers are in the
`3D` section of `scripts/manim_helpers.py`; the worked example is
`examples/saddle/`.

---

## 1. Does this need to be 3D?

**The test: state the claim the scene has to prove, then ask whether a flat
picture can prove it.** If it can, 3D is costing you legibility for nothing —
depth cues eat contrast, occlusion hides half your labels, and the viewer spends
attention reconstructing geometry instead of following an argument.

Three cases genuinely earn it:

| Case | Example |
|---|---|
| The argument *is* the missing dimension | the origin of `z = x² − y²` is a minimum along one slice and a maximum along another; only depth resolves the contradiction |
| The object is 3D | a sphere and its tangent plane, a rotation acting on space, a knot, a solid of revolution |
| The data is a function of two variables | a loss landscape, a probability density over a plane, a field whose height is the value |

Everything else — a bar chart tilted for style, a title flying in on a
perspective slide, a graph that would read better face-on — is decoration, and
`animation_rules.md` Rule 4 already rules it out.

**A 3D video does not have to be 3D throughout.** The strongest use is a single
scene that opens flat, hits a contradiction the flat view cannot resolve, and
tilts. That camera move is the payoff of the whole section, so spend it once.

---

## 2. Subclass `ThreeDScene`, not `Scene`

```python
class MyVideo(ThreeDScene):
    def construct(self):
        ...
```

`ThreeDScene` differs from `Scene` in three ways that all matter:

- `samples = 4` — 4× multisampling. 3D edges alias badly without it.
- `always_depth_test = True` — everything it adds is depth-tested, so what is
  in front is drawn in front. A plain `Scene` with a reoriented frame draws in
  **add order**, so a curve behind a surface paints on top of it.
- `default_frame_orientation = (-30, 70)` — a sensible oblique start.

It also calls `set_flat_stroke(False)` on every VMobject with stroke that it
adds, which is what keeps a curve in space from thinning to nothing at grazing
angles.

The cost of that convenience is ANTI-PATTERN #14: depth testing applies to your
flat 2D content too. See §5.

---

## 3. Aiming the camera

The frame's orientation is three angles, in degrees:

| | Meaning | Useful values |
|---|---|---|
| `theta` | rotation about the vertical axis — which side you view from | −60 … −10 for a standard 3/4 view |
| `phi` | tilt away from looking straight down | `0` = top-down (a 3D scene that reads as 2D), `65–75` = standard oblique, `90` = edge-on |
| `gamma` | roll about the view direction | almost always 0 |

```python
orient(self, theta=0, phi=0, height=8.0)         # instantly, first frame only
orbit(self, theta=-30, phi=68, run_time=3.4)     # animated: this is the reveal
spin(self, 5.0, speed=-5.0)                      # slow ambient rotation
```

- **`phi = 0` → `phi ≈ 68` is the single most valuable move in 3D.** It is the
  visual form of "the flat view was hiding something." Give it 3–4 seconds and
  a narration line, and change nothing else on stage while it happens: the
  whole point is that the geometry did not change, only the viewpoint.
- **Ambient rotation is seasoning, not a course.** Keep `speed` under about
  10°/s; past that the viewer tracks the motion instead of the object. Pick the
  direction that keeps the interesting feature facing the camera — in the saddle
  example, spinning through `theta = 0` puts the near fold in front of the far
  one and the saddle reads as a plain bowl, so the sweep runs the other way.
- **Both helpers record a camera-motion window** into `render_meta.json`. A
  rotating frame produces exactly the pixel signature (edge content, large
  frame-to-frame deltas) that `verify_render.py` checks [1] and [4] are built to
  catch, so an undeclared orbit fails verification even though it is correct.
- `height` is the zoom (the frame height in world units, default 8.0);
  `center` moves the point being orbited. `reorient` takes both.

**Perspective.** The camera has a 45° vertical field of view, i.e. a focal
distance of about 1.2× the frame height (9.66 at the default height of 8). That
is a fairly strong perspective — from directly above, the high corners of a
surface project outward and the sheet bulges. `frame.set_focal_distance(32)` flattens
that toward orthographic. Measured: on a `z = 0.6(x² − y²)` sheet it visibly
reduces the bulge but does not remove it, and the oblique view loses some of its
depth feel, so the default is usually the better trade.

**Light.** `self.camera.light_source` sits at `(-10, 10, 10)` by default; a
surface's lit side and dark side follow it. Moving it is rarely worth it —
adjust the surface's `shading` triple instead (§6).

---

## 4. Captions and every other 2D overlay: `fix()`

In a 3D scene an unfixed `Text` is a flat sheet of glyphs lying in the world's
xy-plane. At `phi = 70` it is read at a 70° slant and the geometry buries it.

```python
from manim_helpers import fix, Caption

cap = Caption(self)          # in a ThreeDScene, fixes itself automatically
title = fix(Text("...").move_to(np.array([0, 3.42, 0])))
```

`fix()` does two things, and doing only the first is the most common 3D defect
there is:

1. `fix_in_frame()` — the mobject leaves world space and is drawn in screen
   coordinates, so the camera no longer skews it.
2. `deactivate_depth_test()` — otherwise the geometry in front of it eats it.

**Measured:** a caption that was added to a `ThreeDScene` and *then* fixed
rendered with its first four characters missing, because `ThreeDScene.add()` had
already switched depth testing on for it. The same caption fixed *before* being
added rendered in full. `fix()` is order-independent; call it whenever.

Fixed content uses ordinary frame coordinates: x ∈ ±7.1, y ∈ ±4, exactly as in
a 2D scene, regardless of where the camera is pointing.

---

## 5. Depth: the five things that bite

**5.1 A flat fill swallows whatever is drawn over it.** Under depth testing, an
opaque VMobject fill hides anything drawn on top of it — measured: a yellow disc
placed **1.0 units toward the camera** from a filled rectangle rendered zero
pixels, in both draw orders. Nudging does not help. Use `flat()` on the layer
that must stay on top:

```python
box = Rectangle(...).set_fill(BLUE_E, 1)
lbl = flat(Text("label").move_to(box))       # deactivate_depth_test()
```

**5.2 A curve drawn on a surface fights it for every pixel.** A slice curve is
by construction coincident with the surface it slices. Measured: in the saddle
example the y-slice rendered zero pixels for the whole top-down section — every
frame the camera spent above it — while the x-slice, coincident in exactly the
same way, happened to win. `slice_curve()` lifts
its curve by `lift=0.05` axis units in z, which always clears a graph surface
because such a surface has exactly one height per (x, y). A marker sitting on a
surface needs the same treatment — put the dot at `axes.c2p(x, y, f(x, y) +
0.08)`.

**5.3 `Dot` is a flat disc.** From the default 3D viewpoint it renders as an
ellipse — measured 19×6 px, aspect 3.2 — and edge-on it disappears to a line.
Use `dot3d()` (a `TrueDot`), which stays circular from any angle and scales
correctly with distance: measured 24, 20, 18 px across for the same dot at three
depths.

**5.4 Strokes need to face the camera.** `set_flat_stroke(False)` makes a stroke
a ribbon that turns toward the viewer. `ThreeDScene.add()` does this for you and
`path3d()` does it at construction; anything you build another way needs it
explicitly.

**5.5 `Surface` is not a `VMobject`.** It has no fill/stroke split, just one
opacity. Any helper that walks `get_family()` looking for VMobjects skips it
silently — which is how a "dim the stage" call can leave the surface at full
brightness. `Dimmer` handles `Surface`, `TrueDot`, `GlowDot` and `DotCloud`
through their own opacity; use it rather than `set_opacity` on a group.

---

## 6. Surfaces

```python
axes = ThreeDAxes(x_range=(-2.2, 2.2, 1), y_range=(-2.2, 2.2, 1),
                  z_range=(-3, 3, 1), width=5.6, height=5.6, depth=3.4)
surf = surface(f, axes=axes, color=TEAL_C, opacity=0.85, resolution=(72, 72))
mesh = mesh_for(surf, resolution=(19, 19), color=WHITE, width=1.0, opacity=0.5)
```

- **Pass `axes`** and the surface is built in that axes' units, so it lines up
  with the ticks and with anything from `slice_curve()`. Without it the surface
  is in raw world coordinates and nothing else will register with it.
- **The mesh is the depth cue, and it is not optional.** A single-colour surface
  with no wireframe reads as a coloured blob until the camera moves; with one,
  the fold is legible in a still frame. Keep it faint — it is texture, not
  content.
- **`shading=(reflectiveness, gloss, shadow)`**, default `(0.3, 0.2, 0.5)`. At
  `(0, 0, 0)` a surface renders as a flat silhouette and every fold in it
  disappears.
- **Keep `opacity` around 0.85.** At 1.0 the axes behind the surface vanish;
  much below 0.7 the surface stops reading as solid and the mesh behind it
  shows through confusingly.
- **Check the range fits the axes.** The same rule as a 2D plot (ANTI-PATTERN
  #8): evaluate the function at the domain corners and confirm the result is
  inside `z_range`, or the surface is clipped flat at the top.
- **Colour is still semantic** (Rule 5). A surface is one object with one
  meaning, so it gets one colour; use `ThreeDAxes` scaffolding in grey and keep
  the emphasis colour transient.

**Cost, measured** on the 95-second `examples/saddle/` scene (a 72×72 surface, a
19×19 mesh, two curves, a rotating camera): 11 s wall clock for a `-l` draft,
21 s for the full 1080p render. Surface resolution is cheap; there is no
reason to draft at a lower one.

---

## 7. Verifying a 3D render

Everything in `checklists.md` still applies. Four things change:

1. **Declare every camera move.** `orbit()` and `spin()` do it for you;
   `frame.animate.reorient(...)` written by hand does not. Check
   `render_meta.json` has a window for each move before running
   `verify_render.py`.
2. **`assert_in_frame()` is meaningless once the camera is tilted** — it
   compares *world* coordinates against the frame rectangle. A label at world
   x = 6.5 can be dead centre on screen. Use `assert_in_frame_3d(self, ...)`,
   which projects through ManimGL's own view matrix and perspective divide
   (verified against rendered pixels: four probe points landed within 1 px of
   prediction). Call it at the orientation the label is meant to be read at — a
   label that is perfectly placed at `theta = −30` can be off the edge at
   `theta = +40`. Use it on labels, markers and small groups, not on a large
   curved body: it projects bounding-box corners the body never reaches, so it
   over-reports. Measured — a saddle surface whose real pixels stayed well
   inside the frame projected to y = −4.25 against a safe limit of 3.65. Let
   check [1] police the geometry; this guard is for the things check [1] cannot
   attribute to a name.
3. **The text-overlap audit projects too**, so `AUDIT=1` reports real screen
   collisions rather than world-space ones. Validate the detector before
   trusting a zero, as always: two labels stacked on screen but 0.94 units apart
   in world x are reported; two labels well separated on screen are not.
4. **Sample contact sheets across the whole rotation**, not one angle. A label
   that is clear at the start of an orbit can be sitting on top of the geometry
   halfway through, and only the sheet shows it.

---

## 8. Minimal skeleton

```python
from manimlib import *
from manim_helpers import (Caption, Dimmer, fix, orient, orbit, spin,
                           surface, mesh_for, dot3d, slice_curve,
                           assert_in_frame_3d, dump_meta, hold)


class MyVideo(ThreeDScene):
    def construct(self):
        self.camera.background_color = BLACK
        cap = Caption(self)                      # fixes itself in 3D

        orient(self, theta=0, phi=0, height=8.0)  # open flat
        axes = ThreeDAxes(x_range=(-3, 3, 1), y_range=(-3, 3, 1),
                          z_range=(-2, 2, 1), width=6, height=6, depth=3)
        surf = surface(lambda x, y: 0.5 * (x * x - y * y), axes=axes,
                       color=TEAL_C)
        mesh = mesh_for(surf)
        self.play(ShowCreation(axes), ShowCreation(surf), ShowCreation(mesh))

        cap.show("The flat view cannot answer this.", narration="...")
        orbit(self, theta=-30, phi=68, run_time=3.4)   # the argument
        hold(self, 2.0)
        spin(self, 5.0, speed=-5.0)

        dump_meta(self, "render_meta.json")
```
