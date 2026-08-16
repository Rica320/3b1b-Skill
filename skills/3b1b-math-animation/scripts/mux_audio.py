#!/usr/bin/env python3
"""
Lay the narration onto a rendered video, at the frames the scene asked for.

    python mux_audio.py videos/MyVideo.mp4 \
        --cues narration_cues.json --audio audio/ -o videos/MyVideo_narrated.mp4

    # with a music bed, ducked under the voice
    python mux_audio.py videos/MyVideo.mp4 --cues narration_cues.json \
        --music bed.mp3 --music-db -24

Each cue in `narration_cues.json` is `{beat, t, duration, file}` -- the time the
scene was at when that line began. Nothing here searches for sync or stretches
anything: the scene already waited for the exact length of every wav, so laying
each file down at its cue time is the whole job. If the result is out of sync,
the scene and the audio were built from different versions of the script, and
the fix is upstream.

The mix is loudness-normalised to -16 LUFS integrated / -1.5 dBTP in two
passes. A single-pass normaliser rides the gain and pumps audibly on speech
with long gaps in it, which is exactly what a narration track is.
"""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TARGET_I = -16.0          # integrated loudness, LUFS (spoken-word streaming)
TARGET_TP = -1.5          # true peak ceiling, dBTP
TARGET_LRA = 11.0         # loudness range
MIX_SR = 48000
MUSIC_DB = -24.0          # music bed level before ducking


def run(cmd, capture=False):
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        sys.exit(f"error: command failed\n  {' '.join(shlex.quote(c) for c in cmd)}\n"
                 f"{p.stderr.decode(errors='replace')[-1500:]}")
    return p.stderr.decode(errors="replace") if capture else None


def probe_duration(path):
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)], capture_output=True)
    if p.returncode != 0:
        sys.exit(f"error: ffprobe failed on {path}")
    return float(p.stdout.decode().strip())


def build_voice_track(cues, out_path, total):
    """Sum every cue's wav at its cue time into one track `total` long."""
    inputs, filters, labels = [], [], []
    for i, c in enumerate(cues):
        inputs += ["-i", str(c["file"])]
        ms = int(round(c["t"] * 1000))
        # adelay wants one delay per channel; the wavs are mono, and `all=1`
        # covers the case where a hand-supplied file is not.
        filters.append(f"[{i}:a]aresample={MIX_SR},adelay={ms}:all=1[v{i}]")
        labels.append(f"[v{i}]")

    if not inputs:
        sys.exit("error: no cues to mux")
    mix = (f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:"
           f"dropout_transition=0[voice]")
    # apad+atrim pins the track to the video length: without it the file ends
    # at the last word and players show a shorter stream than the picture.
    tail = f"[voice]apad,atrim=0:{total:.3f},asetpts=N/SR/TB[out]"
    run(["ffmpeg", "-v", "error", "-y", *inputs,
         "-filter_complex", ";".join(filters + [mix, tail]),
         "-map", "[out]", "-ac", "1", "-ar", str(MIX_SR),
         "-c:a", "pcm_s16le", str(out_path)])
    return out_path


def add_music(voice, music, out_path, total, music_db, duck):
    """Mix a bed under the voice, optionally side-chain ducked by it."""
    if duck:
        chain = (
            f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{total:.3f},"
            f"volume={music_db}dB,aresample={MIX_SR}[bed];"
            f"[0:a]asplit=2[v1][key];"
            f"[bed][key]sidechaincompress=threshold=0.03:ratio=12:"
            f"attack=25:release=500[duckedbed];"
            f"[v1][duckedbed]amix=inputs=2:normalize=0[out]")
    else:
        chain = (
            f"[1:a]aloop=loop=-1:size=2e9,atrim=0:{total:.3f},"
            f"volume={music_db}dB,aresample={MIX_SR}[bed];"
            f"[0:a][bed]amix=inputs=2:normalize=0[out]")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(voice), "-i", str(music),
         "-filter_complex", chain, "-map", "[out]",
         "-ac", "1", "-ar", str(MIX_SR), "-c:a", "pcm_s16le", str(out_path)])
    return out_path


def loudnorm(src, dst):
    """Two-pass EBU R128 normalisation. Returns the written path."""
    stderr = run(["ffmpeg", "-v", "info", "-i", str(src), "-af",
                  f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:"
                  f"print_format=json", "-f", "null", "-"], capture=True)
    start = stderr.rfind("{")
    end = stderr.rfind("}")
    if start < 0 or end < 0:
        print("[mux] warning: loudnorm measurement failed; single pass")
        run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
             f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}",
             "-ar", str(MIX_SR), "-c:a", "pcm_s16le", str(dst)])
        return dst
    m = json.loads(stderr[start:end + 1])
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
         f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:"
         f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
         f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
         f"offset={m['target_offset']}:linear=true:print_format=summary",
         "-ar", str(MIX_SR), "-c:a", "pcm_s16le", str(dst)])
    return dst


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Mux narration cues onto a rendered video.")
    ap.add_argument("video")
    ap.add_argument("--cues", default="narration_cues.json",
                    help="cue sheet written by Narrator.dump()")
    ap.add_argument("--audio", default=None,
                    help="directory holding the beat wavs (default: the paths "
                         "recorded in the cue sheet)")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--music", help="background bed (looped to length)")
    ap.add_argument("--music-db", type=float, default=MUSIC_DB)
    ap.add_argument("--no-duck", action="store_true",
                    help="do not side-chain the bed under the voice")
    ap.add_argument("--keep-wav", action="store_true",
                    help="also write the normalised mix next to the output")
    args = ap.parse_args(argv)

    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            sys.exit(f"error: {tool} not found on PATH")

    video = Path(args.video)
    if not video.exists():
        sys.exit(f"error: no such video: {video}")
    doc = json.loads(Path(args.cues).read_text())
    cues = doc["cues"]

    for c in cues:
        f = Path(c["file"]) if c.get("file") else None
        if args.audio:
            f = Path(args.audio) / f"{c['beat']}.wav"
        if f is None or not f.exists():
            sys.exit(f"error: no audio for beat {c['beat']!r} "
                     f"({f}) -- run tts.py first")
        c["file"] = f

    total = probe_duration(video)
    over = [c for c in cues if c["t"] + c["duration"] > total + 0.05]
    if over:
        for c in over:
            print(f"  {c['beat']}: ends at {c['t'] + c['duration']:.2f}s, "
                  f"video is {total:.2f}s")
        sys.exit("error: narration runs past the end of the video. The scene "
                 "and the audio are out of step -- re-render after tts.py.")

    out = Path(args.out) if args.out else video.with_name(
        video.stem + "_narrated" + video.suffix)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        track = build_voice_track(cues, td / "voice.wav", total)
        if args.music:
            track = add_music(track, args.music, td / "mixed.wav", total,
                              args.music_db, not args.no_duck)
        final = loudnorm(track, td / "final.wav")

        run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(final),
             "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
             "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)])
        if args.keep_wav:
            shutil.copy(final, out.with_suffix(".wav"))

    spoken = sum(c["duration"] for c in cues)
    print(f"wrote {out}")
    print(f"  {len(cues)} lines, {spoken:.1f}s of speech over {total:.1f}s "
          f"of picture ({100 * spoken / total:.0f}% speech)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
