#!/usr/bin/env python3
"""
Synthesise a narration script to per-beat audio files.

    python tts.py script.yaml --out audio/
    python tts.py script.yaml --out audio/ --engine elevenlabs --voice Rachel
    python tts.py script.yaml --out audio/ --engine chatterbox --ref my_voice.wav

The script is the single source of truth for what is spoken. The scene file
refers to beats by id and never contains prose, so the audio can be re-cut
without touching the animation and vice versa.

Script format (YAML or JSON):

    voice:
      engine: kokoro          # kokoro | elevenlabs | chatterbox | openai | say
      name: am_michael        # engine-specific voice id
      speed: 1.0
      reference: voice.wav    # cloning reference, cloning engines only
    beats:
      - id: s0.question
        text: >
          Forty-three quintillion arrangements. [[0.45]] So how does one
          person memorise a way out of all of them?
      - id: s1.fail
        text: ...
        speed: 0.95           # per-beat override

`[[0.45]]` is an explicit 0.45-second pause. It is honoured identically by
every engine because the pause is *cut in by this script*, not asked of the
model: each chunk is synthesised separately, silence-trimmed, and rejoined with
exactly that much digital silence between. Engine-native break tags drift or
are ignored, and the duration the scene waits for has to be the duration the
file actually is.

Output:
    <out>/<beat_id>.wav        one file per beat, 24 kHz mono
    <out>/narration.json       measured duration of each, plus the text hash

Re-running is cheap: a beat whose text, engine, voice and speed are unchanged
is not re-synthesised.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

SAMPLE_RATE = 24000
PAUSE_RE = re.compile(r"\[\[\s*([0-9]*\.?[0-9]+)\s*\]\]")

# Silence trimmed from each chunk before the authored pause is inserted.
TRIM_DB = -45.0           # anything quieter than this counts as silence
TRIM_KEEP = 0.03          # seconds of room tone kept either side
PEAK_TARGET = 0.89        # per-beat peak normalisation


# ──────────────────────────────────────────────────────────────────────────
# Audio primitives (numpy float32 mono at SAMPLE_RATE throughout)
# ──────────────────────────────────────────────────────────────────────────

def _np():
    import numpy as np
    return np


def trim_silence(samples, sr):
    """Strip leading/trailing silence so authored pauses are the only pauses.

    Every engine pads its output, and the padding is not constant: measured on
    Kokoro, the same sentence came back with between 30 ms and 210 ms of lead-in
    depending on the first phoneme. Left in, that padding lands inside the gap
    the scene reserved for the line and the sync drifts a little further with
    every beat.
    """
    np = _np()
    if len(samples) == 0:
        return samples
    thresh = 10.0 ** (TRIM_DB / 20.0)
    win = max(1, int(0.01 * sr))
    n = len(samples) // win
    if n == 0:
        return samples
    env = np.abs(samples[:n * win]).reshape(n, win).max(axis=1)
    loud = np.nonzero(env > thresh)[0]
    if len(loud) == 0:
        return samples[:0]
    keep = int(TRIM_KEEP * sr)
    a = max(0, loud[0] * win - keep)
    b = min(len(samples), (loud[-1] + 1) * win + keep)
    return samples[a:b]


def silence(seconds, sr):
    np = _np()
    return np.zeros(int(round(seconds * sr)), dtype=np.float32)


def write_wav(path, samples, sr):
    np = _np()
    s = np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0)
    peak = float(np.abs(s).max()) if len(s) else 0.0
    if peak > 1e-6:
        s = s * (PEAK_TARGET / peak)
    pcm = (s * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as fh:
        fh.setnchannels(1)
        fh.setsampwidth(2)
        fh.setframerate(sr)
        fh.writeframes(pcm.tobytes())
    return len(pcm) / float(sr)


def resample(samples, src_sr, dst_sr):
    np = _np()
    if src_sr == dst_sr or len(samples) == 0:
        return samples
    n = int(round(len(samples) * dst_sr / src_sr))
    return np.interp(np.linspace(0, len(samples) - 1, n),
                     np.arange(len(samples)), samples).astype(np.float32)


def decode_to_mono(path, sr=SAMPLE_RATE):
    """Any audio file -> float32 mono at `sr`, via ffmpeg."""
    np = _np()
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr),
         "-f", "f32le", "-"], capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg could not decode {path}: "
                           f"{p.stderr.decode(errors='replace')[:300]}")
    return np.frombuffer(p.stdout, dtype="<f4").copy()


# ──────────────────────────────────────────────────────────────────────────
# Engines
#
# Each returns (samples, sample_rate) for one chunk of plain text. Add one by
# writing a synth function and registering it in ENGINES; nothing else in the
# pipeline needs to know about it.
# ──────────────────────────────────────────────────────────────────────────

class Engine:
    """Base class. Subclasses implement `say(text, speed) -> (samples, sr)`."""

    #: True if this engine takes a reference clip and clones the voice in it.
    clones = False

    def __init__(self, voice=None, reference=None, **kw):
        self.voice = voice
        self.reference = reference

    def say(self, text, speed):
        raise NotImplementedError


class KokoroEngine(Engine):
    """Kokoro-82M via onnxruntime. Apache-2.0, local, ~5x realtime on CPU.

    Model files (325 MB + 28 MB) are not bundled; setup_env.sh fetches them to
    ~/.cache/kokoro. Set KOKORO_MODEL / KOKORO_VOICES to override.

    Voices: af_* / am_* US female/male, bf_* / bm_* British. am_michael and
    bm_george are the two that read as an explainer narrator rather than an
    audiobook; af_heart is the warmest of the female voices.
    """

    DEFAULT_VOICE = "am_michael"

    def __init__(self, voice=None, reference=None, lang="en-us", **kw):
        super().__init__(voice or self.DEFAULT_VOICE, reference)
        self.lang = lang
        try:
            from kokoro_onnx import Kokoro
        except ImportError:
            sys.exit("error: kokoro-onnx is not installed.\n"
                     "       pip install kokoro-onnx soundfile, then run "
                     "scripts/setup_env.sh --tts to fetch the model files.")
        home = Path(os.path.expanduser("~/.cache/kokoro"))
        model = Path(os.environ.get("KOKORO_MODEL",
                                    home / "kokoro-v1.0.onnx"))
        voices = Path(os.environ.get("KOKORO_VOICES",
                                     home / "voices-v1.0.bin"))
        if not model.exists() or not voices.exists():
            sys.exit(f"error: Kokoro model files not found at {home}.\n"
                     f"       run scripts/setup_env.sh --tts")
        self.k = Kokoro(str(model), str(voices))
        if self.voice not in self.k.get_voices():
            sys.exit(f"error: unknown Kokoro voice {self.voice!r}. "
                     f"available: {', '.join(sorted(self.k.get_voices()))}")

    def say(self, text, speed):
        samples, sr = self.k.create(text, voice=self.voice, speed=speed,
                                    lang=self.lang)
        return samples, sr


class ElevenLabsEngine(Engine):
    """ElevenLabs. Best quality available, and the cloning is instant.

    Needs ELEVENLABS_API_KEY. `voice` is a voice id or a name from your
    library; `reference` uploads a clip and clones it (30-90 s of clean speech
    is plenty) the first time, then reuses that voice id.
    """

    clones = True
    DEFAULT_VOICE = "Rachel"
    MODEL = "eleven_multilingual_v2"

    def __init__(self, voice=None, reference=None, **kw):
        super().__init__(voice or self.DEFAULT_VOICE, reference)
        try:
            from elevenlabs.client import ElevenLabs
        except ImportError:
            sys.exit("error: pip install elevenlabs")
        key = os.environ.get("ELEVENLABS_API_KEY")
        if not key:
            sys.exit("error: ELEVENLABS_API_KEY is not set")
        self.client = ElevenLabs(api_key=key)
        self.voice_id = self._resolve()

    def _resolve(self):
        if self.reference:
            ref = Path(self.reference)
            if not ref.exists():
                sys.exit(f"error: reference clip not found: {ref}")
            name = f"cloned-{ref.stem}"
            for v in self.client.voices.get_all().voices:
                if v.name == name:
                    return v.voice_id
            with open(ref, "rb") as fh:
                v = self.client.voices.ivc.create(name=name, files=[fh])
            print(f"[tts] cloned {ref.name} -> voice {v.voice_id}")
            return v.voice_id
        for v in self.client.voices.get_all().voices:
            if self.voice in (v.name, v.voice_id):
                return v.voice_id
        return self.voice        # assume it is already an id

    def say(self, text, speed):
        from elevenlabs import VoiceSettings
        audio = self.client.text_to_speech.convert(
            voice_id=self.voice_id, model_id=self.MODEL, text=text,
            output_format="mp3_44100_128",
            voice_settings=VoiceSettings(stability=0.45,
                                         similarity_boost=0.8,
                                         speed=speed),
        )
        tmp = Path(os.environ.get("TMPDIR", "/tmp")) / "_11l_chunk.mp3"
        tmp.write_bytes(b"".join(audio))
        return decode_to_mono(tmp), SAMPLE_RATE


class ChatterboxEngine(Engine):
    """Chatterbox (Resemble AI). MIT, local, zero-shot cloning.

    `reference` is a 7-20 s clean clip of the voice to clone; without one it
    uses the built-in voice. Pulls in torch, and on CPU runs slower than
    realtime -- fine for a 4-minute script, painful for a long one. Set
    CHATTERBOX_DEVICE=mps on Apple silicon.
    """

    clones = True

    def __init__(self, voice=None, reference=None, **kw):
        super().__init__(voice, reference)
        try:
            from chatterbox.tts import ChatterboxTTS
        except ImportError:
            sys.exit("error: pip install chatterbox-tts")
        device = os.environ.get("CHATTERBOX_DEVICE", "cpu")
        self.m = ChatterboxTTS.from_pretrained(device=device)

    def say(self, text, speed):
        kw = {"audio_prompt_path": self.reference} if self.reference else {}
        wav = self.m.generate(text, **kw)
        samples = wav.squeeze(0).cpu().numpy()
        out = resample(samples, self.m.sr, SAMPLE_RATE)
        if abs(speed - 1.0) > 1e-3:
            out = _time_scale(out, speed)
        return out, SAMPLE_RATE


class OpenAIEngine(Engine):
    """OpenAI gpt-4o-mini-tts. Needs OPENAI_API_KEY. No cloning."""

    DEFAULT_VOICE = "onyx"
    MODEL = "gpt-4o-mini-tts"

    def __init__(self, voice=None, reference=None, instructions=None, **kw):
        super().__init__(voice or self.DEFAULT_VOICE, reference)
        try:
            from openai import OpenAI
        except ImportError:
            sys.exit("error: pip install openai")
        self.client = OpenAI()
        self.instructions = instructions or (
            "Calm, warm, unhurried explainer narration. Land the full stops.")

    def say(self, text, speed):
        tmp = Path(os.environ.get("TMPDIR", "/tmp")) / "_oai_chunk.mp3"
        with self.client.audio.speech.with_streaming_response.create(
                model=self.MODEL, voice=self.voice, input=text,
                instructions=self.instructions, speed=speed) as r:
            r.stream_to_file(tmp)
        return decode_to_mono(tmp), SAMPLE_RATE


class SayEngine(Engine):
    """macOS `say`. Always available, clearly synthetic.

    A structural placeholder: it lets the whole pipeline -- timings, cues, mux,
    verification -- be exercised before any model is downloaded or any key is
    set. Do not ship a video with it.
    """

    DEFAULT_VOICE = "Samantha"

    def __init__(self, voice=None, reference=None, **kw):
        super().__init__(voice or self.DEFAULT_VOICE, reference)
        if not shutil.which("say"):
            sys.exit("error: `say` is macOS-only")

    def say(self, text, speed):
        tmp = Path(os.environ.get("TMPDIR", "/tmp")) / "_say_chunk.aiff"
        subprocess.run(["say", "-v", self.voice, "-r", str(int(180 * speed)),
                        "-o", str(tmp), text], check=True)
        return decode_to_mono(tmp), SAMPLE_RATE


def _time_scale(samples, speed):
    """Change duration without changing pitch, via ffmpeg atempo."""
    np = _np()
    tmp_in = Path(os.environ.get("TMPDIR", "/tmp")) / "_scale_in.wav"
    write_wav(tmp_in, samples, SAMPLE_RATE)
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(tmp_in), "-filter:a",
         f"atempo={speed:.4f}", "-ac", "1", "-ar", str(SAMPLE_RATE),
         "-f", "f32le", "-"], capture_output=True)
    if p.returncode != 0:
        return samples
    return np.frombuffer(p.stdout, dtype="<f4").copy()


ENGINES = {
    "kokoro": KokoroEngine,
    "elevenlabs": ElevenLabsEngine,
    "chatterbox": ChatterboxEngine,
    "openai": OpenAIEngine,
    "say": SayEngine,
}


# ──────────────────────────────────────────────────────────────────────────
# Script -> audio
# ──────────────────────────────────────────────────────────────────────────

def load_script(path):
    text = Path(path).read_text()
    if str(path).endswith((".yml", ".yaml")):
        import yaml
        doc = yaml.safe_load(text)
    else:
        doc = json.loads(text)
    if not isinstance(doc, dict) or "beats" not in doc:
        sys.exit(f"error: {path} has no `beats` list")
    ids = [b["id"] for b in doc["beats"]]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        sys.exit(f"error: duplicate beat ids in {path}: {sorted(dupes)}")
    return doc


def spoken_words(text):
    return len(PAUSE_RE.sub(" ", text).split())


def synth_beat(engine, text, speed):
    """One beat -> samples. Chunks split on [[pause]] markers, joined exactly."""
    np = _np()
    parts, pauses = PAUSE_RE.split(text)[::2], PAUSE_RE.findall(text)
    out = []
    for i, part in enumerate(parts):
        part = " ".join(part.split())
        if part:
            samples, sr = engine.say(part, speed)
            samples = resample(np.asarray(samples, dtype=np.float32),
                               sr, SAMPLE_RATE)
            out.append(trim_silence(samples, SAMPLE_RATE))
        if i < len(pauses):
            out.append(silence(float(pauses[i]), SAMPLE_RATE))
    if not out:
        return silence(0.2, SAMPLE_RATE)
    return np.concatenate(out)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Synthesise a narration script to per-beat audio.")
    ap.add_argument("script", help="script.yaml / script.json")
    ap.add_argument("--out", default="audio", help="output directory")
    ap.add_argument("--engine", help="override the script's engine")
    ap.add_argument("--voice", help="override the script's voice")
    ap.add_argument("--speed", type=float, help="override the script's speed")
    ap.add_argument("--ref", help="reference clip for a cloning engine")
    ap.add_argument("--only", help="re-synthesise just this beat id")
    ap.add_argument("--force", action="store_true",
                    help="re-synthesise even if the text is unchanged")
    args = ap.parse_args(argv)

    if shutil.which("ffmpeg") is None:
        sys.exit("error: ffmpeg not found on PATH")

    doc = load_script(args.script)
    vcfg = dict(doc.get("voice") or {})
    engine_name = args.engine or vcfg.pop("engine", "kokoro")
    voice = args.voice or vcfg.pop("name", None)
    speed = args.speed if args.speed is not None else vcfg.pop("speed", 1.0)
    reference = args.ref or vcfg.pop("reference", None)
    if engine_name not in ENGINES:
        sys.exit(f"error: unknown engine {engine_name!r}. "
                 f"choose from {', '.join(ENGINES)}")
    if reference and not ENGINES[engine_name].clones:
        print(f"[tts] warning: {engine_name} cannot clone; ignoring reference")
        reference = None

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "narration.json"
    old = {}
    if index_path.exists() and not args.force:
        try:
            old = json.loads(index_path.read_text()).get("beats", {})
        except json.JSONDecodeError:
            old = {}

    engine = None
    beats, total, made = {}, 0.0, 0
    for b in doc["beats"]:
        bid, text = b["id"], " ".join(str(b["text"]).split())
        bspeed = float(b.get("speed", speed))
        stamp = hashlib.sha1(
            f"{text}|{engine_name}|{voice}|{bspeed}|{reference}"
            .encode()).hexdigest()[:16]
        wav = out_dir / f"{bid}.wav"

        reuse = (old.get(bid, {}).get("hash") == stamp and wav.exists()
                 and (args.only is None or args.only != bid))
        if reuse:
            dur = old[bid]["duration"]
        else:
            if engine is None:
                engine = ENGINES[engine_name](voice=voice, reference=reference)
                voice = voice or getattr(engine, "voice", None)
            dur = write_wav(wav, synth_beat(engine, text, bspeed), SAMPLE_RATE)
            made += 1
        words = spoken_words(text)
        beats[bid] = {
            "file": wav.name, "duration": round(dur, 3), "words": words,
            "wps": round(words / dur, 2) if dur > 0 else 0.0,
            "hash": stamp, "text": text,
        }
        total += dur
        flag = " " if reuse else "*"
        print(f"  {flag} {bid:<24} {dur:6.2f}s  {words:3d}w  "
              f"{beats[bid]['wps']:.2f} w/s")

    index_path.write_text(json.dumps({
        "engine": engine_name, "voice": voice, "speed": speed,
        "reference": reference, "sample_rate": SAMPLE_RATE,
        "total_duration": round(total, 2), "beats": beats,
    }, indent=2) + "\n")

    spoken = sum(b["words"] for b in beats.values())
    print(f"\n{len(beats)} beats, {made} synthesised, "
          f"{total:.1f}s of speech, {spoken} words "
          f"({spoken / total:.2f} w/s overall)")
    print(f"wrote {index_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
