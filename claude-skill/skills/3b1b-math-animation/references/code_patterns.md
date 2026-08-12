# Verified ManimGL Code Patterns

Every snippet below was actually rendered headlessly (no display) during the writing of this skill and produced correct output — colors, LaTeX, layout all confirmed by inspecting extracted frames. Start from these rather than free-handing the API from memory.

All snippets assume `from manimlib import *` at the top of the file, and one `Scene` subclass per file-beat (see the workflow in `SKILL.md`).

## Title card

```python
class TitleCard(Scene):
    def construct(self):
        title = Text("Pythagorean theorem", font="CMU Serif", font_size=48)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait()
```

## Equation with color-coded parts

The standard "notice this variable" move — colors a substring of a LaTeX expression without touching the rest.

```python
class ColoredEquation(Scene):
    def construct(self):
        eq = Tex("a^2 + b^2 = c^2")
        eq.scale(1.5)
        eq.set_color_by_tex("a", BLUE)
        eq.set_color_by_tex("b", YELLOW)
        eq.set_color_by_tex("c", GREEN)
        self.play(Write(eq))
        self.wait()
```

**Substring gotcha, confirmed by testing:** `set_color_by_tex` matches on substrings, not whole tokens. Coloring `"x^2"` in the expression `(x + dx)^2 = x^2 + 2x\,dx + dx^2` also colors the `x^2` that's part of `dx^2` at the end, since `"x^2"` is textually a substring of `"dx^2"`. If that's not the intent, either color the more specific/unique substring (e.g. distinguish via spacing or grouping in the LaTeX source) or color mobject pieces by index instead of by text match.

## Shape-to-shape transform ("this becomes that")

The core visual-continuity move — use this instead of a cut whenever two consecutive visuals are conceptually related.

```python
class ShapeTransform(Scene):
    def construct(self):
        square = Square()
        circle = Circle()
        circle.set_fill(BLUE, opacity=0.5)
        circle.set_stroke(BLUE_E, width=4)

        self.play(ShowCreation(square))
        self.play(Transform(square, circle))
        self.wait()
```

## Coordinate system with a plotted function

The single most common 3b1b beat — an axes system with a labeled, colored function graph.

```python
class GraphScene(Scene):
    def construct(self):
        axes = Axes(
            x_range=(-3, 3, 1),
            y_range=(-2, 2, 1),
            height=6, width=10,
        )
        axes.add_coordinate_labels()

        graph = axes.get_graph(lambda x: np.sin(x), color=YELLOW)
        label = Tex("f(x) = \\sin(x)").set_color(YELLOW)
        label.to_corner(UR)

        self.play(Write(axes))
        self.play(ShowCreation(graph), run_time=2)
        self.play(FadeIn(label))
        self.wait()
```

## Interactive iterative development (ManimGL's signature workflow)

ManimGL is built around live-tweaking a scene rather than blind write-render-check cycles. Two ways in:

1. **Drop into an interactive session at a specific line:**
   ```bash
   manimgl file.py SceneName -se <line_number>
   ```
   This opens an IPython terminal at that point in `construct()`, with all mobjects created so far available in the local namespace, so you can call `self.play(...)` interactively and see the effect immediately.

2. **`self.embed()` inside `construct()`** does the same thing from within the code itself — execution pauses there and drops into an IPython shell with the current scene state live.

3. **`checkpoint_paste()`**, called from within that IPython session, runs whatever code is on the clipboard. If the pasted code starts with a comment, the first run at that comment saves a checkpoint of the scene state; subsequent runs of code starting with the same comment first revert to that saved state before re-running — letting you tweak a block of animation code and re-trigger it without re-running everything before it. (3b1b binds this to editor keyboard shortcuts in his own workflow; see the `3b1b/videos` repo README for the Sublime Text plugin he uses.)

**In a headless/agentic context with no one watching a live window**, the practical substitute for this whole workflow is: render at low quality frequently (`-l`) and inspect extracted frames, rather than iterating live. See `SKILL.md` for that loop.

## Render invocations (always headless via xvfb)

```bash
# Low-quality draft, fast iteration
xvfb-run -a manimgl scenes.py SceneName -w -o -l

# Full quality (default resolution/fps from custom_config.yml or manimlib defaults)
xvfb-run -a manimgl scenes.py SceneName -w -o

# Just the final frame as a still image (fast style/color check, no video encode)
xvfb-run -a manimgl scenes.py SceneName -so
```

Or use `scripts/render.sh scenes.py SceneName [flags]`, which wraps the `xvfb-run -a` boilerplate.
