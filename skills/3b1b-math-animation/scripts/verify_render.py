#!/usr/bin/env python3
"""
Post-render verification for 3b1b-style ManimGL output.

Checks the rendered pixels, not the source. Every check here exists because a
real video shipped the corresponding defect; see references/anti_patterns.md.

    python verify_render.py <video.mp4> [--meta render_meta.json]

`--meta` is the sidecar written by manim_helpers.dump_meta(). It declares the
windows in which the camera is deliberately moving, so checks [1] and [4] can
stay strict everywhere else instead of being loosened globally to accommodate
a couple of intentional close-ups.

Exit status: 0 if every check passes, 1 if any fails, 2 if the video or
ffmpeg could not be read.
"""

import argparse
import json
import shutil
import subprocess
import sys

import numpy as np

EDGE_MARGIN_PX = 8        # outer band that counts as "touching the edge"
EDGE_THRESH = 40          # gray level that counts as content
# "Blank" must mean nothing is visible at all, not merely that little is.
# A single deliberate element on an otherwise empty frame (one glyph holding
# an idea across a boundary) is good style, so measure bright pixels against
# a low bar rather than penalising sparse frames.
BLANK_BRIGHT = 60         # gray level that counts as visible
BLANK_INK_FRAC = 0.0005   # below this fraction of visible px, truly empty
BLANK_MIN_RUN = 0.4       # seconds of blank before it is a defect
FREEZE_DELTA = 0.05       # mean abs frame delta below this is "frozen"
# A silent render is meant to carry voiceover, so a still frame is only a
# defect once it outlasts any single narration line. The longest line in a
# well-paced script runs ~45 words -> ~11s. Anything longer is dead air that
# no narration is covering.
FREEZE_MAX = 11.0
CUT_DELTA = 12.0          # mean abs frame delta above this looks like a cut
GREY_SAT = 0.15           # below this saturation a pixel reads as colourless
MIN_COLOURED = 0.25       # fraction of lit pixels that must carry colour

EDGE_FPS = 5              # sample rate for the off-frame check
MOTION_FPS = 10           # sample rate for the blank/freeze/cut checks
COLOUR_FPS = 1            # sample rate for the colour check
MOTION_W, MOTION_H = 480, 270    # downscale for the motion checks
# Every check analyses at a fixed resolution rather than the video's native
# one, so a draft render (-l, 854x480) and a final 4K render are held to the
# same thresholds — EDGE_MARGIN_PX would otherwise mean a different fraction
# of the frame at each quality.
EDGE_W, EDGE_H = 1920, 1080
FADE_GRACE = 1.5          # opening/closing seconds exempt from the blank check


def decode(path, fps, w, h, pix="gray"):
    """Decode the video to a numpy array of frames at `fps`, scaled to w x h."""
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path,
         "-vf", f"fps={fps},scale={w}:{h}", "-pix_fmt", pix,
         "-f", "rawvideo", "-"],
        capture_output=True)
    if p.returncode != 0:
        sys.exit(f"error: ffmpeg failed on {path}\n"
                 f"{p.stderr.decode(errors='replace')[:400]}")
    ch = 3 if pix == "rgb24" else 1
    buf = np.frombuffer(p.stdout, dtype=np.uint8)
    n = len(buf) // (w * h * ch)
    if n == 0:
        sys.exit(f"error: decoded 0 frames from {path} at fps={fps}")
    return buf[:n * w * h * ch].reshape((n, h, w, ch) if ch == 3 else (n, h, w))


def runs_of(mask, fps, min_len):
    """[(start_s, end_s)] for each run of True at least `min_len` seconds."""
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            if (j - i) / fps >= min_len:
                out.append((i / fps, j / fps))
            i = j
        else:
            i += 1
    return out


def check_off_frame(path, in_cam, failures):
    """[1] Content touching the outer edge of the frame."""
    frames = decode(path, EDGE_FPS, EDGE_W, EDGE_H)
    m = EDGE_MARGIN_PX
    hits = []
    for i, f in enumerate(frames):
        if in_cam(i / EDGE_FPS):
            continue
        edges = {"L": f[:, :m].max(), "R": f[:, -m:].max(),
                 "T": f[:m, :].max(), "B": f[-m:, :].max()}
        bad = [k for k, v in edges.items() if v > EDGE_THRESH]
        if bad:
            hits.append((i / EDGE_FPS, "".join(bad)))

    if hits:
        # collapse consecutive samples sharing the same edge set into one
        # reportable window, so a 3-second bleed is one finding not fifteen
        grouped, start, prev, key = [], hits[0][0], hits[0][0], hits[0][1]
        for t, k in hits[1:]:
            if t - prev > 0.4 or k != key:
                grouped.append((start, prev, key))
                start, key = t, k
            prev = t
        grouped.append((start, prev, key))
        for a, b, k in grouped:
            failures.append(f"OFF-FRAME  {a:6.1f}s-{b:6.1f}s  edges={k}")
    print(f"[1] off-frame content ......... "
          f"{'FAIL' if hits else 'pass'} ({len(hits)} frames)")


