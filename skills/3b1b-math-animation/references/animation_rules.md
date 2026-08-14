# Animation Rules

These are **rules, not preferences.** Each one is stated as an instruction the
generator must follow. Where a rule has a mechanical helper, it is named.
`scripts/manim_helpers.py` implements all of them.

---

## Rule 1 — Transform, don't cut

**Objects that represent the same idea must morph, not disappear and reappear.**
Continuity of object identity is the core of this style; it is often the argument
itself that two things are related.

- Never end a beat with `FadeOut(VGroup(everything))` followed by construction of
  a fresh mobject set. That is a slideshow.
- Across a section boundary, **at least one object must survive** — transformed,
  moved, recoloured, or zoomed — carrying the idea into the next section.
- Use `ReplacementTransform` (or `morph()`) whenever two consecutive visuals are
  conceptually the same thing. The blurred face *becomes* a point on the plane;
  the question mark *becomes* the generator's output; the two objective terms
  *become* `min_G max_D`.
- If the two visuals genuinely cannot morph (different mobject types, e.g. an
  `ImageMobject` field), cross-dissolve them **while genuinely transforming
  something else derived from the same data** (`swap_raster(..., extra=[Transform(profile, new_profile)])`).
  The eye reads continuity from the thing that truly morphed.

**Build the whole video as ONE `Scene`.** Rendering beats as separate files and
concatenating them guarantees a black frame at every boundary — that alone put
24 seconds of blank screen (11% of the runtime) into the v1 GANs video. Use
section methods on a single `Scene` and pass persistent mobjects between them.

**Verify:** `verify_render.py` checks [2] blank windows and [4] hard cuts must
both be zero.

---

## Rule 2 — One idea on screen at a time

**Everything not currently load-bearing fades or dims.**

- Prefer **dimming to 0.15–0.25** over deleting. Context you delete has to be
  rebuilt later, which forces a cut. Use `Dimmer` — never `Group.set_opacity()`
  (see ANTI-PATTERN #6).
- When a moment deserves the whole frame (the payoff question, a single
  definition), dim the entire stage and put one thing at centre.
- Two captions must never coexist. Use `Caption`, which clears before writing.

---

## Rule 3 — Nothing appears unmotivated

**Every new element enters because the narration just asked for it.**

- No element may appear before the line that motivates it.
- Build in dependency order: nodes before the edges that connect them, axes
  before the curve on them, the surface before the symbol that names it.
- Notation is always last in its beat (see `narrative_template.md` §5).

---

## Rule 4 — Direct attention with position and camera, not decoration

**Move the frame to what matters rather than adding arrows or highlights.**

- Use `push_in(scene, target, height)` / `pull_back(scene)` for close-ups.
  These record camera windows into `render_meta.json` so post-render checks can
  distinguish a deliberate crop from content falling off the edge.
- Reach for `Indicate`/`FlashAround` only when the thing to notice is already
  on screen and cannot be moved to.
- Reserve arrows for depicting actual relationships (data flow, a gradient
  direction), never as a "look here" pointer.

---

## Rule 5 — Colour is semantic and consistent

**The same concept keeps the same colour for the whole video. Document the
mapping in the script before writing code.**

| Colour | Means |
|---|---|
| `BLUE_C` | the real / given / input data |
| `ORANGE` | the generated / model's own / output |
| `TEAL_C` | the second actor (critic, classifier, learned function) |
| `GREEN` | gradient / direction of improvement |
| `YELLOW` | **transient** emphasis: whatever is load-bearing right now |
| `GREY_B` / `WHITE` | neutral scaffolding — axes, seeds, connectives |

- Yellow must stay transient. Do not also make it an object's identity colour —
  v1 used yellow for the generator, for emphasis text, for a needle, and for
  `z₂`, which destroyed it as an attention signal.
- An object with no colour of its own is fine and often better: the generator is
  identified by the colour of what it *produces*.
- Fill and stroke of the same concept use the same hue at different opacities.

**Verify:** `verify_render.py` check [5] measures what fraction of lit pixels
are actually saturated. Below 25% means colours are not reaching the screen —
almost always ANTI-PATTERN #1.

---

## Rule 6 — Stagger related elements

**Use `lag_ratio`; never pop a group in simultaneously.**

- `stagger(anims, lag_ratio=...)` wraps `LaggedStart`.
- Rough values: `0.01–0.03` for large point clouds (60+ dots), `0.08–0.15` for a
  handful of labels, `0.2–0.45` for sequential steps in a diagram.
- Total `run_time` should still be short; staggering is about *order*, not
  duration.

---

## Rule 7 — Hold for comprehension, and vary the hold

**Hold ~0.5–1.5s after each reveal so the eye can land. Pace to comprehension,
not to the clock.**

- `hold(scene, 1.0)` ≈ 0.9s for a simple reveal; `hold(scene, 2.0)` ≈ 1.35s for
  a dense frame or an emotional peak.
- **Uniform holds are a defect.** v1 used `self.wait(2.0)` after every beat,
  which dragged on trivial frames and rushed dense ones. Twelve holds of ≥2s
  contributed 27.8s of frozen screen.
- For narration-carrying holds, pass the actual spoken line to
  `Caption.show(text, narration=...)`. The hold is then derived from the line's
  word count, so it varies with content automatically.
- A still frame is *not* dead air if narration is playing over it. The ceiling is
  the longest single narration line (~11s); beyond that nothing is covering it.

**Verify:** check [3] flags frozen holds beyond that ceiling.

---

## Rule 8 — Never ship content that leaves the frame

- Call `assert_in_frame(name=mobj, ...)` **before** `self.play` for anything
  positioned relative to another mobject. `next_to(x, RIGHT)` after
  `x.to_corner(DR)` is how content walks off the edge unnoticed — it put a
  labelled image fully off-screen for 3.2s in v1.
- Call `assert_no_overlap([...])` for pairs you know are at risk, and run the
  full `audit_text_overlaps` sweep (see checklists) for the ones you didn't
  predict.
- Check the y-range of any plotted function actually contains the function's
  range over the plotted x-range. v1 clipped a parabola against the top edge for
  9.8 continuous seconds.

**Verify:** check [1] must report zero frames with content in the outer 8px.
