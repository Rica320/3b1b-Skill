"""
Narration timing for a ManimGL scene.

The narration is written once, in `script.yaml`, and synthesised by `tts.py`
*before* the scene renders. The scene then asks this module how long each line
actually takes and paces itself to that, and records the wall-clock time at
which each line starts. `mux_audio.py` reads those cue times back and lays each
wav down at exactly the frame the scene expected it.

That order matters. The obvious pipeline -- render the animation, then fit
narration to it -- cannot work: a spoken line is not compressible, so anything
that runs long either overlaps the next line or has to be cut. Grant records
the audio first and animates against it; this is the same thing, mechanised.

    from narration import Narrator

    nar = Narrator(_HERE / "script.yaml", _HERE / "audio")
    cap = Caption(self, narrator=nar)

    cap.show("The obvious move: slice it.", "s1.slice")   # beat id, not prose
    nar.under(self, "s1.both", ShowCreation(cut_y))       # line over an anim
    nar.wait(self, "s1.disagree")                         # line over a hold
    ...
    nar.dump(_HERE / "narration_cues.json")

Without synthesised audio every duration falls back to a word-count estimate,
so a draft render still paces roughly right; `nar.estimated` is True in that
case and `dump()` refuses to write a cue file, because approximate cue times
would silently desynchronise the mux.
"""

import json
from pathlib import Path

# Words per second of delivered narration. Only used when there is no measured
# audio; the measured value for any real script is in audio/narration.json.
SPEAK_WPS = 2.55

# Silence after a line before the next thing happens. A line that ends exactly
# as the next animation starts reads as an interruption.
DEFAULT_TAIL = 0.35


