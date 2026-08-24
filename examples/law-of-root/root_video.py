"""
"No two players in Root are playing by the same rules. So what makes it one
game?"

A narrated 3D explainer of Root's rules, built on a real rules model: every
position is a state of woodland.py, every action in the worked game is checked
legal before it is animated, and every claim the narration makes is re-derived
in verify_root.py.

    TTS:     ../../env/bin/python ../../skills/3b1b-math-animation/scripts/tts.py \
                 script.yaml --out audio
    Render:  bash ../../skills/3b1b-math-animation/scripts/render.sh root_video.py LawOfRoot
    Mux:     ../../env/bin/python ../../skills/3b1b-math-animation/scripts/mux_audio.py \
                 videos/LawOfRoot.mp4 --cues narration_cues.json
    Verify:  ../../env/bin/python ../../skills/3b1b-math-animation/scripts/verify_render.py \
                 videos/LawOfRoot.mp4 --meta render_meta.json
             ../../env/bin/python ../../skills/3b1b-math-animation/scripts/verify_audio.py \
                 videos/LawOfRoot_narrated.mp4 --cues narration_cues.json
             ../../env/bin/python verify_root.py

Spine
  QUESTION    six factions, six rulebooks. What makes it one game?
  MOTIVATION  the obvious answer - they share a thirty-point scoreboard - is
              not enough: four private engines in four corners is a race, not
              a war. Something has to force them into the same room.
  BUILD       the map does, through one sentence (2.8): the ruler of a
              clearing is whoever has the most warriors and buildings in it.
              Move needs it, building needs it, crafting is paid in clearings.
  PAYOFF      every faction in the box is an edit to that one sentence. They
              are not playing different games; they are playing different
              answers to the same question - who holds this clearing?

Carried metaphor: THE SKYLINE. Warriors and buildings have height because
those are the two things 2.8 counts; tokens and pawns lie flat because 2.8
excludes them. Tower heights are computed from the state, never authored, so
an impossible skyline cannot be drawn.

The one camera move that is an argument: the video opens top-down, where a
clearing is a scatter you have to count, and tilts to 60 degrees once the
pieces have been gathered into towers - after which rule is something you see
rather than something you work out.

Colour
  Faction colours belong to the factions; nothing else uses them, and emphasis
  is applied by dimming plus a white ring rather than by tinting - which is
  also why YELLOW is not an emphasis colour here (it is the Lizard Cult).
  The ground carries the printed board's suit hues pulled far down in value.
"""

import os
import sys
from pathlib import Path

import numpy as np
from manimlib import *

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1] / "skills" / "3b1b-math-animation"
                      / "scripts"))

import board_view as bv                                       # noqa: E402
import demo_game as dg                                        # noqa: E402
import woodland as w                                          # noqa: E402
from woodland import (MARQUISE, EYRIE, ALLIANCE, VAGABOND, CULT,             # noqa: E402
                      RIVERFOLK, FOX, RABBIT, MOUSE, FACTION_NAME)
from manim_helpers import (                                   # noqa: E402
    Caption, Dimmer, hold, stagger, dump_meta, fix, flat, orient, orbit,
    audit_text_overlaps, assert_in_frame_3d, FONT,
)
from narration import Narrator                                # noqa: E402

FC = bv.FACTION_COLOR
C_HUD = bv.C_HUD
DIM = 0.14

THETA, PHI = 0, 60         # square-on, so the map still reads as a map
FLAT_H, TILT_H = 10.6, 8.0   # frame height before and after the tilt
FLAT_C = [0, 0.10, 0]        # seen from above, the map needs the room
ASSETS = _HERE / "assets"

SHORT = {MARQUISE: "Marquise", EYRIE: "Eyrie", ALLIANCE: "Alliance",
         VAGABOND: "Vagabond", CULT: "Lizard Cult", RIVERFOLK: "Riverfolk"}

CREST = {MARQUISE: "Faction_M.png", EYRIE: "Faction_E.png",
         ALLIANCE: "Faction_A.png", VAGABOND: "Faction_V.png",
         CULT: "Faction_L.png", RIVERFOLK: "Faction_O.png"}
SIX = [MARQUISE, EYRIE, ALLIANCE, VAGABOND, CULT, RIVERFOLK]


def crest(faction, height=0.62):
    return ImageMobject(str(ASSETS / CREST[faction]), height=height)


def hud_text(s, size=24, color=C_HUD):
    return Text(s, font=FONT, font_size=size).set_color(color)


