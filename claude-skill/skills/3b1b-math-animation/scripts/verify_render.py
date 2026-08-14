#!/usr/bin/env python3
"""
Post-render verification for 3b1b-style ManimGL output.

Checks the rendered pixels, not the source. Every check here exists because
the v1 GANs video shipped the corresponding defect (see DEFECTS.md).

    python verify_render.py <video.mp4> [--sections sections.json]

Exit code is non-zero if any check fails.
"""

import subprocess
import sys
import json
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


def decode(path, fps, w, h, pix="gray"):
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path,
         "-vf", f"fps={fps},scale={w}:{h}", "-pix_fmt", pix,
         "-f", "rawvideo", "-"],
        capture_output=True)
    if p.returncode != 0:
        sys.exit(f"ffmpeg failed: {p.stderr.decode()[:400]}")
    ch = 3 if pix == "rgb24" else 1
    buf = np.frombuffer(p.stdout, dtype=np.uint8)
    n = len(buf) // (w * h * ch)
    return buf[:n * w * h * ch].reshape((n, h, w, ch) if ch == 3 else (n, h, w))


def runs_of(mask, fps, min_len):
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


def main():
    path = sys.argv[1]
    failures = []

    # Camera-motion windows declared by the scene (see gan_lib.dump_meta).
    # Inside them the frame is deliberately cropped and moving, so the
    # off-frame and hard-cut checks do not apply.
    cam = []
    if "--meta" in sys.argv:
        with open(sys.argv[sys.argv.index("--meta") + 1]) as fh:
            cam = json.load(fh).get("camera_windows", [])
    if cam:
        print(f"    (camera-motion windows declared: {len(cam)})")

    def in_cam(t, pad=0.35):
        return any(a - pad <= t <= b + pad for a, b in cam)

    # ── 1. content off the edge of the frame ────────────────────────────
    F = decode(path, 5, 1920, 1080)
    m = EDGE_MARGIN_PX
    hits = []
    for i, f in enumerate(F):
        if in_cam(i / 5):
            continue
        e = {"L": f[:, :m].max(), "R": f[:, -m:].max(),
             "T": f[:m, :].max(), "B": f[-m:, :].max()}
        bad = [k for k, v in e.items() if v > EDGE_THRESH]
        if bad:
            hits.append((i / 5, "".join(bad)))
    if hits:
        grouped, start, prev, key = [], hits[0][0], hits[0][0], hits[0][1]
        for t, k in hits[1:]:
            if t - prev > 0.4 or k != key:
                grouped.append((start, prev, key))
                start, key = t, k
            prev = t
        grouped.append((start, prev, key))
        for a, b, k in grouped:
            failures.append(
                f"OFF-FRAME  {a:6.1f}s-{b:6.1f}s  edges={k}")
    print(f"[1] off-frame content ......... "
          f"{'FAIL' if hits else 'pass'} ({len(hits)} frames)")

    # ── 2. blank frames / cuts through black ────────────────────────────
    G = decode(path, 10, 480, 270)
    ink = (G > BLANK_BRIGHT).sum(axis=(1, 2)) / (480 * 270)
    blanks = runs_of(ink < BLANK_INK_FRAC, 10, BLANK_MIN_RUN)
    # the opening fade-in and closing fade-out are legitimate
    dur = len(G) / 10
    blanks = [(a, b) for a, b in blanks if a > 1.5 and b < dur - 1.5]
    total_blank = sum(b - a for a, b in blanks)
    for a, b in blanks:
        failures.append(f"BLANK      {a:6.1f}s-{b:6.1f}s  ({b-a:.1f}s empty)")
    print(f"[2] blank-frame windows ....... "
          f"{'FAIL' if blanks else 'pass'} "
          f"({len(blanks)} windows, {total_blank:.1f}s)")

    # ── 3. frozen holds that drag ───────────────────────────────────────
    d = np.abs(np.diff(G.astype(np.int16), axis=0)).mean(axis=(1, 2))
    freezes = runs_of(d < FREEZE_DELTA, 10, FREEZE_MAX)
    for a, b in freezes:
        failures.append(f"DRAG       {a:6.1f}s-{b:6.1f}s  ({b-a:.1f}s frozen)")
    print(f"[3] over-long frozen holds .... "
          f"{'FAIL' if freezes else 'pass'} ({len(freezes)})")

    # ── 4. hard cuts (a transform should never look like a jump) ────────
    # A true cut is instantaneous: one big delta with quiet frames either
    # side. A camera move or a fast transform is sustained change over many
    # frames, and is not a cut - so require the neighbours to be quiet.
    cuts = []
    for i in range(1, len(d) - 1):
        t = (i + 1) / 10
        if d[i] > CUT_DELTA and not in_cam(t):
            neighbours = max(d[i - 1], d[i + 1])
            if neighbours < d[i] * 0.45:
                cuts.append(t)
    for t in cuts:
        failures.append(f"HARD CUT   {t:6.1f}s  (isolated delta spike)")
    print(f"[4] hard cuts ................. "
          f"{'FAIL' if cuts else 'pass'} ({len(cuts)})")

    # ── 5. colour actually reaching the screen ──────────────────────────
    # Catches the ManimGL Dot/Arrow/Circle `color=` trap: elements that were
    # asked for a colour but render white. Sampled across the whole run.
    R = decode(path, 1, 480, 270, pix="rgb24").astype(np.int16)
    fr_sat = []
    for f in R:
        px = f.reshape(-1, 3)
        px = px[px.max(axis=1) > 90]
        if len(px) < 50:
            continue
        mx, mn = px.max(axis=1), px.min(axis=1)
        sat = (mx - mn) / np.maximum(mx, 1)
        fr_sat.append((sat > GREY_SAT).mean())
    coloured = float(np.mean(fr_sat)) if fr_sat else 0.0
    if coloured < 0.25:
        failures.append(
            f"COLOURLESS  only {100*coloured:.0f}% of lit pixels are "
            f"saturated - check for Dot/Arrow(color=) being ignored")
    print(f"[5] colour reaching screen .... "
          f"{'FAIL' if coloured < 0.25 else 'pass'} "
          f"({100*coloured:.0f}% of lit pixels saturated)")

    # ── report ──────────────────────────────────────────────────────────
    print()
    if failures:
        print(f"{len(failures)} finding(s):")
        for f in failures:
            print("  " + f)
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
