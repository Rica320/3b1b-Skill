"""
"The same chart, two opposite bets. What decides which one is right?"

A narrated 3D explainer on momentum. Everything drawn is computed by panel.py
-- the price paths, the rankings, the deciles, all 1152 backtests and the
landscape they trace out -- so no frame can assert something the arithmetic
does not support.

    TTS:     ../../env/bin/python \
                 ../../skills/3b1b-math-animation/scripts/tts.py script.yaml --out audio
    Render:  bash ../../skills/3b1b-math-animation/scripts/render.sh \
                 momentum.py Momentum
    Mux:     ../../env/bin/python \
                 ../../skills/3b1b-math-animation/scripts/mux_audio.py \
                 videos/Momentum.mp4 --cues narration_cues.json
    Verify:  ../../env/bin/python .../verify_render.py videos/Momentum.mp4 \
                 --meta render_meta.json
             ../../env/bin/python .../verify_audio.py \
                 videos/Momentum_narrated.mp4 --cues narration_cues.json
             ../../env/bin/python verify_panel.py     # every spoken number
    Audit:   AUDIT=1 ... manimgl momentum.py Momentum -l

Spine (full version in SPINE.md)
  QUESTION    one chart, and two people betting opposite ways on it. Momentum
              says it keeps going, reversion says it comes back. What decides
              which one is right?
  MOTIVATION  measure it. Rank the cross-section on its six-month return, buy
              the top tenth, short the bottom tenth: +1.20% a month. Then
              change the six to a one: -0.55. Change it to forty-eight: -0.12.
              The answer lives in the parameter, not in the market.
  BUILD       there are two such parameters -- lookback k and holding period h
              -- so a strategy is a point on a floor and what it pays is a
              height above that floor. Apply all 1152 heights while the camera
              is straight down, and nothing appears to happen. Then tilt.
  PAYOFF      it is one landscape: a ridge where momentum pays, a basin in the
              far corner where reversion pays, a notch at one month. Momentum
              and mean reversion are the same sentence read at two different
              horizons.

Carried metaphor: THE MAP OF STRATEGIES. Every strategy is a point on the
floor; what it pays is the height of the ground under it; the argument between
the two camps is two people standing at opposite ends of one slice. The
construction is the argument: the 240-stock ranking column collapses into the
single dot that turns out to be one strategy among 1152.

Colour
  ORANGE   continuation: the winners, buying them, and the ground where
           momentum pays
  BLUE_C   reversal: the losers, buying them, and the ground where reversion
           pays
  GREY_B   scaffolding: the price panel, the axes, the mesh, connectives
  YELLOW   transient emphasis only -- the question, the current strategy
  RED_C    cost, and nothing else

The surface has no colour of its own: it is coloured by its own sign. Orange is
the winners and the people who bet on them, blue is the losers and the people
who bet on them, and the colour of the ground says which of them was right
there.
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

import panel as pn                                        # noqa: E402
from manim_helpers import (                               # noqa: E402
    Caption, Dimmer, stagger, dump_meta, equation,
    audit_text_overlaps, assert_in_frame_3d, assert_no_overlap, project,
    fix, flat, orient, orbit, spin, surface, mesh_for, dot3d, slice_curve,
    FONT,
)
from narration import Narrator                            # noqa: E402

# ── colour ───────────────────────────────────────────────────────────────
C_UP = ORANGE           # continuation: winners, and ground that pays
C_DOWN = BLUE_C         # reversal: losers, and ground that loses
C_HOT = YELLOW          # transient emphasis only
C_NEUT = GREY_B
C_COST = RED_C

QUESTION = "The same chart, two opposite bets.\nWhat decides which one is right?"

# ── the data, computed once ──────────────────────────────────────────────
COST = 0.10                       # percent of the traded amount, one way

_MKT = pn.build()
LOGP = _MKT["log_p"]
GRID = pn.landscape(LOGP)
GRID_NET = pn.landscape(LOGP, cost=COST)

N_SIDE = int(round(pn.DECILE * pn.N))          # 24 names a leg

# The window the price panel shows: four years of history ending "today".
T_NOW, HIST = 1800, 48
_W = LOGP[T_NOW - HIST:T_NOW + 1] - LOGP[T_NOW - HIST]     # (49, 240), rebased

# The one stock §0 opens on: the strongest six-month run among the stocks
# whose whole four-year path stays inside the panel §0 draws it at.
_R6 = _W[-1] - _W[-7]
HERO = int(np.where(np.abs(_W).max(axis=0) < 1.0, _R6, -np.inf).argmax())

# ── panel geometry (world units; §0-§1 are viewed from straight above, so
#    world x/y and screen x/y are the same thing there) ────────────────────
PX0, PX1 = -6.55, 0.85            # the price panel, 48 months wide
PYC = -0.20                       # its zero line
PZ = -0.03                        # scaffolding sits behind the data it holds
S0_SCALE = 2.45 / np.abs(_W[:, HERO]).max()        # §0: one stock fills it
S1_SCALE = 2.45 / np.abs(_W).max()                 # §1: all 240 fit inside it

COL_X, COL_Y = 3.45, 2.45         # the ranking column
# 240 dots stacked in one 4.9-unit line land 1.2 px apart at 1080p and beat
# against the pixel grid into a dashed line. Each stock keeps its own small
# horizontal offset instead, which spreads the column into a swarm and makes
# a re-sort visible as motion rather than as a shimmer.
COL_JITTER = np.random.default_rng(3).uniform(-0.30, 0.30, pn.N)

# ── the map ──────────────────────────────────────────────────────────────
KMAX, HMAX = 48, 24
XU, YU = float(np.log2(KMAX)), float(np.log2(HMAX))
Z_LO, Z_HI = -0.8, 1.4

K_TICKS = [1, 2, 4, 8, 16, 32]
H_TICKS = [1, 2, 4, 8, 16]

# The three places on the map the video names, as (k, h).
RIDGE = (6, 2)
NOTCH = (1, 1)
BASIN = (48, 24)

# The oblique viewpoint everything after the tilt is read at. Chosen by
# projecting the three labelled features through the camera and sweeping
# theta: at -34 the ridge and the basin land 0.58 units apart on screen and
# their labels overlap, and at -20 they are 1.4 apart. The drift below stays
# inside [-20, -9], where that separation only grows.
THETA, PHI = -20, 64

# A long focal distance flattens the projection toward orthographic, and that
# is what makes §2's last beat honest: with the default 45-degree field of
# view a point rising 1.3 units toward a top-down camera is thrown 16%
# outward, so the heights would be half legible from straight above and the
# tilt would be proving something the viewer had already seen. At 32 it is 4%.
FOCAL = 32.0


def x_of(month):
    return PX0 + (month / HIST) * (PX1 - PX0)


def ranking(k, t=T_NOW):
    """(rank of each stock, winners, losers) on a k-month lookback, at t."""
    m = LOGP[t] - LOGP[t - k]
    order = np.argsort(m)
    rank = np.empty(pn.N, dtype=int)
    rank[order] = np.arange(pn.N)
    return rank, set(order[-N_SIDE:].tolist()), set(order[:N_SIDE].tolist())


def col_y(rank):
    """Where a stock of this rank sits in the sorted column."""
    return -COL_Y + (2 * COL_Y) * rank / (pn.N - 1)


def height_uv(u, v, grid=None):
    """The landscape, in the map's own (log2 k, log2 h) coordinates."""
    return pn.height(GRID if grid is None else grid, 2.0 ** u, 2.0 ** v)


