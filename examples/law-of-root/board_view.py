"""
The Woodland, in three dimensions.

The whole visual grammar of the video is one sentence of the rules:

    2.8  "The ruler of a clearing is the player with the most total warriors
          and buildings in that clearing. (Tokens and pawns do not contribute
          to rule.)"

So warriors and buildings are the only pieces with HEIGHT. They stack into a
tower per faction per clearing, and the tallest tower rules. Tokens lie flat on
the ground and the Vagabond's pawn is a ball beside the tower - both visibly
contribute nothing to the skyline, which is exactly what the rule says.

Tower heights are never authored. They are len(state.pieces) filtered by
woodland.COUNTS_FOR_RULE, so an impossible skyline cannot be drawn.

Pieces are tracked by object identity, so a warrior that moves from one
clearing to another is the SAME mobject moving - continuity for free
(animation_rules.md Rule 1), and a removed warrior is a mobject that shrinks
out rather than a redrawn frame.
"""

from __future__ import annotations

import numpy as np
from manimlib import *

import woodland as w
from manim_helpers import FONT
from woodland import (WARRIOR, BUILDING, TOKEN, PAWN, COUNTS_FOR_RULE,
                      MARQUISE, EYRIE, ALLIANCE, VAGABOND, CULT, RIVERFOLK,
                      FOX, RABBIT, MOUSE)

# ── colour ───────────────────────────────────────────────────────────────
# Faction colours belong to the factions the way a photograph's colours belong
# to what it is a photograph of. Nothing else in the video uses them, and
# emphasis is applied by DIMMING everything else plus a white ring - never by
# tinting, which would have to borrow a colour that already means something.
FACTION_COLOR = {
    MARQUISE:  "#D9722A",
    EYRIE:     "#3E7CC4",
    ALLIANCE:  "#4E9A51",
    VAGABOND:  "#9AA0A6",
    CULT:      "#D8C34A",
    RIVERFOLK: "#3FB8AF",
}

# The ground is terrain, not a player: same hue relationships the printed
# board uses for its suits (fox orange, rabbit yellow, mouse red), pulled far
# down in value so no clearing can be mistaken for a faction.
SUIT_COLOR = {FOX: "#22170A", RABBIT: "#1A1B09", MOUSE: "#231014"}
SUIT_BRIGHT = {FOX: "#C8813A", RABBIT: "#C6B94A", MOUSE: "#C05A66"}

C_PATH = "#7A7268"
C_RIVER_INK = "#37535F"
C_RUIN = "#6E6E6E"
C_WOOD = "#8A6A3A"
C_HUD = GREY_A
C_EMPH = WHITE

# ── geometry ─────────────────────────────────────────────────────────────
SX, SY = 3.56, 3.87        # board space [-1,1] -> world; y is stretched
                           # because a phi=60 camera compresses it by cos(60)
DISC_R = 0.70
BLOCK_H = 0.207             # one unit of rule = one block of this height
W_SIDE = 0.262              # a warrior block
B_SIDE = 0.40              # a building block: same height, wider footprint
TOWER_DX = 0.40            # side-by-side towers, so rule is a comparison
TOWER_DY = 0.16            # towers sit back; flat pieces sit in front
FLAT_Y = -0.36
FLAT_DX = 0.235

SHADE_PIECE = (0.25, 0.35, 0.30)
SHADE_GROUND = (0.06, 0.0, 0.62)

# The order towers are laid out in, left to right, so a faction keeps the same
# side of a clearing from one turn to the next.
FACTION_ORDER = [MARQUISE, EYRIE, ALLIANCE, CULT, RIVERFOLK, VAGABOND]


def world(clearing: w.Clearing, z=0.0):
    return np.array([clearing.x * SX, clearing.y * SY, z])


