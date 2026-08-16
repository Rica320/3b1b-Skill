# Narration and Audio

Everything here was verified by synthesising a real 31-beat script, rendering
against it, muxing, and measuring the result. Where a number appears, it was
measured. The worked example is `examples/rubiks/`; the anti-patterns are
#19–#22 in `anti_patterns.md`.

---

## 1. The order is not negotiable: audio first, animation second

The obvious pipeline is to animate, then narrate over the finished video. It
cannot work, and the reason is worth stating precisely: **a spoken line has one
correct duration and no slack.** Speed it up and it sounds gabbled; stretch it
and it sounds drugged. An animation, by contrast, is trivially stretchable — a
hold is any length you like.

So the fixed thing has to come first. Grant records his audio and animates
against it; this pipeline does the same, mechanically:

```
script.yaml ──tts.py──▶ audio/*.wav + narration.json   (measured durations)
                                 │
                                 ▼
                          Narrator, in the scene
                    every hold is the length of a real wav
                                 │
                    render ──▶ narration_cues.json      (measured start times)
                                 │
                                 ▼
        mux_audio.py: lay each wav at the frame the scene asked for
```

Nothing in the mux searches for sync or nudges anything. The scene already
waited for the exact length of every file, so placing each one at its recorded
cue time is the whole job. **If the output is out of sync, the scene and the
audio came from different versions of the script** — the fix is upstream, never
in the mux.

---

## 2. The script is the only place the words exist

`script.yaml` holds every spoken line. The scene refers to beats by id and
contains no prose:

```yaml
voice:
  engine: kokoro
  name: am_michael
  speed: 0.92
beats:
  - id: s2.damage
    text: >
      Out of everything on this cube, one corner and one edge have changed,
      [[0.4]] and the rest is untouched.
```

```python
nar = Narrator(_HERE / "script.yaml", _HERE / "audio")
cap = Caption(self, narrator=nar)

cap.show("Out, do something, back.", "s2.name")     # a beat id, not prose
```

Two copies of a sentence is one copy too many: the version that gets edited is
never the version that gets spoken. Keeping them in one file also means the
voice can be recast — a different engine, a different speed, a cloned voice —
without touching a line of animation code, and the narration can be
proof-read as prose, which is the only way to hear that it is an argument.

`Narrator.dump()` reports any beat in the script that no cue used. A beat you
wrote and forgot to place is silent in the render and invisible in review.

---

## 3. The four ways a line meets the picture

| | Use when |
|---|---|
| `cap.show(text, "beat.id")` | the caption *is* the beat: write it, hold for the line, move on |
| `cap.show(text, "beat.id", hold=False)` … `nar.finish(self)` | the line runs over animations that follow the caption |
| `nar.under(self, "beat.id", *anims, run_time=…)` | one animation under one line |
| `nar.wait(self, "beat.id")` | a line over a still frame |

`nar.finish()` is the workhorse: cue a line, play whatever the line is about
across as many `play` calls as it takes, then call `finish()` and it holds out
exactly what remains. It returns a negative number if the visuals overran the
line, which is worth printing while pacing.

**Cue before the caption is written, not after.** `Caption.show` does this: the
voice starts as the words appear, so the line's clock starts at the first frame
of the `Write`, not the last. Cueing after would put every line about 1.3 s
late and the error compounds down the video.

**Do not stretch an animation to fill a line.** An animation has a right speed;
slowing a turn to nine seconds looks like the render is broken. Play it at its
own pace and let the remainder be a hold — or better, find something the line
deserves to have shown under it (§5).

---

## 4. Pauses belong to the tool, not the model

`[[0.4]]` in the script is a 0.4-second pause. `tts.py` implements it by
synthesising each side separately, trimming the silence off both, and joining
them with exactly that much digital silence.

It is done this way rather than with an engine's own break tag because the
duration the scene waits for has to be the duration the file actually is.
Engine-native breaks drift or are ignored; worse, engines pad their output
unpredictably — measured on Kokoro, the same sentence came back with between
30 ms and 210 ms of lead-in depending on the first phoneme. Left in, that
padding lands inside the gap the scene reserved and the sync walks.

Pauses are also the main tool for making synthetic narration sound like
thinking rather than reading. One before the answer to a question, one after a
number worth absorbing. Roughly one every two or three sentences; more than
that and it sounds hesitant.

---

## 5. Silence is a thing you spend

Two measurements from the Rubik's build, both from `verify_audio.py` and
`verify_render.py` on the same first cut:

- **92% of the runtime was speech.** There was nowhere to look. The check
  fails above 88% for that reason: a viewer needs beats where the picture is
  the only thing happening.
- **Two frozen holds of 14.2 s and 12.7 s.** Both were long narration lines
  playing over a still frame, which is the same defect from the other side:
  the words were doing all the work.

The fixes are the same fix. Where a long line sits over a still cube, *show the
claim* — "every turn moves nine cubies at once" became one layer lit, turned,
and turned back. Where the video needs air, give it a wordless beat with slow
motion under it: a `spin()` at 5°/s, three or four seconds, nothing said. Both
raise the picture's share of the work, which is the actual goal; passing the
checks is a side effect.

