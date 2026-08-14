# ManimGL CLI Reference & Known Gotchas

## Useful CLI flags

| Flag | Effect |
|---|---|
| `-w` | Write the scene to a video file |
| `-o` | Write and open the result |
| `-s` | Skip to the end, show only the final frame |
| `-so` | Save the final frame as a still image (no video encode — fast style check) |
| `-n <k>` | Skip ahead to the k'th animation in the scene |
| `-l` | Low quality (fast iteration) |
| `-se <line>` | Drop into an interactive session at a given line number |
| `-f` | Fullscreen playback window (not relevant headless) |

## Output defaults

Without a `custom_config.yml` override: 1920×1080, 30fps, h264 mp4, background is a dark charcoal grey, written under `./videos/<module>/` relative to wherever `manimgl` is invoked.

With `assets/custom_config.yml.template` applied (matching 3b1b's own config): pure black background (`#000000`), `CMU Serif` for `Text()`, 4K resolution available (3840×2160) if you opt into it — see the template for the exact keys.

Frame geometry: 16:9 aspect ratio, logical frame height 8 units regardless of pixel resolution (`FRAME_HEIGHT = 8.0`, `FRAME_WIDTH = FRAME_HEIGHT * 16/9`). Position values like `UP`, `to_edge()`, `to_corner()` are in these logical units, not pixels.

## Known gotchas (all encountered directly while building this skill)

| Symptom | Cause | Fix |
|---|---|---|
| `pangocairo >= 1.30.0 is required` during `pip install manimgl` | Missing dev headers for building `manimpango` | `apt-get install pkg-config libpango1.0-dev libcairo2-dev` |
| `LaTeX Error: File 'dsfont.sty' not found` on any `Tex(...)` call | ManimGL's default tex preamble needs a package outside base texlive | `apt-get install texlive-fonts-extra texlive-latex-extra texlive-science` |
| `FileNotFoundError: dvisvgm` | `dvisvgm` binary not installed separately from texlive | `apt-get install dvisvgm` |
| Rendering hangs, crashes, or errors about no display/context, even with `-w` and no window requested | ModernGL needs a real or virtual OpenGL context regardless of whether output is a window or just a file | Always wrap render commands in `xvfb-run -a ...` (or use `scripts/render.sh`) |
| `pyglet.display.xlib.NoSuchDisplayException: Cannot connect to "None"` from a **plain `import manimlib`**, before any rendering is attempted | `manimlib.window` creates a GL shadow window at import time as a side effect — even importing the package needs a display, not just rendering with it | Don't sanity-check the install with `python3 -c "import manimlib"`; use `pip show manimgl` instead, or wrap the import itself in `xvfb-run -a` |
| `Text(...)` renders in an unexpected monospace or generic sans font | The intended font (`CMU Serif`, matching 3b1b's own config) isn't installed | `apt-get install fonts-cmu`, then pass `font="CMU Serif"` explicitly or set it in `custom_config.yml`; refresh with `fc-cache -f` if it still doesn't apply |
| Confusing errors when following tutorials found by searching "manim" | Most search results and tutorials are for the unrelated Community Edition (`pip install manim`), which has an incompatible API | Always specify **ManimGL** / `manimgl` when searching docs or installing; never mix instructions between the two |
| `FileNotFoundError: [Errno 2] No such file or directory: 'latex'` on any `Tex(...)` call, on macOS, even though TeX Live is installed | A MacTeX/TeX Live install can exist under `/usr/local/texlive/<year>/bin/<platform>-darwin/` without being on `PATH` for non-interactive shells | `export PATH="/usr/local/texlive/<year>/bin/universal-darwin:$PATH"` (check the actual dir with `find /usr/local/texlive -maxdepth 2 -type d`) before invoking `manimgl` |

## Two unrelated libraries named "manim"

| | ManimGL (this skill) | Manim Community Edition |
|---|---|---|
| PyPI package | `manimgl` | `manim` |
| Renderer | OpenGL (needs a GL context even headless) | Cairo (no display dependency) |
| Source | [3b1b/manim](https://github.com/3b1b/manim) — Grant Sanderson's own tool | [ManimCommunity/manim](https://github.com/ManimCommunity/manim) — community fork |

They are not interchangeable. Mixing install instructions or API usage between them is the single most common source of confusion when working with either.
