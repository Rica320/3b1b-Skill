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
  Handles: installing and configuring ManimGL for headless rendering
  (including the xvfb virtual display and LaTeX packages it needs, which
  are easy to get wrong), writing a narrative spine that builds an argument
  rather than listing facts, writing Scene code that matches 3b1b's visual
  language (transform-driven continuity, semantic colour, pure-black
  background, CMU Serif titles), and verifying the rendered pixels.
---

# 3Blue1Brown-Style Math Animation

Produces math explainer videos with [ManimGL](https://github.com/3b1b/manim) that
match 3Blue1Brown's actual visual and pedagogical style — not generic "Manim
output." Setup steps, code patterns, and gotchas were verified by installing
ManimGL and rendering real scenes; the anti-patterns were found by rendering a
full video, measuring the result, and fixing what was broken. Trust these over
anything that contradicts them from general knowledge of Manim.

**Scope defaults** (adjust if the user says otherwise): produce a silent render
with timing paced to spoken narration, so the user can layer their own audio
afterward. Build the whole video as **one `Scene`** with one method per section —
not one `Scene` per beat (see below). Deliver a single mp4.

## The two rules that matter most

1. **One `Scene`, not many.** Rendering beats as separate scenes and
   concatenating them guarantees a black frame at every boundary and makes
   transform-based transitions impossible. This one mistake put 24 seconds of
   blank screen — 11% of the runtime — into a real video.
2. **Never pass a bare `color=` to `Dot`, `Arrow` or `Circle`.** ManimGL
   silently ignores it and renders white/grey/red. This one mistake destroyed
   colour semantics across an entire video. Use the constructors in
   `scripts/manim_helpers.py`.

Both are covered in detail in `references/anti_patterns.md`, along with ten more.

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

3. **Write the scene against the rules.** `references/animation_rules.md` states
   the eight non-negotiables (transform don't cut; one idea on screen; nothing
   unmotivated; camera over decoration; semantic colour; stagger; vary the holds;
   never leave the frame). Copy `scripts/manim_helpers.py` next to your scene file
   and use its helpers — each one exists to prevent a specific shipped defect.
   Pull working API snippets from `references/code_patterns.md`.

4. **Check `references/anti_patterns.md` before rendering.** Most of these
   defects are invisible in the source and only appear on screen.

5. **Run the pre-render checklist** in `references/checklists.md`, then
   draft-render fast: `bash scripts/render.sh scenes.py MyVideo -l`.
   Review **contact sheets**, not a handful of frames:
   `ffmpeg -i out.mp4 -vf "fps=1/4,scale=636:358,tile=4x3" -q:v 3 sheet_%02d.jpg`

6. **Full-quality render**, then **verify the pixels**:
   ```bash
   bash scripts/render.sh scenes.py MyVideo
   python scripts/verify_render.py out.mp4 --meta render_meta.json
   ```
   All five checks must pass. Then work the post-render checklist — the
   automated checks cannot judge composition or narrative.

7. **Deliver** the mp4 plus the script and the verification result.

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
- `references/animation_rules.md` — the eight rules, each with its helper
- `references/anti_patterns.md` — twelve shipped defects with verified fixes
- `references/checklists.md` — pre-render and post-render gates

**Reference as needed:**
- `references/style_guide.md` — visual language, colour system, motion grammar
- `references/code_patterns.md` — verified working ManimGL snippets
- `references/cli_reference.md` — CLI flags, output defaults, gotchas table

**Code:**
- `scripts/manim_helpers.py` — safe constructors, `Caption`, `Dimmer`,
  `push_in`/`pull_back`, `equation`/`box_around`, `assert_in_frame`,
  `audit_text_overlaps`, `raster_field`/`swap_raster`
- `scripts/verify_render.py` — five post-render pixel checks
- `scripts/render.sh` — render wrapper (headless on Linux, direct on macOS)
- `scripts/setup_env.sh` — idempotent environment setup
- `assets/custom_config.yml.template` — pure black, CMU Serif, optional 4K