Target roughly **75–85% speech coverage**, and put the silence where the viewer
needs to think: after the driving question, after the payoff frame, and on the
one image the whole section was building to.

---

## 6. Engines, and voice cloning

`tts.py` takes `--engine`; add one by writing a `say()` method and registering
it. What is there now:

| Engine | Local | Clones | Notes |
|---|---|---|---|
| `kokoro` | yes | no | Apache-2.0, 82M params. ~5× realtime on CPU, no key, and genuinely good. The default. `am_michael` and `bm_george` read as an explainer narrator; `af_heart` is the warmest female voice. |
| `elevenlabs` | no | **yes** | Best quality available and the cloning is instant — 30–90 s of clean speech. Needs `ELEVENLABS_API_KEY`; paid per character. |
| `chatterbox` | yes | **yes** | MIT, zero-shot cloning from a 7–20 s clip. Pulls in torch; slower than realtime on CPU. `CHATTERBOX_DEVICE=mps` on Apple silicon. |
| `openai` | no | no | `gpt-4o-mini-tts`, takes a style instruction. |
| `say` | yes | no | macOS built-in. A structural placeholder — it lets the whole pipeline be exercised before anything is downloaded. Do not ship with it. |

**To clone a voice**, drop a reference clip next to the script and name it:

```yaml
voice:
  engine: chatterbox        # or elevenlabs
  reference: voice_sample.wav
```

or pass `--ref voice_sample.wav`. What makes a good sample: 30–90 seconds
(ElevenLabs) or 7–20 seconds (Chatterbox) of **one** speaker, no music, no
room echo, no clipping, and — the part people skip — *read in the register you
want back*. A clip of someone laughing on a podcast clones a voice that laughs.
Read a paragraph of explainer narration at explainer pace.

Passing a reference to an engine that cannot clone is a warning, not an error;
the run continues with the stock voice.

**Re-synthesis is cached** on a hash of text, engine, voice and speed, so
editing one line re-cuts one file. `--only <beat>` and `--force` are there for
the rest.

**Pick the speed once, early.** Kokoro at 1.0 delivers about 3.0 words/second,
which is faster than the 2.6 this style wants; 0.92 lands at 2.82. Changing it
later re-cuts every file and re-times the whole render.

---

## 7. The mix

`mux_audio.py` builds the track, then normalises it to **−16 LUFS integrated,
−1.5 dBTP** in two passes. Two passes matters: a single-pass normaliser rides
the gain and pumps audibly on speech with long gaps in it, which is exactly
what a narration track is.

A music bed is `--music bed.mp3 --music-db -24`, side-chain ducked under the
voice by default. Keep it quiet enough that you stop noticing it — if you can
follow the tune, it is competing with the words.

---

## 8. Verifying

```bash
python scripts/verify_audio.py videos/Video_narrated.mp4 --cues narration_cues.json
```

| # | Check | Fails when |
|---|---|---|
| 1 | audio stream present | no stream, or length differs from the picture by >0.5 s |
| 2 | loudness / true peak | outside −18…−14 LUFS, or above −1.0 dBTP |
| 3 | line overlap / overrun | two lines share seconds, or one runs past the end |
| 4 | **speech present at each cue** | the mix is silent where a line was cued |
| 5 | narration coverage | below 40% (dead air) or above 88% (no room to look) |
| 6 | longest wordless stretch | more than 14 s with nothing said |

**Check [4] is the one that matters.** Everything upstream can agree with
itself and still be wrong: a scene re-rendered after the script changed
produces a perfectly consistent cue sheet pointing at the wrong seconds. Check
[4] runs ffmpeg's silence detector over the finished audio and confirms sound
is actually there at every cue time, which no amount of internal consistency
can fake.

The pacing report at the end is advisory: above 3.3 w/s a line is rushed, below
2.0 it drags. Fix a rushed line by cutting words, not by slowing the voice —
the voice speed is global and re-times everything.

---

## 9. Minimal skeleton

```python
from narration import Narrator
from manim_helpers import Caption, dump_meta, spin

class MyVideo(ThreeDScene):
    def construct(self):
        nar = Narrator(_HERE / "script.yaml", _HERE / "audio")
        cap = Caption(self, narrator=nar)

        cap.show("The obvious move: slice it.", "s1.slice")

        cap.show("Both slices are correct.", "s1.both", hold=False)
        self.play(ShowCreation(cut_y), run_time=1.4)
        self.play(Write(claim))
        nar.finish(self)

        spin(self, 3.5, speed=-5.0)          # a wordless beat, on purpose

        dump_meta(self, _HERE / "render_meta.json")
        nar.dump(_HERE / "narration_cues.json", scene=self)
        nar.report()
```

Then:

```bash
python scripts/tts.py script.yaml --out audio
bash   scripts/render.sh scenes.py MyVideo
python scripts/mux_audio.py videos/MyVideo.mp4 --cues narration_cues.json
python scripts/verify_audio.py videos/MyVideo_narrated.mp4 --cues narration_cues.json
```

Without synthesised audio every duration falls back to a word-count estimate,
so a draft render still paces roughly right — and `dump()` refuses to write a
cue file in that state, because approximate cue times would desynchronise the
mux silently.
