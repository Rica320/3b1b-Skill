"""
The cube on screen, kept in lockstep with the cube in `cube_model`.

Two independent things have to agree: the mobjects the viewer sees, which move
because a `Rotate` was applied to a group of them, and the logical state, which
moves because a permutation table was applied to a tuple. They are computed
separately on purpose -- `check()` reads the colours and orientations back off
the rendered geometry and compares them against the model, so "the cube in the
video is a real cube" is something the build verifies rather than something the
narration asserts.

    cube = CubeView(size=3.3)
    scene.add(cube.group)
    cube.turn(scene, "R", run_time=0.28)
    cube.turns(scene, parse("U R U' R'"))
    cube.check()                     # raises if picture and model disagree

Every face here is a `Square3D`, which is a `Surface`, NOT a `Square`, which is
a VMobject. See ANTI-PATTERN #18: a VMobject's fill is drawn by winding number
in screen space, so a filled polygon turned away from the camera fills with the
opposite sign and disappears. Measured: a cube built from `Square`s rendered
with every near face missing and the far interior showing through -- an object
turned inside out.
"""

import numpy as np
from manimlib import (
    Group, Square, Square3D, Rotate, Succession, VGroup,
    ORIGIN, RIGHT, UP, PI,
)

import cube_model as cm

# The cube's own six colours. These are not part of the video's palette -- they
# belong to the object, the way a photograph's colours do, and nothing else in
# the scene is allowed to use them (see README, "colour").
STICKER = {
    "W": "#EFEFE7",     # white   (down)
    "Y": "#F2CE2B",     # yellow  (up)
    "G": "#1FA84A",     # green   (front)
    "B": "#1B62C4",     # blue    (back)
    "O": "#E5741A",     # orange  (right)
    "R": "#C0272D",     # red     (left)
}
BODY = "#0C0C0C"        # the plastic between the stickers

# ── why these four numbers ───────────────────────────────────────────────
#
# All in units of one cubie. Every one of them is set by a depth-buffer
# constraint, not by taste, so changing any of them means re-checking a
# zoomed frame:
#
#   BODY at 0.5 exactly    -> a cubie's outer face and its neighbour's inner
#                             face are COINCIDENT. Both are black, so it
#                             looks harmless, but they carry opposite normals
#                             and therefore different shading, and the depth
#                             test picks a different winner per pixel per
#                             frame. Measured: light hairlines crawling along
#                             every cubie boundary, worst during a turn.
#                             0.485 leaves a 0.03 gap between neighbours,
#                             which nothing can see (it looks into the black
#                             side of the next cubie) and which no two
#                             surfaces share.
#
#   STICKER 0.82           -> a black gap of 0.18 between adjacent colours,
#                             about twice what a real cube has. 0.90 gives
#                             0.10: 0.035 of plate border either side plus
#                             the 0.03 body gap.
#
#   LIFT +0.03             -> the sticker stands 0.03 proud of the body, so
#                             at the silhouette the far side's stickers poke
#                             past it as coloured hairlines and up close the
#                             tiles look like they are hovering. +0.008 is
#                             0.0096 world units at CUBE_SIZE 3.6 -- four
#                             times what the depth buffer needed here, and
#                             sub-pixel at 1080p, so it reads as flush.
#
# Checked the way pixel problems have to be: the same frame of the same
# rotation, rendered under both, cropped to four stickers and magnified 3x.
# Under the old numbers every black channel has a grey hairline down the
# middle of it -- one plate winning a strip of the fight. Under these, the
# channels are solid black.
BODY_SIZE = 0.97
BODY_FACE = 0.485       # distance from the cubie's centre to its own face
STICKER_SIZE = 0.90
LIFT = BODY_FACE + 0.008

STICKER_SHADING = (0.28, 0.15, 0.30)
BODY_SHADING = (0.10, 0.05, 0.45)

# ── the one place the two coordinate conventions meet ────────────────────
#
# cube_model is y-up: U is +y and F is +z, which is how anyone writing cube
# code thinks. ManimGL's 3D camera is z-up: `reorient(theta, phi)` sweeps
# about +z, and phi = 0 looks straight down at the xy-plane. Building the
# model's axes directly into the scene puts the cube on its side -- measured:
# at the standard three-quarter view the top face rendered as the front one.
#
# So the model keeps its convention and the view rotates it, once, here. The
# basis is chosen to put U on top, F to the front-left and R to the
# front-right at theta = -32, which is how a cube is normally photographed
# and, more to the point, means the viewer can see the R face during the
# hundred R turns the video spends on it.
BASIS = np.array([[0, 0, -1],
                  [-1, 0, 0],
                  [0, 1, 0]], dtype=float)      # model -> world


