# Examples

Videos built with the `3b1b-math-animation` skill. Setup instructions are in
the [root README](../README.md); this page is the index.

| | Runtime | What it is for |
|---|---|---|
| [`gans/`](gans/) | 6:15 | The skill's evidence. A full explainer, plus the frame-by-frame audit of the build it replaced and the verification of the rebuild against that audit. |
| [`harmonic/`](harmonic/) | 1:25 | The control. Written from the skill's documentation alone, to test whether the written rules are sufficient without the author's memory of the first video. |
| [`saddle/`](saddle/) | 1:35 | The 3D one. Opens top-down where the question cannot be answered, and resolves it with a camera move — the rules in `three_d.md`, applied. |
| [`rubiks/`](rubiks/) | 4:58 | The narrated one. A synthesised voice track the animation is paced *to*, not laid over — the rules in `narration.md` — around a cube whose state cannot be illegal and whose rendered stickers are checked against the model at every stage. |

They all render the same way. **Run from the example's own directory** — ManimGL
reads `custom_config.yml` from the working directory, and rendering from
elsewhere silently falls back to its default dark-grey background.

```bash
cd gans                                   # or harmonic, saddle, rubiks
python prepare_assets.py                  # gans only, one time
bash ../../skills/3b1b-math-animation/scripts/render.sh gans.py GANs -l
python ../../skills/3b1b-math-animation/scripts/verify_render.py \
    videos/GANs.mp4 --meta render_meta.json
```

Drop the `-l` for a full-quality 1080p render.

`rubiks/` has two extra steps around that, because it has sound. Synthesise
the narration **before** rendering — the scene asks the audio how long each
line is and paces itself to the answer — and mux it afterwards:

```bash
cd rubiks
python ../../skills/3b1b-math-animation/scripts/tts.py script.yaml --out audio
bash   ../../skills/3b1b-math-animation/scripts/render.sh rubiks.py Rubiks
python ../../skills/3b1b-math-animation/scripts/mux_audio.py \
    videos/Rubiks.mp4 --cues narration_cues.json
python ../../skills/3b1b-math-animation/scripts/verify_audio.py \
    videos/Rubiks_narrated.mp4 --cues narration_cues.json
```

The Kokoro model files are a one-time 353 MB download:
`bash skills/3b1b-math-animation/scripts/setup_env.sh --tts`.

## What to read them for

`gans/gans.py` is the reference implementation of the skill's two hardest rules:
one continuous `Scene` with a method per section, and a single object carried
across the whole runtime. The landscape built in §2 is still the same mobject on
screen in §7 — it is repainted, sliced, flattened and collapsed, never torn down
and rebuilt. `gans/docs/DEFECTS.md` shows what the video looked like before that
constraint was imposed.

`harmonic/harmonic.py` is the smaller read: the same structure at a quarter of
the length, and a good starting point to copy.

`rubiks/` is what to copy for anything with a voice track, and it is the
longest of the four. `script.yaml` holds every spoken word and `rubiks.py`
holds none of them — it refers to beats by id, which is what lets the voice be
recast (or cloned) without touching a line of animation code. It is also worth
reading for the part that has nothing to do with audio: `cube_model.py` keeps
the cube as 26 rotations rather than four permutation arrays, so an impossible
position cannot be represented, and `cube_view.check()` reads the rendered
stickers back off the geometry and compares them to the model after every
stage.

`saddle/saddle.py` is what to copy for anything with depth in it. It is the same
structure again, in a `ThreeDScene`: the 2D overlay layer is fixed in frame, the
curves are lifted clear of the surface they slice, the camera moves are declared
into `render_meta.json`, and the `phi = 0 → 68` tilt is the section that carries
the argument.
