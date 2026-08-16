"""
A 3x3x3 cube that cannot represent an impossible state.

The usual way to model a cube is four arrays -- corner permutation, corner
orientation, edge permutation, edge orientation -- with the move tables written
out by hand. Those tables are where cube code goes wrong, and a transcription
slip produces a cube that still turns and still looks fine but is no longer a
cube: stickers appear that no rotation could have produced, and a "solution"
solves something that could never have existed.

So nothing here is transcribed. The state is 26 rotations -- one per cubie
slot -- and a move is a rotation applied to the nine cubies in a layer, exactly
what a hand does. Every reachable state is reachable by turning a real cube,
because turning is the only operation there is. The three validity laws
(permutation parity, corner twist sum = 0 mod 3, edge flip sum = 0 mod 2) hold
automatically rather than being checked; `laws()` verifies them anyway, since a
check that can never fire is still the cheapest possible regression test.

The 24 orientations are indexed, and each move is precomputed as
(slot permutation, orientation relabelling), so applying one is 9 array writes
and the solver can search hundreds of thousands of states.

    state = SOLVED
    state = apply(state, parse("R U R' U'"))
    color_at(state, (1, 1, 1), UP)      -> 'Y'

Coordinates are ManimGL's: +x right, +y up, +z toward the viewer. The scene
file builds its geometry from exactly these slots and applies exactly these
rotations, so the picture and the model are the same object twice.
"""

import itertools
import random

# ── faces, colours, geometry ─────────────────────────────────────────────

UP, DOWN = (0, 1, 0), (0, -1, 0)
RIGHT, LEFT = (1, 0, 0), (-1, 0, 0)
FRONT, BACK = (0, 0, 1), (0, 0, -1)

FACE_NORMAL = {"U": UP, "D": DOWN, "R": RIGHT, "L": LEFT,
               "F": FRONT, "B": BACK}
NORMAL_FACE = {v: k for k, v in FACE_NORMAL.items()}

# White on the bottom, yellow on top: the beginner method builds its first
# layer downward. Chirality checked: rotating this 180 degrees about the F
# axis gives white-up / green-front / red-right, the standard Western scheme.
FACE_COLOUR = {"U": "Y", "D": "W", "F": "G", "B": "B", "R": "O", "L": "R"}

SLOTS = [p for p in itertools.product((-1, 0, 1), repeat=3) if p != (0, 0, 0)]
SLOT_INDEX = {p: i for i, p in enumerate(SLOTS)}

CORNER_SLOTS = [p for p in SLOTS if 0 not in p]
EDGE_SLOTS = [p for p in SLOTS if p.count(0) == 1]
CENTRE_SLOTS = [p for p in SLOTS if p.count(0) == 2]


# ── the 24 orientations ──────────────────────────────────────────────────

def _mul(a, b):
    return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3))
                       for j in range(3)) for i in range(3))


def _apply(m, v):
    return tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3))


def _det(m):
    return (m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]))


def _rotations():
    """Every signed permutation matrix with determinant +1: the 24 rotations."""
    out = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            m = tuple(tuple(signs[i] if perm[i] == j else 0
                            for j in range(3)) for i in range(3))
            if _det(m) == 1:
                out.append(m)
    return out


ROTS = _rotations()
ROT_INDEX = {m: i for i, m in enumerate(ROTS)}
IDENT = ROT_INDEX[((1, 0, 0), (0, 1, 0), (0, 0, 1))]
# compose[a][b] = index of ROTS[a] . ROTS[b]
COMPOSE = [[ROT_INDEX[_mul(a, b)] for b in ROTS] for a in ROTS]


def _turn(axis, quarter_turns):
    """Rotation matrix: `quarter_turns` * 90 degrees about `axis` (right-hand).

    Rodrigues' formula, but every quantity is an integer: for a quarter turn
    sin and cos are only ever 0 or +/-1, so the matrix comes out exact and can
    be used as a dict key.
    """
    ax, ay, az = axis
    q = quarter_turns % 4
    sin_t = (0, 1, 0, -1)[q]
    cos_t = (1, 0, -1, 0)[q]
    k = ((0, -az, ay), (az, 0, -ax), (-ay, ax, 0))
    k2 = _mul(k, k)
    ident = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
    return tuple(tuple(ident[i][j] + sin_t * k[i][j]
                       + (1 - cos_t) * k2[i][j]
                       for j in range(3)) for i in range(3))


