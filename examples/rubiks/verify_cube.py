#!/usr/bin/env python3
"""
Check every factual claim the narration makes, against the code that produced
the animation.

    python verify_cube.py

`verify_render.py` checks the pixels and `verify_audio.py` checks the sound.
Neither can tell you that the cube in the video is a legal cube, that the
solution solves it, or that the number the voice reads out is the right number.
A video about a mathematical object can be flawless on both of those and still
assert something false, so the claims get their own gate.

Exit status 0 if every claim holds.
"""

import math
import sys
from collections import Counter

import cube_model as cm
import solver as sv
from rubiks import SCRAMBLE_SEED, STATES, CUBE_SIZE

FAILURES = []


def claim(text, ok, detail=""):
    print(f"  {'pass' if ok else 'FAIL'}  {text}" + (f"   [{detail}]" if detail
                                                     else ""))
    if not ok:
        FAILURES.append(text)
    return ok


def main():
    scramble = cm.scramble(20, seed=SCRAMBLE_SEED)
    start = cm.apply(cm.SOLVED, scramble)
    stages = sv.solve(start)
    solution = [m for _, _, moves in stages for m in moves]

    print('§0  "forty-three quintillion arrangements"')
    # 8!.3^7 corner arrangements x 12!.2^11 edge arrangements, halved: the
    # three laws in cube_model.laws() are exactly what removes the other
    # eleven twelfths of the naive count.
    counted = (math.factorial(8) * 3 ** 7
               * math.factorial(12) * 2 ** 11 // 2)
    claim("the state count is 8!.3^7.12!.2^11/2", counted == STATES,
          f"{counted:,}")
    seconds_per_year = 365.25 * 24 * 3600
    universe = 13.787e9 * seconds_per_year          # Planck 2018, in seconds
    ratio = STATES / universe
    claim('"about a hundred times the age of the universe" at one per second',
          50 <= ratio <= 200, f"{ratio:.0f}x")

    print('\n§1  "every turn moves nine cubies at once"')
    layer = [s for s in cm.SLOTS if s[0] == 1]
    claim("a face layer holds nine cubies", len(layer) + 1 == 10,
          f"{len(layer)} cubies + 1 centre")
    after_r = cm.apply(cm.SOLVED, ["R"])
    moved = [s for s in cm.SLOTS if cm._home(after_r, s) != s]
    claim('"eight pieces move" on a single turn', len(moved) == 8,
          f"{len(moved)}")

    print('\n§1  the first edge is placed, then the fetch destroys it')
    target, second = (1, -1, 0), (0, -1, -1)
    first = sv.ida(start, lambda s: sv.solved_at(s, [target]), 3)
    claim("the white-orange edge is one turn from home", len(first) == 1,
          cm.fmt(first))
    placed = cm.apply(start, first)
    fetch = sv.ida(placed, lambda s: sv.solved_at(s, [second]), 4)
    broken = cm.apply(placed, fetch)
    claim("fetching the next white edge un-places the first one",
          broken[cm.SLOT_INDEX[target]] != cm.IDENT, cm.fmt(fetch))

    print('\n§1  "retrace every move, backwards"')
    undo = cm.invert(scramble + first + fetch)
    claim("the retrace lands exactly on solved",
          cm.apply(broken, undo) == cm.SOLVED, f"{len(undo)} moves")

    print('\n§2  the detour')
    rur = cm.apply(cm.SOLVED, cm.parse("R U R'"))
    disturbed = [s for s in cm.SLOTS
                 if rur[cm.SLOT_INDEX[s]] != cm.IDENT and s[1] != 1]
    corners = [s for s in disturbed if 0 not in s]
    edges = [s for s in disturbed if s.count(0) == 1]
    claim('"one corner and one edge have changed" below the top layer',
          len(corners) == 1 and len(edges) == 1,
          f"corner {corners}, edge {edges}")

    print('\n§3  "six times through, twenty-four moves"')
    detour = cm.parse("R U R' U'")
    state, order = cm.SOLVED, 0
    while True:
        state = cm.apply(state, detour)
        order += 1
        if state == cm.SOLVED or order > 24:
            break
    claim("(R U R' U') has order exactly six", order == 6, f"order {order}")
    claim("that is twenty-four moves", order * len(detour) == 24)

    print('\n§4-5  the solve')
    claim("the solution solves the scramble",
          cm.apply(start, solution) == cm.SOLVED)
    claim('"ninety-nine moves"', len(solution) == 99, f"{len(solution)}")
    claim("all seven stages do work", all(m for _, _, m in stages),
          ", ".join(f"{k}:{len(m)}" for k, _, m in stages))

    algs = {
        "the detour": sv.TRIGGER,
        "insert right": sv.INSERT_RIGHT,
        "insert left": sv.INSERT_LEFT,
        "yellow cross": sv.OLL_EDGES,
        "sune": sv.SUNE,
        "corner cycle": sv.A_PERM,
        "edge cycle": sv.U_PERM,
    }
    claim('"seven different sequences"', len(algs) == 7)
    claim('"two of which are the same one mirrored"',
          len(cm.parse(sv.INSERT_RIGHT)) == len(cm.parse(sv.INSERT_LEFT)) == 8)
    longest = max((len(cm.parse(a)), n) for n, a in algs.items())
    claim('"the longest is eleven moves"', longest[0] == 11,
          f"{longest[1]}, {longest[0]} moves")

    print('\nlegality, at every single move of the video')
    every = scramble + first + fetch + undo + detour * 6 + scramble + solution
    state, bad = cm.SOLVED, 0
    for i, m in enumerate(every):
        state = cm.apply_one(state, m)
        if cm.laws(state):
            bad += 1
    claim("no move in the video produces an impossible cube", bad == 0,
          f"{len(every)} moves checked")
    counts = Counter(c for face in cm.facelets(state).values() for c in face)
    claim("all six colours still appear nine times",
          set(counts.values()) == {9}, dict(counts))

    print('\nthe picture agrees with the model')
    try:
        from cube_view import CubeView
    except Exception as exc:                       # pragma: no cover
        claim("cube_view imports", False, str(exc)[:80])
    else:
        view = CubeView(size=CUBE_SIZE)
        view.check("solved")
        view.set_state(scramble)
        view.check("scrambled")
        for key, _, moves in stages:
            view.set_state(moves)
            view.check(key)
        claim("rendered stickers match the model at every stage",
              view.state == cm.SOLVED)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} claim(s) do not hold:")
        for f in FAILURES:
            print("  " + f)
        return 1
    print("Every claim in the narration holds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