class LawOfRoot(ThreeDScene):

    # ── plumbing ────────────────────────────────────────────────────────
    def wait(self, *args, **kwargs):
        r = super().wait(*args, **kwargs)
        if os.environ.get("AUDIT"):
            audit_text_overlaps(self)
        return r

    def construct(self):
        self.camera.background_color = BLACK
        self.nar = Narrator(_HERE / "script.yaml", _HERE / "audio")
        self.cap = Caption(self, narrator=self.nar)

        self.steps = {s[0]: s for s in dg.steps()}
        self.order = [s[0] for s in dg.steps()]
        self.S0 = self.steps["setup"][2]

        orient(self, theta=THETA, phi=0, center=FLAT_C, height=FLAT_H)
        self.camera.frame.set_focal_distance(24.0)

        self.s0_question()
        self.s1_scoreboard()
        self.s2_ground()
        self.s3_permission()
        self.s4_battle()
        self.s5_factions()
        self.s6_game()
        self.s7_payoff()

        dump_meta(self, str(_HERE / "render_meta.json"))
        self.nar.dump(_HERE / "narration_cues.json", scene=self)
        self.nar.report()

    # a focused inset: dim everything but these clearings, run body, restore
    def focus(self, *clearings, run_time=0.7):
        d = Dimmer(self.view.others(*clearings))
        self.play(*d.to(DIM), run_time=run_time)
        return d

    def unfocus(self, d, run_time=0.7):
        self.play(*d.restore(), run_time=run_time)

    def revert(self, state, run_time=1.0, flat=False):
        """Put the board back to `state` after a suppose-this demonstration."""
        anims = self.view.sync(state, flat=flat)
        if anims:
            self.play(*anims, run_time=run_time)

    # ── §0  the question ────────────────────────────────────────────────
    def s0_question(self):
        photo = ImageMobject(str(ASSETS / "board_dark.png"), height=6.9)
        fix(photo)
        title = fix(hud_text("The Law of Root", size=62, color=WHITE)
                    .move_to([0, 0.55, 0]))
        sub = fix(hud_text("a woodland game of might and right", size=27)
                  .move_to([0, -0.25, 0]))
        assert_in_frame_3d(self, photo=photo, title=title, sub=sub)

        self.nar.cue(self, "s0.open")
        self.play(FadeIn(photo, run_time=1.6))
        self.play(Write(title), run_time=1.4)
        self.play(FadeIn(sub, shift=UP * 0.12), run_time=0.8)
        self.nar.finish(self)

        self.crests = Group()
        for f in SIX:
            c = crest(f)
            name = hud_text(SHORT[f], size=19)
            name.next_to(c, DOWN, buff=0.26)
            self.crests.add(Group(c, name))
        self.crests.arrange(RIGHT, buff=0.78)
        self.crests.move_to([0, -2.60, 0])
        fix(*self.crests, *[m for g in self.crests for m in g])

        dim_title = Dimmer(title, sub)
        self.cap.show("Six factions. Six rulebooks.", "s0.asym", hold=False)
        self.play(photo.animate.set_height(4.7).move_to([0, 0.85, 0]),
                  Group(title, sub).animate.move_to([0, 0.85, 0]),
                  *dim_title.to(0.35), run_time=1.1)
        self.play(stagger([FadeIn(g, shift=UP * 0.2) for g in self.crests],
                          lag_ratio=0.14), run_time=2.0)
        self.nar.finish(self)

        rings = Group()
        for f, g in zip(SIX, self.crests):
            r = Circle(radius=0.40).set_stroke(FC[f], 3.0).set_fill(opacity=0)
            r.move_to(g[0])
            fix(r)
            rings.add(r)
        self.nar.cue(self, "s0.pieces")
        self.play(stagger([ShowCreation(r) for r in rings], lag_ratio=0.12),
                  run_time=1.8)
        self.nar.finish(self)

        # The driving question, alone on the frame.
        self.q_text = fix(hud_text(
            "No two players are playing by the same rules.\n"
            "So what makes it one game?", size=40, color=WHITE)
            .move_to([0, 0.35, 0]))
        self.cap.clear(run_time=0.4)
        self.nar.cue(self, "s0.question")
        self.play(FadeOut(title), FadeOut(sub),
                  *Dimmer(photo).to(0.10), run_time=0.9)
        self.play(Write(self.q_text), run_time=2.0)
        self.nar.finish(self)
        self.nar.silence(self, 1.6)          # let the question sit

        self.photo = photo
        self.rings0 = rings

    # ── §1  the obvious answer, and how it fails ────────────────────────
    def s1_scoreboard(self):
        self.track = bv.ScoreTrack([MARQUISE, EYRIE, ALLIANCE])
        fix(*self.track.group)
        thirty_box = fix(Circle(radius=0.30)
                         .set_stroke(WHITE, 2.6).set_fill(opacity=0)
                         .move_to([self.track.X1, self.track.Y, 0]))

        self.cap.show("One finish line.", "s1.obvious", hold=False)
        self.play(FadeOut(self.q_text, shift=UP * 0.3),
                  FadeOut(self.photo), run_time=0.8)
        self.play(ShowCreation(self.track.line),
                  stagger([ShowCreation(t) for t in self.track.ticks],
                          lag_ratio=0.012),
                  FadeIn(self.track.zero), FadeIn(self.track.thirty),
                  run_time=1.8)
        self.play(ShowCreation(thirty_box), run_time=0.7)
        self.play(stagger([FadeIn(self.track.markers[f], shift=UP * 0.2)
                           for f in (MARQUISE, EYRIE)], lag_ratio=0.2),
                  run_time=0.9)
        self.nar.finish(self)

        # The crests have done their work; the two corners that follow are
        # identified by colour, which is the video's whole colour contract.
        self.play(FadeOut(self.crests), FadeOut(self.rings0), run_time=0.8)

        # The pieces of the real setup, in their two corners, top-down and
        # flat: the same mobjects the rest of the video uses.
        self.view = bv.BoardView(self.S0)
        empty = w.State()
        empty.vp = dict(self.S0.vp)
        self.view.build(empty)
        self.add(self.view.pieces)

        corner = empty.clone()
        for p in self.S0.pieces[dg.KEEP]:
            corner.pieces[dg.KEEP].append(p)
        for p in self.S0.pieces[dg.EYRIE_CORNER]:
            corner.pieces[dg.EYRIE_CORNER].append(p)

        # The two corners are identified where they are. At phi=0 the map
        # projects linearly, so these positions are just world * 8 / FLAT_H.
        cat_c = crest(MARQUISE, height=0.60)
        bird_c = crest(EYRIE, height=0.60)
        cat_c.move_to([-3.45, 2.45, 0])
        bird_c.move_to([3.45, -2.55, 0])
        self.corner_crests = Group(cat_c, bird_c)
        fix(self.corner_crests, cat_c, bird_c)
        assert_in_frame_3d(self, corners=self.corner_crests)

        self.cap.show("Both scores climb. Nothing has made them meet.",
                      "s1.corners", hold=False)
        self.play(stagger([FadeIn(c, scale=0.7) for c in self.corner_crests],
                          lag_ratio=0.25), run_time=0.9)
        half = empty.clone()
        for p in self.S0.pieces[dg.KEEP][:2]:
            half.pieces[dg.KEEP].append(p)
        for p in self.S0.pieces[dg.EYRIE_CORNER][:3]:
            half.pieces[dg.EYRIE_CORNER].append(p)
        self.play(*self.view.sync(half, flat=True), run_time=1.3)
        self.play(*self.track.move_to_vp({MARQUISE: 4, EYRIE: 3}),
                  run_time=1.0)
        self.play(*self.view.sync(corner, flat=True), run_time=1.4)
        self.play(*self.track.move_to_vp({MARQUISE: 9, EYRIE: 8}),
                  run_time=1.2)
        self.nar.finish(self)

        divider = Line([-6.6, 3.0, 0], [6.6, -3.0, 0])
        divider.set_stroke(GREY_C, 2.0, opacity=0.55)
        fix(divider)
        self.cap.show("A race, not a war.", "s1.need", hold=False)
        self.play(ShowCreation(divider), run_time=1.0)
        hold(self, 1.2)
        # The hypothetical ends: the scores it invented go back to zero.
        self.play(FadeOut(divider), FadeOut(thirty_box),
                  FadeOut(self.corner_crests),
                  *self.track.move_to_vp({MARQUISE: 0, EYRIE: 0}),
                  run_time=1.1)
        self.nar.finish(self)
        self.corner_state = corner

    # ── §2  the ground, and one sentence ────────────────────────────────
    def s2_ground(self):
        self.cap.show("Clearings, joined by paths.", "s2.map", hold=False)
        self.play(stagger([GrowFromCenter(self.view.discs[c.id])
                           for c in self.view.map], lag_ratio=0.05),
                  run_time=2.2)
        self.play(stagger([ShowCreation(p) for p in self.view.paths],
                          lag_ratio=0.035), run_time=2.0)
        self.play(ShowCreation(self.view.river[0]), run_time=1.2)
        # Rings and slot marks live at zero opacity until something needs
        # them. They are added here so later animations have something on
        # stage to drive, and taken out of the depth test so they always draw
        # over the ground disc they sit on (ANTI-PATTERN #14).
        self.add(self.view.ring_group(), self.view.slot_group())
        flat(*self.view.ring_group(), *self.view.slot_group().get_family(),
             *self.view.suit_ring_group())
        self.nar.finish(self)

        legend = fix(bv.suit_legend().move_to([0, -3.05, 0]))
        self.cap.show("Fox, rabbit, mouse.", "s2.suit", hold=False)
        self.play(FadeIn(legend, shift=UP * 0.15), run_time=0.8)
        for suit in (FOX, RABBIT, MOUSE):
            self.play(stagger(self.view.flash_suit(suit), lag_ratio=0.06),
                      run_time=0.55)
            self.play(*self.view.flash_suit(suit, up=False), run_time=0.45)
        self.nar.finish(self)

        slots = self.view.slot_group()
        ruins = self.view.ruin_group()
        self.cap.show("Slots. Four of them start as ruins.", "s2.slots",
                      hold=False)
        self.play(stagger([m.animate.set_stroke(GREY_B, 1.8, opacity=0.9)
                           for m in slots.get_family() if m.has_points()],
                          lag_ratio=0.02), run_time=1.6)
        self.play(stagger([GrowFromCenter(r) for r in ruins], lag_ratio=0.15),
                  run_time=1.2)
        self.nar.finish(self)

        # The rest of the setup arrives: the garrison, the two other buildings.
        self.cap.show("The ruler of a clearing is the player with the most "
                      "warriors and buildings in it.", "s2.sentence",
                      hold=False, size=27)
        self.play(*self.view.sync(self.S0, flat=True), run_time=2.0)
        self.play(*[m.animate.set_stroke(opacity=0.0)
                    for m in slots.get_family() if m.has_points()],
                  FadeOut(legend), run_time=0.8)
        self.nar.finish(self)

        pl = fix(bv.piece_legend().move_to([0, -3.0, 0]))
        self.cap.show("Tokens do not count. Pawns do not count.",
                      "s2.notcount", hold=False)
        self.play(stagger([FadeIn(c, shift=UP * 0.15) for c in pl],
                          lag_ratio=0.16), run_time=1.5)
        self.nar.finish(self)

        # The problem the flat view cannot solve.
        d = self.focus(dg.FIELD, 5)
        self.play(FadeOut(pl), run_time=0.5)
        self.cap.show("Who rules this one?", "s2.cant", hold=False)
        self.play(*self.view.highlight(dg.FIELD, 5), run_time=0.8)
        hold(self, 1.6)
        self.nar.finish(self)
        self.play(*self.view.unhighlight(), run_time=0.5)
        self.unfocus(d)

        # Gather: the pieces that count become the pieces with height.
        self.cap.show("Let the pieces that count be the pieces with height.",
                      "s2.tilt", hold=False, size=27)
        self.play(*self.view.sync(self.S0, flat=False), run_time=2.4)
        self.nar.finish(self)

        # THE TILT. Nothing else moves: the geometry was always this shape.
        self.cap.show("Rule is a skyline.", "s2.skyline", hold=False)
        orbit(self, theta=THETA, phi=PHI, center=ORIGIN, height=TILT_H,
              run_time=3.6)
        self.nar.finish(self)
        orbit(self, theta=-13, phi=57, run_time=3.4)      # a wordless beat
        orbit(self, theta=THETA, phi=PHI, run_time=2.6)

    # ── §3  rule is a permission slip ───────────────────────────────────
    def s3_permission(self):
        SRC, DST = 5, dg.FIELD
        d = self.focus(SRC, DST)
        orbit(self, center=[-0.15, 0.30, 0], height=6.8, run_time=1.6)

        self.cap.show("Not a prize. A permission slip.", "s3.prize",
                      hold=False)
        self.play(*self.view.highlight(SRC, DST), run_time=0.8)
        self.nar.finish(self)

        # She rules the origin outright, so the move is legal (4.2.1).
        st = self.S0.clone()
        st.place_warrior(MARQUISE, SRC, 1)
        self.play(*self.view.sync(st), run_time=0.9)

        arrow = Arrow(bv.world(self.view.map[SRC]) + np.array([0, 0, 0.5]),
                      bv.world(self.view.map[DST]) + np.array([0, 0, 0.5]),
                      buff=0.35)
        arrow.set_fill(WHITE, 1).set_stroke(WHITE, 3.5)
        flat(arrow)
        ok = fix(hud_text("legal", size=28, color=WHITE)
                 .move_to([-4.6, 2.35, 0]))
        assert_in_frame_3d(self, ok=ok)

        self.cap.show("Rule the origin, the destination, or both.", "s3.move",
                      hold=False)
        self.play(GrowArrow(arrow), run_time=0.9)
        self.play(FadeIn(ok, shift=UP * 0.2), run_time=0.6)
        st2 = st.clone()
        st2.move(MARQUISE, SRC, DST, 2)
        self.play(*self.view.sync(st2), run_time=1.4)
        self.nar.finish(self)

        # Level the towers and the same move is illegal.
        st3 = st2.clone()
        st3.place_warrior(EYRIE, SRC, st3.presence(SRC, MARQUISE))
        self.cap.show("Level the towers, and it is not.", "s3.tie", hold=False)
        self.play(*self.view.sync(st3), run_time=1.2)
        no = fix(hud_text("illegal", size=28, color=GREY_B)
                 .move_to([-4.6, 2.35, 0]))
        bar = flat(Line(arrow.get_start(), arrow.get_end())
                   .set_stroke(GREY_C, 5.0, opacity=0.85))
        assert not st3.can_move(MARQUISE, SRC, DST)[0], "4.2.1"
        self.play(FadeOut(ok), FadeIn(no), FadeOut(arrow),
                  ShowCreation(bar), run_time=0.9)
        self.nar.finish(self)
        self.play(FadeOut(no), FadeOut(bar), run_time=0.5)

        # Build: a clearing you rule, and an open slot.
        st4 = st2.clone()
        marks = self.view.slot_marks[DST]
        self.cap.show("A clearing you rule, and an open slot.", "s3.build",
                      hold=False)
        self.play(*self.view.sync(st4), run_time=0.8)
        self.play(*[m.animate.set_stroke(GREY_B, 1.8, opacity=0.9)
                    for m in marks], run_time=0.6)
        st5 = st4.clone()
        st5.place_building(MARQUISE, DST, "sawmill")
        self.play(*self.view.sync(st5), run_time=1.1)
        self.play(marks[0].animate.set_stroke(FC[MARQUISE], 2.2, opacity=0.9),
                  run_time=0.4)
        self.nar.finish(self)
        self.play(*[m.animate.set_stroke(opacity=0.0) for m in marks],
                  run_time=0.4)

        # Craft: the cost is paid in clearings, by suit.
        self.unfocus(d)
        orbit(self, center=ORIGIN, height=8.0, run_time=1.5)
        card = fix(VGroup(
            RoundedRectangle(width=1.30, height=1.85, corner_radius=0.10)
            .set_fill("#161616", 1).set_stroke(C_HUD, 2.0)))
        pips = VGroup(*[Circle(radius=0.13)
                        .set_fill(bv.SUIT_COLOR[s], 1)
                        .set_stroke(bv.SUIT_BRIGHT[s], 2.0)
                        for s in (FOX, RABBIT)]).arrange(RIGHT, buff=0.18)
        pips.move_to(card.get_center() + DOWN * 0.55)
        cardg = fix(VGroup(card, pips).move_to([-5.5, 1.5, 0]))

        fox_ids = [c.id for c in self.view.map if c.suit == FOX
                   and self.S0.at(c.id, MARQUISE)][:1]
        rab_ids = [c.id for c in self.view.map if c.suit == RABBIT
                   and self.S0.at(c.id, MARQUISE)][:1]
        lit = fox_ids + rab_ids

        self.cap.show("A card's cost is paid in clearings.", "s3.craft",
                      hold=False)
        self.play(FadeIn(cardg, shift=RIGHT * 0.2), run_time=0.8)
        self.play(*self.view.highlight(*lit), run_time=0.8)
        self.play(*[self.view.suit_rings[c].animate.set_stroke(
            bv.SUIT_BRIGHT[self.view.map[c].suit], 5.0, opacity=1.0)
            for c in lit], run_time=0.7)
        self.nar.finish(self)
        self.play(*[self.view.suit_rings[c].animate.set_stroke(
            bv.SUIT_BRIGHT[self.view.map[c].suit], 2.6, opacity=0.60)
            for c in lit],
            *self.view.unhighlight(), FadeOut(cardg), run_time=0.8)

        self.cap.show("Bolted to this board.", "s3.bolted", hold=False)
        self.revert(self.S0, run_time=1.2)
        orbit(self, theta=-11, phi=58, run_time=2.4)
        orbit(self, theta=THETA, phi=PHI, run_time=1.8)
        self.nar.finish(self)

    # ── §4  the turn, and the loud action ───────────────────────────────
    def s4_battle(self):
        chips = VGroup()
        for name in ("Birdsong", "Daylight", "Evening"):
            box = RoundedRectangle(width=2.35, height=0.62, corner_radius=0.14)
            box.set_fill("#141414", 1).set_stroke(C_HUD, 1.8, opacity=0.5)
            lab = hud_text(name, size=25).move_to(box)
            chips.add(VGroup(box, lab))
        chips.arrange(RIGHT, buff=0.32).move_to([0, 2.62, 0])
        fix(*chips, *[m for c in chips for m in c])
        assert_in_frame_3d(self, phases=chips)

        self.cap.show("Three phases, always in this order.", "s4.phases",
                      hold=False)
        self.play(stagger([FadeIn(c, shift=UP * 0.15) for c in chips],
                          lag_ratio=0.22), run_time=1.5)
        for c in chips:
            self.play(c[0].animate.set_stroke(WHITE, 2.4, opacity=1.0),
                      run_time=0.42)
            self.play(c[0].animate.set_stroke(C_HUD, 1.8, opacity=0.5),
                      run_time=0.34)
        self.nar.finish(self)

        self.cap.show("Battle is the loud one.", "s4.quiet", hold=False)
        self.play(chips[1][0].animate.set_stroke(WHITE, 2.4, opacity=1.0),
                  run_time=0.6)
        self.nar.finish(self)

        # A battle in clearing 9, on a suppose-this state.
        FIELD = dg.FIELD
        st = self.S0.clone()
        st.place_building(MARQUISE, FIELD, "sawmill")
        st.place_warrior(EYRIE, FIELD, 4)
        d = self.focus(FIELD)
        self.play(*self.view.sync(st), run_time=1.4)
        orbit(self, center=[0.35, -0.20, 0], height=6.8, run_time=1.7)

        self.cap.show("Choose a clearing, choose a defender, roll both dice.",
                      "s4.choose", hold=False, size=27)
        self.play(*self.view.highlight(FIELD), run_time=0.7)
        self.nar.finish(self)

        d1, d2 = bv.die(3), bv.die(2)
        dice = fix(VGroup(d1, d2).arrange(RIGHT, buff=0.34)
                   .move_to([-5.2, 1.6, 0]))
        atk_lab = fix(hud_text("attacker  3", size=24, color=FC[EYRIE])
                      .move_to([-5.2, 0.62, 0]))
        def_lab = fix(hud_text("defender  2", size=24, color=FC[MARQUISE])
                      .move_to([-5.2, 0.12, 0]))
        self.cap.show("Higher roll to the attacker, lower to the defender.",
                      "s4.rolls", hold=False, size=27)
        self.play(FadeIn(dice, shift=UP * 0.2), run_time=0.9)
        self.play(Write(atk_lab), run_time=0.6)
        self.play(Write(def_lab), run_time=0.6)
        self.nar.finish(self)

        # She rolled 2 and has one warrior standing there, so she deals 1.
        assert st.warriors(FIELD, MARQUISE) == 1
        cap_note = fix(hud_text("one warrior there, so one hit",
                                size=22, color=WHITE)
                       .move_to([-5.2, -0.62, 0]))
        def_capped = fix(hud_text("defender  1", size=24, color=FC[MARQUISE])
                         .move_to([-5.2, 0.12, 0]))
        assert_in_frame_3d(self, cap_note=cap_note)
        self.cap.show("The roll is a ceiling. The tower is the limit.",
                      "s4.cap", hold=False, size=27)
        self.play(*[m.animate.scale(1.14) for m in
                    self.view.mobs_in(FIELD, MARQUISE, w.WARRIOR)],
                  run_time=0.5)
        self.play(*[m.animate.scale(1 / 1.14) for m in
                    self.view.mobs_in(FIELD, MARQUISE, w.WARRIOR)],
                  run_time=0.45)
        self.play(FadeTransform(def_lab, def_capped), Write(cap_note),
                  run_time=1.0)
        def_lab = def_capped
        self.nar.finish(self)

        self.cap.show("No warriors at all, and the attacker gets one more.",
                      "s4.defenceless", hold=False, size=27)
        self.play(*[m.animate.set_opacity(0.30) for m in
                    self.view.mobs_in(FIELD, MARQUISE, w.WARRIOR)],
                  run_time=0.7)
        plus = fix(hud_text("+1", size=30, color=WHITE)
                   .next_to(atk_lab, RIGHT, buff=0.28))
        assert_in_frame_3d(self, plus=plus)
        self.play(FadeIn(plus, shift=RIGHT * 0.15), run_time=0.5)
        self.play(FadeOut(plus),
                  *[m.animate.set_opacity(1.0) for m in
                    self.view.mobs_in(FIELD, MARQUISE, w.WARRIOR)],
                  run_time=0.6)
        self.nar.finish(self)

        st2 = st.clone()
        rep = st2.battle(EYRIE, MARQUISE, FIELD, rolls=(3, 2))
        assert rep["attacker_hits"] == 3 and rep["defender_hits"] == 1, rep
        assert rep["attacker_vp"] == 1, rep
        self.cap.show("Both sides deal at once. Warriors first.", "s4.simul",
                      hold=False)
        self.play(*self.view.sync(st2), run_time=1.6)
        self.nar.finish(self)

        self.cap.show("A point for every enemy building or token removed.",
                      "s4.vp", hold=False, size=27)
        self.play(*self.track.move_to_vp({EYRIE: rep["attacker_vp"]}),
                  run_time=1.0)
        self.play(*self.view.unhighlight(), run_time=0.5)
        orbit(self, center=ORIGIN, height=8.0, run_time=1.6)
        self.unfocus(d)
        self.revert(self.S0, run_time=1.2)
        self.play(*self.track.move_to_vp({MARQUISE: 0, EYRIE: 0, ALLIANCE: 0}),
                  FadeOut(dice), FadeOut(atk_lab), FadeOut(def_lab),
                  FadeOut(cap_note), FadeOut(chips), run_time=1.0)
        self.nar.finish(self)

    # ── §5  six factions, six edits to one sentence ─────────────────────
    def _crest_hud(self, faction, old=None):
        c = crest(faction, height=0.78)
        name = hud_text(FACTION_NAME[faction], size=23)
        g = Group(c, name).arrange(RIGHT, buff=0.22).move_to([-4.9, 2.62, 0])
        fix(g, c, name)
        if old is None:
            self.play(FadeIn(g, shift=RIGHT * 0.2), run_time=0.6)
        else:
            self.play(FadeOut(old, shift=LEFT * 0.2), run_time=0.3)
            self.play(FadeIn(g, shift=RIGHT * 0.2), run_time=0.45)
        return g

    def s5_factions(self):
        self.cap.show("Six rulebooks, one sentence.", "s5.turn", hold=False)
        self.play(stagger([FadeIn(g, shift=UP * 0.15) for g in self.crests],
                          lag_ratio=0.11), run_time=1.6)
        self.nar.finish(self)
        self.play(FadeOut(self.crests), run_time=0.7)

        base = self.S0
        hud = None

        # ── Marquise: score IS height ──────────────────────────────────
        hud = self._crest_hud(MARQUISE)
        C = dg.KEEP
        d = self.focus(C)
        st = base.clone()
        self.cap.show("Her score and her grip on the map are one object.",
                      "s5.cat", hold=False, size=27)
        st.place_building(MARQUISE, 4, "sawmill")
        self.play(*self.view.sync(st), run_time=1.1)
        self.play(*self.track.move_to_vp({MARQUISE: 2}), run_time=0.8)
        self.nar.finish(self)

        self.cap.show("Wood is flat. Buildings are not.", "s5.cat2",
                      hold=False)
        wood = Group()
        for cid in (2, 4):
            t = Disk3D(radius=0.13, color=bv.C_WOOD, opacity=1,
                       shading=(0.2, 0.1, 0.5))
            t.move_to(bv.world(self.view.map[cid])
                      + np.array([-0.42, bv.FLAT_Y, 0.02]))
            wood.add(t)
        self.play(stagger([GrowFromCenter(t) for t in wood], lag_ratio=0.2),
                  run_time=0.9)
        st2 = st.clone()
        st2.place_building(MARQUISE, 5, "sawmill")
        self.play(FadeOut(wood, scale=0.3), *self.view.sync(st2), run_time=1.3)
        self.play(*self.track.move_to_vp({MARQUISE: 4}), run_time=0.7)
        self.nar.finish(self)
        self.unfocus(d)
        self.revert(base, run_time=0.9)

        # ── Eyrie: they rule on a tie ──────────────────────────────────
        hud = self._crest_hud(EYRIE, hud)
        C = dg.FIELD
        d = self.focus(C)
        st = base.clone()
        st.place_warrior(EYRIE, C, st.presence(C, MARQUISE))
        assert st.presence(C, EYRIE) == st.presence(C, MARQUISE)
        assert st.ruler(C) == EYRIE and st.ruler(C, variant=False) is None
        self.cap.show("Tied for most is enough.", "s5.eyrie", hold=False)
        self.play(*self.view.sync(st), run_time=1.2)
        self.play(*self.view.highlight(C, width=3.4), run_time=0.6)
        tie = fix(hud_text("tied  —  and the Eyrie rule", size=25,
                           color=WHITE).move_to([0, -2.85, 0]))
        self.play(Write(tie), run_time=0.9)
        self.nar.finish(self)
        self.play(FadeOut(tie), *self.view.unhighlight(), run_time=0.5)

        st2 = base.clone()
        st2.place_building(EYRIE, C, "roost")
        self.cap.show("Roosts score every Evening. The Decree is the price.",
                      "s5.eyrie2", hold=False, size=27)
        self.play(*self.view.sync(st2), run_time=1.0)
        self.play(*self.track.move_to_vp({EYRIE: 3}), run_time=0.7)
        decree = VGroup()
        for name in ("Recruit", "Move", "Battle", "Build"):
            box = Rectangle(width=1.06, height=1.40)
            box.set_fill("#141414", 1).set_stroke(C_HUD, 1.6, opacity=0.55)
            lab = hud_text(name, size=17).next_to(box, DOWN, buff=0.10)
            decree.add(VGroup(box, lab))
        decree.arrange(RIGHT, buff=0.16).move_to([4.05, 1.10, 0])
        fix(decree, *decree, *[m for c in decree for m in c])
        assert_in_frame_3d(self, decree=decree)
        self.play(stagger([FadeIn(c, shift=UP * 0.12) for c in decree],
                          lag_ratio=0.14), run_time=1.1)
        cards = VGroup()
        for i, k in enumerate((1, 2, 0)):
            c = RoundedRectangle(width=0.86, height=0.30, corner_radius=0.06)
            c.set_fill(bv.SUIT_COLOR[(FOX, RABBIT, MOUSE)[i]], 1)
            c.set_stroke(bv.SUIT_BRIGHT[(FOX, RABBIT, MOUSE)[i]], 1.8)
            c.move_to(decree[k][0].get_center() + UP * (0.38 - 0.28 * i))
            cards.add(c)
        fix(cards, *cards)
        self.play(stagger([FadeIn(c, shift=DOWN * 0.2) for c in cards],
                          lag_ratio=0.25), run_time=1.2)
        turmoil = fix(hud_text("turmoil", size=27, color=WHITE)
                      .move_to(decree[3][0].get_center()))
        self.play(decree[3][0].animate.set_stroke(WHITE, 2.6, opacity=1.0),
                  run_time=0.5)
        self.play(Write(turmoil), run_time=0.6)
        self.nar.finish(self)
        self.play(FadeOut(decree), FadeOut(cards), FadeOut(turmoil),
                  run_time=0.6)
        self.unfocus(d)
        self.revert(base, run_time=0.9)

        # ── Alliance: scoring with no height at all ────────────────────
        hud = self._crest_hud(ALLIANCE, hud)
        symp = [11, 8, 10]
        d = self.focus(*symp)
        st = base.clone()
        for cid in symp:
            st.place_token(ALLIANCE, cid, "sympathy")
        self.cap.show("Sympathy is a token. Tokens have no height.",
                      "s5.alliance", hold=False, size=27)
        self.play(*self.view.sync(st), run_time=1.6)
        self.play(*self.track.move_to_vp({ALLIANCE: 5}), run_time=0.9)
        for cid in symp:
            assert st.presence(cid, ALLIANCE) == 0
        self.nar.finish(self)

        self.cap.show("Attacking her funds her.", "s5.outrage", hold=False)
        st2 = st.clone()
        assert st2.outrage_triggered(MARQUISE, 11)
        st2.move(MARQUISE, 9, 11, 1)
        self.play(*self.view.sync(st2), run_time=1.3)
        card = fix(RoundedRectangle(width=0.62, height=0.88, corner_radius=0.08)
                   .set_fill(bv.SUIT_COLOR[MOUSE], 1)
                   .set_stroke(bv.SUIT_BRIGHT[MOUSE], 2.0)
                   .move_to([1.2, -1.2, 0]))
        self.play(FadeIn(card), run_time=0.5)
        self.play(card.animate.move_to([-4.9, 1.55, 0]).scale(0.8),
                  run_time=1.0)
        self.play(FadeOut(card), run_time=0.4)
        self.nar.finish(self)
        self.unfocus(d)
        self.revert(base, run_time=0.9)

        # ── Vagabond: no height, and no permission needed ──────────────
        hud = self._crest_hud(VAGABOND, hud)
        A, B = 5, dg.FIELD
        d = self.focus(A, B)
        st = base.clone()
        st.place_pawn(A)
        st.place_warrior(EYRIE, A, 4)
        st.place_warrior(EYRIE, B, 4)
        assert st.presence(A, VAGABOND) == 0
        assert st.ruler(A) == EYRIE
        self.cap.show("A pawn, not a warrior.", "s5.vagabond", hold=False)
        self.play(*self.view.sync(st), run_time=1.5)
        self.play(*self.view.highlight(A, width=3.2), run_time=0.6)
        ok, why = st.can_move(VAGABOND, A, B)
        assert ok and "Nimble" in why
        assert not st.can_move(MARQUISE, A, B)[0]
        st2 = st.clone()
        pawn = [p for p in st2.pieces[A] if p.kind == w.PAWN][0]
        st2.pieces[A].remove(pawn)
        st2.pieces[B].append(pawn)
        self.play(*self.view.sync(st2), run_time=1.4)
        self.play(*self.view.highlight(B, width=3.2),
                  *self.view.unhighlight(A), run_time=0.7)
        st3 = st2.clone()
        pawn = [p for p in st3.pieces[B] if p.kind == w.PAWN][0]
        st3.pieces[B].remove(pawn)
        st3.pieces[6].append(pawn)
        assert st3.map.adjacent(B, 6)
        self.play(*self.view.sync(st3), run_time=1.5)
        orbit(self, theta=-9, phi=57, run_time=2.6)
        self.nar.finish(self)
        orbit(self, theta=THETA, phi=PHI, run_time=1.5)
        self.play(*self.view.unhighlight(), run_time=0.4)
        self.unfocus(d)
        self.revert(base, run_time=0.9)

        # ── Cult: a garden overrules any tower ─────────────────────────
        hud = self._crest_hud(CULT, hud)
        C = dg.FIELD
        d = self.focus(C)
        st = base.clone()
        st.place_warrior(EYRIE, C, 6)
        assert st.ruler(C) == EYRIE
        self.play(*self.view.sync(st), run_time=1.2)
        st2 = st.clone()
        st2.place_building(CULT, C, "garden")
        assert st2.ruler(C) == CULT and st2.presence(C, EYRIE) > st2.presence(C, CULT)
        self.cap.show("Wherever the Cult has a garden, the Cult rules.",
                      "s5.cult", hold=False, size=27)
        self.play(*self.view.sync(st2), run_time=1.2)
        self.play(*self.view.highlight(C, width=3.6), run_time=0.6)
        self.nar.finish(self)
        self.play(*self.view.unhighlight(), run_time=0.4)
        self.unfocus(d)
        self.revert(base, run_time=0.9)

        # ── Riverfolk: around the sentence, along the river ────────────
        hud = self._crest_hud(RIVERFOLK, hud)
        A, B = w.MAP.river[1], w.MAP.river[2]
        d = self.focus(A, B)
        st = base.clone()
        st.place_warrior(RIVERFOLK, A, 2)
        st.place_warrior(EYRIE, A, 5)
        st.place_warrior(EYRIE, B, 5)
        ok, why = st.can_move(RIVERFOLK, A, B)
        assert ok and "Swimmers" in why, why
        self.cap.show("Rivers are paths for them and nobody else.",
                      "s5.riverfolk", hold=False, size=27)
        self.play(*self.view.sync(st), run_time=1.3)
        self.play(self.view.river[0].animate.set_stroke(
            "#6FA9BC", 15, opacity=1.0), run_time=0.8)
        st2 = st.clone()
        st2.move(RIVERFOLK, A, B, 2)
        self.play(*self.view.sync(st2), run_time=1.5)
        self.nar.finish(self)
        self.play(self.view.river[0].animate.set_stroke(
            bv.C_RIVER_INK, 13, opacity=0.9), run_time=0.6)
        self.unfocus(d)
        self.revert(base, run_time=0.9)
        self.play(FadeOut(hud), run_time=0.5)
        self.play(*self.track.move_to_vp({MARQUISE: 0, EYRIE: 0, ALLIANCE: 0}),
                  run_time=0.9)

    # ── §6  three turns ─────────────────────────────────────────────────
    def s6_game(self):
        self.cap.show("Watch it run.", "s6.watch")
        FIELD = dg.FIELD

        self.cap.show("A keep in one corner, a warrior in every clearing but "
                      "the far one.", "s6.setup", hold=False, size=26)
        self.play(*self.view.highlight(dg.KEEP, width=3.2), run_time=0.7)
        self.nar.finish(self)
        self.cap.show("The Alliance starts with nothing on the board.",
                      "s6.setup2", hold=False)
        self.play(*self.view.unhighlight(),
                  *self.view.highlight(dg.EYRIE_CORNER, width=3.2),
                  run_time=0.8)
        self.nar.finish(self)
        self.play(*self.view.unhighlight(), run_time=0.4)

        turn = fix(hud_text("Marquise  ·  Birdsong", size=25,
                            color=FC[MARQUISE]).move_to([5.05, 2.62, 0]))
        assert_in_frame_3d(self, turn=turn)

        def phase_to(text, color):
            nonlocal turn
            new = fix(hud_text(text, size=25, color=color)
                      .move_to([5.05, 2.62, 0]))
            self.play(FadeTransform(turn, new), run_time=0.5)
            turn = new

        d = self.focus(FIELD, 2, 5, dg.KEEP, dg.EYRIE_CORNER)
        orbit(self, center=[0.20, -0.25, 0], height=6.9, run_time=1.7)

        self.cap.show("A wood token at each sawmill.", "s6.t1", hold=False)
        self.play(FadeIn(turn, shift=DOWN * 0.15), run_time=0.6)
        wood = Disk3D(radius=0.13, color=bv.C_WOOD, opacity=1,
                      shading=(0.2, 0.1, 0.5))
        wood.move_to(bv.world(self.view.map[2])
                     + np.array([-0.42, bv.FLAT_Y, 0.02]))
        self.play(GrowFromCenter(wood), run_time=0.7)
        self.nar.finish(self)

        phase_to("Marquise  ·  Daylight", FC[MARQUISE])
        self.cap.show("She builds.", "s6.t1build", hold=False)
        st = self.steps["t1.build"][2]
        self.play(FadeOut(wood, scale=0.3), run_time=0.5)
        self.play(*self.view.sync(st), run_time=1.3)
        self.play(*self.track.move_to_vp(st.vp), run_time=0.8)
        self.nar.finish(self)

        self.cap.show("Then she marches. Twice.", "s6.t1march", hold=False)
        self.play(*self.view.sync(self.steps["t1.march"][2]), run_time=1.6)
        self.play(*self.view.sync(self.steps["t1.recruit"][2]), run_time=0.9)
        self.nar.finish(self)

        phase_to("Eyrie  ·  Birdsong", FC[EYRIE])
        self.cap.show("A card goes onto the Decree.", "s6.t2", hold=False)
        card = fix(RoundedRectangle(width=1.02, height=0.34, corner_radius=0.07)
                   .set_fill(bv.SUIT_COLOR[RABBIT], 1)
                   .set_stroke(bv.SUIT_BRIGHT[RABBIT], 1.8)
                   .move_to([5.05, 1.95, 0]))
        dlab = fix(hud_text("Decree · Battle", size=20)
                   .move_to([5.05, 1.52, 0]))
        self.play(FadeIn(card, shift=DOWN * 0.2), Write(dlab), run_time=0.9)
        self.nar.finish(self)

        phase_to("Eyrie  ·  Daylight", FC[EYRIE])
        self.cap.show("Move, then battle.", "s6.t2battle", hold=False)
        self.play(*self.view.sync(self.steps["t2.move"][2]), run_time=1.7)
        self.play(*self.view.highlight(FIELD, width=3.4), run_time=0.6)
        self.nar.finish(self)

        rep = self.steps["t2.battle"][3]
        d1, d2 = bv.die(max(rep["rolls"])), bv.die(min(rep["rolls"]))
        dice = fix(VGroup(d1, d2).arrange(RIGHT, buff=0.32)
                   .move_to([-5.25, 1.75, 0]))
        rl = fix(hud_text(f"attacker {rep['attacker_hits']}   "
                          f"defender {rep['defender_hits']}", size=23)
                 .move_to([-5.25, 1.02, 0]))
        assert_in_frame_3d(self, dice=dice, rl=rl)
        self.cap.show("Higher to the attacker, lower to the defender.",
                      "s6.t2dice", hold=False, size=27)
        self.play(FadeIn(dice, shift=UP * 0.2), run_time=0.8)
        self.play(Write(rl), run_time=0.7)
        self.play(*self.view.sync(self.steps["t2.battle"][2]), run_time=1.5)
        self.nar.finish(self)

        self.cap.show("The clearing is the Eyrie's.", "s6.t2flip", hold=False)
        self.play(*self.view.sync(self.steps["t2.build"][2]), run_time=1.2)
        phase_to("Eyrie  ·  Evening", FC[EYRIE])
        self.play(*self.track.move_to_vp(self.steps["t2.evening"][2].vp),
                  run_time=0.9)
        self.play(FadeOut(dice), FadeOut(rl), run_time=0.5)
        self.nar.finish(self)

        phase_to("Alliance  ·  Birdsong", FC[ALLIANCE])
        self.cap.show("She spreads sympathy.", "s6.t3", hold=False)
        sup = fix(VGroup(*[
            RoundedRectangle(width=0.52, height=0.74, corner_radius=0.07)
            .set_fill(bv.SUIT_COLOR[s], 1)
            .set_stroke(bv.SUIT_BRIGHT[s], 1.6)
            for s in self.steps["t2.evening"][2].supporters
        ]).arrange(RIGHT, buff=0.12).move_to([-5.3, 1.55, 0]))
        slab = fix(hud_text("supporters", size=20).move_to([-5.3, 0.92, 0]))
        self.play(FadeIn(sup, shift=UP * 0.15), Write(slab), run_time=0.9)
        self.play(sup[0].animate.set_opacity(0.15),
                  sup[1].animate.set_opacity(0.15), run_time=0.7)
        self.play(*self.view.sync(self.steps["t3.sympathy"][2]), run_time=1.2)
        self.nar.finish(self)

        self.cap.show("Still not one warrior on the board.", "s6.t3score",
                      hold=False)
        self.play(*self.track.move_to_vp(self.steps["t3.sympathy"][2].vp),
                  run_time=0.9)
        st3 = self.steps["t3.sympathy"][2]
        assert sum(st3.warriors(c.id, ALLIANCE) for c in st3.map) == 0
        self.play(*self.view.sync(self.steps["t3.mobilize"][2]), run_time=0.6)
        self.play(sup[0].animate.set_opacity(1.0), run_time=0.5)
        self.nar.finish(self)

        phase_to("Marquise  ·  Daylight", FC[MARQUISE])
        self.cap.show("The obvious reply.", "s6.reply", hold=False)
        self.nar.finish(self)

        self.cap.show("Outrage.", "s6.outrage", hold=False)
        self.play(*self.view.sync(self.steps["t4.outrage"][2]), run_time=1.6)
        fly = fix(RoundedRectangle(width=0.52, height=0.74, corner_radius=0.07)
                  .set_fill(bv.SUIT_COLOR[RABBIT], 1)
                  .set_stroke(bv.SUIT_BRIGHT[RABBIT], 1.6)
                  .move_to([1.1, -1.0, 0]))
        self.play(FadeIn(fly), run_time=0.4)
        self.play(fly.animate.move_to(sup[1].get_center()), run_time=1.0)
        self.play(FadeOut(fly), sup[1].animate.set_opacity(1.0), run_time=0.4)
        self.nar.finish(self)

        phase_to("Alliance  ·  Birdsong", FC[ALLIANCE])
        self.cap.show("Revolt.", "s6.revolt", hold=False)
        self.play(sup[1].animate.set_opacity(0.15),
                  sup[0].animate.set_opacity(0.15), run_time=0.6)
        removed = []
        anims = self.view.sync(self.steps["t5.revolt"][2], removed=removed)
        self.play(*anims, run_time=2.0)
        self.nar.finish(self)

        rev = self.steps["t5.revolt"][3]
        assert rev["vp"] == 2, rev
        self.cap.show("A point for the sawmill. A point for the roost.",
                      "s6.revolt2", hold=False, size=27)
        self.play(*self.track.move_to_vp(self.steps["t5.revolt"][2].vp),
                  run_time=1.0)
        self.play(*self.view.highlight(FIELD, width=3.6), run_time=0.7)
        self.nar.finish(self)
        # A wordless beat on the one frame the whole section was built to
        # reach. The picture has to carry some of this video on its own.
        orbit(self, theta=-9, phi=57, run_time=2.6)
        orbit(self, theta=THETA, phi=PHI, run_time=2.0)
        self.play(*self.view.unhighlight(), FadeOut(sup), FadeOut(slab),
                  FadeOut(card), FadeOut(dlab), FadeOut(turn), run_time=0.8)
        orbit(self, center=ORIGIN, height=8.0, run_time=1.8)
        self.unfocus(d)

    # ── §7  payoff ──────────────────────────────────────────────────────
    def s7_payoff(self):
        self.cap.clear(run_time=0.5)
        q = fix(hud_text(
            "No two players are playing by the same rules.\n"
            "So what makes it one game?", size=40, color=WHITE)
            .move_to([0, 0.35, 0]))
        stage = Dimmer(self.view.all_static(), self.view.pieces,
                       self.track.group)
        self.nar.cue(self, "s7.restate")
        self.play(*stage.to(0.07), run_time=1.0)
        self.play(Write(q), run_time=2.0)
        self.nar.finish(self)

        ans = fix(hud_text("Who holds this clearing?", size=40, color=WHITE)
                  .move_to([0, 0.35, 0]))
        self.nar.cue(self, "s7.answer")
        self.play(FadeOut(q, shift=UP * 0.3), run_time=0.7)
        self.play(Write(ans), run_time=1.6)
        self.nar.finish(self)

        self.nar.cue(self, "s7.each")
        self.play(ans.animate.scale(0.62).move_to([0, 3.42, 0]), run_time=1.0)
        self.play(*stage.restore(), run_time=1.4)
        crests = Group()
        for f in SIX:
            crests.add(crest(f, height=0.52))
        crests.arrange(RIGHT, buff=0.5).move_to([0, -2.62, 0])
        fix(crests, *crests)
        assert_in_frame_3d(self, closing_crests=crests)
        self.play(stagger([FadeIn(c, shift=UP * 0.15) for c in crests],
                          lag_ratio=0.12), run_time=1.6)
        orbit(self, theta=-11, phi=56, run_time=3.0)
        self.nar.finish(self)

        # Close the loop the video opened: back to flat, which is the board
        # as it sits on a table, and then the table itself.
        self.nar.cue(self, "s7.close")
        self.play(FadeOut(crests), FadeOut(ans), run_time=0.7)
        orbit(self, theta=THETA, phi=0, center=FLAT_C, height=FLAT_H,
              run_time=3.2)
        last = fix(hud_text("The rules differ.  The ground does not.",
                            size=34, color=WHITE).move_to([0, 0.15, 0]))
        photo = ImageMobject(str(ASSETS / "board_dark.png"), height=6.9)
        fix(photo)
        self.nar.finish(self)
        self.play(FadeIn(photo), *stage.to(0.0), run_time=1.8)
        self.play(Write(last), run_time=1.8)
        self.wait(2.0)
        self.play(FadeOut(last), FadeOut(photo), run_time=1.6)
