"""
The three turns §6 shows, as a sequence of legal actions.

Nothing here is a pose. Every step mutates a woodland.State through the same
methods that enforce the rules, so a step that the rules forbid raises here
rather than being animated. `steps()` returns (tag, note, state) triples; the
scene walks them and the verifier re-runs them.

The arc, and why it is this arc: it is the video's thesis running at speed.
  - the Marquise scores by adding height and needs the ground to do it;
  - the Eyrie take that ground off her with dice;
  - the Alliance scores in the same clearing without owning one inch of it,
    is attacked for it, is paid for being attacked, and then takes the whole
    clearing with a revolt.
"""

from __future__ import annotations

import woodland as w
from woodland import (MARQUISE, EYRIE, ALLIANCE, FOX, RABBIT, MOUSE,
                      IllegalAction)

KEEP, EYRIE_CORNER, FIELD = 1, 12, 9      # the contested clearing is 9 (rabbit)


def _setup() -> w.State:
    """6.9 / 7.4 / 8.8, with the free choices in those steps made explicitly."""
    s = w.State()
    s.vp = {MARQUISE: 0, EYRIE: 0, ALLIANCE: 0}

    # 6.9.2 keep in a corner clearing of her choice
    s.place_token(MARQUISE, KEEP, "keep")
    # 6.9.3 a warrior in each clearing except the diagonally opposite corner
    for c in s.map.clearings:
        if c != EYRIE_CORNER:
            s.place_warrior(MARQUISE, c)
    # 6.9.4 sawmill, workshop, recruiter among the keep clearing and any
    #       adjacent clearings (1 is adjacent to 2, 4, 5)
    s.place_building(MARQUISE, 2, "sawmill")
    s.place_building(MARQUISE, KEEP, "workshop")
    s.place_building(MARQUISE, KEEP, "recruiter")

    # 7.4.2 roost + 6 warriors in the corner diagonally opposite the keep
    s.place_building(EYRIE, EYRIE_CORNER, "roost")
    s.place_warrior(EYRIE, EYRIE_CORNER, 6)
    # 7.4.3 leader: Despot - Loyal Viziers begin on Move and Build
    s.leader = "Despot"
    s.decree = {"recruit": [], "move": ["bird"], "battle": [], "build": ["bird"]}

    # 8.8.4 draw 3 supporters.  8.8.1: no Alliance piece starts on the map.
    s.supporters = [RABBIT, RABBIT, MOUSE]
    s.hands = {MARQUISE: [FOX, RABBIT, BIRDLESS] if False else [FOX, RABBIT],
               EYRIE: [RABBIT], ALLIANCE: [RABBIT, MOUSE]}
    return s


BIRDLESS = None   # placeholder never used; hands are only suits we spend