class BoardView:
    """A woodland.State, rendered. Call build() once, then sync() per change."""

    def __init__(self, state: w.State):
        self.state = state
        self.map = state.map
        self.blocks: dict[int, Mobject] = {}      # id(Piece) -> mobject
        self._piece_of: dict[int, w.Piece] = {}

        self.discs = {}
        self.suit_rings = {}
        self.rings = {}
        self.slot_marks = {}
        self.ruins = {}

        self.ground = Group()
        self.paths = VGroup()
        self.river = VGroup()
        self.pieces = Group()

        self._make_ground()

    # ── static furniture ────────────────────────────────────────────────
    def _make_ground(self):
        for a, b in self.map.paths:
            p, q = world(self.map[a]), world(self.map[b])
            d = (q - p) / np.linalg.norm(q - p)
            line = Line(p + d * DISC_R * 0.92, q - d * DISC_R * 0.92)
            line.set_stroke(C_PATH, 2.8, opacity=0.75)
            self.paths.add(line)

        pts = [world(self.map[c], 0.004) for c in self.map.river]
        ribbon = VMobject().set_points_smoothly(pts)
        ribbon.set_stroke(C_RIVER_INK, 13, opacity=0.9)
        self.river.add(ribbon)

        for c in self.map:
            disc = Disk3D(radius=DISC_R, color=SUIT_COLOR[c.suit],
                          opacity=1.0, shading=SHADE_GROUND)
            disc.move_to(world(c, 0.008))
            self.discs[c.id] = disc
            self.ground.add(disc)

            # The suit is carried by a rim, not by the fill: a fill bright
            # enough to name a suit is bright enough to be mistaken for a
            # faction, and faction colour is the one thing that must stay
            # unambiguous.
            sr = Circle(radius=DISC_R * 0.995)
            sr.set_stroke(SUIT_BRIGHT[c.suit], 2.6, opacity=0.60)
            sr.set_fill(opacity=0)
            sr.move_to(world(c, 0.012))
            self.suit_rings[c.id] = sr
            self.ground.add(sr)

            ring = Circle(radius=DISC_R * 1.06)
            ring.set_stroke(C_EMPH, 3.0, opacity=0.0).set_fill(opacity=0)
            ring.move_to(world(c, 0.02))
            self.rings[c.id] = ring

            if c.ruin:
                r = Prism(0.30, 0.30, 0.11, color=C_RUIN, opacity=1,
                          shading=(0.2, 0.1, 0.6))
                r.move_to(world(c) + np.array([DISC_R * 0.46, FLAT_Y + 0.16,
                                               0.055]))
                self.ruins[c.id] = r

            marks = VGroup()
            for k in range(c.slots):
                m = Square(side_length=0.15)
                m.set_stroke(GREY_B, 1.8, opacity=0.0).set_fill(opacity=0)
                m.move_to(world(c, 0.03)
                          + np.array([(k - (c.slots - 1) / 2) * 0.20, 0.33, 0]))
                marks.add(m)
            self.slot_marks[c.id] = marks

    def all_static(self):
        return Group(self.river, self.paths, self.ground)

    # ── layout: where every piece belongs, given a state ────────────────
    def layout(self, state=None):
        state = state or self.state
        out = {}
        for c in self.map:
            centre = world(c)
            towers = [f for f in FACTION_ORDER
                      if any(COUNTS_FOR_RULE[p.kind]
                             for p in state.pieces[c.id] if p.faction == f)]
            n = len(towers)
            for i, f in enumerate(towers):
                stack = [p for p in state.pieces[c.id]
                         if p.faction == f and COUNTS_FOR_RULE[p.kind]]
                # A building is a plinth: it goes at the bottom of its tower.
                stack.sort(key=lambda p: 0 if p.kind == BUILDING else 1)
                dx = (i - (n - 1) / 2) * TOWER_DX
                for k, p in enumerate(stack):
                    out[p] = centre + np.array(
                        [dx, TOWER_DY, BLOCK_H * (k + 0.5)])

            flats = [p for p in state.pieces[c.id]
                     if not COUNTS_FOR_RULE[p.kind]]
            m = len(flats)
            for j, p in enumerate(flats):
                out[p] = centre + np.array(
                    [(j - (m - 1) / 2) * FLAT_DX, FLAT_Y, 0.018])
        return out

    # ── mobjects for pieces ─────────────────────────────────────────────
    def _make_block(self, piece: w.Piece):
        col = FACTION_COLOR[piece.faction]
        if piece.kind == WARRIOR:
            return Prism(W_SIDE, W_SIDE, BLOCK_H, color=col, opacity=1,
                         shading=SHADE_PIECE)
        if piece.kind == BUILDING:
            return Prism(B_SIDE, B_SIDE, BLOCK_H, color=col, opacity=1,
                         shading=(0.35, 0.5, 0.25))
        if piece.kind == PAWN:
            return Sphere(radius=0.115, color=col, opacity=1,
                          shading=(0.3, 0.5, 0.3))
        d = Disk3D(radius=0.15, color=col, opacity=1, shading=(0.2, 0.1, 0.5))
        return d

    def build(self, state=None):
        """Create mobjects for every piece in the state. Returns the Group."""
        state = state or self.state
        pos = self.layout(state)
        for p, xyz in pos.items():
            m = self._make_block(p)
            m.move_to(xyz)
            self.blocks[id(p)] = m
            self._piece_of[id(p)] = p
            self.pieces.add(m)
        return self.pieces

    def sync(self, state, run_time=1.0, added=None, removed=None):
        """Animations that take the view from its current state to `state`.

        Pieces that persist MOVE (same mobject), pieces that are gone shrink
        out, new pieces grow in. Nothing is redrawn, so nothing cuts.
        """
        pos = self.layout(state)
        anims = []
        live = {id(p) for p in pos}

        for pid in list(self.blocks):
            if pid not in live:
                m = self.blocks.pop(pid)
                self._piece_of.pop(pid, None)
                anims.append(FadeOut(m, scale=0.2))
                (removed if removed is not None else []).append(m)

        for p, xyz in pos.items():
            if id(p) in self.blocks:
                m = self.blocks[id(p)]
                if np.linalg.norm(m.get_center() - xyz) > 1e-4:
                    anims.append(m.animate.move_to(xyz))
            else:
                m = self._make_block(p).move_to(xyz)
                self.blocks[id(p)] = m
                self._piece_of[id(p)] = p
                self.pieces.add(m)
                anims.append(GrowFromCenter(m))
                (added if added is not None else []).append(m)
        self.state = state
        return anims

    # ── emphasis ────────────────────────────────────────────────────────
    def mobs_in(self, clearing, faction=None, kind=None):
        out = []
        for pid, m in self.blocks.items():
            p = self._piece_of[pid]
            if p not in self.state.pieces[clearing]:
                continue
            if faction and p.faction != faction:
                continue
            if kind and p.kind != kind:
                continue
            out.append(m)
        return out

    def highlight(self, *clearings, opacity=1.0, width=3.0):
        return [self.rings[c].animate.set_stroke(C_EMPH, width, opacity=opacity)
                for c in clearings]

    def unhighlight(self, *clearings):
        cs = clearings or tuple(self.rings)
        return [self.rings[c].animate.set_stroke(opacity=0.0) for c in cs]

    def ring_group(self):
        return VGroup(*self.rings.values())

    def suit_ring_group(self):
        return VGroup(*self.suit_rings.values())

    def flash_suit(self, suit, up=True):
        """Name a suit by lighting its rims, never by flooding its fill."""
        return [self.suit_rings[c.id].animate.set_stroke(
            SUIT_BRIGHT[suit], 5.0 if up else 2.6, opacity=1.0 if up else 0.60)
            for c in self.map if c.suit == suit]

    def slot_group(self):
        return VGroup(*[g for g in self.slot_marks.values()])

    def ruin_group(self):
        return Group(*self.ruins.values())

    # ── readouts ────────────────────────────────────────────────────────
    def others(self, *clearings):
        """Everything on the board except those clearings - the dim layer."""
        keep = set(clearings)
        g = Group(self.paths, self.river)
        for cid, disc in self.discs.items():
            if cid not in keep:
                g.add(disc)
        for cid in self.ruins:
            if cid not in keep:
                g.add(self.ruins[cid])
        for pid, m in self.blocks.items():
            p = self._piece_of[pid]
            if not any(p in self.state.pieces[c] for c in keep):
                g.add(m)
        return g

    def tower_top(self, clearing, faction):
        """World point just above a faction's tower - where a label goes."""
        h = self.state.presence(clearing, faction)
        return world(self.map[clearing]) + np.array(
            [0, TOWER_DY, BLOCK_H * h + 0.16])