def to_world(v):
    return BASIS @ np.asarray(v, dtype=float)


def to_model(v):
    return BASIS.T @ np.asarray(v, dtype=float)  # a rotation: inverse = T


def _facing(direction, side_length, colour, opacity, shading):
    """A square of the given size, turned to face `direction`."""
    d = tuple(int(round(v)) for v in direction)
    sq = Square3D(side_length=side_length, color=colour, opacity=opacity,
                  shading=shading)
    if d == (0, 0, 1):
        pass
    elif d == (0, 0, -1):
        sq.rotate(PI, axis=UP)
    elif d == (1, 0, 0):
        sq.rotate(PI / 2, axis=UP)
    elif d == (-1, 0, 0):
        sq.rotate(-PI / 2, axis=UP)
    elif d == (0, 1, 0):
        sq.rotate(-PI / 2, axis=RIGHT)
    else:
        sq.rotate(PI / 2, axis=RIGHT)
    return sq


class CubeView:
    """26 cubies of six faces each, plus the logical state they represent."""

    def __init__(self, size=3.3, state=None):
        self.unit = size / 3.0
        self.state = cm.SOLVED if state is None else state
        self.cubies = {}
        for slot in cm.SLOTS:
            self.cubies[slot] = self._build(slot)
        # Group, not VGroup: these are Surfaces. A VGroup rejects them, and a
        # VGroup that did accept them would apply VMobject-only operations.
        self.group = Group(*[self.cubies[s] for s in cm.SLOTS])
        self.group.move_to(ORIGIN)

    def _build(self, slot):
        cub = Group()
        cub.stickers = []
        cub.plates = []
        for face, normal in cm.FACE_NORMAL.items():
            # A black plate on every face, including the six that face inward.
            # Without the inward ones the cube is hollow, and a quarter turn
            # shows daylight through the middle of it for its whole animation.
            out = to_world(normal)
            plate = _facing(out, BODY_SIZE, BODY, 1.0, BODY_SHADING)
            plate.move_to(out * BODY_FACE)
            cub.add(plate)
            cub.plates.append(plate)

            if slot[_axis(normal)] != normal[_axis(normal)]:
                continue                       # inward face: no sticker
            colour = cm.FACE_COLOUR[face]
            st = _facing(out, STICKER_SIZE, STICKER[colour], 1.0,
                         STICKER_SHADING)
            st.move_to(out * LIFT)
            st.colour = colour
            cub.add(st)
            cub.stickers.append(st)

        cub.scale(self.unit)
        cub.move_to(to_world(slot) * self.unit)
        return cub

    # ── turning ──────────────────────────────────────────────────────────

    def _layer(self, move):
        normal = cm.FACE_NORMAL[move[0]]
        ax = _axis(normal)
        return [s for s in self.cubies if s[ax] == normal[ax]]

    def _advance(self, move):
        """Re-key the slots and advance the state. Returns (group, angle, axis).

        The bookkeeping happens when the turn is *built*, not when its
        animation finishes, so several moves can be queued without the slot
        map being momentarily wrong -- and `self.state` moves in the same call
        as the mobjects, which is what makes the two impossible to desync by
        forgetting one of them.
        """
        face = move[0]
        amount = {"": 1, "2": 2, "'": 3}[move[1:]]
        slots = self._layer(move)
        group = Group(*[self.cubies[s] for s in slots])

        rot = cm._turn(cm.FACE_NORMAL[face], -amount)
        moved = {cm._apply(rot, s): self.cubies[s] for s in slots}
        self.cubies.update(moved)
        self.state = cm.apply_one(self.state, move)
        return group, -amount * PI / 2, to_world(cm.FACE_NORMAL[face])

    def turn_anim(self, move, run_time=0.3, **kw):
        group, angle, axis = self._advance(move)
        return Rotate(group, angle=angle, axis=axis, about_point=ORIGIN,
                      run_time=run_time, **kw)

    def turn(self, scene, move, run_time=0.3, **kw):
        scene.play(self.turn_anim(move, run_time=run_time), **kw)

    def turns(self, scene, moves, run_time=0.3, **kw):
        for m in moves:
            self.turn(scene, m, run_time=run_time, **kw)

    def run_anim(self, moves, per_move=0.22):
        """A whole sequence as one animation, for playing under a narration line.

        Built as a Succession rather than as N separate `play` calls so the
        caller can hand it to Narrator.under() and have the line and the moves
        share a clock. Every turn's bookkeeping happens now, at build time, so
        `self.state` is already the state the sequence ends in -- which is what
        lets a section assert what it is about to show before showing it.
        """
        return Succession(*[self.turn_anim(m, run_time=per_move)
                            for m in moves])

    def set_state(self, moves):
        """Apply moves with no animation at all -- for setting up a shot."""
        for m in moves:
            group, angle, axis = self._advance(m)
            group.rotate(angle, axis=axis, about_point=ORIGIN)
        return self

    # ── marks and attention ──────────────────────────────────────────────

    def mark(self, slot, colour, width=7.0, offset=0.06):
        """Outline every sticker of the piece in `slot`, and follow it.

        The outline is added *into* the cubie's own group, so every subsequent
        turn carries it along without an updater. It is the one VMobject in
        the cube: a stroke has no fill to wind the wrong way, and
        set_flat_stroke(False) keeps it a ribbon that faces the camera instead
        of a flat one that thins to nothing edge-on.
        """
        cub = self.cubies[slot]
        centre = self._centre(cub)
        ring = VGroup()
        for st in cub.stickers:
            n = self._outward(st, centre)
            sq = Square(side_length=STICKER_SIZE * self.unit)
            sq.rotate(*_align_to(n))
            sq.move_to(st.get_center() + n * offset * self.unit)
            sq.set_fill(opacity=0.0)
            sq.set_stroke(colour, width=width, opacity=1.0)
            sq.set_flat_stroke(False)
            ring.add(sq)
        cub.add(ring)
        cub.mark = ring
        return ring

    def unmark(self, slot):
        cub = self.cubies[slot]
        ring = getattr(cub, "mark", None)
        if ring is not None:
            cub.remove(ring)
            cub.mark = None
        return ring

    def pieces(self, slots):
        return Group(*[self.cubies[s] for s in slots])

    def others(self, slots):
        keep = set(slots)
        return Group(*[c for s, c in self.cubies.items() if s not in keep])

    # ── the cross-check ──────────────────────────────────────────────────

    def _centre(self, cub):
        """The cubie's true centre: the mean of its six plates.

        Not get_center() -- a marked cubie carries an outline that sits proud
        of one face and pulls the bounding box off centre.
        """
        return np.mean([p.get_center() for p in cub.plates], axis=0)

    def _outward(self, sticker, centre):
        v = sticker.get_center() - centre
        n = np.linalg.norm(v)
        if n < 1e-9:
            raise AssertionError("sticker sits at its cubie's centre")
        return v / n

    def check(self, where=""):
        """Read the geometry back and confirm it is the state we think it is.

        Each sticker's face is worked out from where it sits relative to its
        own cubie, and its slot from where that cubie sits -- both measured off
        the rendered mobjects. A bug in the animation (a layer selected on the
        wrong axis, a turn animated the wrong way round, a sequence applied to
        the picture but not to the model) fails here rather than shipping a
        cube with stickers no real cube could have.
        """
        problems = []
        for slot, cub in self.cubies.items():
            centre = self._centre(cub)
            here = np.round(to_model(centre / self.unit)).astype(int)
            if tuple(here) != slot:
                problems.append(f"cubie keyed {slot} is drawn at {tuple(here)}")
                continue
            for st in cub.stickers:
                out = to_model(self._outward(st, centre))
                n = tuple(int(v) for v in np.round(out))
                if n not in cm.NORMAL_FACE:
                    problems.append(f"{slot}: sticker facing {out}, not an axis")
                    continue
                if np.linalg.norm(out - np.array(n, dtype=float)) > 0.08:
                    problems.append(f"{slot}: sticker facing {out}, askew")
                    continue
                want = cm.color_at(self.state, slot, n)
                if want != st.colour:
                    problems.append(
                        f"{slot} facing {cm.NORMAL_FACE[n]}: drawing "
                        f"{st.colour}, model says {want}")
        broken = cm.laws(self.state)
        if broken:
            problems += [f"illegal cube state: {b}" for b in broken]
        if problems:
            raise AssertionError(
                f"picture and model disagree{' at ' + where if where else ''}:\n"
                + "\n".join("  " + p for p in problems[:12]))
        return True


def _align_to(direction):
    """(angle, axis) that turns an xy-plane mobject to face `direction`."""
    d = tuple(int(round(v)) for v in direction)
    return {
        (0, 0, 1): (0.0, UP),
        (0, 0, -1): (PI, UP),
        (1, 0, 0): (PI / 2, UP),
        (-1, 0, 0): (-PI / 2, UP),
        (0, 1, 0): (-PI / 2, RIGHT),
        (0, -1, 0): (PI / 2, RIGHT),
    }[d]


def _axis(normal):
    return next(i for i, v in enumerate(normal) if v != 0)
