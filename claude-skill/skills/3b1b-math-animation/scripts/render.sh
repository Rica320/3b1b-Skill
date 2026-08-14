#!/usr/bin/env bash
# Render a ManimGL scene, headless.
#
# ManimGL needs an OpenGL context even for file-only output. On Linux with no
# display attached that means xvfb-run, or the render hangs/crashes. macOS
# provides a context without one, and `xvfb-run` does not exist there — calling
# it unconditionally is why this wrapper used to fail on a Mac.
#
# Usage:
#   ./render.sh <scene_file.py> <SceneName> [extra manimgl flags]
#
# Examples:
#   ./render.sh scenes.py MyVideo              # full quality
#   ./render.sh scenes.py MyVideo -l           # fast draft
#   ./render.sh scenes.py MyVideo -so          # final frame as an image

set -e

if [ $# -lt 2 ]; then
  echo "Usage: $0 <scene_file.py> <SceneName> [extra manimgl flags]"
  exit 1
fi

SCENE_FILE="$1"
SCENE_NAME="$2"
shift 2

# LaTeX often isn't on PATH for non-login shells; add the usual locations.
export PATH="$PATH:/Library/TeX/texbin:/usr/local/texlive/2026basic/bin/universal-darwin"

# Prefer a project virtualenv over a global install. Walk up from the scene
# file looking for env/ or venv/ — manimgl is usually installed per project.
MANIM="manimgl"
d="$(cd "$(dirname "$SCENE_FILE")" && pwd)"
while [ "$d" != "/" ]; do
  for v in env venv .venv; do
    if [ -x "$d/$v/bin/manimgl" ]; then MANIM="$d/$v/bin/manimgl"; break 2; fi
  done
  d="$(dirname "$d")"
done

if ! command -v "$MANIM" >/dev/null 2>&1 && [ ! -x "$MANIM" ]; then
  echo "error: manimgl not found on PATH or in a project venv." >&2
  echo "       run scripts/setup_env.sh, or activate the venv first." >&2
  exit 1
fi

if [ "$(uname)" = "Darwin" ]; then
  "$MANIM" "$SCENE_FILE" "$SCENE_NAME" -w -o "$@"
elif command -v xvfb-run >/dev/null 2>&1; then
  xvfb-run -a "$MANIM" "$SCENE_FILE" "$SCENE_NAME" -w -o "$@"
else
  echo "warning: xvfb-run not found; trying manimgl directly" >&2
  "$MANIM" "$SCENE_FILE" "$SCENE_NAME" -w -o "$@"
fi