# ── the flat layout, and why there are two ───────────────────────────────
# A board on a table is a scatter: pieces sit side by side in a clearing and
# you count them. That is the view the video opens in, and it is the view in
# which "who rules this clearing?" is a genuinely hard question. The gather
# into towers is a separate, visible move, and the camera tilt after it is
# what turns counting into seeing.
_FLAT_RING = [np.array([0.0, 0.0, 0.0])] + [
    np.array([np.cos(a), np.sin(a) * 0.72, 0.0]) * r
    for r, n, off in ((0.40, 6, 0.0), (0.68, 8, 0.4))
    for a in (np.linspace(0, TAU, n, endpoint=False) + off)
]


def _flat_offset(i):
    return _FLAT_RING[i % len(_FLAT_RING)]


def _layout_flat(view, state):
    out = {}
    for c in view.map:
        centre = world(c)
        ordered = []
        for f in FACTION_ORDER:
            ordered += [p for p in state.pieces[c.id]
                        if p.faction == f and COUNTS_FOR_RULE[p.kind]]
        for i, p in enumerate(ordered):
            out[p] = centre + _flat_offset(i) + np.array([0, 0, BLOCK_H / 2])
        flats = [p for p in state.pieces[c.id] if not COUNTS_FOR_RULE[p.kind]]
        m = len(flats)
        for j, p in enumerate(flats):
            out[p] = centre + np.array(
                [(j - (m - 1) / 2) * FLAT_DX, FLAT_Y, 0.018])
    return out