# ── moves ────────────────────────────────────────────────────────────────
#
# A face turn is clockwise seen from outside that face, which is a rotation of
# -90 degrees about the face's outward normal.

FACES = ["U", "D", "R", "L", "F", "B"]


def _move_table(face, amount):
    """(which slot each cubie moves to, which rotation it gains).

    The face's own centre is left out. It never changes slot, and its rotation
    about its own axis is invisible on a plain cube -- but tracking it makes
    the state after "R U' R U R U R U' R' U' R2" compare unequal to a solved
    cube, which turns a three-cycle into an order-twelve move and makes the
    last-layer search unsolvable. Measured: that alg's order came out as 12,
    and the only two cubies not back home were the U and R centres.
    """
    normal = FACE_NORMAL[face]
    rot = _turn(normal, -amount)
    ridx = ROT_INDEX[rot]
    axis = normal.index(1) if 1 in normal else normal.index(-1)
    sign = normal[axis]
    perm = {}
    for i, slot in enumerate(SLOTS):
        if slot[axis] == sign and slot.count(0) != 2:
            perm[i] = SLOT_INDEX[_apply(rot, slot)]
    return perm, ridx


MOVES = {}
for _f in FACES:
    for _a, _suffix in ((1, ""), (2, "2"), (3, "'")):
        MOVES[_f + _suffix] = _move_table(_f, _a)

FACE_MOVES = [f + s for f in FACES for s in ("", "2", "'")]

SOLVED = tuple([IDENT] * len(SLOTS))


def apply_one(state, move):
    perm, ridx = MOVES[move]
    out = list(state)
    row = COMPOSE[ridx]
    for i, j in perm.items():
        out[j] = row[state[i]]
    return tuple(out)


def apply(state, moves):
    for m in moves:
        state = apply_one(state, m)
    return state


def parse(text):
    """"R U R' U2" -> ['R', 'U', "R'", 'U2']"""
    out = []
    for tok in text.replace("(", " ").replace(")", " ").split():
        if tok not in MOVES:
            raise ValueError(f"not a move: {tok!r}")
        out.append(tok)
    return out


def invert(moves):
    flip = {"": "'", "'": "", "2": "2"}
    return [m[0] + flip[m[1:]] for m in reversed(moves)]


def fmt(moves):
    return " ".join(moves)


_AMOUNT = {"": 1, "2": 2, "'": 3}
_SUFFIX = {1: "", 2: "2", 3: "'"}
_AXIS_OF = {"U": 0, "D": 0, "R": 1, "L": 1, "F": 2, "B": 2}


def simplify(moves):
    """Cancel what the joins between algorithms left behind.

    Stitching whole algorithms together produces sequences like `... U U' F'
    ...` and `... U2 U ...` at every seam. They are harmless to the state and
    ruinous on screen: a quarter turn immediately undone reads as the render
    stuttering, and the viewer counts it as a move. Adjacent turns of the same
    face are merged; a turn of the opposite face in between does not block
    that, because opposite faces commute.
    """
    out = list(moves)
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(out) - 1:
            j = i + 1
            # step over one opposite-face turn: U D U' is U U' with D moved
            if (j + 1 < len(out) and out[j][0] != out[i][0]
                    and _AXIS_OF[out[j][0]] == _AXIS_OF[out[i][0]]
                    and out[j + 1][0] == out[i][0]):
                j += 1
            if out[j][0] == out[i][0]:
                total = (_AMOUNT[out[i][1:]] + _AMOUNT[out[j][1:]]) % 4
                merged = [out[i][0] + _SUFFIX[total]] if total else []
                out = out[:i] + merged + out[i + 1:j] + out[j + 1:]
                changed = True
                i = max(0, i - 2)
                continue
            i += 1
    return out


# ── reading the cube ─────────────────────────────────────────────────────

def color_at(state, slot, normal):
    """Colour of the sticker at `slot` facing `normal`.

    The sticker now facing `normal` is the one that faced `ori^-1 . normal`
    when the piece was at home, and at home a sticker's colour is the colour of
    the face it pointed at -- so the whole lookup is one inverse rotation. A
    rotation's inverse is its transpose.
    """
    m = ROTS[state[SLOT_INDEX[slot]]]
    home = tuple(sum(m[j][i] * normal[j] for j in range(3)) for i in range(3))
    return FACE_COLOUR[NORMAL_FACE[home]]


