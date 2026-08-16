# The 3Blue1Brown Style, as Concrete Rules

This is what actually makes output look like 3Blue1Brown rather than "generic Manim." Pedagogy and visuals are inseparable in his work — the visual choices exist to serve the explanation.

> **This file covers visual language and motion grammar.** The enforceable rules
> live in `animation_rules.md`, the narrative shape in `narrative_template.md`,
> the known failure modes in `anti_patterns.md`, and the gates in
> `checklists.md`. Read those first; this is the texture layer.

## Pedagogical shape

- **Open with a concrete question or puzzle**, not a definition. The abstract idea shows up later, earned.
- **Visual intuition before formal notation.** Show *why* something is true geometrically/dynamically before writing the symbols for it. The symbols, when they arrive, should feel like a compressed summary of something the viewer already watched happen.
- **One idea per screen.** Resist stacking multiple concepts in the same frame; clear the board (fade out) before introducing the next layer.
- **Build in layers, and let each layer transform into the next** rather than cutting to a new slide — visual continuity is often the argument itself that two things are related.
- **Recurse on "but why?"** — answer a question, then immediately ask why the answer is true, going one level deeper before moving on.
- **Silence and stillness are part of the pacing.** Not every second needs new motion; a beat of stillness after a reveal gives the idea time to land.

## Visual language (verified against 3b1b's own configuration)

- **Background: pure black (`#000000`).** ManimGL's *library* default is actually a dark charcoal grey — but 3b1b's own `custom_config.yml` explicitly pins `background_color: "#000000"`. Use pure black for accurate style matching (see `assets/custom_config.yml.template`).
- **Title/label font: a Computer-Modern-family serif** (3b1b's config sets `text.font: "CMU Serif"`), not a generic sans-serif. This keeps `Text()` visually consistent with the serif math typeface LaTeX (`Tex()`) already renders — titles and equations read as the same typographic family. Confirmed by rendering: a plain title in `CMU Serif` beside a `Tex()` equation reads as a cohesive, recognizably-3b1b frame; a generic sans title next to LaTeX math does not.
- **Color has meaning, and that meaning stays fixed within a video.** Don't reuse red for "error" in one scene and "the second vector" in the next. Establish a mapping early (e.g. "blue is the input, yellow is the output, green is the derivative") and honor it throughout.
- **Palette:** primarily variants of blue (`BLUE_A`–`BLUE_E`) for the "default"/primary objects, `YELLOW` for emphasis or the thing currently being explained, `WHITE`/`GREY` for neutral text and axes, sparing use of `RED`/`GREEN`/`ORANGE`/`TEAL`/`PINK`/`MAROON` when a small number of distinct labeled objects need to be told apart at a glance.
- **Coloring parts of an equation:** `set_color_by_tex(substring, color)` on a `Tex(...)` mobject colors matching substrings without touching the rest of the expression. This is the standard way to say "notice this variable" mid-equation.
- **Minimal on-screen text.** These videos are narration-driven; text mobjects are the equation being discussed or a short label, almost never a paragraph.
- **No hard cuts between related ideas.** Prefer `Transform`/`ReplacementTransform` or a camera pan over a jump cut whenever two consecutive visuals are conceptually related.
- **Titles sit at the top edge** (`to_edge(UP)`); keep the vertical/horizontal center free for the main visual.

## Motion grammar — mapping intent to animation class

| You want to say... | Use |
|---|---|
| "Here's a new object, appearing constructively" | `ShowCreation(mobj)` |
| "Here's a new object, appearing all at once" | `FadeIn(mobj)`, or `Write(mobj)` for text/equations (draws the strokes) |
| "This object is literally the same thing as that one, reshaped" | `Transform(a, b)` or `ReplacementTransform(a, b)` |
| "Remove without ceremony" | `FadeOut(mobj)` |
| "Look here" | `Indicate(mobj)`, `Flash(point)`, `FlashAround(mobj)` (not `Circumscribe` — that's Community Edition only; ManimGL has no `Circumscribe` class) |
| "The camera should move/zoom to follow this" | `self.play(self.camera.frame.animate.move_to(...))` (moving-camera scenes) |
| "The flat picture was hiding something" | tilt the camera out of top-down: `self.play(self.camera.frame.animate.reorient(-30, 68))` — see `three_d.md` |
| "This equation rearranges into that one" | Build both `Tex(...)` mobjects with matching substrings, then `TransformMatchingTex(eq1, eq2)` |

## Pacing

3b1b writes narration first (or alongside animation) and builds visuals to match spoken cadence, not the reverse. Without recorded voiceover, approximate this by:
- Drafting the spoken script / caption text for a beat *before* writing its animation code.
- Timing `run_time=` on `self.play(...)` calls to roughly match how long the corresponding line would take to say aloud (~2.5–3 words/second as a rough baseline).
- Adding a `self.wait()` beat after any reveal that needs a moment to sink in.

## Quality checklist

Superseded by `checklists.md`, which has the full pre-render and post-render
gates plus the commands to run them. The one item worth repeating here:

- [ ] **The math is actually correct** — a beautiful animation of a wrong claim
      is worse than no animation. Prefer a metaphor that *is* the real object
      (compute the field you are drawing) so the visual cannot drift from the
      truth.