_tower_layout = BoardView.layout


def _layout(self, state=None, flat=False):
    state = state or self.state
    return _layout_flat(self, state) if flat else _tower_layout(self, state)


def _build(self, state=None, flat=False):
    state = state or self.state
    pos = self.layout(state, flat=flat)
    for p, xyz in pos.items():
        m = self._make_block(p).move_to(xyz)
        self.blocks[id(p)] = m
        self._piece_of[id(p)] = p
        self.pieces.add(m)
    return self.pieces


def _sync(self, state, flat=False, added=None, removed=None):
    pos = self.layout(state, flat=flat)
    anims, live = [], {id(p) for p in pos}
    for pid in list(self.blocks):
        if pid not in live:
            m = self.blocks.pop(pid)
            self._piece_of.pop(pid, None)
            anims.append(FadeOut(m, scale=0.2))
            if removed is not None:
                removed.append(m)
    for p, xyz in pos.items():
        if id(p) in self.blocks:
            m = self.blocks[id(p)]
            if np.linalg.norm(m.get_center() - xyz) > 1e-4:
                anims.append(m.animate.move_to(xyz))
        else:
            m = self._make_block(p).move_to(xyz)
            self.blocks[id(p)] = m
            self._piece_of[id(p)] = p
            self.pieces.add(m)
            anims.append(GrowFromCenter(m))
            if added is not None:
                added.append(m)
    self.state = state
    return anims


BoardView.layout = _layout
BoardView.build = _build
BoardView.sync = _sync


# ── HUD ──────────────────────────────────────────────────────────────────
# Everything below is fixed in frame: it is a heads-up display, not scenery,
# so it must ignore the camera entirely (three_d.md §4).

