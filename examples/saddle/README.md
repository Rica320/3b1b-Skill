# Is the origin a maximum or a minimum of z = x² − y²?

A 1:35 scene, and the skill's **3D worked example**. It exists to demonstrate one
rule: in 3D the camera move is the argument, not the decoration.

The scene opens looking straight down, where the surface is a flat-looking sheet
and the question cannot be answered. Slicing it — the obvious move — makes things
worse: the slice along x says the origin is a minimum, the slice along y says it
is a maximum, and both slices are correct. Then the camera tilts. Nothing on
stage changes; the two slices lift out of the plane into the parabolas they
always were, and the contradiction resolves into a mountain pass.

It exercises the 3D helper set from
[`three_d.md`](../../skills/3b1b-math-animation/references/three_d.md): `fix`,
`orient`, `orbit`, `spin`, `surface`, `mesh_for`, `dot3d`, `slice_curve`,
`assert_in_frame_3d`, and `Dimmer` over a `Surface`. The one it does not need is
`flat()` — nothing here stacks flat 2D fills.

## Run it

```bash
cd examples/saddle

bash ../../skills/3b1b-math-animation/scripts/render.sh saddle.py Saddle -l   # draft
bash ../../skills/3b1b-math-animation/scripts/render.sh saddle.py Saddle      # 1080p

python ../../skills/3b1b-math-animation/scripts/verify_render.py \
    videos/Saddle.mp4 --meta render_meta.json
```

Run from this directory — `custom_config.yml` is read from the working
directory. No asset preparation is needed. Measured on an M-series Mac: 11 s
for the draft, 21 s for the full 1080p render.

```bash
AUDIT=1 manimgl saddle.py Saddle     # report any two texts sharing screen space
```

In a 3D scene the audit compares **projected** boxes for anything not fixed in
frame, so it reports collisions as the viewer sees them rather than as world
coordinates claim them.

## Verification

```
    (camera-motion windows declared: 4)
[1] off-frame content ......... pass (0 frames)
[2] blank-frame windows ....... pass (0 windows, 0.0s)
[3] over-long frozen holds .... pass (0)
[4] hard cuts ................. pass (0)
[5] colour reaching screen .... pass (97% of lit pixels saturated)
```

The four declared windows are the `phi = 0 → 68` reveal and the three ambient
rotations. An undeclared camera move fails checks [1] and [4] — a rotating frame
produces the same pixel signature as content falling off the edge and as a hard
cut — which is why `orbit()` and `spin()` record them into `render_meta.json`.

## The spine

| | |
|---|---|
| **Question** | Is the origin a maximum or a minimum of z = x² − y²? |
| **Motivation** | Slice it. Along x: a minimum. Along y: a maximum. Both correct, and they contradict each other. |
| **Build** | The contradiction is in the viewpoint, not the algebra. Tilt the camera and the two slices become two parabolas crossing at the origin. |
| **Payoff** | Restate the question, answer it: neither — a saddle, and no single slice can see it. |

The carried object is **the mountain pass**: the surface is the terrain, the
x-slice is the trail that climbs out of it, the y-slice is the ridge that falls
away from it, and the origin is the pass itself.

Colour mapping, fixed for the whole scene: blue for the x direction and its
slice, orange for the y direction and its slice, teal for the surface, yellow
for transient emphasis only, grey for scaffolding.

## What it was built to demonstrate

Each of these was measured on a failing render before being fixed here; the
numbers are in `anti_patterns.md` #13–#17.

- Captions and equations are a **HUD**: `fix()` pins them to the screen and
  takes them out of the depth test. Unfixed, they are drawn at a 70° slant and
  buried in the surface.
- The origin marker is a `TrueDot` (`dot3d`) — a plain `Dot` renders as a 19×6 px
  ellipse from this viewpoint.
- Both slice curves are lifted 0.05 axis units clear of the surface. Coincident
  with it, the orange one was invisible for its entire time on screen.
- The stage is dimmed with `Dimmer`, which knows a `Surface` is not a
  `VMobject`. A VMobject-only walk would have left the terrain at full
  brightness.
- The ambient rotation runs *away* from `theta = 0`: spinning the other way puts
  the near fold in front of the far one and the saddle reads as a plain bowl.
  Only the contact sheets showed that.
