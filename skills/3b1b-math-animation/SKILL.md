---
name: 3b1b-math-animation
description: >
  Create math explainer animation videos in the visual and pedagogical style
  of 3Blue1Brown, using ManimGL (the 3b1b/manim library, PyPI package
  `manimgl` — explicitly NOT the Manim Community Edition, which has a
  different API). Use this whenever the user asks for a math animation,
  an explainer video, a visual proof, a video walking through a formula or
  theorem, or mentions 3Blue1Brown, Grant Sanderson, or "manim" by name —
  even if they don't spell out every detail of what they want animated.
  Covers 3D as well as 2D — surfaces, solids, camera orbits, and 3D
  presentations where the viewpoint change is the argument. Handles:
  installing and configuring ManimGL for headless rendering (including the
  xvfb virtual display and LaTeX packages it needs, which are easy to get
  wrong), writing a narrative spine that builds an argument rather than
  listing facts, writing Scene code that matches 3b1b's visual language
  (transform-driven continuity, semantic colour, pure-black background,
  CMU Serif titles), narrating them with synthesised or voice-cloned speech
  that the animation is paced to rather than laid over, and verifying the
  rendered pixels and the finished audio.
---

# 3Blue1Brown-Style Math Animation

Produces math explainer videos with [ManimGL](https://github.com/3b1b/manim) that
match 3Blue1Brown's actual visual and pedagogical style — not generic "Manim
output." Setup steps, code patterns, and gotchas were verified by installing
ManimGL and rendering real scenes; the anti-patterns were found by rendering a
full video, measuring the result, and fixing what was broken. Trust these over
anything that contradicts them from general knowledge of Manim.

**Scope defaults** (adjust if the user says otherwise): produce a **narrated**
render — synthesise the script first and pace the animation to the real audio
(`references/narration.md`), then deliver both the silent mp4 and the muxed
one. If the user would rather record their own voice, cut the same script with
the placeholder engine and hand them the cue sheet. Build the whole video as
**one `Scene`** with one method per section — not one `Scene` per beat (see
below). Default to 2D; reach for 3D only where the claim cannot be made without
depth, and subclass `ThreeDScene` when you do (`references/three_d.md`).

## The two rules that matter most

1. **One `Scene`, not many.** Rendering beats as separate scenes and
   concatenating them guarantees a black frame at every boundary and makes
   transform-based transitions impossible. This one mistake put 24 seconds of
   blank screen — 11% of the runtime — into a real video.
2. **Never pass a bare `color=` to `Dot`, `Arrow` or `Circle`.** ManimGL
   silently ignores it and renders white/grey/red. This one mistake destroyed
   colour semantics across an entire video. Use the constructors in
   `scripts/manim_helpers.py`.

Both are covered in detail in `references/anti_patterns.md`, along with fifteen
more — five of which only bite in 3D.

## Workflow

1. **Set up the environment** (once per environment, safe to re-run):
   `bash scripts/setup_env.sh`. Installs the apt/LaTeX bits ManimGL needs and
   confirms `manimgl` imports. On macOS there is no `xvfb`; run `manimgl`
   directly (`scripts/render.sh` handles both platforms).

2. **Write the narrative spine first, as prose, and get it approved.** Read
   `references/narrative_template.md`. It must have one driving question stated
   in the first 20 seconds, the obvious answer tried and shown to fail, a single
   carried metaphor, a stated colour mapping, and a payoff that restates the
   opening question verbatim. **Do not write animation code before this is
   approved** — visuals built on a weak spine cannot be rescued by polish.

3. **Cut the narration before writing the scene.** The approved spine becomes
   `script.yaml`, one beat per spoken line; `scripts/tts.py script.yaml --out
   audio` synthesises it and measures every line. Read
   `references/narration.md` first — the order matters and is not a
   preference. A spoken line has one correct duration and an animation hold has
   none, so the audio is cut first and the scene waits for real durations.
   Doing it the other way round leaves only two options at every beat, both
   bad: overlap the next line, or cut the sentence. The scene then refers to
   beats by id and holds no prose at all.

4. **Write the scene against the rules.** `references/animation_rules.md` states
   the nine non-negotiables (transform don't cut; one idea on screen; nothing
   unmotivated; camera over decoration; semantic colour; stagger; vary the holds;
   never leave the frame; in 3D the camera move is the argument). Copy
   `scripts/manim_helpers.py` next to your scene file and use its helpers — each
   one exists to prevent a specific shipped defect. Pull working API snippets
   from `references/code_patterns.md`.

   **If any part of the video is 3D — a surface, a solid, a camera orbit, a
   "3D presentation" — read `references/three_d.md` before writing it.** 3D has
   its own set of failure modes that do not exist in 2D and are invisible in the
   source: captions that render at a slant and get eaten by the geometry, dots
   that render as ellipses, curves on a surface that vanish, in-frame assertions
   that pass while the label is off screen. All measured, all fixable in one
   line each.

5. **Check `references/anti_patterns.md` before rendering.** Most of these
   defects are invisible in the source and only appear on screen.

6. **Run the pre-render checklist** in `references/checklists.md`, then
   draft-render fast: `bash scripts/render.sh scenes.py MyVideo -l`.
   Review **contact sheets**, not a handful of frames:
   `ffmpeg -i out.mp4 -vf "fps=1/4,scale=636:358,tile=4x3" -q:v 3 sheet_%02d.jpg`

7. **Full-quality render**, then **verify the pixels**:
   ```bash
   bash scripts/render.sh scenes.py MyVideo
   python scripts/verify_render.py out.mp4 --meta render_meta.json
   ```
   All five checks must pass. Then work the post-render checklist — the
   automated checks cannot judge composition or narrative.

8. **Lay the narration down and verify the audio**:
   ```bash
   python scripts/mux_audio.py videos/MyVideo.mp4 --cues narration_cues.json
   python scripts/verify_audio.py videos/MyVideo_narrated.mp4 \
       --cues narration_cues.json
   ```
   Six more checks. The one that matters is [4]: it runs a silence detector
   over the finished mix and confirms sound is really present at every cue, so
   a scene rendered against a stale script is caught rather than shipped.

9. **Deliver** both mp4s — silent and narrated — plus the script, the cue
   sheet, and both verification results.

## If something breaks

Check `references/cli_reference.md` first — a verified table of the exact error
messages ManimGL produces for missing dependencies and their one-line fixes
(missing `dsfont.sty`, missing `dvisvgm`, the pango/cairo build failure), plus
the full CLI flag reference.

If a helper module next to the scene file won't import, ManimGL's loader does not
put the scene's directory on `sys.path`; add it explicitly at the top of the
scene file.

## The one thing to never mix up

There are two unrelated libraries called "manim." This skill is **ManimGL**
(`pip install manimgl`, from `3b1b/manim`) — not Manim Community Edition
(`pip install manim`, from `ManimCommunity/manim`). They have incompatible APIs.
If a search result or piece of general knowledge about "manim" doesn't match
what's here, it's very likely describing the Community Edition — don't apply it.

## Bundled resources

**Read before writing anything:**
- `references/narrative_template.md` — question → motivation → build → payoff;
  the carried-metaphor test; script deliverable format; pacing arithmetic
- `references/animation_rules.md` — the nine rules, each with its helper
- `references/anti_patterns.md` — twenty-two shipped defects with verified fixes
- `references/checklists.md` — pre-render and post-render gates

**Read before writing the script, and before any audio work:**
- `references/narration.md` — audio first and why; the script as the only copy
  of the words; the four ways a line meets the picture; pauses; spending
  silence; engines and voice cloning; the mix; the six audio checks

**Read before writing any 3D:**
- `references/three_d.md` — when depth earns its place, aiming the camera,
  fixing the 2D overlay layer, the five depth traps, surfaces, verifying a 3D
  render

**Reference as needed:**
- `references/style_guide.md` — visual language, colour system, motion grammar
- `references/code_patterns.md` — verified working ManimGL snippets
- `references/cli_reference.md` — CLI flags, output defaults, gotchas table

**Code:**
- `scripts/manim_helpers.py` — safe constructors, `Caption`, `Dimmer`,
  `push_in`/`pull_back`, `equation`/`box_around`, `assert_in_frame`,
  `audit_text_overlaps`, `raster_field`/`swap_raster`; and for 3D, `fix`/`flat`,
  `orient`/`orbit`/`spin`, `surface`/`mesh_for`/`dot3d`/`path3d`/`slice_curve`,
  `project`/`assert_in_frame_3d`
- `scripts/narration.py` — `Narrator`: real beat durations drive the scene's
  holds, and the cue times it records drive the mux
- `scripts/tts.py` — script → per-beat audio; Kokoro / ElevenLabs / Chatterbox
  / OpenAI / `say`, voice cloning, exact `[[0.4]]` pauses, cached re-cuts
- `scripts/mux_audio.py` — lay each line at its cue, optional ducked music bed,
  two-pass EBU R128
- `scripts/verify_render.py` — five post-render pixel checks
- `scripts/verify_audio.py` — six post-mux audio checks
- `scripts/render.sh` — render wrapper (headless on Linux, direct on macOS)
- `scripts/setup_env.sh` — idempotent environment setup (`--tts` also fetches
  the Kokoro model files)
- `assets/custom_config.yml.template` — pure black, CMU Serif, optional 4K

**Worked examples** (not bundled — in the source repository,
<https://github.com/Rica320/3b1b-Skill>): `examples/gans/` is a full 6-minute
build applying every rule here, shipped with the frame-by-frame defect audit of
the version it replaced and the verification of the rebuild against it.
`examples/harmonic/` is a shorter one to copy from. `examples/saddle/` is the 3D
one — 1:35, and the camera move is the proof. `examples/rubiks/` is the
narrated one — 4:58 with a synthesised voice track, and the cube in it is a
real cube: its state is 26 rotations rather than four permutation arrays, so an
impossible position cannot be represented, and the rendered stickers are read
back off the geometry and compared against the model at every stage.
