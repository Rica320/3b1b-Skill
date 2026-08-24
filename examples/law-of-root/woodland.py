"""
The Woodland: the map, the pieces, and the rules that decide who holds what.

This is a real model, not a set of poses. Every board position the video shows
is a state of this module, every action it animates is checked legal here
first, and every rule claim the narration makes is re-derived from here by
verify_root.py. An illegal position cannot be represented and an illegal action
raises.

Rule numbers refer to The Law of Root (Third Printing), as supplied in
"The Law of Root: A Woodland Game of Might and Right.html".

THE MAP
    The supplied board photo is 608x504 and shot at an angle; its adjacency and
    suits cannot be read off it. This map is therefore structurally faithful
    rather than a copy: twelve clearings, four of each suit, four corner
    clearings, four ruins, and a river - all of which the rules reference
    guarantees or implies - laid out for legibility at a tilted camera.
    Nothing the video says depends on a specific printed adjacency. To use the
    real autumn map, replace CLEARINGS and PATHS; nothing else changes.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# ── suits ────────────────────────────────────────────────────────────────
# 2.1 Cards: "Each card has a suit: bird, fox, rabbit, or mouse."
# 2.2.2 Suit: "Every clearing has a suit of mouse, rabbit, or fox."
FOX, RABBIT, MOUSE, BIRD = "fox", "rabbit", "mouse", "bird"
CLEARING_SUITS = (FOX, RABBIT, MOUSE)
CARD_SUITS = (FOX, RABBIT, MOUSE, BIRD)

# ── factions ─────────────────────────────────────────────────────────────
MARQUISE, EYRIE, ALLIANCE, VAGABOND, CULT, RIVERFOLK = (
    "marquise", "eyrie", "alliance", "vagabond", "cult", "riverfolk")

FACTION_NAME = {
    MARQUISE:  "Marquise de Cat",
    EYRIE:     "Eyrie Dynasties",
    ALLIANCE:  "Woodland Alliance",
    VAGABOND:  "Vagabond",
    CULT:      "Lizard Cult",
    RIVERFOLK: "Riverfolk Company",
}

# ── the map ──────────────────────────────────────────────────────────────
# (id, suit, x, y, slots, is_corner, has_ruin).  x, y are in [-1, 1] board
# space; the scene scales them.  Ruins occupy one slot each (2.2.4).
CLEARINGS = [
    (1,  FOX,    -0.85,  0.85, 2, True,  False),
    (2,  MOUSE,  -0.05,  0.92, 2, False, False),
    (3,  RABBIT,  0.85,  0.85, 2, True,  False),
    (4,  MOUSE,  -0.88,  0.18, 1, False, False),
    (5,  RABBIT, -0.22,  0.40, 3, False, True),
    (6,  FOX,     0.33,  0.32, 2, False, True),
    (7,  MOUSE,   0.88,  0.20, 1, False, False),
    (8,  FOX,    -0.42, -0.28, 2, False, True),
    (9,  RABBIT,  0.15, -0.18, 3, False, False),
    (10, RABBIT, -0.85, -0.85, 2, True,  False),
    (11, MOUSE,  -0.02, -0.88, 2, False, True),
    (12, FOX,     0.85, -0.85, 1, True,  False),
]

PATHS = [
    (1, 2), (1, 4), (1, 5),
    (2, 3), (2, 5), (2, 6),
    (3, 6), (3, 7),
    (4, 5), (4, 8),
    (5, 6), (5, 9),
    (6, 7), (6, 9),
    (7, 9), (7, 12),
    (8, 9), (8, 10), (8, 11),
    (9, 11), (9, 12),
    (10, 11),
    (11, 12),
]

# 2.3 Rivers "act as paths for only the Riverfolk Company."  The ribbon runs
# through these clearings in order.
RIVER = [2, 5, 9, 11, 10]

# Diagonally opposite corner pairs - the keep and the Eyrie's first roost
# (6.9.2, 7.4.2), and bird dominance (3.3.3).
OPPOSITE_CORNERS = [(1, 12), (3, 10)]


def matches(card_suit, clearing_suit, reverse=False):
    """2.1.1 Birds Are Wild, and 2.1.3 Reverse Substitution.

    A bird card can always be treated as any other suit. The substitution
    does not run the other way: if a rule asks for a bird card, only a bird
    card will do.
    """
    if reverse:
        return card_suit == clearing_suit
    return card_suit == clearing_suit or card_suit == BIRD


@dataclass(frozen=True)
class Clearing:
    id: int
    suit: str
    x: float
    y: float
    slots: int
    corner: bool
    ruin: bool


class Map:
    """Clearings and paths.  2.2."""

    def __init__(self, clearings=CLEARINGS, paths=PATHS, river=RIVER):
        self.clearings = {c[0]: Clearing(*c) for c in clearings}
        self.paths = [tuple(sorted(p)) for p in paths]
        self.river = list(river)
        self._adj = {i: set() for i in self.clearings}
        for a, b in self.paths:
            if a not in self.clearings or b not in self.clearings:
                raise ValueError(f"path {a}-{b} names a clearing that is not on the map")
            self._adj[a].add(b)
            self._adj[b].add(a)
        self._river_adj = {i: set() for i in self.clearings}
        for a, b in zip(self.river, self.river[1:]):
            self._river_adj[a].add(b)
            self._river_adj[b].add(a)

    def __iter__(self):
        return iter(self.clearings.values())

    def __getitem__(self, i) -> Clearing:
        return self.clearings[i]

    def adjacent(self, a, b) -> bool:
        """2.2.1 Adjacency: linked by a path."""
        return b in self._adj[a]

    def neighbours(self, a):
        return sorted(self._adj[a])

    def river_adjacent(self, a, b) -> bool:
        """2.3 Rivers: paths for the Riverfolk only."""
        return b in self._river_adj[a]

    def of_suit(self, suit):
        return [c for c in self.clearings.values() if c.suit == suit]

    def corners(self):
        return [c for c in self.clearings.values() if c.corner]

    def connected(self) -> bool:
        seen, stack = {1}, [1]
        while stack:
            for n in self._adj[stack.pop()]:
                if n not in seen:
                    seen.add(n)
                    stack.append(n)
        return len(seen) == len(self.clearings)


MAP = Map()

# ── pieces ───────────────────────────────────────────────────────────────
# 2.5 Pieces.  Only warriors and buildings have "height": 2.8 counts warriors
# and buildings toward rule, and explicitly excludes tokens and pawns.  That
# distinction is the whole visual grammar of the video, so it lives here.
WARRIOR, BUILDING, TOKEN, PAWN = "warrior", "building", "token", "pawn"
COUNTS_FOR_RULE = {WARRIOR: True, BUILDING: True, TOKEN: False, PAWN: False}


@dataclass(eq=False)          # identity, not value: the view tracks pieces by object
class Piece:
    faction: str
    kind: str          # WARRIOR | BUILDING | TOKEN | PAWN
    name: str = ""     # "sawmill", "roost", "sympathy", "keep", ...


class IllegalAction(Exception):
    pass


@dataclass
class State:
    """A position.  Pieces live in clearings; scores live on the track."""

    map: Map = field(default_factory=lambda: MAP)
    pieces: dict = field(default_factory=dict)      # clearing id -> [Piece]
    vp: dict = field(default_factory=dict)          # faction -> int
    wood: dict = field(default_factory=dict)        # clearing id -> int
    supporters: list = field(default_factory=list)  # Alliance supporters stack
    hands: dict = field(default_factory=dict)       # faction -> [suit]
    log: list = field(default_factory=list)

    def __post_init__(self):
        for c in self.map.clearings:
            self.pieces.setdefault(c, [])
            self.wood.setdefault(c, 0)

    # ── inspection ───────────────────────────────────────────────────────
    def at(self, clearing, faction=None, kind=None):
        out = self.pieces[clearing]
        if faction is not None:
            out = [p for p in out if p.faction == faction]
        if kind is not None:
            out = [p for p in out if p.kind == kind]
        return list(out)

    def warriors(self, clearing, faction):
        return len(self.at(clearing, faction, WARRIOR))

    def buildings(self, clearing, faction=None):
        return len(self.at(clearing, faction, BUILDING))

    def open_slots(self, clearing):
        """2.2.3 Slots.  A ruin fills one (2.2.4)."""
        c = self.map[clearing]
        used = self.buildings(clearing) + (1 if c.ruin else 0)
        return c.slots - used

    def factions_present(self, clearing):
        return sorted({p.faction for p in self.pieces[clearing]})

    # ── 2.8 Ruler ────────────────────────────────────────────────────────
    def presence(self, clearing, faction):
        """"the most total warriors and buildings in that clearing"."""
        return sum(1 for p in self.pieces[clearing]
                   if p.faction == faction and COUNTS_FOR_RULE[p.kind])

    def presences(self, clearing):
        return {f: self.presence(clearing, f)
                for f in self.factions_present(clearing)
                if self.presence(clearing, f) > 0}

    def ruler(self, clearing, variant=True):
        """2.8 Ruler.  Strict most; a tie means no one rules.

        variant=True applies the two faction rules that overwrite this
        sentence, in the precedence the rules give them:
          10.2.4 Pilgrims - the Cult rules any clearing where it has a garden,
                 and this "overrides the Eyrie's Lords of the Forest";
          7.2.2  Lords of the Forest - the Eyrie rule when *tied* for most,
                 but never an empty clearing.
        """
        p = self.presences(clearing)
        if variant and any(x.faction == CULT and x.name == "garden"
                           for x in self.pieces[clearing]):
            return CULT
        if not p:
            return None                      # nobody is in it: nobody rules it
        top = max(p.values())
        leaders = [f for f, n in p.items() if n == top]
        if len(leaders) == 1:
            return leaders[0]
        if variant and EYRIE in leaders:
            return EYRIE                     # 7.2.2, and never an empty clearing
        return None                          # 2.8: a tie means no ruler

    def rules(self, faction, clearing, variant=True):
        return self.ruler(clearing, variant=variant) == faction

    # ── 4.2 Move ─────────────────────────────────────────────────────────
    def can_move(self, faction, src, dst, riverboats=False):
        """4.2 Move, with the two faction exceptions to 4.2.1.

        Returns (ok, reason).
        """
        if faction == VAGABOND:
            # 9.2.3 Nimble - "regardless of who rules his origin or
            # destination clearing".
            if not self.map.adjacent(src, dst):
                return False, "not adjacent"
            return True, "Nimble (9.2.3): rule is not required"
        by_river = self.map.river_adjacent(src, dst)
        if not self.map.adjacent(src, dst):
            # 11.2.2 Swimmers - the Riverfolk treat rivers as paths.
            if not (by_river and (faction == RIVERFOLK or riverboats)):
                return False, "not adjacent"
        if self.warriors(src, faction) == 0:
            return False, "no warriors in the origin clearing"
        if faction == RIVERFOLK and by_river:
            # 11.2.2 - "regardless of who rules their origin or destination".
            return True, "Swimmers (11.2.2): rule is not required along a river"
        if self.rules(faction, src) or self.rules(faction, dst):
            return True, "4.2.1: rules the origin or the destination"
        return False, "4.2.1: must rule the origin clearing, the destination, or both"

    def move(self, faction, src, dst, n, riverboats=False):
        ok, why = self.can_move(faction, src, dst, riverboats)
        if not ok:
            raise IllegalAction(f"move {faction} {src}->{dst}: {why}")
        have = self.warriors(src, faction)
        if n > have:
            raise IllegalAction(f"move {faction} {src}->{dst}: only {have} warriors there")
        moved = 0
        for p in list(self.pieces[src]):
            if moved == n:
                break
            if p.faction == faction and p.kind == WARRIOR:
                self.pieces[src].remove(p)
                self.pieces[dst].append(p)
                moved += 1
        outraged = self.outrage_triggered(faction, dst)
        self.log.append(f"{faction}: move {n} {src}->{dst} ({why})")
        return outraged

    # ── 8.2.6 Outrage ────────────────────────────────────────────────────
    def outrage_triggered(self, faction, clearing):
        """"Whenever another player ... moves any warriors into a sympathetic
        clearing, they must add one card matching the affected clearing ... to
        the Supporters stack." """
        if faction == ALLIANCE:
            return False
        return any(p.faction == ALLIANCE and p.name == "sympathy"
                   for p in self.pieces[clearing])

    # ── 4.3 Battle ───────────────────────────────────────────────────────
    def battle(self, attacker, defender, clearing, rolls=None, rng=None,
               attacker_extra=0, defender_extra=0):
        """4.3 Battle.  Returns a dict describing every step.

        4.3.2.II  attacker deals the higher roll, defender the lower
        4.3.2.I   maximum rolled hits = your warriors in the clearing
        4.3.2.III defenceless: defender has no warriors there -> attacker +1
        4.3.3     hits are dealt simultaneously; the player taking hits must
                  remove all their warriors before any building or token
        3.2.1     one VP per enemy building or token removed
        8.2.2     Guerrilla War: as defender, the Alliance deals the HIGHER
                  roll and the attacker the lower
        """
        if not self.at(clearing, attacker):
            raise IllegalAction("attacker has no pieces in the clearing of battle")
        if not self.at(clearing, defender):
            raise IllegalAction("defender has no pieces in the clearing of battle")
        if attacker == defender:
            raise IllegalAction("a faction cannot battle itself")

        rng = rng or random
        if rolls is None:
            rolls = (rng.randint(0, 3), rng.randint(0, 3))
        hi, lo = max(rolls), min(rolls)

        if defender == ALLIANCE:
            atk_roll, def_roll = lo, hi          # 8.2.2 Guerrilla War
            guerrilla = True
        else:
            atk_roll, def_roll = hi, lo
            guerrilla = False

        atk_warriors = self.warriors(clearing, attacker)
        def_warriors = self.warriors(clearing, defender)
        atk_capped = min(atk_roll, atk_warriors)   # 4.3.2.I
        def_capped = min(def_roll, def_warriors)

        defenceless = def_warriors == 0            # 4.3.2.III
        atk_hits = atk_capped + attacker_extra + (1 if defenceless else 0)
        def_hits = def_capped + defender_extra

        # 4.3.3 simultaneous: both removal lists are computed from the state
        # as it stood before either side removed anything.
        atk_removed = self._plan_removal(clearing, defender, atk_hits)
        def_removed = self._plan_removal(clearing, attacker, def_hits)
        for p in atk_removed + def_removed:
            self.pieces[clearing].remove(p)

        atk_vp = sum(1 for p in atk_removed if p.kind in (BUILDING, TOKEN))
        def_vp = sum(1 for p in def_removed if p.kind in (BUILDING, TOKEN))
        self.vp[attacker] = self.vp.get(attacker, 0) + atk_vp
        self.vp[defender] = self.vp.get(defender, 0) + def_vp

        self.log.append(
            f"battle in {clearing}: {attacker} vs {defender} rolled {rolls} -> "
            f"{atk_hits}/{def_hits} hits")
        return dict(
            clearing=clearing, attacker=attacker, defender=defender,
            rolls=(hi, lo), guerrilla=guerrilla,
            attacker_roll=atk_roll, defender_roll=def_roll,
            attacker_warriors=atk_warriors, defender_warriors=def_warriors,
            attacker_capped=atk_capped, defender_capped=def_capped,
            defenceless=defenceless,
            attacker_hits=atk_hits, defender_hits=def_hits,
            attacker_removed=atk_removed, defender_removed=def_removed,
            attacker_vp=atk_vp, defender_vp=def_vp,
        )

    def _plan_removal(self, clearing, victim, hits):
        """4.3.3: warriors first, then buildings and tokens in any order."""
        pool = self.at(clearing, victim)
        warriors = [p for p in pool if p.kind == WARRIOR]
        rest = [p for p in pool if p.kind in (BUILDING, TOKEN)]
        return (warriors + rest)[:hits]

    # ── scoring ──────────────────────────────────────────────────────────
    def score(self, faction, points, why=""):
        self.vp[faction] = self.vp.get(faction, 0) + points
        self.log.append(f"{faction}: +{points} VP {why}".rstrip())
        return self.vp[faction]

    def winner(self):
        """3.1: the first player to reach 30 victory points immediately wins."""
        for f, v in self.vp.items():
            if v >= 30:
                return f
        return None

    # ── placement helpers (each checks the rule that constrains it) ──────
    def place_warrior(self, faction, clearing, n=1):
        for _ in range(n):
            self.pieces[clearing].append(Piece(faction, WARRIOR))

    def place_building(self, faction, clearing, name):
        if self.open_slots(clearing) < 1:
            raise IllegalAction(
                f"2.2.3: no open slot in clearing {clearing} for a {name}")
        self.pieces[clearing].append(Piece(faction, BUILDING, name))

    def place_token(self, faction, clearing, name):
        if name == "sympathy":
            # 8.2.5.I: "A clearing can hold only one sympathy token."
            if any(p.name == "sympathy" for p in self.pieces[clearing]):
                raise IllegalAction("8.2.5.I: clearing already has sympathy")
        self.pieces[clearing].append(Piece(faction, TOKEN, name))

    def place_pawn(self, clearing):
        self.pieces[clearing].append(Piece(VAGABOND, PAWN, "vagabond"))

    def remove_all_enemies(self, faction, clearing):
        """8.4.1.III Revolt: "Remove all enemy pieces in the chosen clearing." """
        gone = [p for p in self.pieces[clearing] if p.faction != faction]
        for p in gone:
            self.pieces[clearing].remove(p)
        # 3.2.1: one VP per enemy building or token removed.
        pts = sum(1 for p in gone if p.kind in (BUILDING, TOKEN))
        if pts:
            self.score(faction, pts, "(3.2.1: enemy buildings and tokens)")
        return gone, pts

    def clone(self):
        import copy
        return copy.deepcopy(self)


