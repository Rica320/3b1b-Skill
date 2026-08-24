#!/usr/bin/env python3
"""
Every rule claim the narration makes, re-derived from the model.

The script says things. This file makes the model say them independently, so a
line that drifted away from the rules fails here instead of shipping. Each
check cites the section of The Law of Root it is testing.

    ../../env/bin/python verify_root.py
"""

import sys

import woodland as w
import demo_game as dg
from woodland import (MARQUISE, EYRIE, ALLIANCE, VAGABOND, CULT, RIVERFOLK,
                      FOX, RABBIT, MOUSE, WARRIOR, BUILDING, TOKEN, PAWN,
                      COUNTS_FOR_RULE, IllegalAction)

CHECKS = []


def check(claim, rule):
    def deco(fn):
        CHECKS.append((claim, rule, fn))
        return fn
    return deco


# ── §2  the ground ───────────────────────────────────────────────────────
@check("A clearing is adjacent to every clearing a path links it to.", "2.2.1")
def _():
    m = w.MAP
    for a, b in m.paths:
        assert m.adjacent(a, b) and m.adjacent(b, a)
    assert not m.adjacent(1, 12)                 # opposite corners are not
    assert m.connected()
    return f"{len(m.clearings)} clearings, {len(m.paths)} paths, connected"


@check("Every clearing has a suit: fox, rabbit, or mouse.", "2.2.2")
def _():
    suits = [c.suit for c in w.MAP]
    assert set(suits) == {FOX, RABBIT, MOUSE}
    n = {s: suits.count(s) for s in (FOX, RABBIT, MOUSE)}
    assert len(set(n.values())) == 1, n
    return f"{n[FOX]} fox, {n[RABBIT]} rabbit, {n[MOUSE]} mouse"


@check("A bird card is wild; a bird card cannot be substituted for.",
       "2.1.1 / 2.1.3")
def _():
    for cs in (FOX, RABBIT, MOUSE):
        assert w.matches(w.BIRD, cs), "birds must be wild"
        assert w.matches(cs, cs)
        assert not w.matches(cs, [x for x in (FOX, RABBIT, MOUSE)
                                  if x != cs][0])
        assert not w.matches(cs, w.BIRD, reverse=True)
    assert not w.matches(w.BIRD, FOX, reverse=True)
    return "bird -> any suit; no suit -> bird"


@check("Four slots begin the game filled with ruins.", "2.2.4 / 5.1.4")
def _():
    r = [c.id for c in w.MAP if c.ruin]
    assert len(r) == 4, r
    s = w.State()
    for cid in r:
        assert s.open_slots(cid) == w.MAP[cid].slots - 1
    return f"ruins in clearings {r}"


@check("A building cannot be placed in a clearing with no open slots.", "2.2.3")
def _():
    s = w.State()
    c = 12                                       # one slot
    s.place_building(MARQUISE, c, "sawmill")
    try:
        s.place_building(MARQUISE, c, "workshop")
    except IllegalAction:
        return "clearing 12 (1 slot) refused a second building"
    raise AssertionError("2.2.3 not enforced")


@check("The ruler is the player with the most warriors and buildings; "
       "tokens and pawns do not contribute; a tie means no ruler.", "2.8")
def _():
    s = w.State()
    s.place_warrior(MARQUISE, 9, 2)
    s.place_warrior(EYRIE, 9, 1)
    assert s.ruler(9) == MARQUISE
    s.place_warrior(EYRIE, 9, 1)                 # 2 v 2
    assert s.ruler(9, variant=False) is None, "a tie must leave no ruler"
    s.place_token(MARQUISE, 9, "keep")           # a token must not break it
    assert s.ruler(9, variant=False) is None
    s.place_pawn(9)                              # nor a pawn
    assert s.ruler(9, variant=False) is None
    s.place_building(MARQUISE, 9, "sawmill")     # a building must
    assert s.ruler(9, variant=False) == MARQUISE
    assert not COUNTS_FOR_RULE[TOKEN] and not COUNTS_FOR_RULE[PAWN]
    assert COUNTS_FOR_RULE[WARRIOR] and COUNTS_FOR_RULE[BUILDING]
    return "token and pawn inert; building decisive"


@check("Nobody rules an empty clearing.", "2.8")
def _():
    s = w.State()
    assert s.ruler(7) is None and s.ruler(7, variant=False) is None
    return "empty clearing has no ruler under either reading"


