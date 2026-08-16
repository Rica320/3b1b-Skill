# Checklists

Two gates. Do not skip the pre-render one to "just see what it looks like" —
most of these failures are invisible in a draft you scrub through by eye.

---

## Pre-render checklist

Run before spending time on a full-quality render.

### Narrative
- [ ] The script exists as prose and has been approved.
- [ ] **One** driving question, stated within the first 20 seconds.
- [ ] The obvious answer is tried and shown to fail before the real machinery.
- [ ] **One** carried metaphor; its meaning table has ≥4 rows.
- [ ] Every section opens with a spoken sentence that connects it to the last.
- [ ] Every symbol is introduced *after* the picture it names.
- [ ] The payoff restates the opening question verbatim and answers it.

### Structure
- [ ] The whole video is **one `Scene`** with section methods, not N scenes to
      concatenate.
- [ ] At least one object survives every section boundary, transformed.
- [ ] No `FadeOut(VGroup(everything))` followed by building a fresh set.
- [ ] Colour mapping is written down, and each colour has exactly one meaning.
- [ ] Yellow (or whatever the emphasis colour is) is transient only.

### Code
- [ ] No bare `color=` on `Dot`, `Arrow`, or `Circle` — grep for it:
      `grep -nE '(Dot|Arrow|Circle)\([^)]*color=' *.py`
- [ ] No integer indexing into a `Tex` glyph array; equations built from
      separately addressable `Tex` parts.
- [ ] No un-animated `move_to`/`shift` on a mobject already on screen.
- [ ] No `Group.set_opacity()` used to dim-and-restore; use `Dimmer`.
- [ ] No repeated `Transform` onto one `Tex` with a changing glyph count.
- [ ] `assert_in_frame(...)` called for everything positioned relative to
      another mobject.
- [ ] `assert_no_overlap(...)` called for known-risky pairs.
- [ ] Plotted functions: range over the plotted x-interval fits inside
      `y_range`.
- [ ] Connectors are drawn after the things they connect.
- [ ] Every `LaggedStart`/`stagger` has a deliberate `lag_ratio`; no group
      pops in simultaneously.
- [ ] Holds vary with content; narrated captions pass `narration=`.
- [ ] No dead code.
- [ ] `dump_meta(self, "render_meta.json")` at the end of `construct`.

### 3D (skip if the camera never leaves `phi = 0`)
- [ ] The scene needs depth: name the claim that a flat picture cannot make.
- [ ] The scene subclasses `ThreeDScene`, not `Scene`.
- [ ] Every caption, title and legend goes through `fix()` — grep for `Text(`
      and `Tex(` and confirm each one is either fixed or deliberately in world
      space.
- [ ] No flat 2D mobject stacked on a filled one without `flat()`.
- [ ] Dots in space are `dot3d()`/`TrueDot`, not `Dot`.
- [ ] Curves and markers drawn on a surface are lifted clear of it
      (`slice_curve` does this; `lift=0.05` by default).
- [ ] Surfaces have a mesh and non-zero shading; opacity ≈ 0.85.
- [ ] `f(x, y)` over the domain corners fits inside the axes' `z_range`.
- [ ] Camera moves use `orbit()`/`spin()` so they land in `render_meta.json`;
      ambient rotation is under ~10°/s.
- [ ] `assert_in_frame_3d(self, ...)` — not `assert_in_frame` — and called at
      the orientation each label is meant to be read at.
- [ ] Nothing on stage changes during the `phi` reveal.

### Draft
- [ ] A low-quality draft (`-l`) renders end to end without exceptions.
- [ ] Contact sheets reviewed (see command below), not just a few frames.

---

## Post-render verification checklist

Run against the **full-quality** render.

### 1. Automated pixel checks

```bash
python scripts/verify_render.py output/Video.mp4 --meta render_meta.json
```

All five must pass:

| # | Check | Fails when |
|---|---|---|
| 1 | off-frame content | anything in the outer 8px while the camera is at rest |
| 2 | blank-frame windows | ≥0.4s where nothing is visible |
| 3 | over-long frozen holds | a still frame outlasts any plausible narration line |
| 4 | hard cuts | an isolated frame-to-frame delta spike |
| 5 | colour reaching screen | <25% of lit pixels are saturated (→ ANTI-PATTERN #1) |

Camera push-ins legitimately crop and produce large deltas, so declare them:
`push_in()`/`pull_back()` record windows into `render_meta.json` and the checker
skips 1 and 4 inside them. This keeps the checks strict everywhere else instead
of loosening thresholds globally. The same applies to 3D camera moves —
`orbit()` and `spin()` record their own windows; confirm the count printed by
the checker matches the number of moves in the scene before reading the result.

### 2. Text-overlap audit

Wire the audit into `Scene.wait` behind an env flag, then:

```bash
AUDIT=1 manimgl scenes.py MyVideo -w -o -l --video_dir /tmp/audit 2>&1 \
  | tr '\r' '\n' | grep OVERLAP
```

Expect zero lines. **Validate the detector before trusting a zero** — put two
overlapping `Text`s in a throwaway scene and confirm it reports them. A silent
zero is the failure mode here (a `Text` container has no points of its own, so a
`has_points()` filter drops everything).

### 3. Transition boundaries, frame by frame

For each section boundary `t`:

```bash
ffmpeg -ss $(echo "$t-0.35"|bc) -i out.mp4 -frames:v 7 \
  -vf "scale=440:248,tile=7x1" -update 1 -q:v 3 boundary_$t.jpg
```

Look at each strip and name **which object carries across**. If the answer is
"none", Rule 1 is violated regardless of what the automated checks say.

### 4. Contact sheets

```bash
ffmpeg -i out.mp4 -vf "fps=1/4,scale=636:358,pad=640:362:2:2:color=0x444444,tile=4x3" \
  -q:v 3 sheet_%02d.jpg
```

Review every sheet. Automated checks cannot judge composition: crowding, dead
space, a label sitting awkwardly close to an edge, or a field so opaque it hides
the data. Several such issues in the GANs rebuild were found only this way.

For a 3D scene, sample **across the whole rotation** — a label that is clear at
the start of an orbit can be sitting on top of the geometry halfway through, and
a surface that reads as a saddle from one angle reads as a plain bowl from
another. Both were caught this way in `examples/saddle/` and nowhere else.

### 5. Narration sync

For each section, compute `words / duration`:

- **> 3.0 w/s** — rushed. Add holds at landing points *in that section*.
- **< 2.2 w/s** — drags, unless it is the opening or the payoff.
- Target overall ≈ 2.6 w/s.

### 6. Re-read the defect list

If this is a rebuild, walk the original defect list item by item and record
fixed / n/a / still-present for each. Do not mark an item fixed without the
evidence that shows it.

---

## Useful one-liners

```bash
# full-res frame at a suspect moment
ffmpeg -ss 163 -i out.mp4 -frames:v 1 -update 1 -q:v 2 f163.jpg

# where is the video blank or frozen? (see verify_render.py for the real check)
ffprobe -v error -show_entries format=duration -of csv=p=0 out.mp4

# grep for the colour anti-pattern
grep -nE '(Dot|Arrow|Circle)\([^)]*color=' *.py
```