def check_motion(path, in_cam, failures):
    """[2] blank windows, [3] frozen holds, [4] hard cuts — one decode."""
    frames = decode(path, MOTION_FPS, MOTION_W, MOTION_H)
    duration = len(frames) / MOTION_FPS

    # ── 2. blank frames / cuts through black ────────────────────────────
    ink = (frames > BLANK_BRIGHT).sum(axis=(1, 2)) / (MOTION_W * MOTION_H)
    blanks = runs_of(ink < BLANK_INK_FRAC, MOTION_FPS, BLANK_MIN_RUN)
    # the opening fade-in and closing fade-out are legitimate
    blanks = [(a, b) for a, b in blanks
              if a > FADE_GRACE and b < duration - FADE_GRACE]
    for a, b in blanks:
        failures.append(f"BLANK      {a:6.1f}s-{b:6.1f}s  ({b - a:.1f}s empty)")
    print(f"[2] blank-frame windows ....... "
          f"{'FAIL' if blanks else 'pass'} ({len(blanks)} windows, "
          f"{sum(b - a for a, b in blanks):.1f}s)")

    # ── 3. frozen holds that drag ───────────────────────────────────────
    delta = np.abs(np.diff(frames.astype(np.int16), axis=0)).mean(axis=(1, 2))
    freezes = runs_of(delta < FREEZE_DELTA, MOTION_FPS, FREEZE_MAX)
    for a, b in freezes:
        failures.append(f"DRAG       {a:6.1f}s-{b:6.1f}s  ({b - a:.1f}s frozen)")
    print(f"[3] over-long frozen holds .... "
          f"{'FAIL' if freezes else 'pass'} ({len(freezes)})")

    # ── 4. hard cuts (a transform should never look like a jump) ────────
    # A true cut is instantaneous: one big delta with quiet frames either
    # side. A camera move or a fast transform is sustained change over many
    # frames, and is not a cut — so require the neighbours to be quiet.
    cuts = []
    for i in range(1, len(delta) - 1):
        t = (i + 1) / MOTION_FPS
        if delta[i] > CUT_DELTA and not in_cam(t):
            if max(delta[i - 1], delta[i + 1]) < delta[i] * 0.45:
                cuts.append(t)
    for t in cuts:
        failures.append(f"HARD CUT   {t:6.1f}s  (isolated delta spike)")
    print(f"[4] hard cuts ................. "
          f"{'FAIL' if cuts else 'pass'} ({len(cuts)})")


def check_colour(path, failures):
    """[5] Colour actually reaching the screen.

    Catches the ManimGL Dot/Arrow/Circle `color=` trap: elements that were
    asked for a colour but render white. Sampled across the whole run.
    """
    frames = decode(path, COLOUR_FPS, MOTION_W, MOTION_H,
                    pix="rgb24").astype(np.int16)
    per_frame = []
    for f in frames:
        px = f.reshape(-1, 3)
        px = px[px.max(axis=1) > 90]        # lit pixels only
        if len(px) < 50:                    # near-empty frame, no signal
            continue
        mx, mn = px.max(axis=1), px.min(axis=1)
        per_frame.append(((mx - mn) / np.maximum(mx, 1) > GREY_SAT).mean())

    coloured = float(np.mean(per_frame)) if per_frame else 0.0
    if coloured < MIN_COLOURED:
        failures.append(
            f"COLOURLESS  only {100 * coloured:.0f}% of lit pixels are "
            f"saturated — check for Dot/Arrow(color=) being ignored")
    print(f"[5] colour reaching screen .... "
          f"{'FAIL' if coloured < MIN_COLOURED else 'pass'} "
          f"({100 * coloured:.0f}% of lit pixels saturated)")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Five post-render pixel checks for a ManimGL render.")
    ap.add_argument("video", help="path to the rendered .mp4")
    ap.add_argument("--meta", metavar="render_meta.json",
                    help="sidecar from manim_helpers.dump_meta(), declaring "
                         "deliberate camera-motion windows")
    args = ap.parse_args(argv)

    if shutil.which("ffmpeg") is None:
        sys.exit("error: ffmpeg not found on PATH")

    # Camera-motion windows declared by the scene. Inside them the frame is
    # deliberately cropped and moving, so [1] and [4] do not apply.
    cam = []
    if args.meta:
        try:
            with open(args.meta) as fh:
                cam = json.load(fh).get("camera_windows", [])
        except (OSError, json.JSONDecodeError) as exc:
            sys.exit(f"error: could not read {args.meta}: {exc}")
        if cam:
            print(f"    (camera-motion windows declared: {len(cam)})")

    def in_cam(t, pad=0.35):
        return any(a - pad <= t <= b + pad for a, b in cam)

    failures = []
    check_off_frame(args.video, in_cam, failures)
    check_motion(args.video, in_cam, failures)
    check_colour(args.video, failures)

    print()
    if failures:
        print(f"{len(failures)} finding(s):")
        for f in failures:
            print("  " + f)
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
