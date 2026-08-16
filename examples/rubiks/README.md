# What does somebody who can solve a Rubik's cube actually know?

A 4:58 narrated 3D explainer, and the skill's worked example for two things:
the **audio pipeline** (`narration.md`) and building a **3D solid** that is a
real object rather than a picture of one.

The cube starts solved, takes twenty turns, and the video asks what a person
who can solve it is actually carrying in their head — since it is plainly not a
route out of each of 43,252,003,274,489,856,000 positions. The obvious answer,
placing pieces one at a time, dies on the second piece: every turn moves nine
cubies, so fixing one thing unfixes another. The one method that always works —
retrace the scramble backwards — is correct and useless, but it shows why it
works: a move and its undo cancel. Keep that, drop the memory, and you get
`R U R'`: everything the first turn disturbed comes back except what changed
while it was away. One corner and one edge. That is a detour, and because a
detour returns, six of them return the whole cube. The method is then nothing
but detours spent in the right order.

## Run it

```bash
cd examples/rubiks

# 1. cut the narration (needs the Kokoro model files: setup_env.sh --tts)
python ../../skills/3b1b-math-animation/scripts/tts.py script.yaml --out audio

# 2. render against the measured durations
bash ../../skills/3b1b-math-animation/scripts/render.sh rubiks.py Rubiks -l   # draft
bash ../../skills/3b1b-math-animation/scripts/render.sh rubiks.py Rubiks      # 1080p

# 3. lay the voice down at the frames the scene asked for
python ../../skills/3b1b-math-animation/scripts/mux_audio.py \
    videos/Rubiks.mp4 --cues narration_cues.json
```

Run from this directory — `custom_config.yml` is read from the working
directory. Measured on an M-series Mac: 12 s to synthesise 31 beats (260 s of
speech), 70 s for the full 1080p render, 8 s to mux.

## Verification

Four gates, and the last two exist because the first two cannot see what is
wrong with a video about a mathematical object.

```bash
python ../../skills/3b1b-math-animation/scripts/verify_render.py \
    videos/Rubiks.mp4 --meta render_meta.json
python ../../skills/3b1b-math-animation/scripts/verify_audio.py \
    videos/Rubiks_narrated.mp4 --cues narration_cues.json
python verify_cube.py          # every number the narration says
python cube_model.py           # 37 checks on the model itself
```

```
    (camera-motion windows declared: 11)
[1] off-frame content ......... pass (0 frames)
[2] blank-frame windows ....... pass (0 windows, 0.0s)
[3] over-long frozen holds .... pass (0)
[4] hard cuts ................. pass (0)
[5] colour reaching screen .... pass (90% of lit pixels saturated)

[1] audio stream present ...... pass (aac, 48000 Hz, +0.00s vs picture)
[2] loudness / true peak ...... pass (-16.5 LUFS, -1.4 dBTP)
[3] line overlap / overrun .... pass (31 lines)
[4] speech present at each cue  pass (31/31 cues land on sound)
[5] narration coverage ........ pass (87% of 298s)
[6] longest wordless stretch .. pass (6.9s max gap)
```

`AUDIT=1` reports zero text overlaps; the detector was validated on a scene
with two captions deliberately in the same band, where it reports exactly one
pair.

## The cube is a real cube

This is the part that is easy to fake and worth not faking.

**The state cannot be illegal.** The usual model is four arrays — corner
permutation, corner orientation, edge permutation, edge orientation — with the
move tables written out by hand, and a transcription slip there produces a cube
that still turns and still looks right but is no longer a cube. So nothing is
transcribed: the state is **26 rotations, one per cubie slot**, and a move is a
rotation applied to the nine cubies in a layer. Every reachable state is
reachable by turning, because turning is the only operation there is. The three
validity laws (permutation parity, corner twist ≡ 0 mod 3, edge flip ≡ 0 mod 2)
hold structurally; `laws()` checks them anyway, over 200 random scrambles and
at all 189 moves in the video.

