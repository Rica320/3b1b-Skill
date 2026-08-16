# 3b1b-math-animation

A [Claude Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
for producing math explainer videos with [ManimGL](https://github.com/3b1b/manim)
that match 3Blue1Brown's actual visual and pedagogical style — transform-driven
continuity, semantic colour, a single carried metaphor, narration-paced holds.

The skill is not a list of tips. Its rules were derived by rendering a full
video, measuring the output frame by frame, cataloguing every defect, and
rebuilding against the findings — and the 3D rules the same way, by rendering
each failing case and counting the pixels. The videos are in this repository,
along with the measurements.

```
skills/3b1b-math-animation/   the skill itself — install this
examples/gans/                a 6-minute explainer on GANs, plus its audit trail
examples/harmonic/            a 90-second scene, written from the skill alone
examples/rubiks/              a 5-minute narrated 3D scene with a synthesised
                              voice track, and a cube that is provably a cube
examples/saddle/              a 95-second 3D scene, where the camera move is
                              the argument
```

---

## Installing the skill

Copy the skill directory into whichever location your tool reads:

```bash
# Claude Code — personal, available in every project
mkdir -p ~/.claude/skills
cp -r skills/3b1b-math-animation ~/.claude/skills/

# or per-project, checked in alongside your code
mkdir -p .claude/skills
cp -r skills/3b1b-math-animation .claude/skills/
```

It activates on its own when you ask for a math animation, an explainer video,
a visual proof, or mention 3Blue1Brown or "manim" — no need to name it.

## Setting up the render environment

ManimGL needs three things that pip cannot install: **ffmpeg**, a **LaTeX**
distribution, and the **CMU Serif** font. Skipping any of them produces an error
that does not obviously name the missing piece, so do this first.

### Python packages

```bash
python -m venv env
source env/bin/activate          # Windows: env\Scripts\activate
pip install -r requirements.txt
```

Requires Python 3.13 (see `.python-version`). The pinned versions are the ones
the examples were rendered and verified against.

> The package is **`manimgl`** (from `3b1b/manim`), **not `manim`** (Manim
> Community Edition). They are unrelated libraries with incompatible APIs. Most
> "manim" tutorials and answers online describe the Community Edition and will
> not work here.

### System dependencies — Linux

```bash
bash skills/3b1b-math-animation/scripts/setup_env.sh
```

Idempotent and safe to re-run. It installs the apt/LaTeX packages, plus `xvfb` —
on a machine with no display attached, ManimGL cannot get an OpenGL context and
fails even for file-only renders. `scripts/render.sh` wraps renders in
`xvfb-run` automatically.

### System dependencies — macOS

`setup_env.sh` is Debian-only. macOS provides an OpenGL context without `xvfb`,
so there is no virtual display to set up, but LaTeX and the font are manual:

```bash
brew install ffmpeg
brew install --cask basictex font-computer-modern
```

BasicTeX is deliberately minimal, and ManimGL's default LaTeX preamble pulls in
considerably more than it ships. Install the rest in one go rather than
discovering them one failed `Tex()` call at a time:

```bash
sudo tlmgr update --self
sudo tlmgr install dvisvgm doublestroke setspace tipa relsize jknapltx \
  calligra wasysym ragged2e physics microtype psnfss standalone preview \
  varwidth fundus-calligra wasy
```

Then open a new shell so `/Library/TeX/texbin` is on `PATH` (`render.sh` adds it
too, for non-login shells).

### Checking it worked

```bash
cd examples/harmonic
bash ../../skills/3b1b-math-animation/scripts/render.sh harmonic.py Harmonic -l
```

A draft render of the short example. It should finish in well under a minute and
write `videos/Harmonic.mp4`. If it fails, the exact error-to-fix table is in
`skills/3b1b-math-animation/references/cli_reference.md`.

---

## Running the examples

The examples follow the same steps. **Run them from their own
directory** — ManimGL reads `custom_config.yml` (pure black background, CMU
Serif, 1080p) from the current working directory, and rendering from elsewhere
silently gives you ManimGL's default dark-grey background instead.

| | `examples/gans` | `examples/harmonic` | `examples/saddle` | `examples/rubiks` |
|---|---|---|---|---|
| Runtime | 6:15 | 1:25 | 1:35 | 4:58 |
| Scene | `GANs` in `gans.py` | `Harmonic` in `harmonic.py` | `Saddle` in `saddle.py` | `Rubiks` in `rubiks.py` |
| Needs assets | yes — one prep step | no | no | yes — synthesise the narration |
| Narration script | `SCRIPT.md` | in the module docstring | in the module docstring | `script.yaml`, and it is spoken |
| Dimensions | 2D | 2D | 3D | 3D |
| Audio | silent | silent | silent | **narrated** |

### 1. Prepare assets (GANs and Rubik's examples)

```bash
cd examples/gans
python prepare_assets.py
```

Downloads the Olivetti faces dataset via scikit-learn and writes 18 PNGs to
`assets/faces/`. These are not committed — they are derived from a
third-party dataset, so this repository generates them rather than
redistributing them. One-time, a few seconds.

For the Rubik's example the asset is the **voice**, and it has to exist before
the render rather than after it: the scene asks the audio how long each spoken
line is and paces itself to the answer.

```bash
bash skills/3b1b-math-animation/scripts/setup_env.sh --tts   # one time, 353 MB

cd examples/rubiks
python ../../skills/3b1b-math-animation/scripts/tts.py script.yaml --out audio
```

That runs Kokoro locally — Apache-2.0, about 5× realtime on CPU, no API key.
Twelve seconds for the 31 beats. To use a different voice, or to clone one,
edit the `voice:` block at the top of `script.yaml`; see
`skills/3b1b-math-animation/references/narration.md` for what makes a usable
reference clip.

### 2. Render

```bash
# fast draft — use this while iterating
bash ../../skills/3b1b-math-animation/scripts/render.sh gans.py GANs -l

# full quality, 1080p
bash ../../skills/3b1b-math-animation/scripts/render.sh gans.py GANs
```

Output lands in `videos/`. `render.sh` picks the right invocation for your
platform and finds `manimgl` in a project virtualenv if one exists.

### 3. Lay the narration down (narrated examples)

```bash
python ../../skills/3b1b-math-animation/scripts/mux_audio.py \
    videos/Rubiks.mp4 --cues narration_cues.json
```

Each line is placed at the frame the scene recorded for it, and the mix is
loudness-normalised to −16 LUFS in two passes. Nothing here searches for sync:
the scene already waited for the exact length of every file.

### 4. Verify the pixels

```bash
python ../../skills/3b1b-math-animation/scripts/verify_render.py \
    videos/GANs.mp4 --meta render_meta.json
```

```
    (camera-motion windows declared: 2)
[1] off-frame content ......... pass (0 frames)
[2] blank-frame windows ....... pass (0 windows, 0.0s)
[3] over-long frozen holds .... pass (0)
[4] hard cuts ................. pass (0)
[5] colour reaching screen .... pass (64% of lit pixels saturated)

All checks passed.
```

`render_meta.json` is written by the scene itself during the render. It declares
the windows where the camera is deliberately moving, so the off-frame and
hard-cut checks stay strict everywhere else instead of being loosened globally
to tolerate two intentional close-ups.

Exit status is non-zero if any check fails, so it drops into CI unchanged.

### 5. Verify the audio (narrated examples)

```bash
python ../../skills/3b1b-math-animation/scripts/verify_audio.py \
    videos/Rubiks_narrated.mp4 --cues narration_cues.json
```

```
[1] audio stream present ...... pass (aac, 48000 Hz, +0.00s vs picture)
[2] loudness / true peak ...... pass (-16.5 LUFS, -1.4 dBTP)
[3] line overlap / overrun .... pass (31 lines)
[4] speech present at each cue  pass (31/31 cues land on sound)
[5] narration coverage ........ pass (87% of 298s)
[6] longest wordless stretch .. pass (6.9s max gap)
```

Check [4] is the one worth having. Every other check — and every part of the
pipeline upstream of it — can be perfectly self-consistent and still be
describing the wrong seconds, because a scene re-rendered after the script
changed produces a cue sheet that agrees with itself and points nowhere. Check
[4] runs a silence detector over the finished mix and asks whether there is
actually sound where each line was cued.

There is also a build-time text-overlap audit, which walks every visible `Text`
and `Tex` at every hold and reports pairs sharing screen space:

```bash
GANS_AUDIT=1 manimgl gans.py GANs        # AUDIT=1 for the harmonic example
```

---

## Why the examples are here

The GANs example is the skill's evidence, not a demo. `examples/gans/docs/`
contains the full trail:

- **`DEFECTS.md`** — a frame-by-frame audit of the first build. 12 rendering
  bugs, 21 blank-frame windows totalling 24 seconds (11% of the runtime), 15
  distinct visual metaphors for one topic, and zero transforms carrying an idea
  across a scene boundary. Every item confirmed in the rendered pixels, not
  inferred from reading the source.
- **`VERIFICATION.md`** — the rebuild measured against that list, item by item.

Two findings drove most of the skill's rules, and both are invisible in source:

1. **Rendering each beat as a separate `Scene` and concatenating** guarantees a
   black frame at every boundary and makes transform-based transitions
   impossible. Build one `Scene` with a method per section.
2. **ManimGL silently ignores a bare `color=` on `Dot`, `Arrow` and `Circle`.**
   The argument lands in `**kwargs` and is overridden by an explicitly-passed
   default, so the mobject renders white, grey or red. `Dot(ORIGIN, color=ORANGE)`
   produces RGB(253,255,253). This destroyed colour semantics across an entire
   video while every colour in the source read correctly.

The harmonic example is the control: a scene written from the skill's
documentation alone, with no other reference, to test whether the written rules
are sufficient on their own.

The Rubik's example is the narrated one, and it is where the audio pipeline was
worked out and measured. It is also the one with a claim to check that no pixel
test can reach: the cube in it is a real cube. Its state is 26 cubie rotations
rather than four permutation arrays, so no impossible position can be
represented; the rendered stickers are read back off the geometry and compared
against the model after every stage; the solver solves 300 of 300 random
scrambles using only the beginner's method's own sequences; and
`verify_cube.py` checks every number the voice says — the state count, the
"hundred times the age of the universe", the order of `R U R' U'` being exactly
six — against the code that produced the animation.

The saddle example is the 3D one, and it was built the same way as the GANs
rebuild: each 3D rule in the skill was derived by rendering the failing version
first and counting the pixels. A caption fixed in frame *after* being added lost
its first four characters to the surface; a `Dot` in space rendered as a 19×6
ellipse; a slice curve lying on the surface it slices was invisible for its whole
time on screen. All five findings are `anti_patterns.md` #13–#17.

---

## Repository layout

```
skills/3b1b-math-animation/
├── SKILL.md                       entry point and workflow
├── references/
│   ├── narrative_template.md      question → motivation → build → payoff
│   ├── animation_rules.md         the nine non-negotiables
│   ├── anti_patterns.md           seventeen shipped defects, with fixes
│   ├── three_d.md                 3D: earning the depth, aiming the camera,
│   │                              the five depth traps, verifying the render
│   ├── checklists.md              pre- and post-render gates
│   ├── style_guide.md             colour system, motion grammar
│   ├── code_patterns.md           verified ManimGL snippets
│   └── cli_reference.md           flags, and an error → fix table
├── scripts/
│   ├── manim_helpers.py           safe constructors, Caption, Dimmer,
│   │                              raster_field, frame assertions, and the
│   │                              3D set: fix/orbit/spin/surface/dot3d
│   ├── verify_render.py           the five post-render pixel checks
│   ├── render.sh                  render wrapper (headless on Linux)
│   └── setup_env.sh               idempotent environment setup (Debian)
└── assets/custom_config.yml.template

examples/
├── gans/
│   ├── gans.py                    the scene — one Scene, eight sections
│   ├── landscape.py               D(x) as a field over image space
│   ├── prepare_assets.py          generates assets/faces/
│   ├── SCRIPT.md                  narration, timings, colour mapping
│   └── docs/{DEFECTS,VERIFICATION}.md
├── harmonic/
│   └── harmonic.py
├── saddle/
│   └── saddle.py                  the 3D worked example
└── rubiks/
    ├── script.yaml                every spoken line; the scene has no prose
    ├── rubiks.py                  the narrated worked example
    ├── cube_model.py              a cube that cannot hold an illegal state
    ├── cube_view.py               the geometry, cross-checked against it
    ├── solver.py                  the beginner's method, as a search
    └── verify_cube.py             every number the narration says
```

The examples import `manim_helpers.py` from `skills/` rather than keeping their
own copy, so the two cannot drift apart. **In your own project, copy
`manim_helpers.py` next to your scene file instead** — that is what the skill
instructs, and it keeps a project self-contained. Either way you need the
`sys.path` line at the top of the scene file: ManimGL's module loader does not
put the scene's own directory on the path, so a sibling module is not importable
without it.

## License

MIT — see [LICENSE](LICENSE).

The face images generated by `examples/gans/prepare_assets.py` are derived from
the AT&T Database of Faces (Olivetti), fetched at runtime from its distributor
and covered by its own terms. No trained generative model ships in this
repository; the interpolation frames are linear blends between two real faces,
standing in for what a latent walk would produce.
