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
  are easy to get wrong), writing Scene code that matches 3b1b's visual
  language (color-coded equations, Transform-driven continuity, pure-black
  background, CMU Serif titles) and pedagogical structure (concrete question
  first, visual intuition before notation), and rendering to mp4.
---

# 3Blue1Brown-Style Math Animation

Produces math explainer videos with [ManimGL](https://github.com/3b1b/manim) that match 3Blue1Brown's actual visual and pedagogical style — not generic "Manim output." The setup steps, code patterns, and gotchas referenced below were all verified by actually installing ManimGL and rendering test scenes headlessly (no display) while this skill was built, so trust them over anything that contradicts them from general knowledge of Manim.

**Scope defaults** (adjust if the user says otherwise): produce silent scenes with `run_time`/`wait()` timing sketched to match spoken narration cadence, rather than recorded voiceover — the user can layer their own audio on afterward, or ask for narration-synced timing explicitly. Build one `Scene` subclass per beat, deliver each as its own mp4, and offer to concatenate into one file if the user wants a single deliverable. There's no hard length ceiling — a single 30-second concept clip and a 10-scene video both fit the same workflow, just with more beats.

## Workflow

1. **Set up the environment** (once per environment — safe to re-run): `bash scripts/setup_env.sh`. This installs the apt packages and LaTeX bits ManimGL needs and confirms `manimgl` is importable. If it's already been run in this environment, it exits fast without reinstalling anything.

2. **Nail the concept before writing code.** What specific question does this video answer? Write the narration/caption script beat-by-beat first — 3b1b builds visuals to match spoken cadence, not the reverse. Each beat becomes one `Scene` subclass.

3. **Write scenes following the style guide.** Read `references/style_guide.md` before writing scene code — it covers the pedagogical shape (concrete question → visual intuition → formal notation), the verified visual language (pure black background, `CMU Serif` titles, the fixed color-means-something palette), and the motion-grammar table (which animation class to reach for, for a given narrative intent). Pull working code from `references/code_patterns.md` rather than free-handing the ManimGL API from memory — it's a library that drifts from what most general knowledge/tutorials assume (see the two-manims gotcha below), and every snippet there is confirmed working.

4. **Draft-render frequently, at low quality.** `bash scripts/render.sh <file.py> <SceneName> -l` renders fast. Extract a frame or two to sanity-check layout/color/timing (`ffmpeg -ss <t> -update 1 -frames:v 1 frame.png`) before committing to a full-quality render — LaTeX and complex paths are the slow part, so cheap drafts save real time. This is the practical headless substitute for ManimGL's normal live-interactive workflow (see "Interactive development" in `references/code_patterns.md`), which assumes a human watching a window.

5. **Full-quality render once the draft looks right.** `bash scripts/render.sh <file.py> <SceneName>` (drop `-l`). Copy `assets/custom_config.yml.template` to `custom_config.yml` in the project directory first if matching 3b1b's actual look (pure black, CMU Serif, optionally 4K) matters more than fast default rendering.

6. **Run the quality checklist** at the end of `references/style_guide.md` before treating a scene as finished.

7. **Deliver.** Present the rendered mp4(s). If the user wants one file, concatenate with `ffmpeg -f concat`.

## If something breaks

Check `references/cli_reference.md` first — it has a verified table of exact error messages ManimGL produces for missing dependencies and their one-line fixes (missing `dsfont.sty`, missing `dvisvgm`, the pango/cairo build failure, etc.), plus the full CLI flag reference. Almost every setup failure encountered while building this skill is in that table.

## The one thing to never mix up

There are two unrelated libraries called "manim." This skill is **ManimGL** (`pip install manimgl`, from `3b1b/manim`) — not Manim Community Edition (`pip install manim`, from `ManimCommunity/manim`). They have incompatible APIs and installation instructions. If a search result, Stack Overflow answer, or piece of general knowledge about "manim" doesn't match what's in this skill's references, it's very likely describing the Community Edition — don't apply it here.

## Bundled resources

- `scripts/setup_env.sh` — idempotent environment setup
- `scripts/render.sh` — always-headless render wrapper (`xvfb-run -a manimgl ...`)
- `references/style_guide.md` — pedagogy, visual language, color system, motion grammar, quality checklist
- `references/code_patterns.md` — verified working code for common beats (title cards, colored equations, shape transforms, graphs) plus the interactive-development workflow
- `references/cli_reference.md` — CLI flags, output defaults, and the gotchas table
- `assets/custom_config.yml.template` — starter project config matching 3b1b's actual settings (pure black, CMU Serif, optional 4K)