class Marker:
    """A dot on the surface, plus the screen labels that point at it."""

    def __init__(self, dot, kh, world):
        self.dot, self.kh, self.world = dot, kh, world
        self.value = None
        self.note = None


class Momentum(ThreeDScene):

    def wait(self, *args, **kwargs):
        r = super().wait(*args, **kwargs)
        if os.environ.get("AUDIT"):
            audit_text_overlaps(self)
        return r

    def construct(self):
        self.camera.background_color = BLACK
        self.nar = Narrator(_HERE / "script.yaml", _HERE / "audio")
        self.cap = Caption(self, narrator=self.nar)   # fixes itself: ThreeDScene

        sections = [
            ("s0", self.s0_question), ("s1", self.s1_measure),
            ("s2", self.s2_floor), ("s3", self.s3_tilt),
            ("s4", self.s4_shape), ("s5", self.s5_limits),
            ("s6", self.s6_payoff),
        ]
        for name, fn in sections:
            t0 = self.time
            fn()
            print(f"[TIMING] {name} start={t0:6.1f}s dur={self.time - t0:5.1f}s")

        dump_meta(self, str(_HERE / "render_meta.json"))
        self.nar.dump(_HERE / "narration_cues.json", scene=self)
        self.nar.report()

    # ── §0  one chart, two opposite bets ─────────────────────────────────
    def s0_question(self):
        # phi = 0 is straight down: a 3D scene deliberately opened as a flat
        # one. The whole video is the cost of the direction this view lacks.
        orient(self, theta=0, phi=0, height=8.0)
        self.camera.frame.set_focal_distance(FOCAL)

        zero = Line(np.array([PX0, PYC, PZ]), np.array([PX1, PYC, PZ]))
        zero.set_stroke(GREY_D, width=1.6)
        today = DashedLine(np.array([PX1, PYC - 2.7, PZ]),
                           np.array([PX1, PYC + 2.7, PZ]))
        today.set_stroke(GREY_D, width=1.4)
        flat(zero, today)

        path = self.price_path(HERO, S0_SCALE, C_NEUT, width=2.6, opacity=1.0)
        band = self.band_for(6, opacity=0.09)
        band_lbl = self.band_label_for(6)

        self.play(ShowCreation(zero), ShowCreation(today), run_time=0.8)
        self.cap.show("One stock. Four years of it.", "s0.chart", hold=False)
        self.play(ShowCreation(path), run_time=2.0)
        self.play(FadeIn(band), FadeIn(band_lbl), run_time=0.8)
        self.nar.finish(self)

        # The fork: the same chart, continued two ways. Both arrows leave the
        # last real price, so the disagreement is about one point.
        tip = np.array([x_of(HIST), PYC + _W[-1, HERO] * S0_SCALE, 0])
        up = Arrow(tip, tip + np.array([2.4, 1.3, 0]), buff=0.0,
                   stroke_width=4.5)
        up.set_fill(C_UP, 1).set_stroke(C_UP, 4.5, 1)
        down = Arrow(tip, tip + np.array([2.4, -1.45, 0]), buff=0.0,
                     stroke_width=4.5)
        down.set_fill(C_DOWN, 1).set_stroke(C_DOWN, 4.5, 1)

        keeps = Text("it keeps going", font=FONT, font_size=23).set_color(C_UP)
        keeps.next_to(up.get_end(), RIGHT, buff=0.16)
        comes = Text("it comes back", font=FONT, font_size=23)
        comes.set_color(C_DOWN).next_to(down.get_end(), RIGHT, buff=0.16)
        assert_in_frame_3d(self, keeps=keeps, comes=comes)

        self.cap.show("Two people, one chart.", "s0.two", hold=False)
        self.play(GrowArrow(down), FadeIn(comes, shift=RIGHT * 0.2),
                  run_time=1.0)
        self.play(GrowArrow(up), FadeIn(keeps, shift=RIGHT * 0.2), run_time=1.0)
        # "exactly this chart": run a pulse up the price path into the fork,
        # so the thing both of them are looking at is the thing that moves.
        self.play(ShowPassingFlash(path.copy().set_stroke(C_HOT, 6.0),
                                   time_width=0.4), run_time=1.8)
        self.nar.finish(self)

        mark = Text("?", font=FONT, font_size=54).set_color(C_HOT)
        mark.move_to(tip + np.array([1.35, -0.06, 0]))
        self.nar.cue(self, "s0.real")
        self.play(Write(mark), run_time=0.7)
        # Each one has years where it is the only thing working: light one
        # claim, then the other. Without this the line plays over a frozen
        # frame -- measured, a 16.5s freeze that failed check [3].
        for _ in range(2):
            self.play(stagger(
                [ShowPassingFlash(up.copy().set_stroke(C_UP, 8.0),
                                  time_width=0.5),
                 ShowPassingFlash(down.copy().set_stroke(C_DOWN, 8.0),
                                  time_width=0.5)], lag_ratio=0.5),
                run_time=1.7)
        self.nar.finish(self)

        # The driving question, anchored to the fork it is asking about.
        q = Text(QUESTION, font=FONT, font_size=33).set_color(C_HOT)
        fix(q.move_to(np.array([0, -3.05, 0])))
        assert_in_frame_3d(self, question=q)
        self.nar.cue(self, "s0.question")
        self.play(Write(q), run_time=1.9)
        self.nar.finish(self)
        self.wait(3.0)                           # room to read it, unnarrated

        self.fork = VGroup(up, down, keeps, comes, mark)
        self.zero, self.today, self.band = zero, today, band
        self.band_lbl, self.hero_path, self.q = band_lbl, path, q

    # ── §1  stop arguing and measure it ──────────────────────────────────
    def s1_measure(self):
        self.cap.show("So measure it.", "s1.measure", hold=False)
        self.play(FadeOut(self.fork), FadeOut(self.q), run_time=0.8)

        # The same stock, rescaled to make room for the other 239 -- a genuine
        # transform of the object §0 opened on, not a cut to a new picture.
        hero_wide = self.price_path(HERO, S1_SCALE, C_NEUT, width=2.0,
                                    opacity=0.95)
        self.play(Transform(self.hero_path, hero_wide), run_time=1.0)
        self.nar.finish(self)

        self.paths = VGroup(*[
            self.price_path(i, S1_SCALE, C_NEUT, width=1.0, opacity=0.30)
            for i in range(pn.N) if i != HERO])
        self.cap.show("Two hundred and forty of them.", "s1.cross",
                      hold=False)
        self.play(stagger([ShowCreation(p) for p in self.paths],
                          lag_ratio=0.004), run_time=3.2)
        self.nar.finish(self)

        # The signal: the picture of it, then the words, then the symbol.
        self.cap.show("One number each: the six-month return.", "s1.signal",
                      hold=False)
        self.play(self.band[1].animate.set_stroke(C_HOT, width=3.0,
                                                  opacity=0.95),
                  run_time=0.6)
        m_eq = equation(Tex(r"M_t"), Tex("="), Tex(r"\frac{P_t}{P_{t-k}}"),
                        Tex(r"-\,1"), scale=0.8)
        fix(m_eq.move_to(np.array([-4.8, 2.62, 0])))
        k_note = Text("k = how far back you look", font=FONT, font_size=19)
        k_note.set_color(C_HOT)
        fix(k_note.next_to(m_eq, DOWN, buff=0.22))
        assert_in_frame_3d(self, formula=m_eq, k_note=k_note)
        self.play(Write(m_eq), run_time=1.5)
        self.play(FadeIn(k_note), run_time=0.6)
        self.nar.finish(self)
        self.m_eq, self.k_note = m_eq, k_note

        # Rank: every stock leaves its path and takes its place in the order.
        rank6, win6, lose6 = ranking(6)
        self.cap.show("Sort the market by it.", "s1.rank", hold=False)
        self.column = self.end_cloud()
        self.play(FadeIn(self.column), run_time=0.6)
        self.play(Transform(self.column,
                            self.column_cloud(rank6, win6, lose6)),
                  run_time=2.0)

        buy = Text("buy the top tenth", font=FONT, font_size=21)
        buy.set_color(C_UP).move_to(np.array([2.15, COL_Y - 0.05, 0]))
        short = Text("short the bottom tenth", font=FONT, font_size=21)
        short.set_color(C_DOWN).move_to(np.array([2.15, -COL_Y + 0.05, 0]))
        assert_in_frame_3d(self, buy=buy, short=short)
        self.play(self.light_paths(win6, lose6), run_time=1.0)
        self.play(FadeIn(buy), FadeIn(short), run_time=0.7)
        self.nar.finish(self)
        self.legend = VGroup(buy, short)

        # "and then do it again": the rebalance, computed three and six months
        # on, so the shuffle on screen is a real change of ranking.
        self.cap.show("Wait, and do it again.", "s1.rule", hold=False)
        for months in (3, 6):
            rk, wn, ls = ranking(6, T_NOW + months)
            self.play(Transform(self.column, self.column_cloud(rk, wn, ls)),
                      run_time=1.3)
        rk, wn, ls = ranking(6)
        self.play(Transform(self.column, self.column_cloud(rk, win6, lose6)),
                  run_time=0.9)
        self.nar.finish(self)

        # What it pays. Every number from here on is read out of panel.py.
        self.cap.show("Two hundred and fifty years of it.", "s1.result",
                      hold=False)
        self.k_lbl = self.param_label(6)
        self.pay = self.payoff_label(self.g(6, 1))
        self.play(FadeIn(self.k_lbl, shift=UP * 0.15), run_time=0.7)
        self.play(Write(self.pay), run_time=1.2)
        self.play(FlashAround(self.pay, color=C_UP, time_width=0.7),
                  run_time=1.4)
        self.nar.finish(self)

        self.rows = VGroup()
        self.add_result_row(6, self.g(6, 1))

        self.cap.show("Change one number.", "s1.change", hold=False)
        self.play(FlashAround(self.k_lbl, color=C_HOT, buff=0.14),
                  run_time=1.5)
        self.nar.finish(self)

        # The failure that forces §2: one number moves, and the sign flips.
        for beat, k in [("s1.one", 1), ("s1.four", 48)]:
            rk, wn, ls = ranking(k)
            self.nar.cue(self, beat)
            # The window moves first, the ranking follows it, and only then do
            # the two numbers change -- together, because a frame in which the
            # label reads k=1 while the payoff still reads the k=6 answer is a
            # frame that states something false.
            self.play(Transform(self.band, self.band_for(k)),
                      self.relabel_band(k),
                      FadeOut(self.pay), run_time=1.1)
            self.play(Transform(self.column, self.column_cloud(rk, wn, ls)),
                      self.light_paths(wn, ls), run_time=1.6)
            self.pay = self.payoff_label(self.g(k, 1))
            self.play(Transform(self.k_lbl, self.param_label(k)),
                      Write(self.pay), run_time=0.9)
            self.add_result_row(k, self.g(k, 1))
            self.nar.finish(self)

        # The landing: the three answers, from one rule, side by side.
        chart = Dimmer(self.paths, self.hero_path, self.column, self.legend,
                       self.band, self.band_lbl, self.m_eq, self.k_note)
        self.nar.cue(self, "s1.lesson")
        self.play(*chart.to(0.18), run_time=1.0)
        self.play(FlashAround(self.rows, color=C_HOT, buff=0.18), run_time=1.8)
        self.nar.finish(self)
        self.wait(2.6)                           # the three answers, wordless
        self.play(*chart.restore(), run_time=0.9)
        self.chart_dimmer = chart

    # ── §2  a strategy is a point, not a rule ────────────────────────────
    def s2_floor(self):
        # The second parameter, on the object that has been on screen for a
        # minute: the same signal, held for one month and then for two years.
        self.cap.show("And a second number.", "s2.second", hold=False)
        rk, wn, ls = ranking(6)
        self.play(Transform(self.band, self.band_for(6)),
                  self.relabel_band(6),
                  Transform(self.column, self.column_cloud(rk, wn, ls)),
                  self.light_paths(wn, ls),
                  Transform(self.k_lbl, self.param_label(6, 1)),
                  Transform(self.pay, self.payoff_label(self.g(6, 1))),
                  run_time=1.5)
        self.nar.finish(self)

        self.nar.cue(self, "s2.hold")
        self.play(Transform(self.k_lbl, self.param_label(6, 24)),
                  Transform(self.pay, self.payoff_label(self.g(6, 24))),
                  run_time=1.8)
        self.nar.finish(self)

        # Everything except the ranking itself goes; the column is what
        # carries across the boundary, and it is about to become one point.
        self.cap.show("A strategy is a pair of numbers.", "s2.pair",
                      hold=False)
        gone = Dimmer(self.paths, self.hero_path, self.legend, self.band,
                      self.band_lbl, self.zero, self.today, self.m_eq,
                      self.k_note, self.rows)
        self.play(*gone.to(0.0), FadeOut(self.pay), run_time=1.2)
        self.remove(self.paths, self.hero_path, self.legend, self.band,
                    self.band_lbl, self.zero, self.today, self.m_eq,
                    self.k_note, self.rows, self.pay)
        self.nar.finish(self)

        axes = ThreeDAxes(
            x_range=(0, XU, 1), y_range=(0, YU, 1), z_range=(Z_LO, Z_HI, 0.4),
            width=8.0, height=5.2, depth=2.8,
        )
        axes.set_stroke(GREY_D, width=1.8)
        axes.shift(UP * 0.35)          # centre the tilted map in the frame
        self.axes = axes
        # Only the floor is ever drawn. ThreeDAxes puts its z-axis at the
        # (0, 0) corner, which is exactly where the notch is, so it renders as
        # a ticked spike poking up through the surface. The height is named by
        # the legend and read off the callouts instead.
        self.floor = floor = VGroup(axes.x_axis, axes.y_axis)

        self.cap.show("Lookback across, holding period up.", "s2.floor",
                      hold=False)
        self.play(ShowCreation(floor), run_time=1.2)
        self.play(stagger([FadeIn(t) for t in self.tick_labels()],
                          lag_ratio=0.06), run_time=1.5)
        self.nar.finish(self)

        # The hinge of the video: two minutes of work, and it is one dot.
        star_at = axes.c2p(np.log2(6), 0.0, 0.02)
        collapsed = DotCloud(np.tile(star_at, (pn.N, 1)), radius=0.085)
        collapsed.data["rgba"][:] = np.array([*color_to_rgb(C_HOT), 1.0])
        self.cap.show("All of it is one dot.", "s2.dot", hold=False)
        self.play(Transform(self.column, collapsed),
                  FadeOut(self.k_lbl, shift=DOWN * 0.2), run_time=1.6)
        self.remove(self.k_lbl)
        self.star = self.column
        self.play(FlashAround(self.star, color=C_HOT, buff=0.3), run_time=1.4)
        self.nar.finish(self)

        # All 1152 of them, at zero height.
        self.cap.show("Every pair is a different strategy.", "s2.all",
                      hold=False)
        self.dots = self.lattice(flat_z=True)
        self.play(FadeIn(self.dots), run_time=1.8)
        self.nar.finish(self)

        # The heights go on while the camera is straight down, so the frame
        # changes by almost nothing. That is what earns the camera move.
        self.cap.show("Each one has a height: what it paid.", "s2.height",
                      hold=False)
        flat_dots, risen = self.lattice(True), self.lattice(False)
        self.play(Transform(self.dots, risen),
                  self.star.animate.move_to(
                      self.axes.c2p(np.log2(6), 0.0, self.g(6, 1))),
                  run_time=2.4)
        self.nar.finish(self)
        self.wait(3.4)                           # the wordless frame

        # Say it by doing it again. A long line over a frozen picture is the
        # same defect from the other side (ANTI-PATTERN #22): the claim is
        # that this motion is invisible from here, so the motion has to happen
        # while the claim is being made.
        self.nar.cue(self, "s2.nothing")
        for _ in range(2):
            self.play(Transform(self.dots, flat_dots), run_time=1.1)
            self.play(Transform(self.dots, risen), run_time=1.1)
        self.nar.finish(self)

    # ── §3  the tilt ─────────────────────────────────────────────────────
    def s3_tilt(self):
        self.nar.wait(self, "s3.move", tail=0.15)

        # The reveal. Nothing on stage changes; only the viewpoint does.
        orbit(self, theta=THETA, phi=PHI, run_time=3.6)
        self.wait(2.8)                           # let it land, wordless

        assert_in_frame_3d(self, axis_labels=self.axis_labels)

        self.cap.show("They were always at those heights.", "s3.landscape",
                      hold=False)
        legend = Text("height  =  return, % per month", font=FONT,
                      font_size=21).set_color(C_NEUT)
        fix(legend.move_to(np.array([-4.45, 2.72, 0])))
        assert_in_frame_3d(self, legend=legend)
        self.play(FadeIn(legend), run_time=0.6)
        self.legend_hud = legend
        self.nar.finish(self)

        # The dots become the surface they were always sampling. They are
        # coincident with it by construction (ANTI-PATTERN #17), so they go as
        # it arrives rather than fighting it for pixels.
        surf = self.landscape_surface(GRID)
        mesh = mesh_for(surf, resolution=(17, 13), color=WHITE, width=1.0,
                        opacity=0.45)
        self.play(ShowCreation(surf), FadeOut(self.dots),
                  FadeOut(self.star), run_time=2.4)
        self.remove(self.dots, self.star)
        self.play(ShowCreation(mesh), run_time=1.2)
        self.surf, self.mesh = surf, mesh

        spin(self, 5.4, speed=-4.0)              # wordless: let it be a shape

        self.cap.show("Orange ground: buying winners pays.", "s3.ridge",
                      hold=False)
        self.peak = self.marker(RIDGE, C_UP)
        self.play(FadeIn(self.peak.dot, scale=0.5), run_time=0.7)
        self.value_label(self.peak, UP * 0.55)
        self.drift()

        self.cap.show("Blue ground: the same rule loses.", "s3.corner",
                      hold=False)
        self.basin = self.marker(BASIN, C_DOWN)
        self.play(FadeIn(self.basin.dot, scale=0.5), run_time=0.7)
        self.value_label(self.basin, RIGHT * 0.75 + UP * 0.2)
        self.drift()

        self.cap.show("Mean reversion, on the same map.", "s3.tie",
                      hold=False)
        self.notch = self.marker(NOTCH, C_DOWN)
        self.play(FadeIn(self.notch.dot, scale=0.5), run_time=0.7)
        self.value_label(self.notch, LEFT * 0.7 + DOWN * 0.4)
        assert_no_overlap([("peak", self.peak.value, "basin", self.basin.value),
                           ("notch", self.notch.value, "basin",
                            self.basin.value)])
        self.play(stagger([FlashAround(self.notch.value, color=C_DOWN,
                                       buff=0.1),
                           FlashAround(self.basin.value, color=C_DOWN,
                                       buff=0.1)], lag_ratio=0.5),
                  run_time=2.2)
        self.drift()
        self.wait(2.4)                           # the two corners, wordless

    # ── §4  why the map has that shape ───────────────────────────────────
    def s4_shape(self):
        self.cap.show("Three things went into this market.", "s4.shape",
                      hold=False)
        self.play(FadeOut(self.peak.value), FadeOut(self.basin.value),
                  FadeOut(self.notch.value), run_time=0.7)
        self.nar.finish(self)

        for beat, mk, text, off in [
            ("s4.bounce", self.notch, "today's noise,\ngone tomorrow",
             LEFT * 0.55 + DOWN * 0.75),
            ("s4.diffusion", self.peak, "news priced in\nover 16 months",
             UP * 0.95),
            ("s4.overshoot", self.basin, "the overshoot,\nhanded back",
             RIGHT * 1.35 + DOWN * 0.45),
        ]:
            self.cap.show(text.replace("\n", " "), beat, hold=False)
            mk.note = self.note_label(mk, text, off)
            self.play(Write(mk.note),
                      FlashAround(mk.dot, color=C_HOT, buff=0.12),
                      run_time=1.5)
            for other in (self.notch, self.peak, self.basin):
                if other is not mk and other.note is not None:
                    assert_no_overlap([("note", mk.note, "note", other.note)])
            self.drift()

        # One row of the map, drawn on the map: hold for a month, and walk the
        # lookback. It crosses zero twice, which is the whole argument.
        self.cap.show("One line across it: hold for a month.", "s4.slice",
                      hold=False)
        cut = slice_curve(self.axes, height_uv, (0, XU), direction="x",
                          const=0.0, color=C_HOT, width=5.0, lift=0.04)
        self.play(ShowCreation(cut), run_time=2.2)
        self.nar.finish(self)
        self.cut = cut

        self.cap.show("Neither camp is wrong.", "s4.camps", hold=False)
        walker = dot3d(self.axes.c2p(0, 0, self.g(1, 1) + 0.06), C_HOT,
                       radius=0.085)
        self.play(FadeIn(walker, scale=0.5), run_time=0.5)
        self.play(walker.animate.move_to(
            self.axes.c2p(np.log2(6), 0, self.g(6, 1) + 0.06)), run_time=1.8)
        self.play(walker.animate.move_to(
            self.axes.c2p(XU, 0, self.g(48, 1) + 0.06)), run_time=2.2)
        self.play(ShowPassingFlash(cut.copy().set_stroke(WHITE, 7),
                                   time_width=0.4), run_time=2.0)
        self.nar.finish(self)
        self.walker = walker
        spin(self, 3.2, speed=-3.0)              # the whole argument, wordless

    # ── §5  what the map does not know ───────────────────────────────────
    def s5_limits(self):
        self.cap.show("Two things it is not telling you.", "s5.gross",
                      hold=False)
        notes = Dimmer(self.notch.note, self.peak.note, self.basin.note)
        self.play(*notes.to(0.0), FadeOut(self.walker), FadeOut(self.cut),
                  run_time=0.9)
        self.remove(self.notch.note, self.peak.note, self.basin.note,
                    self.walker, self.cut)
        self.nar.finish(self)

        cost = Text(f"cost:  {COST:.2f}% of everything traded", font=FONT,
                    font_size=22).set_color(C_COST)
        fix(cost.move_to(np.array([-4.45, 2.24, 0])))
        assert_in_frame_3d(self, cost=cost)
        assert_no_overlap([("legend", self.legend_hud, "cost", cost)])
        self.nar.cue(self, "s5.cost")
        self.drift()

        # The same 1152 backtests with the turnover charge in them: a real
        # second computation, morphed into rather than cut to.
        net = self.landscape_surface(GRID_NET)
        net_mesh = mesh_for(net, resolution=(17, 13), color=WHITE, width=1.0,
                            opacity=0.45)
        self.cap.show("Charge the turnover, and the near edge sags.",
                      "s5.sag", hold=False)
        self.play(FadeIn(cost), run_time=0.5)
        self.play(Transform(self.surf, net), Transform(self.mesh, net_mesh),
                  self.notch.dot.animate.move_to(
                      self.axes.c2p(0, 0, self.gn(*NOTCH) + 0.06)),
                  run_time=2.8)
        self.value_label(self.notch, LEFT * 0.7 + DOWN * 0.4, grid=GRID_NET)
        self.nar.finish(self)
        self.cost_lbl = cost

        spin(self, 4.4, speed=-4.0)              # wordless

        # The bigger limitation: the map is an estimate, drawn once.
        dim = Dimmer(self.surf, self.mesh, self.floor, self.axis_labels,
                     self.notch.dot, self.peak.dot, self.basin.dot)
        self.cap.show("And I drew it from the past.", "s5.worse", hold=False)
        self.play(*dim.to(0.3), FadeOut(cost), FadeOut(self.notch.value),
                  run_time=1.1)
        self.nar.finish(self)

        # The crest itself: for each holding period, the lookback that paid
        # most. It is the one line on the map anybody actually wants, and it
        # is the line that was estimated -- so it is what is left lit while
        # the point about estimation is made.
        crest = self.ridge_line(GRID_NET)
        self.nar.cue(self, "s5.one_path")
        self.play(ShowCreation(crest), run_time=2.0)
        self.play(ShowPassingFlash(crest.copy().set_stroke(WHITE, 8),
                                   time_width=0.35), run_time=2.4)
        self.play(crest.animate.set_stroke(opacity=0.25), run_time=1.6)
        self.nar.finish(self)
        self.play(*dim.restore(), FadeOut(crest), run_time=1.2)

    # ── §6  payoff ───────────────────────────────────────────────────────
    def s6_payoff(self):
        # The axis furniture goes rather than dims: the payoff is about the
        # shape, and dimmed floor labels sat underneath the answer text (the
        # AUDIT sweep flagged them against it at t=375s).
        stage = Dimmer(self.surf, self.mesh, self.floor,
                       self.notch.dot, self.peak.dot, self.basin.dot)
        self.cap.clear(run_time=0.5)
        # 0.2 took the map below the brightness the blank-frame check counts
        # as visible, and the 1.6s of room before the question came back
        # registered as 2.0s of empty screen. 0.45 still reads as "pushed
        # back" and the frame is never actually empty.
        self.play(*stage.to(0.45), FadeOut(self.legend_hud),
                  FadeOut(self.axis_labels), run_time=1.1)

        # The opening question, verbatim and in its opening styling.
        q = Text(QUESTION, font=FONT, font_size=33).set_color(C_HOT)
        fix(q.move_to(np.array([0, 0.75, 0])))
        assert_in_frame_3d(self, question=q)
        self.wait(1.0)                           # a beat before it returns
        self.nar.cue(self, "s6.restate")
        self.play(Write(q), run_time=2.0)
        self.nar.finish(self)

        ans = Text("How far back you look,\nand how long you hold.",
                   font=FONT, font_size=36).set_color(WHITE)
        fix(ans.move_to(np.array([0, -1.35, 0])))
        assert_in_frame_3d(self, answer=ans)
        assert_no_overlap([("question", q, "answer", ans)])
        self.nar.cue(self, "s6.answer")
        self.play(Write(ans), run_time=2.2)
        self.nar.finish(self)

        self.wait(2.2)                           # let the answer sit
        self.nar.cue(self, "s6.same")
        # The axis furniture stays off from here on. The closing spin carries
        # the viewpoint ~37 degrees away from THETA, and a title fixed to the
        # bottom of the screen stops pointing along the axis it names; the
        # payoff frame wants the shape and the two corners, nothing else.
        self.play(*stage.restore(), FadeOut(q), FadeOut(ans), run_time=1.6)
        self.play(stagger([FlashAround(self.basin.dot, color=C_DOWN,
                                       buff=0.12),
                           FlashAround(self.peak.dot, color=C_UP, buff=0.12)],
                          lag_ratio=0.45), run_time=2.4)
        self.nar.finish(self)

        self.nar.cue(self, "s6.close")
        spin(self, self.nar.duration("s6.close") + 3.4, speed=-4.0)
        self.cap.clear(run_time=0.8)
        self.wait(1.4)

    # ═════════════════════════════════════════════════════════════════════
    # builders
    # ═════════════════════════════════════════════════════════════════════

    def drift(self, speed=3.0, chunk=3.5):
        """Spend what is left of the current line on a slow camera drift.

        A long line over a still 3D frame is two defects at once (ANTI-PATTERN
        #22, and verify_render check [3] fails a freeze past 11s). The map is
        a solid, so the honest thing to put under the words is a few degrees
        of rotation -- and the labels track their markers through it, so
        nothing comes unstuck. The direction alternates, which keeps the
        viewpoint swaying around THETA instead of walking away from it.
        """
        c = self.nar.cues[-1]
        while True:
            left = c["t"] + c["duration"] + self.nar.tail - float(self.time)
            if left <= 5.0:
                break
            theta = self.camera.frame.get_euler_angles()[0] / DEG
            sign = -1.0 if theta - THETA > 1.0 else 1.0
            spin(self, min(chunk, left - 1.2), speed=sign * speed)
        self.nar.finish(self)

    def g(self, k, h, grid=None):
        """What the (k, h) strategy paid, straight out of the backtest grid."""
        grid = GRID if grid is None else grid
        return float(grid[pn.K_VALUES.tolist().index(k),
                          pn.H_VALUES.tolist().index(h)])

    def gn(self, k, h):
        return self.g(k, h, GRID_NET)

    # ── the price panel ──────────────────────────────────────────────────

    def price_path(self, i, scale, color, width=1.0, opacity=1.0):
        pts = np.array([[x_of(m), PYC + _W[m, i] * scale, 0.0]
                        for m in range(HIST + 1)])
        p = VMobject()
        p.set_points_as_corners(pts)
        p.set_stroke(color, width=width, opacity=opacity)
        p.set_flat_stroke(False)
        # ANTI-PATTERN #14: the lookback band is a filled VMobject, and under
        # ThreeDScene's depth testing a fill swallows whatever is drawn over
        # it however far in front that is -- measured here as 240 price paths
        # ending dead at the band's left edge. The whole price panel is flat
        # 2D content seen from straight above, so it comes out of the depth
        # test entirely and draw order decides, which is what we want.
        return flat(p)

    def band_for(self, k, opacity=0.09):
        """The lookback window, marked on the chart.

        The wash is a Square3D and not a filled Rectangle, and that is not a
        style choice. ANTI-PATTERN #18: a VMobject's fill is drawn by winding
        number across the batch it is rendered in, so a filled rectangle
        batched with 240 stroke-only price paths cancels every one of them
        inside its own area. Measured -- the fan stopped dead at the band's
        left edge, and it stopped whether the band was in front or behind,
        depth-tested or not. A Surface has no winding, so the paths survive
        and the wash tints them. The bright edge stays a VMobject: a stroke
        has no fill to wind.
        """
        w = x_of(HIST) - x_of(HIST - k)
        centre = np.array([(x_of(HIST) + x_of(HIST - k)) / 2, PYC, PZ])
        wash = Square3D(side_length=1, color=C_HOT, opacity=opacity)
        wash.set_width(w, stretch=True).set_height(5.4, stretch=True)
        wash.set_shading(0, 0, 0)
        wash.move_to(centre)
        edge = Rectangle(width=w, height=5.4)
        edge.set_fill(opacity=0.0)
        edge.set_stroke(C_HOT, width=2.0, opacity=0.55)
        edge.move_to(centre)
        return Group(wash, flat(edge))

    def relabel_band(self, k):
        """Swap the band's caption without morphing one wording into another.

        "the last 6 months" and "the last month" have different glyph counts,
        so a Transform between them renders as a pile of overlapping letters
        for the whole 0.9s (ANTI-PATTERN #10, and #4 for the frames where both
        are legible at once). The lag_ratio takes the old one off before the
        new one arrives.
        """
        new = self.band_label_for(k)
        old = self.band_lbl
        self.band_lbl = new
        return AnimationGroup(FadeOut(old, shift=UP * 0.18),
                              FadeIn(new, shift=UP * 0.18), lag_ratio=0.55)

    def band_label_for(self, k):
        """The caption above the lookback window.

        Right-aligned to the window's right edge, which is "today" and never
        moves, rather than centred on the window -- centred, the four-year
        version sat on top of the formula in the top-left corner (caught by
        the AUDIT sweep at t=104s).
        """
        months = f"the last {k} months" if k > 1 else "the last month"
        t = Text(months, font=FONT, font_size=19).set_color(C_HOT)
        t.set_opacity(0.85)
        t.next_to(self.band_for(k), UP, buff=0.14)
        t.set_x(x_of(HIST) - t.get_width() / 2)
        return flat(t)

    def light_paths(self, winners, losers):
        """Recolour the fan to the deciles the current lookback picks out."""
        anims = []
        others = [i for i in range(pn.N) if i != HERO]
        for p, idx in zip([*self.paths, self.hero_path], [*others, HERO]):
            if idx in winners:
                anims.append(p.animate.set_stroke(C_UP, width=1.9,
                                                  opacity=1.0))
            elif idx in losers:
                anims.append(p.animate.set_stroke(C_DOWN, width=1.9,
                                                  opacity=1.0))
            else:
                anims.append(p.animate.set_stroke(C_NEUT, width=1.0,
                                                  opacity=0.28))
        return AnimationGroup(*anims, lag_ratio=0.0)

    def end_cloud(self):
        pts = np.array([[x_of(HIST) + COL_JITTER[i],
                         PYC + _W[-1, i] * S1_SCALE, 0.0]
                        for i in range(pn.N)])
        c = DotCloud(pts, radius=0.042)
        c.data["rgba"][:] = np.array([*color_to_rgb(C_NEUT), 1.0])
        return flat(c)

    def column_cloud(self, rank, winners, losers):
        pts = np.array([[COL_X + COL_JITTER[i], col_y(rank[i]), 0.0]
                        for i in range(pn.N)])
        c = DotCloud(pts, radius=0.042)
        rgba = np.tile(np.array([*color_to_rgb(C_NEUT), 1.0]), (pn.N, 1))
        for i in range(pn.N):
            if i in winners:
                rgba[i] = [*color_to_rgb(C_UP), 1.0]
            elif i in losers:
                rgba[i] = [*color_to_rgb(C_DOWN), 1.0]
        c.data["rgba"][:] = rgba
        return flat(c)

    def param_label(self, k, h=None):
        """The parameters, as far as the video has admitted they exist.

        §1 shows only k, because §2's whole move is that the second number was
        there the entire time and nobody looked at it.
        """
        tex = rf"k = {k}\ \text{{mo}}"
        if h is not None:
            tex += rf" \qquad h = {h}\ \text{{mo}}"
        t = Tex(tex)
        t.scale(0.62).set_color(C_HOT)
        fix(t.move_to(np.array([-4.7, -3.2, 0])))
        return t

    def payoff_label(self, value):
        t = Tex(rf"{value:+.2f}\,\%\ \text{{per month}}")
        t.scale(0.82).set_color(C_UP if value > 0 else C_DOWN)
        fix(t.move_to(np.array([3.3, -3.2, 0])))
        return t

    def add_result_row(self, k, value):
        """Keep each answer on screen, so the three can be compared at once."""
        lab = Tex(rf"k = {k}").scale(0.6).set_color(C_NEUT)
        val = Tex(rf"{value:+.2f}").scale(0.6)
        val.set_color(C_UP if value > 0 else C_DOWN)
        row = VGroup(lab, val)
        lab.move_to(np.array([4.85, 0, 0]))
        val.move_to(np.array([6.05, 0, 0]))
        row.shift(UP * {1: 1.15, 6: 0.55, 48: -0.05}[k])
        fix(row)
        assert_in_frame_3d(self, **{f"row_{k}": row})
        self.rows.add(row)
        self.play(FadeIn(row, shift=RIGHT * 0.15), run_time=0.5)
        return row

    # ── the map ──────────────────────────────────────────────────────────

    def tick_labels(self):
        out = []
        for k in K_TICKS:
            t = Text(str(k), font=FONT, font_size=23).set_color(GREY_A)
            t.move_to(self.axes.c2p(np.log2(k), 0, 0)
                      + np.array([0, -0.30, 0]))
            out.append(flat(t))
        for h in H_TICKS:
            t = Text(str(h), font=FONT, font_size=23).set_color(GREY_A)
            t.move_to(self.axes.c2p(0, np.log2(h), 0)
                      + np.array([-0.36, 0, 0]))
            out.append(flat(t))
        # The two axis titles are HUD, not floor paint. On the floor they are
        # stuck between two constraints that cannot both be met: seen from
        # straight down the title has to sit close to the axis or it runs off
        # the bottom of the frame, and seen at phi = 64 a world gap in y is
        # foreshortened by cos(64) = 0.44, so the same gap is not enough to
        # keep the tick numbers off it. Fixed in frame, neither applies.
        xt = Text("lookback  k  (months)", font=FONT, font_size=24)
        xt.set_color(GREY_A)
        fix(xt.move_to(np.array([0.6, -3.35, 0])))
        yt = Text("hold  h  (months)", font=FONT, font_size=24)
        yt.set_color(GREY_A).rotate(PI / 2)
        fix(yt.move_to(np.array([-5.6, 0.4, 0])))
        out += [xt, yt]
        self.axis_labels = VGroup(*out)
        return out

    def lattice(self, flat_z):
        """Every backtest on the grid, as one dot: 48 lookbacks x 24 holds."""
        pts = [self.axes.c2p(np.log2(k), np.log2(h),
                             0.0 if flat_z else self.g(int(k), int(h)))
               for k in pn.K_VALUES for h in pn.H_VALUES]
        c = DotCloud(np.array(pts), radius=0.024)
        c.data["rgba"][:] = np.array([*color_to_rgb(WHITE), 0.9])
        return c

    def landscape_surface(self, grid):
        """The 1152 numbers as a surface, coloured by their own sign."""
        s = surface(lambda u, v: height_uv(u, v, grid), axes=self.axes,
                    color=C_UP, opacity=0.92, resolution=(76, 60),
                    # The shadow term was 0.5, which rendered the whole
                    # camera-facing slope black -- measured on a still, a
                    # wedge across the middle of the map with a jagged edge
                    # that reads as a hole in the geometry.
                    shading=(0.2, 0.1, 0.15))
        z0 = self.axes.c2p(0, 0, 0)[2]
        z1 = self.axes.c2p(0, 0, 1)[2] - z0
        up, down = np.array(color_to_rgb(C_UP)), np.array(color_to_rgb(C_DOWN))

        def rgba(p):
            v = (p[2] - z0) / z1
            base = up if v >= 0 else down
            a = min(1.0, abs(v) / (1.22 if v >= 0 else 0.6)) ** 0.75
            return [*(base * (0.55 + 0.45 * a)), 1.0]

        s.set_color_by_rgba_func(rgba)
        return s

    def ridge_line(self, grid):
        """The crest: for each holding period, the lookback that paid most."""
        best_k = pn.ridge(grid)
        pts = [self.axes.c2p(np.log2(k), np.log2(h),
                             self.g(int(k), int(h), grid) + 0.05)
               for k, h in zip(best_k, pn.H_VALUES)]
        line = VMobject()
        line.set_points_smoothly(np.array(pts))
        line.set_stroke(C_HOT, width=4.5, opacity=1.0)
        line.set_flat_stroke(False)
        return line

    def marker(self, kh, colour, grid=None):
        k, h = kh
        world = self.axes.c2p(np.log2(k), np.log2(h),
                              self.g(k, h, grid) + 0.06)
        return Marker(dot3d(world, colour, radius=0.075), kh, world)

    def _at(self, world, offset):
        """A fixed screen position beside a world point.

        ANTI-PATTERN #15: world coordinates say nothing about where a point
        lands on screen once the camera is tilted, so the label is placed by
        projecting through the camera's own view matrix.
        """
        p = project(self.camera.frame, world)
        return np.array([p[0], p[1], 0.0]) + offset

    def track(self, lbl, world, offset):
        """Keep a fixed-in-frame label beside a world point as the camera moves.

        Without this, every label would have to be taken down before the map
        could rotate -- which is what would force the long lines in §3 to play
        over a frozen frame.
        """
        lbl.add_updater(lambda m: m.move_to(self._at(world, offset)))
        return lbl

    def value_label(self, mk, offset, grid=None):
        k, h = mk.kh
        value = self.g(k, h, grid)
        world = self.axes.c2p(np.log2(k), np.log2(h), value + 0.06)
        lbl = Text(f"{value:+.2f}", font=FONT, font_size=27)
        lbl.set_color(C_UP if value > 0 else C_DOWN)
        fix(lbl.move_to(self._at(world, offset)))
        assert_in_frame_3d(self, **{f"value_{k}_{h}": lbl})
        self.play(Write(lbl), run_time=0.8)
        self.track(lbl, world, offset)
        mk.value = lbl
        return lbl

    def note_label(self, mk, text, offset):
        lbl = Text(text, font=FONT, font_size=22).set_color(C_HOT)
        fix(lbl.move_to(self._at(mk.world, offset)))
        assert_in_frame_3d(self, **{"note_%d_%d" % mk.kh: lbl})
        return self.track(lbl, mk.world, offset)