def find_piece(state, home):
    """Which slot currently holds the piece that belongs at `home`."""
    for slot in SLOTS:
        if _home(state, slot) == home:
            return slot
    raise KeyError(f"no piece belongs at {home}")


def facelets(state):
    """{face: [9 colours]} in reading order, for printing and cross-checks."""
    out = {}
    for face, n in FACE_NORMAL.items():
        rows = _face_grid(face)
        out[face] = [color_at(state, slot, n) for slot in rows]
    return out


def _face_grid(face):
    """The nine slots of a face, in reading order as seen from outside it."""
    n = FACE_NORMAL[face]
    if face == "U":
        return [(x, 1, z) for z in (-1, 0, 1) for x in (-1, 0, 1)]
    if face == "D":
        return [(x, -1, z) for z in (1, 0, -1) for x in (-1, 0, 1)]
    if face == "F":
        return [(x, y, 1) for y in (1, 0, -1) for x in (-1, 0, 1)]
    if face == "B":
        return [(x, y, -1) for y in (1, 0, -1) for x in (1, 0, -1)]
    if face == "R":
        return [(1, y, z) for y in (1, 0, -1) for z in (1, 0, -1)]
    return [(-1, y, z) for y in (1, 0, -1) for z in (-1, 0, 1)]


def show(state):
    """Unfolded net, for eyeballing a state in a terminal."""
    f = facelets(state)
    pad = " " * 8
    lines = [pad + " ".join(f["U"][i:i + 3]) for i in range(0, 9, 3)]
    for r in range(3):
        lines.append(" ".join(f["L"][r * 3:r * 3 + 3]) + " "
                     + " ".join(f["F"][r * 3:r * 3 + 3]) + " "
                     + " ".join(f["R"][r * 3:r * 3 + 3]) + " "
                     + " ".join(f["B"][r * 3:r * 3 + 3]))
    lines += [pad + " ".join(f["D"][i:i + 3]) for i in range(0, 9, 3)]
    return "\n".join(lines)


# ── validity ─────────────────────────────────────────────────────────────

def laws(state):
    """The three laws a physically possible cube state obeys.

    Structurally guaranteed here -- there is no way to build a state except by
    turning -- so this is a regression test on the move tables rather than a
    filter. It is also what makes "the cube in the video is a real cube" a
    checkable claim rather than an assurance.
    """
    problems = []

    # 1. every sticker colour appears exactly nine times
    counts = {}
    for face, cols in facelets(state).items():
        for c in cols:
            counts[c] = counts.get(c, 0) + 1
    bad = {c: n for c, n in counts.items() if n != 9}
    if bad:
        problems.append(f"sticker counts not 9 each: {bad}")

    # 2. corner twists sum to 0 mod 3, edge flips to 0 mod 2
    twist = sum(_corner_twist(state, s) for s in CORNER_SLOTS) % 3
    flip = sum(_edge_flip(state, s) for s in EDGE_SLOTS) % 2
    if twist:
        problems.append(f"corner twist sum = {twist} (mod 3), must be 0")
    if flip:
        problems.append(f"edge flip sum = {flip} (mod 2), must be 0")

    # 3. corner and edge permutations have the same parity
    cpar = _parity([_home(state, s) for s in CORNER_SLOTS], CORNER_SLOTS)
    epar = _parity([_home(state, s) for s in EDGE_SLOTS], EDGE_SLOTS)
    if cpar != epar:
        problems.append("corner and edge permutation parities differ")

    # 4. centres never move
    for s in CENTRE_SLOTS:
        if _home(state, s) != s:
            problems.append(f"centre at {s} came from {_home(state, s)}")
    return problems


def _home(state, slot):
    """Which slot the piece now at `slot` belongs to."""
    m = ROTS[state[SLOT_INDEX[slot]]]
    return tuple(sum(m[j][i] * slot[j] for j in range(3)) for i in range(3))


def _corner_twist(state, slot):
    """0/1/2: how far the piece's U-or-D sticker sits from the slot's U/D face.

    Counted around the corner in a consistent rotational direction, which is
    the whole point -- an unsigned "which axis is it on" count is not invariant
    under a face turn and sums to nothing in particular.
    """
    m = ROTS[state[SLOT_INDEX[slot]]]
    home = _home(state, slot)
    world = _apply(m, (0, home[1], 0))     # where the piece's U/D sticker points
    x, y, z = slot
    e0 = (0, y, 0)
    a, b = (x, 0, 0), (0, 0, z)
    e1, e2 = (a, b) if _det((e0, a, b)) == 1 else (b, a)
    return (e0, e1, e2).index(world)