class ScoreTrack:
    """3.1: one track, thirty spaces, and whoever reaches it first wins."""

    X0, X1, Y = -6.05, 6.05, -3.36

    def __init__(self, factions):
        self.factions = list(factions)
        self.line = Line([self.X0, self.Y, 0], [self.X1, self.Y, 0])
        self.line.set_stroke(C_HUD, 2.0, opacity=0.75)
        self.ticks = VGroup()
        for i in range(31):
            t = Line([self.x(i), self.Y - 0.07, 0], [self.x(i), self.Y + 0.07, 0])
            t.set_stroke(C_HUD, 1.6, opacity=0.35 if i % 5 else 0.80)
            self.ticks.add(t)
        self.zero = Text("0", font=FONT, font_size=21).set_color(C_HUD)
        self.zero.move_to([self.X0, self.Y - 0.32, 0])
        self.thirty = Text("30", font=FONT, font_size=21).set_color(C_HUD)
        self.thirty.move_to([self.X1, self.Y - 0.32, 0])
        self.markers = {}
        for k, f in enumerate(self.factions):
            m = Triangle().set_height(0.28)
            m.set_fill(FACTION_COLOR[f], 1).set_stroke(BLACK, 1.2)
            m.rotate(PI)
            m.move_to([self.x(0), self.Y + 0.30 + 0.012 * k, 0])
            self.markers[f] = m
        self.group = VGroup(self.line, self.ticks, self.zero, self.thirty,
                            *self.markers.values())

    def x(self, vp):
        return self.X0 + (self.X1 - self.X0) * min(vp, 30) / 30

    def move_to_vp(self, vp: dict):
        """Animations sliding each marker to its faction's score."""
        out = []
        for f, m in self.markers.items():
            if f in vp:
                out.append(m.animate.move_to(
                    [self.x(vp[f]), m.get_center()[1], 0]))
        return out


def suit_legend():
    """Three ground colours, named. Fixed in frame."""
    g = VGroup()
    for i, s in enumerate((FOX, RABBIT, MOUSE)):
        d = Circle(radius=0.13).set_fill(SUIT_COLOR[s], 1)
        d.set_stroke(SUIT_BRIGHT[s], 2.0)
        lab = Text(s, font=FONT, font_size=21).set_color(C_HUD)
        lab.next_to(d, RIGHT, buff=0.16)
        g.add(VGroup(d, lab).arrange(RIGHT, buff=0.16))
    g.arrange(RIGHT, buff=0.62)
    return g


def piece_legend():
    """2.8, as four icons: what has height and what does not."""
    rows = [("warrior", 0.26, True), ("building", 0.40, True),
            ("token", None, False), ("pawn", None, False)]
    g = VGroup()
    for name, side, counts in rows:
        if side is not None:
            icon = VGroup(
                Rectangle(width=side, height=0.30).set_fill(C_HUD, 0.85)
                .set_stroke(width=0))
        else:
            icon = VGroup(Circle(radius=0.15).set_fill(C_HUD, 0.85)
                          .set_stroke(width=0))
            icon.shift(DOWN * 0.11)
        lab = Text(name, font=FONT, font_size=20).set_color(C_HUD)
        mark = Text("counts" if counts else "does not count",
                    font=FONT, font_size=18)
        mark.set_color(WHITE if counts else GREY_C)
        col = VGroup(icon, lab, mark).arrange(DOWN, buff=0.14)
        g.add(col)
    g.arrange(RIGHT, buff=0.78)
    return g


def die(value):
    """One of the two battle dice. 4.3.2."""
    box = RoundedRectangle(width=0.78, height=0.78, corner_radius=0.13)
    box.set_fill("#111111", 1).set_stroke(C_HUD, 2.2)
    n = Text(str(value), font=FONT, font_size=40).set_color(WHITE)
    n.move_to(box)
    return VGroup(box, n)