# ── 6.9 / 7.4 / 8.8  Faction setup ───────────────────────────────────────
def standard_setup(keep_corner=1, eyrie_corner=12) -> State:
    """The three factions the video plays: Marquise, Eyrie, Alliance.

    6.9.2  keep in the corner clearing of your choice
    6.9.3  a warrior in each clearing except the diagonally opposite corner
    6.9.4  1 sawmill, 1 workshop, 1 recruiter among the keep clearing and any
           adjacent clearings, in any combination
    7.4.2  1 roost and 6 warriors in the corner diagonally opposite the keep
    8.8    the Alliance places nothing on the map; it draws 3 supporters
    """
    if (min(keep_corner, eyrie_corner), max(keep_corner, eyrie_corner)) not in [
            tuple(sorted(p)) for p in OPPOSITE_CORNERS]:
        raise IllegalAction("7.4.2: the Eyrie start diagonally opposite the keep")

    s = State()
    s.vp = {MARQUISE: 0, EYRIE: 0, ALLIANCE: 0}

    s.place_token(MARQUISE, keep_corner, "keep")
    for c in s.map.clearings:
        if c != eyrie_corner:
            s.place_warrior(MARQUISE, c)
    s.place_building(MARQUISE, keep_corner, "sawmill")
    s.place_building(MARQUISE, keep_corner, "workshop")
    s.place_building(MARQUISE, 5, "recruiter")

    s.place_building(EYRIE, eyrie_corner, "roost")
    s.place_warrior(EYRIE, eyrie_corner, 6)

    s.supporters = [FOX, RABBIT, MOUSE]          # 8.8.4: draw 3
    return s
