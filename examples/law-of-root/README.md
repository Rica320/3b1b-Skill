# The Law of Root — a 3D rules explainer

**"No two players in Root are playing by the same rules. So what makes it one
game?"**

A ~9:45 narrated 3D explainer of Root's rules, built with ManimGL against the
`3b1b-math-animation` skill, and built on a working rules model rather than on
poses.

```
woodland.py     the map, the pieces, and the rules that decide who holds what
demo_game.py    the three turns §6 shows, as a sequence of legal actions
board_view.py   that state, rendered: towers, tokens, ground, HUD
root_video.py   the scene
script.yaml     the only place the spoken words exist
verify_root.py  every rule claim the narration makes, re-derived from the model
```

## The idea

Root's asymmetry looks like six unrelated games sharing a table. It isn't. Every
faction's private engine is bolted to the same board through one sentence:

> **2.8 Ruler.** The ruler of a clearing is the player with the most total
> warriors and buildings in that clearing. *(Tokens and pawns do not contribute
> to rule.)* If there is a tie between players in a clearing, no one there is
> the ruler.

Move needs it (4.2.1). Building needs it. Crafting is paid in clearings (4.1.1).
And then the payoff: **every faction in the box is an edit to that one
sentence** — the Eyrie rule on ties (7.2.2), the Cult rules wherever it has a
garden (10.2.4), the Vagabond can never rule at all (9.2.2), the Alliance scores
with tokens that 2.8 explicitly excludes (8.4.2), the Riverfolk swim past it
(11.2.2). Six factions, six answers to the same question.

## The carried metaphor, and why the video is 3D

**Warriors and buildings have height, because those are the two things 2.8
counts. Tokens and pawns lie flat, because 2.8 excludes them.** Rule is a
skyline: tallest tower holds the clearing, level towers mean nobody does.

Nothing about that is hand-drawn. Every tower height in the render is
`len([p for p in state.pieces[c] if COUNTS_FOR_RULE[p.kind]])`, so an impossible
position cannot be shown, and the Alliance's flat green tokens sitting beside a
tower they contribute nothing to is the rule, not an illustration of it.

The camera opens **top-down at phi = 0** — a board on a table, where a clearing
is a scatter you have to count — and after the pieces gather into towers it
tilts to **phi = 60**, at which point rule is something you see. That move is
spent once, at 2:05, with nothing else on stage changing. It tilts back to flat
for the final frame.

## Verification

```bash
../../env/bin/python verify_root.py                       # 31 rule claims
../../env/bin/python .../verify_render.py videos/LawOfRoot.mp4 --meta render_meta.json
../../env/bin/python .../verify_audio.py videos/LawOfRoot_narrated.mp4 --cues narration_cues.json
AUDIT=1 ../../env/bin/manimgl root_video.py LawOfRoot -l --write_file   # text overlaps
```

`verify_root.py` is the one that matters for a rules video. It does not read the
script; it re-derives each claim from `woodland.py` and `demo_game.py`
independently, so a line that drifted away from the rules fails the build. The
whole worked game — setup, three turns, the Outrage, the revolt — is replayed
through the same methods that enforce the rules, and an illegal action raises
rather than being animated.

## Build

```bash
../../env/bin/python ../../skills/3b1b-math-animation/scripts/tts.py script.yaml --out audio
../../env/bin/manimgl root_video.py LawOfRoot --write_file
../../env/bin/python ../../skills/3b1b-math-animation/scripts/mux_audio.py \
    videos/LawOfRoot.mp4 --cues narration_cues.json
```

## Two things to know about the map

**It is structurally faithful, not a copy.** The supplied board photo is
608×504 and shot at an angle; its adjacency and suits cannot be read off it.
`woodland.py` therefore defines twelve clearings, four of each suit, four corner
clearings, four ruins and a river — everything the rules reference guarantees or
implies — laid out for legibility at a tilted camera. Nothing the video says
depends on a specific printed adjacency. To use the real autumn map, replace
`CLEARINGS` and `PATHS`; nothing else changes.

**No faction-board number is asserted.** The rules reference contains no
victory-point awards, building costs or service prices — those are printed on
the faction boards. Where the video needs one it says "the points the space
underneath reveals" and moves the marker, rather than stating a figure it cannot
check. Supply the faction boards and the exact values drop into `demo_game.py`.

## Deliberately out of scope

Dominance cards (3.3), coalitions (9.2.8), forests (2.4), quests and items
(9.5), the Riverfolk's services in detail (11.4), and each faction's full action
list. The video teaches the shared spine — the map, rule, the turn, battle — and
then what each faction does to it. It is an argument, not the rulebook.
