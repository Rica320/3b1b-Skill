"""
"When is a gap big enough to bet on?"

A narrated explainer on mean reversion and pairs trading. Everything drawn is
computed by market.py -- the prices, the spread, the rolling band, the
z-score, the trades and their P&L -- so no frame can assert something the
arithmetic does not support.

    TTS:     ../../env/bin/python \
                 ../../skills/3b1b-math-animation/scripts/tts.py script.yaml --out audio
    Render:  bash ../../skills/3b1b-math-animation/scripts/render.sh \
                 mean_reversion.py MeanReversion
    Mux:     ../../env/bin/python \
                 ../../skills/3b1b-math-animation/scripts/mux_audio.py \
                 videos/MeanReversion.mp4 --cues narration_cues.json
    Verify:  ../../env/bin/python .../verify_render.py videos/MeanReversion.mp4 \
                 --meta render_meta.json
             ../../env/bin/python .../verify_audio.py \
                 videos/MeanReversion_narrated.mp4 --cues narration_cues.json
             ../../env/bin/python verify_market.py     # every spoken number
    Audit:   AUDIT=1 ... manimgl mean_reversion.py MeanReversion -l

Spine (full version in SPINE.md)
  QUESTION    two stocks ride the same market, so the only interesting number
              is the distance between them. When is that distance big enough
              to bet on?
  MOTIVATION  the obvious answer -- a dollar threshold -- dies on this pair's
              own data: two dollars is silent for 110 days, and forty cents
              fires on 98 of the next 130. A dollar is a fact about dollars.
  BUILD       so take the unit from the gap's own recent past: a rolling mean
              and a rolling sigma. The band breathes. Straighten it into rails
              and the curve comes with it -- that is the z-score. Enter at two
              sigma, exit at zero: six trades, six winners, $3.75, of which
              the quiet ones kept seven cents and four after costs.
  PAYOFF      then the held-out data, where the pull ends. The gap walks
              eleven dollars away, the rolling mean follows it down, and the
              z-score never passes -2.5. One trade gives back $9.32. The ruler
              was only ever measuring an assumption.

Carried metaphor: THE GAP -- the vertical distance between two price paths,
which becomes a curve, then a curve on a breathing band, then the same curve
on flat rails, then the thing that walks away.

Colour
  BLUE_C   stock A's price
  TEAL_C   stock B's price
  ORANGE   the gap -- the carried object, from S1 to the end
  GREEN_C  the ruler: rolling mean, the sigma band, the +/-2 rails
  RED_C    what it costs you: the cost strip, and the loss
  YELLOW   transient emphasis only -- the driving question, the current focus
  GREY_B   scaffolding: axes, ticks, connective labels

Green never means "profit"; it means "what normal is assumed to be", which is
exactly the thing that fails at the end.
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

import market as mk                                       # noqa: E402
from manim_helpers import (                               # noqa: E402
    dot, label, Caption, Dimmer, hold, stagger, dump_meta,
    equation, box_around, assert_in_frame, assert_no_overlap,
    audit_text_overlaps, FONT,
)
from narration import Narrator                            # noqa: E402

# ── colour ───────────────────────────────────────────────────────────────
C_A = BLUE_C            # stock A
# Stock B was TEAL_C until the first contact sheet: teal renders green enough
# that "buy B" sitting on the green sigma rails in §3 read as the same colour
# as the ruler. Violet collides with nothing else on the palette.
C_B = PURPLE_B          # stock B
C_GAP = ORANGE          # the gap: the carried object
C_RULER = GREEN_C       # rolling mean, sigma band, the rails
C_COST = RED_C          # what it costs you
C_HOT = YELLOW          # transient emphasis only
C_NEUT = GREY_B

# ── the window onto the data ─────────────────────────────────────────────
# Day 60 is the first day a 60-day trailing window exists, so it is where
# every chart starts; 60..300 is the 240-day stretch the rule is built on,
# and 300..420 is the held-out stretch S4 reveals.
D0, D_MID, D_END = 60, mk.BREAK_DAY, mk.DAYS
D_QUIET, D_LOUD = 170, D_MID          # the two volatility stretches
D_WIDEST = 197                        # largest gap in the in-sample stretch
D_LOW = 413                           # the day the gap is furthest from home

QUESTION = "When is a gap big enough to bet on?"

# Panel geometry. The two S4 panels share the S1-S3 panel's x mapping exactly
# (same width, same centre x, same x_range), which is what lets one dashed
# line at day 413 read across both of them.
PX, PW = 0.35, 10.6
GAP_Y, GAP_H = -0.60, 4.80             # the single panel, S1-S3
TOP_Y, TOP_H = 1.35, 2.50              # S4, in dollars
BOT_Y, BOT_H = -2.15, 2.10             # S4, in sigmas

Y_GAP = (-6.5, 4.5)                    # display range shared by dollars and
Y_TOP = (-13.0, 4.5)                   # sigmas in S1-S3; S4 zooms the dollars
Y_PRICE = (42.0, 66.0)


class MeanReversion(Scene):

    def wait(self, *args, **kwargs):
        r = super().wait(*args, **kwargs)
        if os.environ.get("AUDIT"):
            audit_text_overlaps(self)
        return r

    # ── construction ─────────────────────────────────────────────────────
    def construct(self):
        self.camera.background_color = BLACK
        self.m = mk.build()
        self.nar = Narrator(_HERE / "script.yaml", _HERE / "audio")
        self.cap = Caption(self, narrator=self.nar)

        for name, fn in [("s0", self.s0_question), ("s1", self.s1_dollars),
                         ("s2", self.s2_ruler), ("s3", self.s3_rule),
                         ("s4", self.s4_holdout), ("s5", self.s5_payoff)]:
            t0 = self.time
            fn()
            print(f"[TIMING] {name} start={t0:6.1f}s dur={self.time - t0:5.1f}s")

        dump_meta(self, str(_HERE / "render_meta.json"))
        self.nar.dump(_HERE / "narration_cues.json", scene=self)
        self.nar.report()

    # ── drawing primitives ───────────────────────────────────────────────
    #
    # Axes are used only as coordinate mappers and are never added to the
    # scene: with an x_range starting at day 60, ManimGL would draw its own
    # y-axis at data x=0, which is off the panel. The visible frame is built
    # explicitly instead, which also keeps tick labels under our control.

    @staticmethod
    def mapper(x_range, y_range, width, height, centre):
        """An Axes positioned by its DATA box, not its mobject box.

        ManimGL anchors an Axes at data (0, 0). Neither of these panels
        contains that point -- day 60 to 300, price 42 to 66 -- so the
        mobject's bounding box extends far past the plotted region and
        move_to() centres the wrong rectangle. Shifting by c2p of the range
        midpoint puts the visible panel where it was asked for.
        """
        ax = Axes(x_range=(x_range[0], x_range[1], 60),
                  y_range=(y_range[0], y_range[1], 2),
                  width=width, height=height)
        mid = ax.c2p((x_range[0] + x_range[1]) / 2,
                     (y_range[0] + y_range[1]) / 2)
        ax.shift(np.asarray(centre, dtype=float) - mid)
        return ax

    @staticmethod
    def series(ax, xs, ys, color, width=3.0):
        """A data series as a polyline. Two series built from the same xs have
        the same point count, so ReplacementTransform between them is an exact
        point-for-point morph -- which is what makes the S2 rescale honest."""
        c = VMobject()
        c.set_points_as_corners([ax.c2p(x, y) for x, y in zip(xs, ys)])
        c.set_stroke(color, width=width)
        c.set_fill(opacity=0.0)
        return c

    @staticmethod
    def region(ax, xs, lo, hi, color, opacity=0.20):
        """The filled area between two series. Same point-count guarantee, so
        the wiggly sigma band morphs cleanly into the flat +/-2 strip."""
        pts = ([ax.c2p(x, y) for x, y in zip(xs, hi)]
               + [ax.c2p(x, y) for x, y in zip(xs[::-1], lo[::-1])])
        p = VMobject()
        p.set_points_as_corners(pts + [pts[0]])
        p.set_fill(color, opacity=opacity)
        p.set_stroke(width=0)
        return p

    @staticmethod
    def hline(ax, y, x_lo, x_hi, color, width=2.0, dashed=False, opacity=1.0):
        a, b = ax.c2p(x_lo, y), ax.c2p(x_hi, y)
        ln = DashedLine(a, b, dash_length=0.09) if dashed else Line(a, b)
        ln.set_stroke(color, width=width, opacity=opacity)
        return ln

    @staticmethod
    def veil(ax, x_lo, x_hi, y_range, opacity=0.78):
        """Black out the half of the chart that is not being discussed.
        Rule 2: one idea on screen. Dimmer works on mobjects; this works on a
        region, which is what a "these hundred and ten days" claim needs."""
        c0, c1 = ax.c2p(x_lo, y_range[0]), ax.c2p(x_hi, y_range[1])
        r = Rectangle(width=abs(c1[0] - c0[0]), height=abs(c1[1] - c0[1]))
        r.move_to((c0 + c1) / 2)
        r.set_fill(BLACK, opacity=opacity)
        r.set_stroke(width=0)
        return r

    def chrome(self, ax, x_lo, x_hi, y_range, y_ticks, fmt, baseline=0.0,
               tick_size=20):
        """Axis lines and y tick labels for a panel."""
        base = self.hline(ax, baseline, x_lo, x_hi, GREY_D, width=1.6)
        left = Line(ax.c2p(x_lo, y_range[0]), ax.c2p(x_lo, y_range[1]))
        left.set_stroke(GREY_D, width=1.6)
        labels = VGroup()
        for v in y_ticks:
            t = Tex(fmt(v)).scale(tick_size / 42.0).set_color(C_NEUT)
            t.next_to(ax.c2p(x_lo, v), LEFT, buff=0.16)
            labels.add(t)
        return VGroup(base, left, labels), labels

    def days(self, lo, hi):
        return list(range(lo, hi + 1))

    # ── §0  the question ─────────────────────────────────────────────────
    def s0_question(self):
        m = self.m
        xs = self.days(D0, D_MID)
        self.p_ax = self.mapper((D0, D_MID), Y_PRICE, PW, 4.60,
                                np.array([PX, -0.55, 0]))
        chrome, _ = self.chrome(self.p_ax, D0, D_MID, Y_PRICE,
                                [45, 50, 55, 60, 65],
                                lambda v: rf"\$ {v}", baseline=Y_PRICE[0])
        self.p_chrome = chrome

        path_a = self.series(self.p_ax, xs, m["p_a"][D0:D_MID + 1], C_A)
        path_b = self.series(self.p_ax, xs, m["p_b"][D0:D_MID + 1], C_B)
        lbl_a = label("A", 30, C_A).next_to(self.p_ax.c2p(D_MID, m["p_a"][D_MID]),
                                            RIGHT, buff=0.16)
        lbl_b = label("B", 30, C_B).next_to(self.p_ax.c2p(D_MID, m["p_b"][D_MID]),
                                            RIGHT, buff=0.16)
        assert_in_frame(chrome=chrome, path_a=path_a, path_b=path_b,
                        lbl_a=lbl_a, lbl_b=lbl_b)

        self.cap.show("Two companies. One industry.", "s0.open", hold=False)
        self.play(ShowCreation(chrome), run_time=0.9)
        self.play(ShowCreation(path_a), ShowCreation(path_b), run_time=2.6)
        self.play(FadeIn(lbl_a), FadeIn(lbl_b), run_time=0.5)
        self.nar.finish(self)

        # The market move is the thing a pairs trade is built to ignore, so it
        # is worth seeing that it dwarfs everything else on the chart.
        self.cap.show("One price tells you almost nothing.", "s0.weather",
                      hold=False)
        self.play(stagger([Indicate(path_a, color=C_A, scale_factor=1.0),
                           Indicate(path_b, color=C_B, scale_factor=1.0)],
                          lag_ratio=0.35), run_time=1.8)
        self.nar.finish(self)

        # The gap, as a literal vertical distance, at every fifth day.
        comb = VGroup()
        for d in range(D0, D_MID + 1, 5):
            seg = Line(self.p_ax.c2p(d, m["p_b"][d]),
                       self.p_ax.c2p(d, m["p_a"][d]))
            seg.set_stroke(C_GAP, width=1.8, opacity=0.55)
            comb.add(seg)
        self.comb = comb

        self.cap.show("But the distance between them holds.", "s0.gap",
                      hold=False)
        self.play(stagger([ShowCreation(s) for s in comb], lag_ratio=0.012),
                  run_time=2.0)
        # ...and then, here, it stretches.
        widest = Line(self.p_ax.c2p(D_WIDEST, m["p_b"][D_WIDEST]),
                      self.p_ax.c2p(D_WIDEST, m["p_a"][D_WIDEST]))
        widest.set_stroke(C_HOT, width=5.0)
        q_mark = Tex("?").scale(0.9).set_color(C_HOT)
        q_mark.next_to(widest, RIGHT, buff=0.12)
        assert_in_frame(widest=widest, q_mark=q_mark)
        self.play(ShowCreation(widest), FadeIn(q_mark), run_time=0.8)
        self.nar.finish(self)

        # The driving question, alone, under the picture it belongs to.
        self.cap.clear(run_time=0.35)
        q = Text(QUESTION, font=FONT, font_size=40).set_color(C_HOT)
        q.move_to(np.array([0, -3.15, 0]))
        assert_in_frame(q=q)
        self.nar.cue(self, "s0.question")
        self.play(Write(q), run_time=1.9)
        self.nar.finish(self)
        self.wait(3.2)                      # wordless: let the question sit

        self.play(FadeOut(q, shift=DOWN * 0.25),
                  FadeOut(q_mark), FadeOut(widest), run_time=0.7)
        self.path_a, self.path_b = path_a, path_b
        self.lbl_a, self.lbl_b = lbl_a, lbl_b

    # ── §1  the obvious answer, and the way it fails ─────────────────────
    def s1_dollars(self):
        m = self.m
        xs = self.days(D0, D_MID)

        # beta is not a definition here: it is the stretch that makes the two
        # paths comparable, and once it has been applied the visible vertical
        # distance IS the spread, exactly.
        path_bs = self.series(self.p_ax, xs, m["b_scaled"][D0:D_MID + 1], C_B)
        lbl_bs = label(f"{mk.BETA} x B", 26, C_B)
        lbl_bs.next_to(self.p_ax.c2p(D_MID, m["b_scaled"][D_MID]), RIGHT,
                       buff=0.16)
        comb_bs = VGroup()
        for i, d in enumerate(range(D0, D_MID + 1, 5)):
            seg = Line(self.p_ax.c2p(d, m["b_scaled"][d]),
                       self.p_ax.c2p(d, m["p_a"][d]))
            seg.set_stroke(C_GAP, width=1.8, opacity=0.55)
            comb_bs.add(seg)
        assert_in_frame(path_bs=path_bs, lbl_bs=lbl_bs)

        self.cap.show("Scale B until it matches A.", "s1.beta", hold=False)
        self.play(ReplacementTransform(self.path_b, path_bs),
                  ReplacementTransform(self.lbl_b, lbl_bs),
                  ReplacementTransform(self.comb, comb_bs),
                  run_time=2.2)
        beta_eq = equation(Tex(r"\text{gap}_t").set_color(C_GAP), Tex("="),
                           Tex("P_{A,t}").set_color(C_A), Tex("-"),
                           Tex(rf"{mk.BETA}\,P_{{B,t}}").set_color(C_B),
                           scale=0.72)
        beta_eq.move_to(np.array([-3.4, 2.45, 0]))
        assert_in_frame(beta_eq=beta_eq)
        self.play(Write(beta_eq), run_time=1.4)
        self.nar.finish(self)

        # Subtract B from A, literally: B flattens onto zero and A becomes the
        # difference. The gap is not a new picture, it is this one rearranged.
        self.g_ax = self.mapper((D0, D_MID), Y_GAP, PW, GAP_H,
                                np.array([PX, GAP_Y, 0]))
        g_chrome, g_ticks = self.chrome(
            self.g_ax, D0, D_MID, Y_GAP, [2, 0, -2, -4],
            lambda v: (rf"+\$ {v}" if v > 0 else
                       (r"\$ 0" if v == 0 else rf"-\$ {abs(v)}")))
        gap_curve = self.series(self.g_ax, xs, m["spread"][D0:D_MID + 1], C_GAP)
        zero_flat = self.series(self.g_ax, xs, np.zeros(len(xs)), C_B)
        comb_flat = VGroup()
        for d in range(D0, D_MID + 1, 5):
            seg = Line(self.g_ax.c2p(d, 0.0), self.g_ax.c2p(d, m["spread"][d]))
            seg.set_stroke(C_GAP, width=1.8, opacity=0.55)
            comb_flat.add(seg)
        assert_in_frame(g_chrome=g_chrome, gap_curve=gap_curve)

        self.cap.show("What's left over is the gap.", "s1.lift", hold=False)
        self.play(
            ReplacementTransform(self.path_a, gap_curve),
            ReplacementTransform(path_bs, zero_flat),
            ReplacementTransform(comb_bs, comb_flat),
            ReplacementTransform(self.p_chrome, g_chrome),
            FadeOut(self.lbl_a), FadeOut(lbl_bs),
            run_time=2.6,
        )
        self.play(FadeOut(comb_flat), FadeOut(zero_flat), run_time=0.8)
        self.nar.finish(self)

        self.g_chrome, self.g_ticks = g_chrome, g_ticks
        self.gap_curve = gap_curve

        # The obvious rule: a fixed number of dollars.
        veil_loud = self.veil(self.g_ax, D_QUIET, D_MID, Y_GAP)
        thr_hi = self.hline(self.g_ax, 2.0, D0, D_MID, C_HOT, width=2.4,
                            dashed=True)
        thr_lo = self.hline(self.g_ax, -2.0, D0, D_MID, C_HOT, width=2.4,
                            dashed=True)
        thr_lbl = label("$2", 26, C_HOT)
        thr_lbl.next_to(self.g_ax.c2p(D_MID, 2.0), RIGHT, buff=0.14)
        assert_in_frame(thr_lbl=thr_lbl)

        self.cap.show("Call anything past two dollars unusual.", "s1.obvious",
                      hold=False)
        self.play(FadeIn(veil_loud), run_time=0.7)
        self.play(ShowCreation(thr_hi), ShowCreation(thr_lo),
                  FadeIn(thr_lbl), run_time=1.1)
        self.nar.finish(self)

        span_q = self.span_label(D0, D_QUIET, "110 quiet days")
        # Below the span bracket, not level with its caption: at -4.6 the two
        # landed on the same screen row and drew on top of each other.
        count_q = label("fires on 0 of them", 26, C_HOT)
        count_q.move_to(self.g_ax.c2p((D0 + D_QUIET) / 2, -5.75))
        assert_in_frame(span_q=span_q, count_q=count_q)
        assert_no_overlap([("span_q", span_q, "count_q", count_q)], pad=0.05)
        self.cap.show("110 days. It never fires.", "s1.silent", hold=False)
        self.play(FadeIn(span_q), run_time=0.6)
        self.play(Write(count_q), run_time=1.0)
        self.nar.finish(self)

        # Lower it until it has something to say.
        low = mk.DOLLAR_THRESHOLD / 5.0            # $0.40
        thr_hi2 = self.hline(self.g_ax, low, D0, D_MID, C_HOT, width=2.4,
                             dashed=True)
        thr_lo2 = self.hline(self.g_ax, -low, D0, D_MID, C_HOT, width=2.4,
                             dashed=True)
        thr_lbl2 = label("$0.40", 26, C_HOT)
        thr_lbl2.next_to(self.g_ax.c2p(D_MID, low), RIGHT, buff=0.14)
        hits_q = self.hits(D0, D_QUIET, low)
        assert_in_frame(thr_lbl2=thr_lbl2)

        self.cap.show("So lower it.", "s1.lower", hold=False)
        self.play(ReplacementTransform(thr_hi, thr_hi2),
                  ReplacementTransform(thr_lo, thr_lo2),
                  ReplacementTransform(thr_lbl, thr_lbl2),
                  run_time=1.0)
        self.nar.finish(self)

        count_q2 = label("fires on 2 of them", 26, C_HOT)
        count_q2.move_to(count_q)
        self.play(ReplacementTransform(count_q, count_q2),
                  stagger([FadeIn(h, scale=0.6) for h in hits_q],
                          lag_ratio=0.25),
                  run_time=1.2)

        # ...and on the loud stretch the same line is on almost every day.
        veil_quiet = self.veil(self.g_ax, D0, D_QUIET, Y_GAP)
        span_l = self.span_label(D_QUIET, D_MID, "the next 130 days")
        hits_l = self.hits(D_QUIET, D_MID, low)
        count_l = label("fires on 98 of them", 26, C_HOT)
        count_l.move_to(self.g_ax.c2p((D_QUIET + D_MID) / 2, -5.75))
        assert_in_frame(span_l=span_l, count_l=count_l)
        assert_no_overlap([("span_q", span_q, "span_l", span_l),
                           ("span_l", span_l, "count_l", count_l),
                           ("count_q", count_q, "count_l", count_l)], pad=0.05)

        self.cap.show("98 days out of 130.", "s1.shout", hold=False)
        self.play(FadeOut(veil_loud), FadeIn(veil_quiet),
                  FadeIn(span_l), run_time=1.0)
        self.play(stagger([FadeIn(h, scale=0.6) for h in hits_l],
                          lag_ratio=0.012), run_time=2.0)
        self.play(Write(count_l), run_time=1.0)
        self.nar.finish(self)

        self.cap.show("No dollar number works for both.", "s1.lesson",
                      hold=False)
        self.play(FadeOut(veil_quiet), run_time=0.8)
        self.play(stagger([Indicate(count_q2, color=C_HOT),
                           Indicate(count_l, color=C_HOT)], lag_ratio=0.5),
                  run_time=1.6)
        self.nar.finish(self)
        self.wait(2.6)              # wordless: the two counts, side by side

        self.play(FadeOut(VGroup(thr_hi2, thr_lo2, thr_lbl2, count_q2,
                                 count_l, span_q, span_l)),
                  FadeOut(hits_q), FadeOut(hits_l),
                  FadeOut(beta_eq),
                  run_time=1.0)

    def span_label(self, d_lo, d_hi, text):
        """A bracket under the x-axis naming a stretch of days."""
        y = -4.05
        bar = self.hline(self.g_ax, y, d_lo + 2, d_hi - 2, C_NEUT, width=3.0,
                         opacity=0.75)
        t = label(text, 24, C_NEUT)
        t.next_to(bar, DOWN, buff=0.14)
        return VGroup(bar, t)

    def hits(self, d_lo, d_hi, threshold):
        """A marker on every day the gap is past the threshold."""
        s = self.m["spread"]
        g = VGroup()
        for d in range(d_lo, d_hi):
            if abs(s[d]) > threshold:
                g.add(dot(self.g_ax.c2p(d, s[d]), C_HOT, radius=0.045))
        return g

    # ── §2  a unit the pair supplies itself ──────────────────────────────
    def s2_ruler(self):
        m = self.m
        xs = self.days(D0, D_MID)
        mu = m["mu"][D0:D_MID + 1]
        sd = m["sd"][D0:D_MID + 1]

        self.cap.show("The unit has to come from the pair.", "s2.need")

        # One window, shown as an object, before it becomes a band.
        win = self.veil(self.g_ax, D0, D0 + 60, Y_GAP, opacity=0.0)
        win.set_fill(C_HOT, opacity=0.16)
        win_lbl = label("60 days", 24, C_HOT)
        win_lbl.next_to(win, UP, buff=0.10)
        assert_in_frame(win=win, win_lbl=win_lbl)

        self.cap.show("The last sixty days.", "s2.window", hold=False)
        self.play(FadeIn(win), FadeIn(win_lbl), run_time=0.8)
        self.bring_to_front(self.gap_curve)     # the window is a wash, not a lid
        self.nar.finish(self)

        mean_line = self.series(self.g_ax, xs, mu, C_RULER, width=2.6)
        band = self.region(self.g_ax, xs, mu - 2 * sd, mu + 2 * sd,
                           C_RULER, opacity=0.22)
        band_in = self.region(self.g_ax, xs, mu - sd, mu + sd,
                              C_RULER, opacity=0.16)
        assert_in_frame(mean_line=mean_line, band=band)

        self.cap.show("Narrow when quiet. Wide when loud.", "s2.band",
                      hold=False)
        shift = self.g_ax.c2p(D_MID - 60, 0) - self.g_ax.c2p(D0, 0)
        self.add(band, band_in)
        band.set_opacity(0.0)
        band_in.set_opacity(0.0)
        self.bring_to_front(self.gap_curve)
        self.play(
            win.animate.shift(shift),
            win_lbl.animate.shift(shift),
            band.animate.set_fill(C_RULER, opacity=0.22),
            band_in.animate.set_fill(C_RULER, opacity=0.16),
            ShowCreation(mean_line),
            run_time=5.0,
        )
        self.play(FadeOut(win), FadeOut(win_lbl), run_time=0.6)
        self.nar.finish(self)
        self.wait(4.0)                      # wordless: watch the band breathe

        # The same question, in units of the band.
        self.cap.show("Ask again — in band-widths.", "s2.ruler")

        # The rescale. Every target below is built from the same xs as its
        # source, so this is a point-for-point morph: the band straightens into
        # a strip at +/-2, the mean flattens onto zero, and the curve comes
        # with them. Nothing here is a redraw.
        z = m["z"][D0:D_MID + 1]
        z_curve = self.series(self.g_ax, xs, z, C_GAP)
        rails = self.region(self.g_ax, xs, np.full(len(xs), -2.0),
                            np.full(len(xs), 2.0), C_RULER, opacity=0.22)
        rails_in = self.region(self.g_ax, xs, np.full(len(xs), -1.0),
                               np.full(len(xs), 1.0), C_RULER, opacity=0.16)
        zero_line = self.series(self.g_ax, xs, np.zeros(len(xs)), C_RULER,
                                width=2.6)
        z_ticks = VGroup(*[
            Tex(t).scale(20 / 42.0).set_color(C_NEUT).move_to(old)
            for t, old in zip([r"+2\sigma", r"0", r"-2\sigma", r"-4\sigma"],
                              self.g_ticks)])
        assert_in_frame(z_curve=z_curve, rails=rails)

        self.cap.show("Same gap. New ruler.", "s2.rescale", hold=False)
        self.play(
            ReplacementTransform(self.gap_curve, z_curve),
            ReplacementTransform(band, rails),
            ReplacementTransform(band_in, rails_in),
            ReplacementTransform(mean_line, zero_line),
            ReplacementTransform(self.g_ticks, z_ticks),
            run_time=2.8,
        )
        rail_hi = self.hline(self.g_ax, 2.0, D0, D_MID, C_RULER, width=2.0)
        rail_lo = self.hline(self.g_ax, -2.0, D0, D_MID, C_RULER, width=2.0)
        self.play(ShowCreation(rail_hi), ShowCreation(rail_lo), run_time=0.9)
        self.nar.finish(self)

        # Only now, the symbol for what has just been watched.
        num = equation(Tex(r"\text{gap}_t").set_color(C_GAP), Tex("-"),
                       Tex(r"\mu_t").set_color(C_RULER), buff=0.12)
        den = Tex(r"\sigma_t").set_color(C_RULER)
        bar = Line(LEFT * 0.95, RIGHT * 0.95).set_stroke(WHITE, width=2.0)
        frac = VGroup(num, bar, den).arrange(DOWN, buff=0.16)
        z_eq = VGroup(Tex("z_t =").scale(1.0), frac).arrange(RIGHT, buff=0.24)
        z_eq.scale(1.15).move_to(ORIGIN)
        assert_in_frame(z_eq=z_eq)

        stage = Dimmer(self.g_chrome, z_ticks, z_curve, rails, rails_in,
                       zero_line, rail_hi, rail_lo)
        self.cap.show("The z-score.", "s2.z", hold=False)
        self.play(*stage.to(0.12), FadeIn(z_eq, shift=UP * 0.2), run_time=1.0)
        num_box = box_around(num, C_GAP)
        self.play(ShowCreation(num_box), run_time=0.8)
        self.wait(1.4)
        z_small = z_eq.copy().scale(0.5).move_to(np.array([-4.55, 2.42, 0]))
        assert_in_frame(z_small=z_small)
        # The box belongs to the equation's moment at centre screen. Left
        # behind, it does not travel with the shrunken copy -- it sat in the
        # middle of the chart for the rest of the video in the first draft.
        self.play(*stage.restore(), FadeOut(num_box),
                  ReplacementTransform(z_eq, z_small), run_time=1.3)
        self.nar.finish(self)
        self.wait(3.0)              # wordless: the gap, on its new ruler

        self.z_curve, self.rails, self.rails_in = z_curve, rails, rails_in
        self.zero_line, self.rail_hi, self.rail_lo = zero_line, rail_hi, rail_lo
        self.z_ticks, self.z_eq = z_ticks, z_small

    # ── §3  the rule, and what it actually pays ──────────────────────────
    def s3_rule(self):
        m = self.m
        trades = [t for t in m["trades"] if t["entry"] < D_MID]

        self.cap.show("Outside the rails, bet it closes.", "s3.rule",
                      hold=False)
        self.play(stagger([Indicate(self.rail_hi, color=C_HOT),
                           Indicate(self.rail_lo, color=C_HOT)],
                          lag_ratio=0.3), run_time=1.4)
        self.nar.finish(self)

        # Which leg is which. Blue and teal have meant A and B since §0, so
        # naming the two sides needs no new visual system.
        t0 = trades[3]                       # a clean short, day 187 -> 203
        legs = VGroup(label("sell A", 24, C_A), label("buy B", 24, C_B))
        legs.arrange(DOWN, buff=0.12)
        legs.next_to(self.g_ax.c2p(t0["entry"], t0["z_in"]), UP, buff=0.22)
        assert_in_frame(legs=legs)
        self.cap.show("You are not predicting the market.", "s3.market",
                      hold=False)
        self.play(FadeIn(legs, shift=UP * 0.15), run_time=0.8)
        self.wait(1.2)
        self.play(FadeOut(legs), run_time=0.6)
        self.nar.finish(self)

        # Holding periods go behind the band and the curve: at full weight and
        # on top they read as columns of grey noise and wash the rails out.
        strips = VGroup(*[self.trade_strip(t) for t in trades])
        marks = VGroup(*[self.trade_mark(t) for t in trades])
        assert_in_frame(marks=marks, strips=strips)

        total = label(f"6 trades   +${sum(t['net'] for t in trades):.2f}",
                      28, WHITE)
        total.move_to(np.array([3.5, 2.45, 0]))
        assert_in_frame(total=total)
        assert_no_overlap([("z_eq", self.z_eq, "total", total)], pad=0.05)

        self.cap.show("Six trades. Six winners.", "s3.six", hold=False)
        self.add(strips)
        strips.set_opacity(0.0)
        self.bring_to_back(strips)
        self.play(strips.animate.set_fill(WHITE, opacity=0.06),
                  stagger([FadeIn(g) for g in marks], lag_ratio=0.22),
                  run_time=2.2)
        self.play(Write(total), run_time=0.9)
        self.nar.finish(self)
        self.wait(3.4)              # wordless: six round trips, all of them

        self.cap.show("Look at the first two.", "s3.but", hold=False)
        self.play(stagger([Indicate(marks[0], color=C_HOT),
                           Indicate(marks[1], color=C_HOT)], lag_ratio=0.35),
                  run_time=1.4)
        self.nar.finish(self)

        # The gross move, and what survives the round trip.
        n0 = self.trade_note(trades[0], r"27\text{c} \to 7\text{c}", up=True)
        n1 = self.trade_note(trades[1], r"24\text{c} \to 4\text{c}", up=False)
        assert_in_frame(n0=n0, n1=n1)
        assert_no_overlap([("n0", n0, "n1", n1)], pad=0.04)
        self.cap.show("Twenty-seven cents. Seven cents kept.", "s3.cost",
                      hold=False)
        self.play(FadeIn(n0, shift=UP * 0.12), run_time=0.8)
        self.play(FadeIn(n1, shift=DOWN * 0.12), run_time=0.8)
        self.nar.finish(self)

        # Cost is a fixed number of dollars, so in band-widths it breathes the
        # other way: fat where sigma is small, invisible where sigma is large.
        xs = self.days(D0, D_MID)
        cz = mk.COST / self.m["sd"][D0:D_MID + 1]
        strip = self.region(self.g_ax, xs, -cz, cz, C_COST, opacity=0.30)
        strip_hi = self.series(self.g_ax, xs, cz, C_COST, width=1.6)
        strip_lo = self.series(self.g_ax, xs, -cz, C_COST, width=1.6)
        cost_lbl = label("cost of a round trip", 24, C_COST)
        cost_lbl.next_to(self.g_ax.c2p(D0 + 26, cz[26]), UP, buff=0.16)
        assert_in_frame(strip=strip, cost_lbl=cost_lbl)

        self.cap.show("Cost is fixed. Sigma is not.", "s3.strip", hold=False)
        self.add(strip, strip_hi, strip_lo)
        strip.set_opacity(0.0)
        strip_hi.set_stroke(opacity=0.0)
        strip_lo.set_stroke(opacity=0.0)
        self.bring_to_front(self.z_curve, marks)
        self.play(strip.animate.set_fill(C_COST, opacity=0.30),
                  strip_hi.animate.set_stroke(C_COST, opacity=1.0),
                  strip_lo.animate.set_stroke(C_COST, opacity=1.0),
                  FadeIn(cost_lbl), run_time=1.6)
        self.nar.finish(self)
        self.wait(2.6)              # wordless: the strip, fat here, thin there

        n5 = self.trade_note(trades[5], r"+\$ 1.58", up=True)
        assert_in_frame(n5=n5)
        self.cap.show("Same signal. Forty times the payoff.", "s3.same",
                      hold=False)
        self.play(FadeIn(n5, shift=UP * 0.12), run_time=0.8)
        self.play(stagger([Indicate(n1, color=C_HOT), Indicate(n5, color=C_HOT)],
                          lag_ratio=0.4), run_time=1.6)
        self.nar.finish(self)

        self.marks, self.total = VGroup(marks, strips), total
        self.notes = VGroup(n0, n1, n5)
        self.cost_strip = VGroup(strip, strip_hi, strip_lo, cost_lbl)

    def trade_strip(self, t):
        """The days a position is open."""
        c0, c1 = self.g_ax.c2p(t["entry"], 0), self.g_ax.c2p(t["exit"], 0)
        lo, hi = self.g_ax.c2p(0, Y_GAP[0])[1], self.g_ax.c2p(0, Y_GAP[1])[1]
        strip = Rectangle(width=max(abs(c1[0] - c0[0]), 0.04), height=hi - lo)
        strip.move_to(np.array([(c0[0] + c1[0]) / 2, (hi + lo) / 2, 0]))
        strip.set_fill(WHITE, opacity=0.06)
        strip.set_stroke(width=0)
        return strip

    def trade_mark(self, t):
        """One round trip: where it was entered, and where it was closed."""
        entry = dot(self.g_ax.c2p(t["entry"], t["z_in"]), WHITE, radius=0.062)
        exit_ = Circle(radius=0.062)
        exit_.set_stroke(WHITE, width=2.0)
        exit_.set_fill(BLACK, opacity=1.0)
        exit_.move_to(self.g_ax.c2p(t["exit"], t["z_out"]))
        return VGroup(entry, exit_)

    def trade_note(self, t, tex, up=True):
        n = Tex(tex).scale(0.5).set_color(WHITE)
        anchor = self.g_ax.c2p(t["entry"], t["z_in"])
        n.next_to(anchor, UP if up else DOWN, buff=0.20)
        return n

    # ── §4  the part of the data we did not look at ──────────────────────
    def s4_holdout(self):
        m = self.m

        # Every number in the rule was chosen against the picture on screen.
        self.cap.show("Every number came from this picture.", "s4.fitted",
                      hold=False)
        self.play(FadeOut(self.cost_strip), FadeOut(self.notes), run_time=0.7)
        self.play(stagger([Indicate(self.rail_hi, color=C_HOT),
                           Indicate(self.rail_lo, color=C_HOT),
                           Indicate(self.z_eq, color=C_HOT)], lag_ratio=0.3),
                  run_time=2.0)
        self.nar.finish(self)

        # The split: one event, two rulers. The z chart shrinks into the lower
        # panel and a copy of it un-rescales back into dollars above -- the S2
        # morph run backwards, which is why the band reappears wiggly.
        xs_in = self.days(D0, D_MID)
        self.t_ax = self.mapper((D0, D_END), Y_TOP, PW, TOP_H,
                                np.array([PX, TOP_Y, 0]))
        self.b_ax = self.mapper((D0, D_END), Y_GAP, PW, BOT_H,
                                np.array([PX, BOT_Y, 0]))

        mu_in = m["mu"][D0:D_MID + 1]
        sd_in = m["sd"][D0:D_MID + 1]
        top_curve = self.series(self.t_ax, xs_in, m["spread"][D0:D_MID + 1],
                                C_GAP, width=2.4)
        top_band = self.region(self.t_ax, xs_in, mu_in - 2 * sd_in,
                               mu_in + 2 * sd_in, C_RULER, opacity=0.22)
        top_mean = self.series(self.t_ax, xs_in, mu_in, C_RULER, width=2.0)
        bot_curve = self.series(self.b_ax, xs_in, m["z"][D0:D_MID + 1], C_GAP,
                                width=2.4)
        bot_rails = self.region(self.b_ax, xs_in, np.full(len(xs_in), -2.0),
                                np.full(len(xs_in), 2.0), C_RULER, opacity=0.22)
        bot_zero = self.series(self.b_ax, xs_in, np.zeros(len(xs_in)), C_RULER,
                               width=2.0)

        top_chrome, top_ticks = self.chrome(
            self.t_ax, D0, D_END, Y_TOP, [0, -5, -10],
            lambda v: (r"\$ 0" if v == 0 else rf"-\$ {abs(v)}"), tick_size=18)
        bot_chrome, bot_ticks = self.chrome(
            self.b_ax, D0, D_END, Y_GAP, [2, 0, -2],
            lambda v: (rf"+{v}\sigma" if v > 0 else
                       (r"0" if v == 0 else rf"-{abs(v)}\sigma")),
            tick_size=18)
        top_name = label("the gap, in dollars", 22, C_NEUT)
        top_name.move_to(self.t_ax.c2p(D0 + 46, 3.0))
        bot_name = label("the gap, in sigmas", 22, C_NEUT)
        bot_name.move_to(self.b_ax.c2p(D0 + 46, 3.3))
        rail_hi2 = self.hline(self.b_ax, 2.0, D0, D_END, C_RULER, width=1.6)
        rail_lo2 = self.hline(self.b_ax, -2.0, D0, D_END, C_RULER, width=1.6)

        # Where the fitted data ends and the held-out data begins.
        div_t = DashedLine(self.t_ax.c2p(D_MID, Y_TOP[0]),
                           self.t_ax.c2p(D_MID, Y_TOP[1]), dash_length=0.08)
        div_b = DashedLine(self.b_ax.c2p(D_MID, Y_GAP[0]),
                           self.b_ax.c2p(D_MID, Y_GAP[1]), dash_length=0.08)
        for d in (div_t, div_b):
            d.set_stroke(C_HOT, width=1.8, opacity=0.75)
        held = label("held out", 24, C_HOT)
        held.next_to(self.b_ax.c2p((D_MID + D_END) / 2, Y_GAP[0]), DOWN,
                     buff=0.18)
        assert_in_frame(top_chrome=top_chrome, bot_chrome=bot_chrome,
                        top_name=top_name, bot_name=bot_name, held=held)
        assert_no_overlap([("top_name", top_name, "bot_name", bot_name)])

        self.cap.show("The part we haven't looked at.", "s4.holdout",
                      hold=False)
        self.play(
            ReplacementTransform(self.z_curve, bot_curve),
            ReplacementTransform(self.rails, bot_rails),
            ReplacementTransform(self.zero_line, bot_zero),
            ReplacementTransform(self.g_chrome, bot_chrome),
            ReplacementTransform(self.z_ticks, bot_ticks),
            ReplacementTransform(self.rail_hi, rail_hi2),
            ReplacementTransform(self.rail_lo, rail_lo2),
            ReplacementTransform(self.z_curve.copy(), top_curve),
            ReplacementTransform(self.rails_in, top_band),
            FadeOut(self.marks), FadeOut(self.total), FadeOut(self.z_eq),
            run_time=2.4,
        )
        self.play(FadeIn(top_chrome), FadeIn(top_ticks), ShowCreation(top_mean),
                  FadeIn(top_name), FadeIn(bot_name), run_time=1.0)
        self.play(ShowCreation(div_t), ShowCreation(div_b), FadeIn(held),
                  run_time=0.8)
        self.nar.finish(self)
        self.wait(2.8)              # wordless: one event, two rulers, no data

        # The held-out stretch, drawn as it happens.
        self.top_curve, self.bot_curve = top_curve, bot_curve
        self.top_band, self.top_mean = top_band, top_mean
        self.bot_rails, self.bot_zero = bot_rails, bot_zero

        entry_day = 330
        self.draw_forward(D_MID, entry_day + 8)
        e_top = dot(self.t_ax.c2p(entry_day, m["spread"][entry_day]), WHITE,
                    radius=0.055)
        e_bot = dot(self.b_ax.c2p(entry_day, m["z"][entry_day]), WHITE,
                    radius=0.055)
        buy = label("the rule buys", 22, WHITE)
        buy.next_to(e_bot, DOWN, buff=0.16)
        assert_in_frame(buy=buy)
        self.cap.show("The rule buys.", "s4.enter", hold=False)
        self.play(FadeIn(e_top), FadeIn(e_bot), FadeIn(buy), run_time=0.8)
        self.nar.finish(self)

        self.cap.show("And it does not come back.", "s4.walk", hold=False)
        self.play(FadeOut(buy), run_time=0.4)
        self.draw_forward(entry_day + 8, D_END, run_time=5.2)
        self.nar.finish(self)
        self.wait(3.2)              # wordless: it really does not come back

        # The money frame: the same day, read on both rulers.
        never = self.hline(self.b_ax, -2.5, D_MID, D_END, C_HOT, width=1.8,
                           dashed=True)
        # Inside the panel: to the right of day 420 there is no room for it.
        never_lbl = label("never past  -2.5", 22, C_HOT)
        never_lbl.move_to(self.b_ax.c2p(D_MID + 46, -3.9))
        # A playhead rather than a static rule: it starts at the entry and
        # sweeps to the low, so the two readings are compared day by day
        # instead of asserted at one. It also has to *move* -- ShowCreation of
        # a thin curve adds a pixel or two per frame, which is below
        # verify_render's motion threshold, so a traced line alone reads as a
        # frozen hold even though something is visibly happening.
        probe = DashedLine(self.t_ax.c2p(entry_day, Y_TOP[1]),
                           self.b_ax.c2p(entry_day, Y_GAP[0]), dash_length=0.07)
        probe.set_stroke(WHITE, width=1.4, opacity=0.7)
        sweep = self.t_ax.c2p(D_LOW, 0) - self.t_ax.c2p(entry_day, 0)
        r_top = Tex(rf"-\$ {abs(m['spread'][D_LOW]):.2f}").scale(0.55)
        r_top.set_color(C_GAP)
        r_top.next_to(self.t_ax.c2p(D_LOW, m["spread"][D_LOW]), LEFT, buff=0.16)
        r_bot = Tex(rf"z = {m['z'][D_LOW]:.1f}").scale(0.55).set_color(C_GAP)
        r_bot.next_to(self.b_ax.c2p(D_LOW, m["z"][D_LOW]), UP, buff=0.14)
        assert_in_frame(never_lbl=never_lbl, r_top=r_top, r_bot=r_bot)

        # "It never once passes minus two and a half" is a claim about the
        # whole collapse, so the whole collapse is traced rather than held
        # still under the sentence (ANTI-PATTERN #22).
        xs_c = self.days(entry_day, D_END - 1)
        z_trace = self.series(self.b_ax, xs_c, m["z"][entry_day:D_END], C_HOT,
                              width=3.2)

        self.cap.show("The z-score never sounds an alarm.", "s4.z", hold=False)
        self.play(ShowCreation(never), FadeIn(never_lbl), run_time=1.0)
        self.play(FadeIn(probe), run_time=0.5)
        self.play(ShowCreation(z_trace), probe.animate.shift(sweep),
                  run_time=5.2, rate_func=linear)
        self.play(FadeIn(r_top), FadeIn(r_bot), run_time=0.8)
        self.nar.finish(self)
        self.wait(2.2)                      # wordless: sit with both readings

        # Why: the mean is not fixed, and it is walking away with the gap.
        # The sixty-day window comes back, on the collapse this time. It is
        # the same object from §2, and watching it slide down is the claim:
        # the mean is not fixed, it is an average of days that are falling.
        win2 = self.veil(self.t_ax, entry_day - 60, entry_day, Y_TOP,
                         opacity=0.0)
        win2.set_fill(C_HOT, opacity=0.14)
        win2_lbl = label("the last 60 days", 20, C_HOT)
        win2_lbl.next_to(win2, UP, buff=0.08)
        slide = self.t_ax.c2p(D_END - 1, 0) - self.t_ax.c2p(entry_day, 0)
        assert_in_frame(win2=win2, win2_lbl=win2_lbl)

        self.cap.show("The mean is chasing the gap down.", "s4.why",
                      hold=False)
        self.play(FadeOut(probe), FadeOut(r_top), FadeOut(r_bot),
                  FadeOut(never), FadeOut(never_lbl), FadeOut(z_trace),
                  run_time=0.6)
        self.play(FadeIn(win2), FadeIn(win2_lbl), run_time=0.5)
        self.bring_to_front(self.top_curve, self.top_mean)
        self.play(win2.animate.shift(slide), win2_lbl.animate.shift(slide),
                  run_time=6.4, rate_func=linear)
        self.play(FadeOut(win2), FadeOut(win2_lbl),
                  Indicate(self.top_mean, color=C_HOT, scale_factor=1.0),
                  run_time=1.6)
        chase = Tex(r"\mu_t").scale(0.6).set_color(C_RULER)
        chase.next_to(self.t_ax.c2p(D_END, m["mu"][D_END - 1]), RIGHT,
                      buff=0.12)
        assert_in_frame(chase=chase)
        self.play(FadeIn(chase), run_time=0.6)
        self.nar.finish(self)

        # The tally.
        held_span = Rectangle(
            width=abs(self.b_ax.c2p(D_END - 1, 0)[0]
                      - self.b_ax.c2p(entry_day, 0)[0]),
            height=abs(self.b_ax.c2p(0, Y_GAP[1])[1]
                       - self.b_ax.c2p(0, Y_GAP[0])[1]))
        held_span.move_to((self.b_ax.c2p(entry_day, 0)
                           + self.b_ax.c2p(D_END - 1, 0)) / 2)
        held_span.set_fill(C_COST, opacity=0.16)
        held_span.set_stroke(width=0)
        # The clear band between the two panels: the only place on this frame
        # wide enough for the tally without landing on either chart.
        tally = VGroup(
            label("6 winners   +$3.75", 26, WHITE),
            label("1 trade back   -$9.32", 26, C_COST),
            label("89 days held", 22, C_COST),
        ).arrange(RIGHT, buff=0.75)
        tally.move_to(np.array([PX, -0.52, 0]))
        assert_in_frame(tally=tally, held_span=held_span)
        assert_no_overlap([("tally", tally, "held", held)], pad=0.05)

        # "Eighty-nine days spent holding it" is shown by the position being
        # held: the span grows a day at a time from the entry rather than
        # appearing whole under a still frame.
        seed = held_span.copy().stretch_to_fit_width(0.02)
        seed.move_to(self.b_ax.c2p(entry_day, Y_GAP[0] + 5.5))

        self.cap.show("Six winners. One trade back.", "s4.tally", hold=False)
        self.add(seed)
        self.bring_to_back(seed)
        self.play(ReplacementTransform(seed, held_span), run_time=3.6,
                  rate_func=linear)
        self.play(stagger([Write(t) for t in tally], lag_ratio=0.45),
                  run_time=3.4)
        self.nar.finish(self)
        self.wait(2.0)              # wordless: the two numbers, together

        self.held_span, self.tally, self.held_lbl = held_span, tally, held
        self.stage = Dimmer(bot_chrome, bot_ticks, top_chrome, top_ticks,
                            top_curve, top_band, top_mean, bot_curve,
                            bot_rails, bot_zero, rail_hi2, rail_lo2,
                            top_name, bot_name, div_t, div_b, held,
                            held_span, tally, e_top, e_bot, chase)

    def draw_forward(self, d_from, d_to, run_time=1.4):
        """Extend both panels through the held-out days, together."""
        m = self.m
        xs = self.days(d_from, d_to - 1)
        mu = m["mu"][d_from:d_to]
        sd = m["sd"][d_from:d_to]
        top_ext = self.series(self.t_ax, xs, m["spread"][d_from:d_to], C_GAP,
                              width=2.4)
        band_ext = self.region(self.t_ax, xs, mu - 2 * sd, mu + 2 * sd,
                               C_RULER, opacity=0.22)
        mean_ext = self.series(self.t_ax, xs, mu, C_RULER, width=2.0)
        bot_ext = self.series(self.b_ax, xs, m["z"][d_from:d_to], C_GAP,
                              width=2.4)
        self.add(band_ext)
        self.bring_to_front(top_ext, mean_ext, self.top_curve, self.top_mean)
        band_ext.set_opacity(0.0)
        self.play(ShowCreation(top_ext), ShowCreation(bot_ext),
                  ShowCreation(mean_ext),
                  band_ext.animate.set_fill(C_RULER, opacity=0.22),
                  run_time=run_time)
        # Keep the extensions in the dimmable stage by folding them into the
        # curves they continue.
        self.top_curve = VGroup(self.top_curve, top_ext)
        self.top_mean = VGroup(self.top_mean, mean_ext)
        self.top_band = VGroup(self.top_band, band_ext)
        self.bot_curve = VGroup(self.bot_curve, bot_ext)

    # ── §5  payoff ───────────────────────────────────────────────────────
    def s5_payoff(self):
        self.cap.clear(run_time=0.4)
        q = Text(QUESTION, font=FONT, font_size=40).set_color(C_HOT)
        q.move_to(np.array([0, 0.55, 0]))
        assert_in_frame(q=q)
        self.nar.cue(self, "s5.restate")
        self.play(*self.stage.to(0.12), FadeIn(q, shift=UP * 0.2),
                  run_time=1.1)
        self.nar.finish(self)

        ans = Text("Never in dollars.\nOnly in sigmas.",
                   font=FONT, font_size=40).set_color(WHITE)
        ans.move_to(np.array([0, 0.55, 0]))
        assert_in_frame(ans=ans)
        self.nar.cue(self, "s5.answer")
        self.play(FadeOut(q, shift=UP * 0.3), run_time=0.5)
        self.play(Write(ans), run_time=1.6)
        caveat = Text("— and only while the sigmas still measure something.",
                      font=FONT, font_size=26).set_color(C_NEUT)
        caveat.next_to(ans, DOWN, buff=0.42)
        assert_in_frame(caveat=caveat)
        self.play(FadeIn(caveat, shift=UP * 0.12), run_time=1.0)
        self.nar.finish(self)
        self.wait(3.0)              # wordless: the answer, on its own

        # Point back at the object that answered it.
        # The answer keeps a place on the closing frame, but not the bottom
        # right corner: that is where "held out" lives, and the two drew on
        # top of each other. The top panel's lower-left is genuinely empty --
        # the gap does not go below a dollar until the held-out stretch.
        ans_home = np.array([-2.45, 0.78, 0])
        self.cap.show("A ruler made out of the recent past.", "s5.ruler",
                      hold=False)
        self.play(FadeOut(caveat), *self.stage.to(0.85),
                  ans.animate.scale(0.55).move_to(ans_home),
                  run_time=1.2)
        assert_in_frame(ans_small=ans)
        assert_no_overlap([("ans", ans, "tally", self.tally)], pad=0.05)
        self.play(Indicate(self.top_band, color=C_RULER, scale_factor=1.0),
                  run_time=1.4)
        self.play(Indicate(self.top_mean, color=C_HOT, scale_factor=1.0),
                  run_time=1.4)
        self.nar.finish(self)

        # The closing list is not a list: every item on it is already on this
        # frame, so each one lights up as it is named -- out-of-sample, then
        # what it cost, then the drawdown it cost it over.
        self.cap.show("How much of the edge was ever there?", "s5.close",
                      hold=False)
        self.play(Indicate(self.held_lbl, color=C_HOT), run_time=1.8)
        self.play(stagger([Indicate(self.tally[0], color=WHITE),
                           Indicate(self.tally[1], color=C_COST)],
                          lag_ratio=0.4), run_time=2.2)
        self.play(stagger([Indicate(self.tally[2], color=C_COST),
                           Indicate(self.held_span, color=C_COST,
                                    scale_factor=1.0)], lag_ratio=0.35),
                  run_time=2.2)
        self.play(Indicate(ans, color=C_HOT), run_time=1.6)
        self.nar.finish(self)
        self.wait(2.4)                      # wordless: the closing frame

        self.play(FadeOut(Group(*self.mobjects)), run_time=2.8)
        self.wait(0.5)