class Narrator:
    """Beat durations from synthesised audio, and the cue log for the mux.

    `script` is the YAML/JSON narration script. `audio` is the directory
    tts.py wrote, containing narration.json. Either may be omitted: with no
    audio the durations are estimates; with neither, `duration()` raises.
    """

    def __init__(self, script=None, audio=None, tail=DEFAULT_TAIL,
                 strict=True):
        self.tail = tail
        self.strict = strict
        self.texts = {}
        self.durations = {}
        self.files = {}
        self.cues = []
        self.estimated = True
        self.meta = {}

        if script is not None:
            for b in _load(script).get("beats", []):
                self.texts[b["id"]] = " ".join(str(b["text"]).split())

        index = Path(audio) / "narration.json" if audio else None
        if index and index.exists():
            doc = json.loads(index.read_text())
            self.meta = {k: v for k, v in doc.items() if k != "beats"}
            for bid, rec in doc["beats"].items():
                self.durations[bid] = float(rec["duration"])
                self.files[bid] = str(Path(audio) / rec["file"])
                self.texts.setdefault(bid, rec.get("text", ""))
            self.estimated = False
            missing = set(self.texts) - set(self.durations)
            if missing and self.strict:
                raise KeyError(
                    f"script beats with no synthesised audio: "
                    f"{sorted(missing)} -- re-run tts.py")
        elif audio is not None:
            print(f"[narration] no {index}: pacing from word counts. "
                  f"Run tts.py before the final render.")

    # ── durations ────────────────────────────────────────────────────────

    def duration(self, beat):
        if beat in self.durations:
            return self.durations[beat]
        if beat in self.texts:
            words = len([w for w in self.texts[beat].replace("[[", " ")
                         .replace("]]", " ").split()
                         if not _is_number(w)])
            pauses = sum(_pause_values(self.texts[beat]))
            return words / SPEAK_WPS + pauses + 0.3
        raise KeyError(f"unknown narration beat {beat!r}. "
                       f"known: {', '.join(sorted(self.texts)) or '(none)'}")

    def __contains__(self, beat):
        return beat in self.texts or beat in self.durations

    # ── cueing ───────────────────────────────────────────────────────────

    def cue(self, scene, beat, overlap_ok=False):
        """Mark that `beat` starts speaking now. Returns its duration.

        Raises if the previous line has not finished. Two lines sharing the
        same seconds is the audio equivalent of two captions in the same band
        (ANTI-PATTERN #4) and is inaudible rather than merely ugly, so it is a
        build failure, not a warning.
        """
        t = round(float(scene.time), 3)
        dur = self.duration(beat)
        if self.cues and not overlap_ok:
            prev = self.cues[-1]
            end = prev["t"] + prev["duration"]
            if t < end - 1e-3:
                raise AssertionError(
                    f"narration overlap: {beat!r} starts at {t:.2f}s but "
                    f"{prev['beat']!r} runs to {end:.2f}s "
                    f"({end - t:.2f}s of overlap). Give the previous line "
                    f"room, or pass overlap_ok=True if it is deliberate.")
        self.cues.append({"beat": beat, "t": t, "duration": round(dur, 3),
                          "file": self.files.get(beat),
                          "text": self.texts.get(beat, "")})
        return dur

    def finish(self, scene, tail=None):
        """Hold until the line that is currently speaking has finished.

        The workhorse. Cue a line, play whatever the line is describing --
        however many separate `play` calls that takes -- and then call this;
        it works out what is left of the line and waits exactly that long.
        Returns the seconds waited, which is negative if the visuals overran
        the line (worth knowing: it means the next line will start late).
        """
        if not self.cues:
            raise RuntimeError("finish() with no line cued")
        c = self.cues[-1]
        tail = self.tail if tail is None else tail
        left = c["t"] + c["duration"] + tail - float(scene.time)
        if left > 0:
            scene.wait(left)
        return left

    def wait(self, scene, beat, tail=None, spent=0.0, overlap_ok=False):
        """Speak `beat` over a still frame. Returns the time consumed."""
        dur = self.cue(scene, beat, overlap_ok)
        tail = self.tail if tail is None else tail
        left = max(0.0, dur + tail - spent)
        scene.wait(left)
        return left

    def under(self, scene, beat, *anims, tail=None, run_time=None,
              overlap_ok=False, **play_kwargs):
        """Speak `beat` while `anims` play, then hold out the rest of the line.

        The animation is not stretched to the line: an animation has its own
        right speed and slowing it to fill 9 seconds of narration looks like
        the render is broken. It plays at `run_time`, and whatever is left of
        the line is a hold.
        """
        self.cue(scene, beat, overlap_ok)
        t0 = scene.time
        if anims:
            scene.play(*anims, run_time=run_time or 1.0, **play_kwargs)
        self.finish(scene, tail)
        return scene.time - t0

    def silence(self, scene, seconds):
        """A deliberate beat with no words. Distinct from an unfilled gap."""
        scene.wait(seconds)

    # ── output ───────────────────────────────────────────────────────────

    def dump(self, path, scene=None):
        """Write the cue sheet mux_audio.py consumes."""
        if self.estimated:
            raise RuntimeError(
                "refusing to write cues from estimated durations: the mux "
                "would place every line at a time the render does not match. "
                "Run tts.py, then render again.")
        unused = sorted(set(self.texts) - {c["beat"] for c in self.cues})
        doc = {
            "voice": self.meta,
            "video_duration": (round(float(scene.time), 2) if scene else None),
            "cues": self.cues,
            "unused_beats": unused,
        }
        Path(path).write_text(json.dumps(doc, indent=2) + "\n")
        spoken = sum(c["duration"] for c in self.cues)
        print(f"[NARRATION] wrote {path}: {len(self.cues)} cues, "
              f"{spoken:.1f}s of speech"
              + (f", {len(unused)} unused beat(s): {unused}" if unused else ""))
        return doc

    def report(self):
        """Per-cue delivery rate, for the pacing check in checklists.md."""
        for c in self.cues:
            words = len(self.texts.get(c["beat"], "").split())
            rate = words / c["duration"] if c["duration"] else 0
            print(f"  {c['t']:7.2f}s  {c['beat']:<24} "
                  f"{c['duration']:5.2f}s  {rate:4.2f} w/s")


# ──────────────────────────────────────────────────────────────────────────

def _load(path):
    text = Path(path).read_text()
    if str(path).endswith((".yml", ".yaml")):
        import yaml
        return yaml.safe_load(text)
    return json.loads(text)


def _is_number(word):
    try:
        float(word)
        return True
    except ValueError:
        return False


def _pause_values(text):
    import re
    return [float(v) for v in
            re.findall(r"\[\[\s*([0-9]*\.?[0-9]+)\s*\]\]", text)]
