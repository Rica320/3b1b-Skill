#!/usr/bin/env python3
"""
Post-mux verification for a narrated render.

    python verify_audio.py videos/MyVideo_narrated.mp4 --cues narration_cues.json

Six checks, on the muxed file rather than on the plan that produced it. Check
[4] is the one that matters most: it runs ffmpeg's silence detector over the
finished audio and confirms that sound is actually present at every cue time.
Everything upstream can agree with itself and still be wrong -- a scene
re-rendered after the script changed produces a perfectly consistent cue sheet
pointing at the wrong seconds.

Exit status: 0 if every check passes, 1 if any fails, 2 if the file could not
be read.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

I_RANGE = (-18.0, -14.0)      # acceptable integrated loudness, LUFS
TP_MAX = -1.0                 # true peak ceiling, dBTP
DUR_TOL = 0.5                 # audio/video length mismatch, seconds
SILENCE_DB = -50              # below this counts as silence
SILENCE_MIN = 0.30            # shortest gap the detector reports
COVERAGE = (0.40, 0.88)       # fraction of runtime carrying speech
MAX_GAP = 14.0                # longest wordless stretch mid-video
RATE = (2.0, 3.3)             # words per second: drags / rushed


def ffprobe_json(path, args):
    p = subprocess.run(["ffprobe", "-v", "error", "-of", "json", *args,
                        str(path)], capture_output=True)
    if p.returncode != 0:
        sys.exit(f"error: ffprobe failed on {path}\n"
                 f"{p.stderr.decode(errors='replace')[:400]}")
    return json.loads(p.stdout)


def measure_loudness(path):
    p = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(path), "-af",
         "loudnorm=print_format=json", "-f", "null", "-"],
        capture_output=True)
    err = p.stderr.decode(errors="replace")
    a, b = err.rfind("{"), err.rfind("}")
    if a < 0 or b < 0:
        return None
    return json.loads(err[a:b + 1])


def silent_windows(path):
    """[(start, end)] of every silent stretch, from ffmpeg silencedetect."""
    p = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(path), "-af",
         f"silencedetect=noise={SILENCE_DB}dB:d={SILENCE_MIN}",
         "-f", "null", "-"], capture_output=True)
    err = p.stderr.decode(errors="replace")
    starts = [float(m) for m in
              re.findall(r"silence_start: (-?[0-9.]+)", err)]
    ends = [float(m) for m in re.findall(r"silence_end: (-?[0-9.]+)", err)]
    out, i = [], 0
    for s in starts:
        e = next((x for x in ends[i:] if x > s), None)
        if e is None:
            out.append((s, float("inf")))
            break
        i = ends.index(e) + 1
        out.append((s, e))
    return out


def in_silence(windows, t, pad=0.12):
    return any(a + pad <= t <= b - pad for a, b in windows)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Six post-mux checks for a narrated render.")
    ap.add_argument("video")
    ap.add_argument("--cues", default="narration_cues.json")
    args = ap.parse_args(argv)

    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            sys.exit(f"error: {tool} not found on PATH")

    video = Path(args.video)
    if not video.exists():
        sys.exit(f"error: no such file: {video}")

    failures = []

    # ── 1. an audio stream exists, and it is as long as the picture ──────
    info = ffprobe_json(video, ["-show_streams", "-show_format"])
    streams = info.get("streams", [])
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    videos = [s for s in streams if s.get("codec_type") == "video"]
    if not audio:
        failures.append("NO AUDIO   the file has no audio stream at all")
        print("[1] audio stream present ...... FAIL")
        print("\n1 finding(s):\n  " + failures[0])
        return 1

    a_dur = float(audio[0].get("duration") or info["format"]["duration"])
    v_dur = float(videos[0].get("duration") or info["format"]["duration"])
    skew = a_dur - v_dur
    bad_len = abs(skew) > DUR_TOL
    if bad_len:
        failures.append(f"LENGTH     audio {a_dur:.2f}s vs video {v_dur:.2f}s "
                        f"({skew:+.2f}s)")
    print(f"[1] audio stream present ...... {'FAIL' if bad_len else 'pass'} "
          f"({audio[0]['codec_name']}, {audio[0]['sample_rate']} Hz, "
          f"{skew:+.2f}s vs picture)")

    # ── 2. loudness and headroom ────────────────────────────────────────
    m = measure_loudness(video)
    if m is None:
        failures.append("LOUDNESS   could not measure")
        print("[2] loudness / true peak ...... FAIL (unmeasurable)")
    else:
        lufs, tp = float(m["input_i"]), float(m["input_tp"])
        bad = not (I_RANGE[0] <= lufs <= I_RANGE[1]) or tp > TP_MAX
        if not (I_RANGE[0] <= lufs <= I_RANGE[1]):
            failures.append(f"LOUDNESS   {lufs:.1f} LUFS, want "
                            f"{I_RANGE[0]} to {I_RANGE[1]}")
        if tp > TP_MAX:
            failures.append(f"PEAK       {tp:.1f} dBTP, want <= {TP_MAX}")
        print(f"[2] loudness / true peak ...... {'FAIL' if bad else 'pass'} "
              f"({lufs:.1f} LUFS, {tp:.1f} dBTP)")

    # ── the cue sheet, for checks 3-6 ───────────────────────────────────
    cue_path = Path(args.cues)
    if not cue_path.exists():
        print(f"[3-6] skipped: no cue sheet at {cue_path}")
        print()
        if failures:
            print(f"{len(failures)} finding(s):")
            for f in failures:
                print("  " + f)
            return 1
        print("All checks passed.")
        return 0
    cues = json.loads(cue_path.read_text())["cues"]
    cues = sorted(cues, key=lambda c: c["t"])

    # ── 3. lines do not overlap, and none runs off the end ──────────────
    clashes = []
    for a, b in zip(cues, cues[1:]):
        end = a["t"] + a["duration"]
        if b["t"] < end - 0.01:
            clashes.append(f"OVERLAP    {a['beat']} ends {end:.2f}s, "
                           f"{b['beat']} starts {b['t']:.2f}s")
    for c in cues:
        if c["t"] + c["duration"] > v_dur + 0.05:
            clashes.append(f"OVERRUN    {c['beat']} ends "
                           f"{c['t'] + c['duration']:.2f}s, video {v_dur:.2f}s")
    failures.extend(clashes)
    print(f"[3] line overlap / overrun .... "
          f"{'FAIL' if clashes else 'pass'} ({len(cues)} lines)")

    # ── 4. sound is really there at every cue ───────────────────────────
    # The check that catches a scene rendered against a different script.
    windows = silent_windows(video)
    missed = []
    for c in cues:
        probe = c["t"] + min(0.35, c["duration"] * 0.4)
        if in_silence(windows, probe):
            missed.append(f"NO SPEECH  {c['beat']} cued at {c['t']:.2f}s "
                          f"but the mix is silent there")
    failures.extend(missed)
    print(f"[4] speech present at each cue  "
          f"{'FAIL' if missed else 'pass'} "
          f"({len(cues) - len(missed)}/{len(cues)} cues land on sound)")

    # ── 5. how much of the runtime carries narration ────────────────────
    spoken = sum(c["duration"] for c in cues)
    frac = spoken / v_dur if v_dur else 0.0
    bad_cov = not (COVERAGE[0] <= frac <= COVERAGE[1])
    if frac < COVERAGE[0]:
        failures.append(f"DEAD AIR   only {100 * frac:.0f}% of the runtime "
                        f"carries narration")
    elif frac > COVERAGE[1]:
        failures.append(f"NO ROOM    {100 * frac:.0f}% of the runtime is "
                        f"speech; the viewer never gets a beat to look")
    print(f"[5] narration coverage ........ {'FAIL' if bad_cov else 'pass'} "
          f"({100 * frac:.0f}% of {v_dur:.0f}s)")

    # ── 6. no long wordless stretch in the middle ───────────────────────
    gaps, prev = [], 0.0
    for c in cues:
        if c["t"] - prev > MAX_GAP:
            gaps.append((prev, c["t"]))
        prev = max(prev, c["t"] + c["duration"])
    if v_dur - prev > MAX_GAP:
        gaps.append((prev, v_dur))
    for a, b in gaps:
        failures.append(f"SILENT     {a:6.1f}s-{b:6.1f}s ({b - a:.1f}s with "
                        f"no narration)")
    print(f"[6] longest wordless stretch .. {'FAIL' if gaps else 'pass'} "
          f"({max([c2['t'] - (c1['t'] + c1['duration']) for c1, c2 in zip(cues, cues[1:])] or [0]):.1f}s max gap)")

    # ── pacing report (informative, not a gate) ─────────────────────────
    slow = [c for c in cues
            if c["duration"] > 0 and _rate(c) and _rate(c) < RATE[0]]
    fast = [c for c in cues if _rate(c) and _rate(c) > RATE[1]]
    if slow or fast:
        print(f"\npacing: {len(fast)} line(s) above {RATE[1]} w/s (rushed), "
              f"{len(slow)} below {RATE[0]} w/s (drags)")
        for c in fast + slow:
            print(f"  {c['t']:7.2f}s  {c['beat']:<26} {_rate(c):.2f} w/s")

    print()
    if failures:
        print(f"{len(failures)} finding(s):")
        for f in failures:
            print("  " + f)
        return 1
    print("All checks passed.")
    return 0


def _rate(cue):
    text = cue.get("text")
    if not text or not cue["duration"]:
        return None
    return len(text.split()) / cue["duration"]


if __name__ == "__main__":
    sys.exit(main())