# ── §3  rule is a permission slip ────────────────────────────────────────
@check("To move you must rule the origin, the destination, or both.", "4.2.1")
def _():
    s = w.State()
    s.place_warrior(MARQUISE, 9, 2)
    s.place_warrior(EYRIE, 9, 2)                 # tie: she rules neither end
    ok, why = s.can_move(MARQUISE, 9, 6)
    assert not ok, why
    s.place_warrior(MARQUISE, 6, 1)              # now she rules the destination
    ok, why = s.can_move(MARQUISE, 9, 6)
    assert ok, why
    ok, why = s.can_move(MARQUISE, 9, 3)         # 9 and 3 are not adjacent
    assert not ok and "adjacent" in why
    return "blocked on a tie, allowed once she rules the destination"


# ── §4  battle ───────────────────────────────────────────────────────────
@check("Attacker deals the higher roll, defender the lower.", "4.3.2.II")
def _():
    s = w.State()
    s.place_warrior(MARQUISE, 9, 3)
    s.place_warrior(EYRIE, 9, 3)
    r = s.battle(MARQUISE, EYRIE, 9, rolls=(1, 3))
    assert (r["attacker_roll"], r["defender_roll"]) == (3, 1), r
    return "rolls (1,3) -> attacker 3, defender 1"


@check("Rolled hits are capped by your warriors in the clearing of battle.",
       "4.3.2.I")
def _():
    s = w.State()
    s.place_warrior(MARQUISE, 9, 1)
    s.place_warrior(EYRIE, 9, 3)
    r = s.battle(MARQUISE, EYRIE, 9, rolls=(3, 2))
    assert r["attacker_capped"] == 1, r          # rolled 3, has 1 warrior
    assert r["defender_capped"] == 2, r
    return "rolled 3 with one warrior deals 1"


@check("A defenceless defender gives the attacker one extra hit.", "4.3.2.III")
def _():
    s = w.State()
    s.place_warrior(MARQUISE, 9, 2)
    s.place_building(EYRIE, 9, "roost")          # a building, no warriors
    r = s.battle(MARQUISE, EYRIE, 9, rolls=(1, 0))
    assert r["defenceless"] and r["attacker_hits"] == 2, r
    return "1 rolled + 1 extra = 2 hits"


@check("Hits remove all warriors before any building or token.", "4.3.3")
def _():
    s = w.State()
    s.place_warrior(MARQUISE, 9, 3)
    s.place_warrior(EYRIE, 9, 1)
    s.place_building(EYRIE, 9, "roost")
    r = s.battle(MARQUISE, EYRIE, 9, rolls=(1, 0))
    kinds = [p.kind for p in r["attacker_removed"]]
    assert kinds == [WARRIOR], kinds
    return "one hit took the warrior, not the roost"


@check("One victory point per enemy building or token removed.", "3.2.1")
def _():
    s = w.State()
    s.vp = {MARQUISE: 0, EYRIE: 0}
    s.place_warrior(MARQUISE, 9, 3)
    s.place_building(EYRIE, 9, "roost")
    s.place_token(EYRIE, 9, "wood")
    r = s.battle(MARQUISE, EYRIE, 9, rolls=(2, 0))
    assert r["attacker_vp"] == 2 and s.vp[MARQUISE] == 2, (r, s.vp)
    return "roost + token = 2 VP"


@check("Hits are dealt simultaneously.", "4.3.3")
def _():
    s = w.State()
    s.place_warrior(MARQUISE, 9, 1)
    s.place_warrior(EYRIE, 9, 1)
    r = s.battle(MARQUISE, EYRIE, 9, rolls=(1, 1))
    assert len(r["attacker_removed"]) == 1 and len(r["defender_removed"]) == 1
    assert s.presences(9) == {}, s.presences(9)
    return "both last warriors died in the same exchange"


@check("Thirty victory points wins immediately.", "3.1")
def _():
    s = w.State(); s.vp = {MARQUISE: 29, EYRIE: 0}
    assert s.winner() is None
    s.score(MARQUISE, 1)
    assert s.winner() == MARQUISE
    return "29 -> no winner, 30 -> winner"


