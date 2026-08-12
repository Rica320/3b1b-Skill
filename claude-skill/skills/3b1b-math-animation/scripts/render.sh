#!/usr/bin/env bash
# Thin wrapper around manimgl that always runs it inside xvfb-run.
# ManimGL needs an OpenGL context even for file-only output with no display
# attached — skip this wrapper and headless rendering will hang or crash.
#
# Usage:
#   ./render.sh <scene_file.py> <SceneName> [extra manimgl flags]
#
# Examples:
#   ./render.sh scenes.py IntroScene              # full-quality render + open
#   ./render.sh scenes.py IntroScene -l            # low-quality draft (fast)
#   ./render.sh scenes.py IntroScene -so           # save final frame as an image only

set -e

if [ $# -lt 2 ]; then
  echo "Usage: $0 <scene_file.py> <SceneName> [extra manimgl flags]"
  exit 1
fi

SCENE_FILE="$1"
SCENE_NAME="$2"
shift 2

xvfb-run -a manimgl "$SCENE_FILE" "$SCENE_NAME" -w -o "$@"