def _edge_flip(state, slot):
    """0/1, using the standard U/D-then-F/B orientation convention."""
    m = ROTS[state[SLOT_INDEX[slot]]]
    home = _home(state, slot)
    ref = (0, home[1], 0) if home[1] else (0, 0, home[2])
    world = _apply(m, ref)
    good = (0, slot[1], 0) if slot[1] else (0, 0, slot[2])
    return 0 if world == good else 1


def _parity(homes, slots):
    order = {s: i for i, s in enumerate(slots)}
    perm = [order[h] for h in homes]
    seen, par = [False] * len(perm), 0
    for i in range(len(perm)):
        if seen[i]:
            continue
        j, n = i, 0
        while not seen[j]:
            seen[j] = True
            j = perm[j]
            n += 1
        par ^= (n - 1) & 1
    return par


# ── scrambles ────────────────────────────────────────────────────────────

def scramble(n=20, seed=None):
    """A random move sequence with no redundant pairs, WCA-style."""
    rng = random.Random(seed)
    axis_of = {"U": 0, "D": 0, "R": 1, "L": 1, "F": 2, "B": 2}
    out = []
    while len(out) < n:
        face = rng.choice(FACES)
        if out and face == out[-1][0]:
            continue
        if (len(out) >= 2 and axis_of[face] == axis_of[out[-1][0]]
                and axis_of[face] == axis_of[out[-2][0]]):
            continue
        out.append(face + rng.choice(["", "'", "2"]))
    return out


# ── self-test ────────────────────────────────────────────────────────────

def _test():
    ok = True

    def check(name, cond):
        nonlocal ok
        print(f"  {'pass' if cond else 'FAIL'}  {name}")
        ok = ok and cond

    check("solved state has no law violations", laws(SOLVED) == [])
    check("solved white face is all white",
          set(facelets(SOLVED)["D"]) == {"W"})

    for f in FACES:
        s = apply(SOLVED, [f] * 4)
        check(f"{f} has order 4", s == SOLVED)
        check(f"{f}2 == {f}{f}", apply(SOLVED, [f + "2"]) ==
              apply(SOLVED, [f, f]))
        check(f"{f}' undoes {f}", apply(SOLVED, [f, f + "'"]) == SOLVED)

    for a, b in (("U", "D"), ("R", "L"), ("F", "B")):
        check(f"{a} and {b} commute",
              apply(SOLVED, [a, b]) == apply(SOLVED, [b, a]))

    sexy = parse("R U R' U'")
    st = SOLVED
    for i in range(1, 7):
        st = apply(st, sexy)
        if i < 6:
            check(f"(R U R' U')^{i} != solved", st != SOLVED)
    check("(R U R' U')^6 == solved", st == SOLVED)

    # the algorithms the solver leans on, checked for what they claim to do
    def moved(state, slots):
        return [s for s in slots if state[SLOT_INDEX[s]] != IDENT]

    d_and_middle = ([s for s in SLOTS if s[1] == -1]
                    + [s for s in EDGE_SLOTS if s[1] == 0])
    for name, alg in (("sune", "R U R' U R U2 R'"),
                      ("OLL edges", "F R U R' U' F'"),
                      ("A-perm", "R' F R' B2 R F' R' B2 R2"),
                      ("U-perm", "R U' R U R U R U' R' U' R2")):
        st = apply(SOLVED, parse(alg))
        check(f"{name} preserves the first two layers",
              moved(st, d_and_middle) == [])
    st = apply(SOLVED, parse("R' F R' B2 R F' R' B2 R2"))
    check("A-perm leaves every edge alone", moved(st, EDGE_SLOTS) == [])
    st = apply(SOLVED, parse("R U' R U R U R U' R' U' R2"))
    check("U-perm leaves every corner alone", moved(st, CORNER_SLOTS) == [])

    for i in range(200):
        st = apply(SOLVED, scramble(25, seed=i))
        if laws(st):
            check(f"scramble {i} is a legal state", False)
            break
    else:
        check("200 random scrambles are all legal states", True)

    st = apply(SOLVED, scramble(25, seed=7))
    check("a scramble is undone by its inverse",
          apply(st, invert(scramble(25, seed=7))) == SOLVED)
    return ok


if __name__ == "__main__":
    import sys
    print("cube_model self-test")
    sys.exit(0 if _test() else 1)