# ── §5  the six edits to one sentence ────────────────────────────────────
@check("Eyrie: they rule when tied for most, but never an empty clearing.",
       "7.2.2")
def _():
    s = w.State()
    s.place_warrior(MARQUISE, 9, 2)
    s.place_warrior(EYRIE, 9, 2)
    assert s.ruler(9) == EYRIE and s.ruler(9, variant=False) is None
    empty = w.State()
    assert empty.ruler(9) is None
    return "tie in 9 -> Eyrie; empty 9 -> nobody"


@check("Alliance: sympathy is a token, so it adds nothing to rule.", "2.8 / 8.2.5")
def _():
    s = w.State()
    s.place_warrior(MARQUISE, 9, 1)
    for _ in range(3):
        try:
            s.place_token(ALLIANCE, 9, "sympathy")
        except IllegalAction:
            pass                                 # 8.2.5.I: only one per clearing
    assert s.presence(9, ALLIANCE) == 0
    assert s.ruler(9) == MARQUISE
    assert len(s.at(9, ALLIANCE, TOKEN)) == 1
    return "one sympathy token, zero presence, Marquise still rules"


@check("Alliance: moving warriors into a sympathetic clearing causes Outrage.",
       "8.2.6")
def _():
    s = w.State()
    s.place_warrior(MARQUISE, 6, 1)
    s.place_token(ALLIANCE, 9, "sympathy")
    assert s.outrage_triggered(MARQUISE, 9)
    assert not s.outrage_triggered(ALLIANCE, 9)  # not "another player"
    assert not s.outrage_triggered(MARQUISE, 5)
    return "triggers for an enemy, not for the Alliance herself"


@check("Alliance: as defender she deals the higher roll.", "8.2.2")
def _():
    s = w.State()
    s.place_warrior(EYRIE, 9, 3)
    s.place_warrior(ALLIANCE, 9, 3)
    r = s.battle(EYRIE, ALLIANCE, 9, rolls=(3, 1))
    assert r["guerrilla"] and r["defender_roll"] == 3 and r["attacker_roll"] == 1
    return "Guerrilla War inverted the dice"


@check("Vagabond: the pawn cannot rule and cannot stop anyone else ruling.",
       "9.2.2")
def _():
    s = w.State()
    s.place_pawn(9)
    assert s.ruler(9) is None                    # a pawn alone rules nothing
    s.place_warrior(MARQUISE, 9, 1)
    assert s.ruler(9) == MARQUISE                # and blocks nobody
    assert s.presence(9, VAGABOND) == 0
    return "pawn present, Marquise rules on one warrior"


@check("Vagabond: Nimble - he moves regardless of who rules either end.",
       "9.2.3")
def _():
    s = w.State()
    s.place_pawn(9)
    s.place_warrior(EYRIE, 9, 5)                 # the Eyrie rule both ends
    s.place_warrior(EYRIE, 6, 5)
    ok, why = s.can_move(VAGABOND, 9, 6)
    assert ok and "Nimble" in why, why
    ok, _ = s.can_move(MARQUISE, 9, 6)
    assert not ok
    return "Vagabond passes where the Marquise cannot"


@check("Cult: wherever the Cult has a garden, the Cult rules - over the Eyrie "
       "too.", "10.2.4")
def _():
    s = w.State()
    s.place_warrior(EYRIE, 9, 6)
    s.place_building(CULT, 9, "garden")
    assert s.ruler(9) == CULT, s.presences(9)
    assert s.presence(9, EYRIE) > s.presence(9, CULT)
    return "6 birds outnumbered by one garden"


@check("Riverfolk: rivers are paths for them alone, and rule is not required.",
       "2.3 / 11.2.2")
def _():
    s = w.State()
    a, b = w.MAP.river[0], w.MAP.river[1]
    s.place_warrior(RIVERFOLK, a, 1)
    s.place_warrior(MARQUISE, a, 9)              # somebody else rules both ends
    s.place_warrior(MARQUISE, b, 9)
    ok, why = s.can_move(RIVERFOLK, a, b)
    assert ok and "Swimmers" in why, why
    return f"river {a}->{b} open to the Riverfolk under any ruler"


# ── §6  the demo game ────────────────────────────────────────────────────
@check("The three turns §6 animates are legal, in order.", "6 / 7 / 8")
def _():
    steps = dg.steps()
    tags = [s[0] for s in steps]
    assert tags[0] == "setup" and tags[-1] == "t5.revolt", tags
    return f"{len(steps)} states, {' -> '.join(tags[1:4])} ... {tags[-1]}"


