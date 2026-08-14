# GANs, explained visually

> *"What do you write down as the score, when there is no right answer?"*

A 6:15 explainer on generative adversarial networks. Silent render, paced to
~985 words of narration at ~2.6 words/second, so voiceover can be laid over it
afterwards. The full script is in [`SCRIPT.md`](SCRIPT.md).

## Run it

```bash
cd examples/gans
python prepare_assets.py                    # one time — writes assets/faces/

bash ../../skills/3b1b-math-animation/scripts/render.sh gans.py GANs -l   # draft
bash ../../skills/3b1b-math-animation/scripts/render.sh gans.py GANs      # 1080p

python ../../skills/3b1b-math-animation/scripts/verify_render.py \
    videos/GANs.mp4 --meta render_meta.json
```

Run from this directory: `custom_config.yml` (pure black, CMU Serif, 1080p30) is
picked up from the working directory. A full-quality render takes a few minutes;
`-l` is the fast path while iterating.

`prepare_assets.py` fetches the Olivetti faces dataset through scikit-learn and
writes 18 PNGs. They are not committed — derived from a third-party dataset, so
this repository generates them rather than redistributing them.

To check that no two pieces of text ever share screen space:

```bash
GANS_AUDIT=1 manimgl gans.py GANs
```

This walks every visible `Text` and `Tex` at every hold and prints `[OVERLAP]`
for any collision. The current build reports zero across the full run.

## Files

| | |
|---|---|
| `gans.py` | The scene. One `Scene`, eight sections, one method each. |
| `landscape.py` | `D(x)` as a scalar field over image space — the carried metaphor. |
| `prepare_assets.py` | Generates `assets/faces/`. |
| `SCRIPT.md` | Narration, section timings, the colour mapping, the spine. |
| `docs/DEFECTS.md` | Frame-by-frame audit of the build this replaced. |
| `docs/VERIFICATION.md` | The rebuild measured against that audit, item by item. |

## The one object

Everything after 2:16 happens on a single picture: a plane where every point is
an image, and a height over it for how real that point looks. That height *is*
the discriminator.

| Idea | Same object, later |
|---|---|
| the discriminator | a shaded field over the plane |
| its training signal | the slope of the field |
| the adversarial loop | the field repainting as the cloud moves |
| convergence | the field flattening to ½ |
| mode collapse | the cloud draining into one peak |

The field is computed, not keyframed. It is literally

```
D*(x) = p_data(x) / (p_data(x) + p_G(x))
```

evaluated on a grid and rasterised, so when the generated cloud slides onto the
real one the field flattens to ½ everywhere as an arithmetic consequence of
moving the cloud — not because someone animated it flattening. The convergence
beat is honest for that reason, and that is the point of `landscape.py`
existing at all.

`mean_face.png` works the same way: §1 claims that a pixel-wise score rewards
blur, and the image on screen is the actual arithmetic mean of the dataset —
the literal minimiser — rather than an illustration of one.

## Why `docs/` is worth reading

`DEFECTS.md` is the audit of the first build of this video, measured in the
rendered pixels rather than read out of the source. It found 12 rendering bugs,
24 seconds of blank frames across 21 windows (11% of the runtime), 15 distinct
visual metaphors for one topic, and zero transforms carrying an idea across a
scene boundary.

Most of those defects are invisible in the source. The two that mattered most:

- **Eleven `Scene`s concatenated into one video** put a black frame at 10 of the
  11 boundaries and made transform-based transitions impossible to write. This
  build is one `Scene`, which is why check [2] can report zero blank windows.
- **`Dot(point, color=ORANGE)` renders white.** ManimGL 1.7.x declares
  `fill_color=WHITE` explicitly in `Dot.__init__` and passes it up to the
  parent, so a `color=` in `**kwargs` is silently discarded. Same trap in
  `Arrow` (grey) and `Circle` (red). Every dot in the first video rendered
  colourless while the source read correctly. Everything here goes through
  `manim_helpers.dot()` / `.arrow()` instead.

`VERIFICATION.md` walks the defect list item by item with the evidence for each
fix, plus the transition-boundary and narration-sync measurements.

> The first build's source is not in this repository — it was removed in favour
> of the rebuild. `DEFECTS.md` cites it by file and line as a record of what was
> measured; those paths no longer resolve.

## Note on the assets

There is no trained generative model here. The interpolation frames are linear
blends between two real faces, standing in for what a latent walk would produce.
The video uses them only for the beat about the *continuity* of the space, which
that substitution supports honestly; it never claims they are generated samples.