A pleasant consequence: a slot holds the identity rotation exactly when the
piece in it is its own piece, correctly oriented. Every "is this bit solved"
predicate in the solver is that one test.

**The picture is checked against the state.** `CubeView.check()` reads each
sticker's colour and facing back off the *rendered geometry* — where the cubie
actually sits, where the sticker actually sits relative to it — and compares
against the model. It runs after every stage of the video. A layer selected on
the wrong axis, or a sequence applied to the picture but not to the model,
fails there rather than shipping.

**The solve is a real beginner's solve.** `solver.py` is deliberately not a
good solver: a Kociemba solution is twenty moves no human could reconstruct,
and the video's claim is the opposite one. So the search is breadth-first over
*the method's own algorithms* — the detour, the two middle-layer inserts, and
the four last-layer sequences — with each stage told to keep whatever is
already solved. It solves **300 of 300** random scrambles in 5.3 s. The one
exception is the white cross, where the alphabet is the eighteen face turns,
because the cross is the only part with no algorithm and beginners really do
find it by looking.

The scramble in the video is `cm.scramble(20, seed=30)` and the solution is
99 moves in seven stages. `verify_cube.py` checks every number the voice says
against the code: the state count as 8!·3⁷·12!·2¹¹/2, "about a hundred times
the age of the universe" (99×), "eight pieces move" on a single turn, "one
corner and one edge" left changed by `R U R'`, the order of `R U R' U'` being
exactly six, ninety-nine moves, seven sequences, and the longest at eleven.

## Colour

The cube's six face colours belong to the cube, the way a photograph's colours
do. That breaks the usual rule — `animation_rules.md` §5 wants one meaning per
colour, and here six of them are spoken for before the video starts.

So attention is directed by **dimming**, not by tinting: `Dimmer` pushes
everything else back and the piece under discussion is simply the one still
lit. That is the only way to highlight part of an object whose colours are
already its meaning, and it is what makes the §2 payoff frame work — the whole
cube at 16% with one corner and one edge at full brightness.

Exactly one colour is added, `TEAL_C`, which is not on the cube, and it is used
only to outline the one piece being followed. Captions and the HUD are white
and grey.

## What it was built to demonstrate

- **Audio first.** The script is cut and measured before the scene exists;
  every hold is the length of a real wav; the render records the frame each
  line starts on and the mux lays the file down there. Nothing searches for
  sync.
- **The script is the only copy of the words.** `rubiks.py` contains no prose,
  only beat ids. The voice can be recast — including cloned — without touching
  animation code.
- **Silence is spent deliberately.** The first cut was 92% speech with frozen
  holds of 14.2 s and 12.7 s. Both were fixed the same way: show the claim
  instead of asserting it over a still frame (*"every turn moves nine cubies"*
  became one layer lit, turned, and turned back), and give the video wordless
  beats with a slow spin under them.
- **ANTI-PATTERN #18.** The first build used `Square` for the faces and
  rendered inside out — every near face missing, the far interior showing
  through. A VMobject's fill is drawn by winding number in screen space, so a
  polygon seen from behind cancels. `Square3D` is a `Surface` and has no such
  problem.
- **Seams, and what they hid.** The second build had a grey hairline down the
  middle of every black channel: a cubie's outer face and its neighbour's
  inner face were exactly coincident, same plane, opposite normals, so the
  depth test split each channel between them. The fix is a 0.03 gap between
  cubie bodies, not a larger sticker offset — the stickers were never the pair
  that was fighting, and pushing them further out gives them their own defect,
  coloured rims poking past the silhouette. Then, with the seams quiet,
  `verify_render.py` check [3] immediately found a 12.6 s frozen hold in §4
  that every previous run had passed: the z-fighting had been churning enough
  pixels to keep the frame-delta above the freeze threshold on its own.
- **Two coordinate conventions, meeting in one place.** `cube_model` is y-up,
  because that is how anyone writing cube code thinks; ManimGL's 3D camera is
  z-up. The model keeps its convention and `cube_view.BASIS` rotates it once.
  Building the model's axes straight into the scene put the cube on its side.
