#!/usr/bin/env bash
# Sets up a headless ManimGL (3b1b/manim) environment. Idempotent — safe to
# re-run; each step is skipped if already satisfied.
#
# Every package installed here earned its place by causing a specific,
# confusing failure during testing. See references/cli_reference.md for the
# failure -> fix table if something here doesn't apply to your base image.

set -e

echo "== 3b1b-math-animation: environment setup =="

# --- System packages -------------------------------------------------------
# pkg-config + libpango1.0-dev: required to BUILD manimpango (a manimgl dep).
#   Without them, `pip install manimgl` fails at wheel-build with
#   "pangocairo >= 1.30.0 is required" even if runtime cairo/pango are present.
# texlive-fonts-extra: provides dsfont.sty, which manimgl's default tex
#   preamble pulls in. Without it, any Tex(...) call fails.
# texlive-latex-extra, texlive-science: broaden LaTeX package coverage for
#   less common math macros.
# dvisvgm: separate binary manimgl shells out to (not bundled with
#   texlive-latex-base). Without it: FileNotFoundError: dvisvgm.
# xvfb: virtual framebuffer so ModernGL/OpenGL can get a context with no
#   physical display attached. Required even for file-only (-w) renders.
# fonts-cmu: provides "CMU Serif", the font 3b1b's own custom_config.yml
#   uses for Text() so it visually matches the LaTeX (Tex) typeface.
NEEDED_APT_PKGS="ffmpeg pkg-config libcairo2-dev libpango1.0-dev xvfb \
texlive-base texlive-latex-base texlive-latex-extra texlive-fonts-extra \
texlive-science dvisvgm fonts-cmu"

MISSING=""
for pkg in $NEEDED_APT_PKGS; do
  dpkg -s "$pkg" >/dev/null 2>&1 || MISSING="$MISSING $pkg"
done

if [ -n "$MISSING" ]; then
  echo "Installing missing apt packages:$MISSING"
  apt-get update -qq
  apt-get install -y -qq $MISSING
else
  echo "All required apt packages already present."
fi

# --- Python package ----------------------------------------------------
# IMPORTANT: the package is `manimgl`, NOT `manim` (that's the unrelated
# Community Edition, with an incompatible API).
#
# Check via `pip show`, NOT `python3 -c "import manimlib"` — importing
# manimlib itself tries to open a GL shadow window at import time and
# fails with an unrelated-looking "Cannot connect to display" error if no
# display (real or virtual) is available. This trips up naive sanity
# checks; xvfb-run is required even to import the package, not just to
# render with it.
if python3 -m pip show manimgl >/dev/null 2>&1; then
  echo "manimgl already installed."
else
  echo "Installing manimgl..."
  pip install manimgl --break-system-packages 2>/dev/null || pip install manimgl
fi

# --- Font cache ----------------------------------------------------------
fc-cache -f >/dev/null 2>&1 || true

echo "== Setup complete. Verify with: =="
echo "  xvfb-run -a manimgl example_scenes.py OpeningManimExample -w -o"