def steps():
    """Every state the video shows, in order."""
    s = _setup()
    out = [("setup", "6.9 / 7.4 / 8.8", s.clone())]

    # ── Turn 1: Marquise ────────────────────────────────────────────────
    # 6.4 Birdsong: place one wood token at each sawmill.
    s.wood[2] += 1
    out.append(("t1.birdsong", "6.4: a wood token at each sawmill", s.clone()))

    # 6.5.4 Build.  Chosen clearing 9: she rules it (one warrior, nobody
    # else). The wood sits in 2; 6.5.4.II lets her pay from "any clearings
    # connected to the chosen clearing you rule through any number of
    # clearings you rule" - 9-6-2, and she rules 6 and 2.
    assert s.rules(MARQUISE, FIELD), "6.5.4.II: must rule the chosen clearing"
    assert s.rules(MARQUISE, 6) and s.rules(MARQUISE, 2)
    assert s.map.adjacent(9, 6) and s.map.adjacent(6, 2)
    assert s.open_slots(FIELD) >= 1
    s.wood[2] -= 1
    s.place_building(MARQUISE, FIELD, "sawmill")
    s.score(MARQUISE, 1, "(6.5.4.III: the space revealed on her board)")
    out.append(("t1.build", "6.5.4: build a sawmill in 9, paid from 2",
                s.clone()))

    # 6.5.2 March: take two moves.
    s.move(MARQUISE, KEEP, 5, 1)
    s.move(MARQUISE, 5, FIELD, 2)
    out.append(("t1.march", "6.5.2: two moves, 1->5 then 5->9", s.clone()))

    # 6.5.3 Recruit: place one warrior at each recruiter (the recruiter is in 1)
    s.place_warrior(MARQUISE, KEEP, 1)
    out.append(("t1.recruit", "6.5.3: a warrior at each recruiter", s.clone()))

    # ── Turn 2: Eyrie ───────────────────────────────────────────────────
    # 7.4.2 Birdsong: add one or two cards to the Decree. One rabbit, to Battle.
    s.decree["battle"].append(RABBIT)
    out.append(("t2.decree", "7.4.2: a rabbit card added to Battle", s.clone()))

    # 7.5.2 resolve left to right: Recruit, Move, Battle, Build.
    # Move (bird vizier - 2.1.1 birds are wild, so any clearing)
    s.move(EYRIE, EYRIE_CORNER, FIELD, 5)
    out.append(("t2.move", "7.5.2: Move - five birds from 12 to 9", s.clone()))

    # Battle (the rabbit card; 9 is a rabbit clearing)
    assert s.map[FIELD].suit == RABBIT
    rep = s.battle(EYRIE, MARQUISE, FIELD, rolls=(2, 1))
    out.append(("t2.battle", "4.3: rolled 2 and 1", s.clone(), rep))

    # Build (bird vizier): a roost in a clearing they rule with no roost
    assert s.rules(EYRIE, FIELD), "7.5.2: must rule the clearing to build"
    assert not any(p.faction == EYRIE and p.name == "roost"
                   for p in s.pieces[FIELD])
    assert s.open_slots(FIELD) >= 1
    s.place_building(EYRIE, FIELD, "roost")
    out.append(("t2.build", "7.5.2: Build - a roost in 9", s.clone()))

    # 7.6.1 Evening: score for roosts on the map (value is on the faction board)
    s.score(EYRIE, 1, "(7.6.1: the rightmost empty space of the Roosts track)")
    out.append(("t2.evening", "7.6.1: score for roosts", s.clone()))

    # ── Turn 3: Alliance ────────────────────────────────────────────────
    # 8.4.2 Spread Sympathy into 9. No sympathetic clearing yet, so any
    # clearing may be chosen (8.4.2.I). 8.4.2.II.a Martial Law: one extra
    # matching supporter, because another player has at least three warriors.
    assert s.warriors(FIELD, EYRIE) >= 3, "8.4.2.II.a Martial Law"
    assert s.supporters.count(RABBIT) >= 2
    s.supporters.remove(RABBIT)
    s.supporters.remove(RABBIT)                 # base cost + Martial Law
    s.place_token(ALLIANCE, FIELD, "sympathy")
    s.score(ALLIANCE, 1, "(8.4.2.III: the space revealed on her board)")
    out.append(("t3.sympathy", "8.4.2: sympathy in 9, +1 for Martial Law",
                s.clone()))

    # 8.5.2 Daylight, Mobilize: add a card from hand to the Supporters stack.
    s.hands[ALLIANCE].remove(RABBIT)
    s.supporters.append(RABBIT)
    out.append(("t3.mobilize", "8.5.2: Mobilize a rabbit", s.clone()))

    # ── Turn 4: the Marquise's obvious reply ────────────────────────────
    # 6.5.2 March is two moves: she gathers in 6, then enters the clearing.
    s.move(MARQUISE, 2, 6, 1)
    outraged = s.move(MARQUISE, 6, FIELD, 2)
    assert outraged, "8.2.6 Outrage must trigger"
    s.hands[MARQUISE].remove(RABBIT)
    s.supporters.append(RABBIT)                 # 8.2.6: a matching card
    out.append(("t4.outrage", "8.2.6: Outrage - she hands over a rabbit",
                s.clone()))

    # ── Turn 5: Alliance Birdsong, Revolt ───────────────────────────────
    # 8.4.1: a sympathetic clearing matching an unbuilt base; spend two
    # supporters of that suit; remove all enemy pieces; place the base and
    # warriors equal to the number of sympathetic clearings of that suit;
    # then one warrior in the Officers box.
    assert s.supporters.count(RABBIT) >= 2
    s.supporters.remove(RABBIT)
    s.supporters.remove(RABBIT)
    gone, pts = s.remove_all_enemies(ALLIANCE, FIELD)
    sympathetic_rabbit = sum(
        1 for c in s.map if c.suit == RABBIT
        and any(p.faction == ALLIANCE and p.name == "sympathy"
                for p in s.pieces[c.id]))
    s.place_building(ALLIANCE, FIELD, "base")
    s.place_warrior(ALLIANCE, FIELD, sympathetic_rabbit)
    s.officers = 1
    out.append(("t5.revolt", "8.4.1: revolt in 9", s.clone(),
                {"removed": gone, "vp": pts, "warriors": sympathetic_rabbit}))
    return out


if __name__ == "__main__":
    for st in steps():
        tag, note, s = st[0], st[1], st[2]
        print(f"{tag:14s} {note}")
        print(f"{'':14s} clearing 9: ruler={s.ruler(FIELD)} "
              f"presences={s.presences(FIELD)} vp={s.vp} "
              f"supporters={sorted(s.supporters)}")