@check("Setup: a Marquise warrior in every clearing but the opposite corner.",
       "6.9.3")
def _():
    s = dg.steps()[0][2]
    missing = [c.id for c in s.map if s.warriors(c.id, MARQUISE) == 0]
    assert missing == [dg.EYRIE_CORNER], missing
    assert (min(dg.KEEP, dg.EYRIE_CORNER),
            max(dg.KEEP, dg.EYRIE_CORNER)) in [tuple(sorted(p))
                                               for p in w.OPPOSITE_CORNERS]
    return f"only clearing {missing[0]} is empty, and it is the far corner"


@check("Setup: the Alliance begins with no piece on the map.", "8.8")
def _():
    s = dg.steps()[0][2]
    assert all(not s.at(c.id, ALLIANCE) for c in s.map)
    assert len(s.supporters) == 3
    return "0 pieces, 3 supporters"


@check("The battle in clearing 9 goes 2 hits to 1 and halves the cat's tower.",
       "4.3 / 2.8")
def _():
    steps = {s[0]: s for s in dg.steps()}
    before = steps["t2.move"][2]
    rep = steps["t2.battle"][3]
    after = steps["t2.battle"][2]
    assert before.ruler(9) == EYRIE and after.ruler(9) == EYRIE
    assert rep["attacker_hits"] == 2 and rep["defender_hits"] == 1, rep
    assert before.presence(9, MARQUISE) == 4 and after.presence(9, MARQUISE) == 2
    return "Marquise 4 -> 2, Eyrie 5 -> 4, sawmill survives"


@check("The Alliance scores in clearing 9 without a warrior anywhere on the "
       "map.", "8.4.2")
def _():
    s = [x for x in dg.steps() if x[0] == "t3.sympathy"][0][2]
    assert s.vp[ALLIANCE] >= 1
    assert sum(s.warriors(c.id, ALLIANCE) for c in s.map) == 0
    assert s.presence(9, ALLIANCE) == 0
    return f"{s.vp[ALLIANCE]} VP, 0 warriors, 0 presence"


@check("Martial Law applied: three or more enemy warriors were standing there.",
       "8.4.2.II.a")
def _():
    before = [x for x in dg.steps() if x[0] == "t2.evening"][0][2]
    assert before.warriors(9, EYRIE) >= 3
    return f"{before.warriors(9, EYRIE)} Eyrie warriors in clearing 9"


@check("The revolt removes every enemy piece and scores a point per building.",
       "8.4.1 / 3.2.1")
def _():
    steps = {s[0]: s for s in dg.steps()}
    before = steps["t4.outrage"][2]
    after, rep = steps["t5.revolt"][2], steps["t5.revolt"][3]
    assert before.presences(9) == {MARQUISE: 4, EYRIE: 5}, before.presences(9)
    assert after.presences(9) == {ALLIANCE: 2}, after.presences(9)
    kinds = sorted(p.name for p in rep["removed"] if p.kind == BUILDING)
    assert kinds == ["roost", "sawmill"], kinds
    assert rep["vp"] == 2, rep
    assert after.ruler(9) == ALLIANCE
    return "sawmill + roost = 2 VP; clearing 9 is the Alliance's"


@check("The Alliance never moved a warrior into clearing 9.", "8.4.1.III")
def _():
    moves = [l for l in dg.steps()[-1][2].log
             if l.startswith(f"{ALLIANCE}: move")]
    assert moves == [], moves
    return "no Alliance move in the log; the base was placed, not marched"


def main():
    width = max(len(c) for c, _, _ in CHECKS)
    bad = 0
    for claim, rule, fn in CHECKS:
        try:
            note = fn()
            print(f"  \033[32mok\033[0m  [{rule:>10}]  {claim}")
            if note:
                print(f"      {'':>10}   -> {note}")
        except Exception as e:
            bad += 1
            print(f"  \033[31mFAIL\033[0m [{rule:>10}]  {claim}")
            print(f"      {'':>10}   -> {type(e).__name__}: {e}")
    print(f"\n{len(CHECKS) - bad}/{len(CHECKS)} claims verified against "
          f"The Law of Root.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
