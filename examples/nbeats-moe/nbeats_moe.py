"""N-BEATS-MoE — "Who decides how much each piece counts?"

A ~4:40 explainer of Matos, Roque & Cerqueira, *N-BEATS-MOE: N-BEATS with a
Mixture-of-Experts Layer for Heterogeneous Time Series Forecasting*
(arXiv:2508.07490).  Narrative spine and colour mapping: SCRIPT.md.
Everything numeric is computed in nbeats_data.py and checked by
verify_numbers.py.

    Verify:  python verify_numbers.py
    Draft:   bash ../../skills/3b1b-math-animation/scripts/render.sh \
                 nbeats_moe.py NBeatsMoE -l
    Render:  bash ../../skills/3b1b-math-animation/scripts/render.sh \
                 nbeats_moe.py NBeatsMoE
    Check:   python ../../skills/3b1b-math-animation/scripts/verify_render.py \
                 videos/NBeatsMoE.mp4 --meta render_meta.json
    Audit:   AUDIT=1 ../../env/bin/manimgl nbeats_moe.py NBeatsMoE -w -o -l

Spine
  QUESTION    a forecast is a sum of pieces, and every piece is added with a
              coefficient of exactly one. Who chose those ones?
  MOTIVATION  "the block will learn to output something small" — it can't:
              the blocks are global, so their scale is a dataset compromise.
  BUILD       put a real number back in front of each piece and read it off
              the input window: softmax(Linear(LayerNorm(x0))).
  PAYOFF      the series decides.

Carried metaphor: THREE BARS IN FRONT OF THREE CURVES (see SCRIPT.md for the
full meaning table). The bars are a real softmax over a real linear layer, so
they move because the series changed — not because a keyframe said so.

Colour mapping (fixed for the whole scene)
  BLUE_C   the given data — observed history, the true future
  ORANGE   the model's own output — stack curves, the N-BEATS-MoE forecast
  TEAL_C   the gate — the second actor
  GREEN    improvement / a win
  YELLOW   transient emphasis ONLY
  GREY_B   scaffolding, and the plain-N-BEATS baseline (the neutral "before")
"""

from manimlib import *
from pathlib import Path
import sys
import os

# ManimGL's loader does not put the scene file's directory on sys.path.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1] / "skills" / "3b1b-math-animation"
                       / "scripts"))

from manim_helpers import (                                   # noqa: E402
    arrow, label, Caption, Dimmer, hold, stagger,
    push_in, pull_back, dump_meta, equation, box_around,
    assert_in_frame, assert_no_overlap, audit_text_overlaps,
    FONT,
)
import nbeats_data as D                                       # noqa: E402


# ── colour mapping ────────────────────────────────────────────────────────
C_DATA = BLUE_C       # observed history, true future
C_MODEL = ORANGE      # the model's own output
C_GATE = TEAL_C       # the gate
C_WIN = GREEN         # improvement
C_HOT = YELLOW        # transient emphasis only
C_NEUT = GREY_B       # scaffolding, and the plain-N-BEATS baseline

# ── layout (one stage, held for the whole video) ──────────────────────────
IN_C = np.array([-5.0, 2.35, 0])          # input window panel
IN_W, IN_H = 3.4, 1.15

GATE_C = np.array([-2.0, 2.35, 0])        # the gating network
GATE_W, GATE_H = 1.4, 0.84

LANE_X = -5.0                             # the three stack lanes
LANE_W, LANE_H = 3.4, 1.0
LANE_Y = [0.45, -1.10, -2.68]
LANE_NAME = ["Identity", "Trend", "Seasonality"]
LANE_YRANGE = [(121, 128), (0, 3.2), (0, 17)]

BAR_X0 = -3.0                             # the three gate bars
BAR_MAX, BAR_H = 2.6, 0.26
NUM_X = 0.30

FC_C = np.array([3.7, -0.9, 0])           # the forecast panel
FC_W, FC_H = 5.4, 3.4

EQ_X = 3.7
EQ_SUM_Y = 2.55
EQ_GATE_Y = 1.70

UNIFORM = np.array([1 / 3, 1 / 3, 1 / 3])


# ── small builders ────────────────────────────────────────────────────────

class Panel(VGroup):
    """A plotting area with its own coordinate map.

    Not `Axes`: ManimGL's Axes places the two number lines so they cross at
    the DATA origin, so a series living at 123-140 puts the x-axis 123 data
    units below the visible band and the mobject's bounding box becomes ~35
    units tall. Every panel here plots a range that excludes zero, so the
    mapping is done directly instead.
    """

    def __init__(self, x_range, y_range, width, height, center,
                 frame="L", stroke=1.5):
        super().__init__()
        self.xr = (float(x_range[0]), float(x_range[1]))
        self.yr = (float(y_range[0]), float(y_range[1]))
        self.pw, self.ph = float(width), float(height)
        self.pc = np.array(center, dtype=float)

        bl = self.pc + np.array([-self.pw / 2, -self.ph / 2, 0])
        br = self.pc + np.array([self.pw / 2, -self.ph / 2, 0])
        tl = self.pc + np.array([-self.pw / 2, self.ph / 2, 0])
        parts = [Line(bl, br)]
        if frame == "L":
            parts.append(Line(bl, tl))
        for p in parts:
            p.set_stroke(GREY_D, width=stroke, opacity=1.0)
            p.set_fill(opacity=0)
        self.add(*parts)

    def c2p(self, x, y):
        fx = (float(x) - self.xr[0]) / (self.xr[1] - self.xr[0]) - 0.5
        fy = (float(y) - self.yr[0]) / (self.yr[1] - self.yr[0]) - 0.5
        return self.pc + np.array([fx * self.pw, fy * self.ph, 0.0])


def panel(x_range, y_range, width, height, center, frame="L", stroke=1.5):
    return Panel(x_range, y_range, width, height, center, frame, stroke)


def curve(p, func, color, width=3.0, opacity=1.0, x_range=None, samples=96):
    """A basis function drawn on a panel. The function is sampled directly,
    so the picture cannot drift from nbeats_data.py."""
    x0, x1 = x_range if x_range else p.xr
    xs = np.linspace(x0, x1, samples)
    ys = np.asarray(func(xs), dtype=float)
    m = VMobject()
    m.set_points_smoothly([p.c2p(x, y) for x, y in zip(xs, ys)])
    m.set_stroke(color, width=width, opacity=opacity)
    m.set_fill(opacity=0)
    return m


def fit_to_panel(p, ys, pad=0.10):
    """Rescale a series into a panel's y-range.

    The ensembles in §3 span levels from ~40 to ~900; drawn against the hero
    panel's fixed range they leave the frame entirely. The gate LayerNorms its
    input before reading it, so a normalised window is the honest thing to
    show in the slot the gate feeds from.
    """
    ys = np.asarray(ys, dtype=float)
    lo, hi = float(ys.min()), float(ys.max())
    if hi - lo < 1e-9:
        hi = lo + 1.0
    y0, y1 = p.yr
    return y0 + (y1 - y0) * pad + (ys - lo) / (hi - lo) * (y1 - y0) * (1 - 2 * pad)


def polyline(p, xs, ys, color, width=3.0, opacity=1.0):
    """Observed (noisy) data: corners, not a smoothed fit."""
    m = VMobject()
    m.set_points_as_corners([p.c2p(x, y) for x, y in zip(xs, ys)])
    m.set_stroke(color, width=width, opacity=opacity)
    m.set_fill(opacity=0)
    return m


def make_bar(weight, y, color, opacity=0.85):
    ln = max(float(weight) * BAR_MAX, 0.03)
    r = Rectangle(width=ln, height=BAR_H)
    r.set_fill(color, opacity=opacity)
    r.set_stroke(color, width=1.4, opacity=1.0)
    r.move_to(np.array([BAR_X0 + ln / 2, y, 0]))
    return r


def marker(point, color, size=0.13, opacity=1.0):
    """A win/loss tick. Square, so it is never mistaken for a data point."""
    s = Square(side_length=size)
    s.set_fill(color, opacity=opacity)
    s.set_stroke(color, width=1.0, opacity=opacity)
    s.move_to(point)
    return s


class NBeatsMoE(Scene):

    def wait(self, *args, **kwargs):
        r = super().wait(*args, **kwargs)
        if os.environ.get("AUDIT"):
            audit_text_overlaps(self)
        return r

    def construct(self):
        self.camera.background_color = BLACK
        self.cap = Caption(self)
        for name, fn in [("s0 question", self.s0_question),
                         ("s1 global", self.s1_global),
                         ("s2 gate", self.s2_gate),
                         ("s3 evidence", self.s3_evidence),
                         ("s4 readout", self.s4_readout),
                         ("s5 payoff", self.s5_payoff)]:
            t0 = self.time
            fn()
            print(f"[TIMING] {name:12s} start={t0:6.1f}s "
                  f"dur={self.time - t0:5.1f}s")
        dump_meta(self, str(_HERE / "render_meta.json"))

    # ── helpers bound to the stage ───────────────────────────────────────
    def set_weights(self, w, run_time=1.0, extra=(), color=None):
        """Drive the three bars (and their readouts) to a weight vector."""
        anims = []
        for i, wi in enumerate(w):
            col = color or self.bars[i].get_fill_color()
            anims.append(Transform(self.bars[i],
                                   make_bar(wi, LANE_Y[i], col)))
            anims.append(self.trackers[i].animate.set_value(float(wi)))
        self.play(*anims, *extra, run_time=run_time)

    # ── §0  The question ─────────────────────────────────────────────────
    def s0_question(self):
        hist_idx = np.arange(-D.N_HIST, 1)
        hist = D.HERO.observed(hist_idx)
        lo, hi = hist.min() - 2.5, hist.max() + 2.5

        big = panel((-D.N_HIST, 0), (lo, hi), 10.0, 4.2,
                    np.array([0, -0.35, 0]), stroke=1.8)
        big_curve = polyline(big, hist_idx, hist, C_DATA, width=3.4)
        assert_in_frame(big=big, big_curve=big_curve)

        self.play(ShowCreation(big), run_time=0.9)
        self.play(ShowCreation(big_curve), run_time=2.4)
        self.cap.show(
            "A monthly time series.",
            "Here is a monthly time series — thirty-six months of history, and "
            "eight months ahead that we would like to predict. And here is how "
            "N-BEATS goes about forecasting it.", size=30)

        self.cap.show(
            "N-BEATS doesn't predict the curve. It predicts pieces of it.",
            "It doesn't predict the curve directly. It predicts pieces of it "
            "— a flat level, a slow trend, a repeating seasonal shape — and "
            "then adds them up.", size=30)

        # The opening object survives: it shrinks into the input-window slot.
        in_panel = panel((-D.N_HIST, 0), (lo, hi), IN_W, IN_H, IN_C,
                         frame="base")
        in_curve = polyline(in_panel, hist_idx, hist, C_DATA, width=2.0)
        x0_lbl = VGroup(label("input window", 18, C_NEUT),
                        Tex("x_0").scale(0.50).set_color(C_DATA))
        x0_lbl.arrange(RIGHT, buff=0.14)
        x0_lbl.next_to(in_panel, DOWN, buff=0.20)
        assert_in_frame(in_panel=in_panel, x0_lbl=x0_lbl)

        self.play(ReplacementTransform(big, in_panel),
                  ReplacementTransform(big_curve, in_curve),
                  run_time=1.5)
        self.play(FadeIn(x0_lbl), run_time=0.5)

        # The three lanes: axes first, then curves, then names (Rule 3 —
        # connectors and labels never precede the thing they attach to).
        self.lanes, self.lane_curves, self.lane_names = [], [], []
        stack_fn = [D.HERO.identity, D.HERO.trend, D.HERO.seasonal]
        for i in range(3):
            ax = panel((1, D.H), LANE_YRANGE[i], LANE_W, LANE_H,
                       np.array([LANE_X, LANE_Y[i], 0]), frame="base")
            g = curve(ax, stack_fn[i], C_MODEL, width=2.8)
            nm = label(LANE_NAME[i], 19, C_NEUT)
            # Position from the lane's logical top, not from the Panel's
            # bounding box — for frame="base" that box is only the baseline.
            nm.move_to(np.array([LANE_X - LANE_W / 2,
                                 LANE_Y[i] + LANE_H / 2 + 0.16, 0]))
            nm.shift(RIGHT * nm.get_width() / 2)
            self.lanes.append(ax)
            self.lane_curves.append(g)
            self.lane_names.append(nm)
        assert_in_frame(**{f"lane{i}": m for i, m in enumerate(self.lanes)},
                        **{f"name{i}": m for i, m in enumerate(self.lane_names)})

        self.play(stagger([ShowCreation(a) for a in self.lanes],
                          lag_ratio=0.35), run_time=1.3)
        self.play(stagger([ShowCreation(g) for g in self.lane_curves],
                          lag_ratio=0.35), run_time=1.8)
        self.play(stagger([FadeIn(n) for n in self.lane_names],
                          lag_ratio=0.25), run_time=0.9)
        hold(self, 1.4)

        # The sum. Built from separately addressable Tex parts (ANTI-PATTERN
        # #5) so the coefficients can be boxed and flown out on their own.
        self.terms = [Tex(r"\hat{y}_%d" % (i + 1)) for i in range(3)]
        self.coefs = [Tex("1\\,\\cdot") for _ in range(3)]
        self.eq_sum = equation(Tex(r"\hat{y}"), "=",
                               self.coefs[0], self.terms[0], "+",
                               self.coefs[1], self.terms[1], "+",
                               self.coefs[2], self.terms[2],
                               buff=0.13, scale=0.72)
        self.eq_sum.move_to(np.array([EQ_X, EQ_SUM_Y, 0]))
        for c in self.coefs:
            c.set_opacity(0.0)
        assert_in_frame(eq_sum=self.eq_sum)

        self.cap.show(
            "Then it adds them up.",
            "Three stacks, three outputs, and a forecast that is just their "
            "sum. That addition looks like bookkeeping, but it is the part "
            "worth looking at.", size=30)
        self.play(Write(self.eq_sum), run_time=1.4)
        hold(self, 1.2)

        self.cap.show(
            "Written out in full, every piece carries a coefficient.",
            "Because written out in full, every piece is added with a "
            "coefficient of exactly one. Nobody chose those ones.", size=30)
        self.play(stagger([c.animate.set_opacity(1.0).set_color(C_HOT)
                           for c in self.coefs], lag_ratio=0.25),
                  run_time=1.2)
        hold(self, 1.6)

        # The coefficients BECOME the bars — the carried object enters by
        # transformation, not by appearing beside them.
        self.bars = [make_bar(UNIFORM[i], LANE_Y[i], C_NEUT) for i in range(3)]
        self.trackers = [ValueTracker(1 / 3) for _ in range(3)]
        self.nums = []
        for i in range(3):
            n = Tex("1").scale(0.60).set_color(C_NEUT)
            n.move_to(np.array([NUM_X, LANE_Y[i], 0]))
            self.nums.append(n)
        assert_in_frame(**{f"bar{i}": m for i, m in enumerate(self.bars)},
                        **{f"num{i}": m for i, m in enumerate(self.nums)})

        self.play(
            stagger([AnimationGroup(
                ReplacementTransform(self.coefs[i].copy(), self.bars[i]),
                FadeIn(self.nums[i]))
                for i in range(3)], lag_ratio=0.3),
            run_time=1.7)
        self.play(*[c.animate.set_color(C_NEUT).set_opacity(0.75)
                    for c in self.coefs], run_time=0.6)
        hold(self, 1.3)

        self.cap.show(
            "And the same ones are used for every series in the dataset.",
            "And the same ones are used for every single series in the "
            "dataset.", size=30)

        # The driving question, in the area the forecast panel will later use.
        self.q_text = "Who decides how much\neach piece counts?"
        q = Text(self.q_text, font=FONT, font_size=36).set_color(C_HOT)
        q.move_to(np.array([EQ_X, -1.35, 0]))
        assert_in_frame(q=q)
        self.stage = Dimmer(*self.lanes, *self.lane_curves, *self.lane_names,
                            in_panel, in_curve, x0_lbl, self.eq_sum,
                            *self.bars, *self.nums)
        self.play(*self.stage.to(0.30), Write(q), run_time=1.6)
        self.wait(3.0)
        self.play(*self.stage.restore(), FadeOut(q, shift=DOWN * 0.25),
                  run_time=1.0)

        self.in_panel, self.in_curve, self.x0_lbl = in_panel, in_curve, x0_lbl

    # ── §1  The obvious answer, and why it fails ─────────────────────────
    def s1_global(self):
        self.cap.show(
            "The blocks are trained — won't they just shrink themselves?",
            "The obvious answer is that nobody has to. These blocks are "
            "trained. If the trend doesn't matter for a series, the trend "
            "block will just learn to output something small.", size=30)

        # Why it can't: one block, one learned scale, thousands of series.
        # Ghosts of the trend each of several series would need, against the
        # single curve the global block actually produces.
        ghosts = VGroup()
        for k in (0.25, 0.55, 1.45, 2.1, 2.8):
            g = curve(self.lanes[1],
                      lambda x, k=k: k * D.HERO.trend(x),
                      C_MODEL, width=1.8, opacity=0.30)
            ghosts.add(g)
        self.play(stagger([ShowCreation(g) for g in ghosts], lag_ratio=0.12),
                  run_time=1.5)
        self.cap.show(
            "But there is one trend block, shared by every series.",
            "That would be fine, except for one thing. These blocks are "
            "global. There is one trend block, with one set of weights, "
            "serving all six hundred and seventeen series in this dataset.",
            size=30)

        n_lbl = label("617 series, one block", 20, C_NEUT)
        n_lbl.next_to(self.lanes[1], DOWN, buff=0.12)
        assert_in_frame(n_lbl=n_lbl)
        self.play(FadeIn(n_lbl), run_time=0.6)
        hold(self, 1.4)

        self.cap.show(
            "So the scale it learns is a compromise across all of them.",
            "It sees a different input window each time, but the scale it "
            "learned is a compromise across all of them. Watch what that "
            "costs.", size=30)

        # The compromise, on this series: the block's output is pushed to the
        # dataset-average amplitude the paper measured, [1, 3].
        over = curve(self.lanes[1], D.nbeats_trend, C_NEUT, width=3.0)
        self.play(FadeOut(ghosts, run_time=0.7),
                  Transform(self.lane_curves[1], over), run_time=1.4)
        self.play(FlashAround(self.lanes[1], color=C_HOT, run_time=1.2))

        # Close-up. No caption inside a camera window — the caption band sits
        # at a fixed world y and would be outside the crop.
        self.cap.clear(run_time=0.35)
        rng_true = Tex(r"\text{this series needs } [0.4,\ 0.9]")
        rng_true.scale(0.40).set_color(C_MODEL)
        rng_over = Tex(r"\text{the global block gives } [1,\ 3]")
        rng_over.scale(0.40).set_color(C_NEUT)
        rng_true.move_to(np.array([LANE_X, LANE_Y[1] - 0.82, 0]))
        rng_over.move_to(np.array([LANE_X, LANE_Y[1] - 1.16, 0]))
        want = curve(self.lanes[1], D.HERO.trend, C_MODEL, width=2.2,
                     opacity=0.55)

        # The annotations sit over the band lane 3 occupies, so everything
        # except the trend lane is pushed back for the duration of the crop.
        near = Dimmer(*[m for i, m in enumerate(self.lanes) if i != 1],
                      *[m for i, m in enumerate(self.lane_curves) if i != 1],
                      *[m for i, m in enumerate(self.lane_names) if i != 1],
                      *self.bars, *self.nums)
        self.play(FadeOut(n_lbl), run_time=0.5)
        push_in(self, np.array([LANE_X, LANE_Y[1] - 0.42, 0]), height=3.0,
                run_time=1.2)
        self.play(*near.to(0.05), run_time=0.6)
        self.play(ShowCreation(want), Write(rng_true), run_time=1.1)
        self.play(Write(rng_over), run_time=1.0)
        self.wait(2.2)
        self.play(FadeOut(VGroup(rng_true, rng_over, want)),
                  *near.restore(), run_time=0.8)
        pull_back(self, run_time=1.2)

        # The second half of the miss, per §4.5 of the paper: the seasonal
        # stack smooths over the sharp swings this series actually has.
        self.cap.show(
            "Its seasonal block smooths over the sharp swings, too.",
            "And its seasonal block smooths over the sharp drops and spikes "
            "this series actually has.", size=30)
        damp = curve(self.lanes[2], D.nbeats_seasonal, C_NEUT, width=3.0)
        true_seas = curve(self.lanes[2], D.HERO.seasonal, C_MODEL,
                          width=1.8, opacity=0.40)
        self.play(ShowCreation(true_seas), run_time=0.6)
        self.play(Transform(self.lane_curves[2], damp), run_time=1.3)
        hold(self, 1.5)

        # Consequence: the forecast panel.
        self.cap.show(
            "Add those in with a coefficient of one each.",
            "Add those in with a coefficient of one each, and the forecast "
            "comes apart.", size=30)

        t = D.HERO.horizon_idx()
        truth = D.HERO.truth()
        nb = D.nbeats_forecast(t)
        moe = D.moe_forecast(t)
        flo = min(truth.min(), nb.min(), moe.min()) - 2.0
        fhi = max(truth.max(), nb.max(), moe.max()) + 3.4
        self.fc = panel((1, D.H), (flo, fhi), FC_W, FC_H, FC_C)
        self.fc_truth = polyline(self.fc, t, truth, C_DATA, width=3.4)
        self.fc_nb = polyline(self.fc, t, nb, C_NEUT, width=3.0)
        self.fc_moe = polyline(self.fc, t, moe, C_MODEL, width=3.2)
        assert_in_frame(fc=self.fc, fc_truth=self.fc_truth, fc_nb=self.fc_nb,
                        fc_moe=self.fc_moe)

        leg = VGroup()
        for txt, col in [("truth", C_DATA), ("N-BEATS", C_NEUT),
                         ("N-BEATS-MoE", C_MODEL)]:
            sw = Line(ORIGIN, RIGHT * 0.32).set_stroke(col, width=3.2)
            tx = label(txt, 18, col).next_to(sw, RIGHT, buff=0.12)
            leg.add(VGroup(sw, tx))
        leg.arrange(RIGHT, buff=0.42).move_to(np.array([FC_C[0], -2.95, 0]))
        self.leg = leg
        self.leg_moe = leg[2]
        self.leg_moe.set_opacity(0.0)
        assert_in_frame(leg=leg)

        self.sm_nb = label("SMAPE  7.34%", 22, C_NEUT)
        self.sm_nb.move_to(self.fc.c2p(D.H, fhi) + np.array([-0.72, -0.28, 0]))
        self.sm_moe = label("SMAPE  2.68%", 22, C_WIN)
        self.sm_moe.next_to(self.sm_nb, DOWN, buff=0.16)
        self.sm_moe.set_opacity(0.0)
        assert_in_frame(sm_nb=self.sm_nb, sm_moe=self.sm_moe)
        assert_no_overlap([("sm_nb", self.sm_nb, "fc_truth", self.fc_truth)])

        self.play(ShowCreation(self.fc), FadeIn(leg[0]), FadeIn(leg[1]),
                  run_time=1.0)
        self.play(ShowCreation(self.fc_truth), run_time=1.3)
        self.play(ShowCreation(self.fc_nb), run_time=1.3)
        self.play(Write(self.sm_nb), run_time=0.9)

        self.cap.show(
            "Seven point three percent error, on a flat series.",
            "Seven point three percent error, on a series that barely needed "
            "a trend at all.", size=30, color=C_NEUT)
        self.wait(2.4)

        self.true_seas = true_seas

    # ── §2  Put the number back ──────────────────────────────────────────
    def s2_gate(self):
        self.cap.show(
            "So the contribution has to be adjustable, per series.",
            "So the contribution has to be adjustable per series, without "
            "retraining the block. Which means putting a real number back in "
            "front of each piece.", size=30)
        self.play(FadeOut(self.true_seas),
                  stagger([Indicate(b, color=C_HOT, scale_factor=1.12)
                           for b in self.bars], lag_ratio=0.18),
                  run_time=1.5)

        self.cap.show(
            "Read it off the one thing that differs: the input window.",
            "Where does that number come from? From the one thing that is "
            "already different for every series — the input window.", size=30)

        # Node before connector (ANTI-PATTERN #9): the gate box, then its
        # input arrow, then the fan-out to the bars.
        gbox = RoundedRectangle(width=GATE_W, height=GATE_H, corner_radius=0.16)
        gbox.set_stroke(C_GATE, width=2.4, opacity=1.0)
        gbox.set_fill(C_GATE, opacity=0.10)
        gbox.move_to(GATE_C)
        glbl = Tex("G").scale(0.72).set_color(C_GATE).move_to(GATE_C)
        assert_in_frame(gbox=gbox, glbl=glbl)
        self.play(ShowCreation(gbox), Write(glbl), run_time=0.9)

        a_in = arrow(self.in_panel.get_right() + RIGHT * 0.06,
                     gbox.get_left() + LEFT * 0.04, C_GATE, stroke_width=2.6)
        self.play(ShowCreation(a_in), run_time=0.6)

        fan = VGroup(*[
            arrow(gbox.get_bottom() + DOWN * 0.04,
                  np.array([BAR_X0 - 0.10, LANE_Y[i], 0]),
                  C_GATE, stroke_width=2.0)
            for i in range(3)])
        for f in fan:
            f.set_stroke(C_GATE, width=1.5, opacity=0.32)
            f.set_fill(C_GATE, opacity=0.32)
        assert_in_frame(fan=fan)
        self.play(stagger([ShowCreation(f) for f in fan], lag_ratio=0.22),
                  run_time=1.1)
        self.bring_to_front(*self.bars, *self.nums)

        # The bars stop being fixed scaffolding and become the gate's doing.
        self.play(*[Transform(self.bars[i],
                              make_bar(UNIFORM[i], LANE_Y[i], C_GATE))
                    for i in range(3)],
                  *[n.animate.set_color(C_GATE) for n in self.nums],
                  run_time=1.0)

        # Formalism arrives only now, naming a picture already on screen.
        self.cap.show(
            "One linear layer, then a softmax.",
            "Run it through a single linear layer, take a softmax, and you "
            "get three numbers — positive, and summing to one.", size=30)
        eq_g = equation(Tex(r"\hat{G}_\ell"), "=",
                        Tex(r"\text{softmax}_\ell\big(\text{Linear}"
                            r"_\ell(x_0)\big)"),
                        buff=0.14, scale=0.62)
        eq_g.move_to(np.array([EQ_X, EQ_GATE_Y, 0]))
        assert_in_frame(eq_g=eq_g)
        assert_no_overlap([("eq_g", eq_g, "eq_sum", self.eq_sum)], pad=0.05)
        self.play(Write(eq_g), run_time=1.5)
        hold(self, 1.4)

        # The coefficients in the sum become the gate weights.
        self.cap.show(
            "The sum becomes a weighted sum.",
            "That is the whole modification. The sum becomes a weighted sum, "
            "and the weights are read off the input.", size=30)
        new_coefs = [Tex(r"\hat{G}_%d\,\cdot" % (i + 1)).set_color(C_GATE)
                     for i in range(3)]
        new_terms = [Tex(r"\hat{y}_%d" % (i + 1)) for i in range(3)]
        eq2 = equation(Tex(r"\hat{y}"), "=",
                       new_coefs[0], new_terms[0], "+",
                       new_coefs[1], new_terms[1], "+",
                       new_coefs[2], new_terms[2],
                       buff=0.13, scale=0.72)
        eq2.move_to(np.array([EQ_X, EQ_SUM_Y, 0]))
        assert_in_frame(eq2=eq2)
        self.play(ReplacementTransform(self.eq_sum, eq2), run_time=1.3)
        self.eq_sum, self.coefs, self.terms = eq2, new_coefs, new_terms
        hold(self, 1.3)

        # The special case: a uniform gate IS the original model. Computed —
        # the drawn MoE forecast with equal weights lands on the baseline.
        self.cap.show(
            "Make all three equal, and you get N-BEATS back exactly.",
            "Notice what happens when all three weights are equal. You get "
            "the original N-BEATS back, exactly. Plain N-BEATS is this model "
            "with the gate frozen.", size=30)
        third = [DecimalNumber(1 / 3, num_decimal_places=2, color=C_GATE)
                 .scale(0.52).move_to(np.array([NUM_X, LANE_Y[i], 0]))
                 for i in range(3)]
        assert_in_frame(**{f"third{i}": m for i, m in enumerate(third)})
        self.play(stagger([ReplacementTransform(self.nums[i], third[i])
                           for i in range(3)], lag_ratio=0.15),
                  run_time=1.0)
        # Attach the updaters only after the transform, so the readouts do not
        # fight the animation that is placing them. set_value rebuilds the
        # glyphs, so re-anchor each frame (ANTI-PATTERN #10: never repeatedly
        # Transform a Tex whose digit count changes).
        for i, dn in enumerate(third):
            dn.add_updater(lambda m, i=i: m.set_value(
                self.trackers[i].get_value()).move_to(
                    np.array([NUM_X, LANE_Y[i], 0])))
        self.nums = third
        frozen = box_around(VGroup(*self.bars), C_HOT, buff=0.16)
        self.play(ShowCreation(frozen), run_time=0.8)
        self.wait(2.0)
        self.play(FadeOut(frozen), run_time=0.5)

        # Why the input is normalised first.
        self.cap.show(
            "The input is normalised first — or the gate collapses.",
            "One detail matters here. The input is normalised before the "
            "linear layer.", size=30)
        ln_lbl = label("LayerNorm", 18, C_GATE)
        ln_lbl.next_to(a_in, UP, buff=0.10)
        assert_in_frame(ln_lbl=ln_lbl)
        self.play(FadeIn(ln_lbl), run_time=0.6)
        self.set_weights([0.97, 0.02, 0.01], run_time=1.0, color=C_HOT)
        self.cap.show(
            "Without it, one expert takes everything.",
            "Without that, the gate collapses: one weight takes everything "
            "and the other two never get trained.", size=30, color=C_HOT)
        self.set_weights(UNIFORM, run_time=1.0, color=C_GATE)

        # And now the real gate, on the real window.
        g = D.gate(D.HERO.window())
        self.cap.show(
            "On this series, the gate pulls the trend down to 17%.",
            "And now, on this series, the gate pulls the trend down to "
            "seventeen percent.", size=30)
        back = curve(self.lanes[1], D.HERO.trend, C_MODEL, width=3.0)
        back_s = curve(self.lanes[2], D.HERO.seasonal, C_MODEL, width=3.0)
        self.set_weights(g, run_time=1.6,
                         extra=[Transform(self.lane_curves[1], back),
                                Transform(self.lane_curves[2], back_s)])
        hold(self, 1.5)

        self.cap.show(
            "The forecast follows the truth. Two point seven.",
            "The forecast follows the truth. Two point seven percent.",
            size=30, color=C_MODEL)
        self.play(ShowCreation(self.fc_moe), run_time=1.4)
        self.play(self.leg_moe.animate.set_opacity(1.0),
                  self.sm_moe.animate.set_opacity(1.0),
                  self.fc_nb.animate.set_stroke(opacity=0.45),
                  run_time=0.9)
        self.wait(2.6)

        self.gbox, self.glbl, self.a_in, self.fan = gbox, glbl, a_in, fan
        self.eq_g, self.ln_lbl = eq_g, ln_lbl

    # ── §3  Where it wins, and where it doesn't ──────────────────────────
    def s3_evidence(self):
        # The forecast panel has done its job; the bars carry the boundary.
        self.cap.show(
            "Twelve datasets. A hundred thousand series.",
            "Twelve datasets, a hundred thousand series.", size=30)
        self.play(FadeOut(VGroup(self.fc, self.fc_truth, self.fc_nb,
                                 self.fc_moe, self.leg, self.sm_nb,
                                 self.sm_moe, self.ln_lbl)),
                  run_time=1.0)

        head = label("mixed domains", 24, C_DATA)
        head.move_to(np.array([FC_C[0], 1.05, 0]))
        sub = label("M1  ·  M3  ·  M4", 19, C_NEUT)
        sub.next_to(head, DOWN, buff=0.14)
        assert_in_frame(head=head, sub=sub)
        self.play(FadeIn(head), FadeIn(sub), run_time=0.8)

        # Table 3's record, as a strip of ticks rather than a table dump.
        strip = VGroup()
        for j, (_, _, win) in enumerate(D.RECORD_MIXED):
            strip.add(marker(ORIGIN, C_WIN if win else C_NEUT, size=0.24,
                             opacity=1.0 if win else 0.40))
        strip.arrange(RIGHT, buff=0.14)
        strip.next_to(sub, DOWN, buff=0.30)
        rec = label("6 of 9 to N-BEATS-MoE", 20, C_WIN)
        rec.next_to(strip, DOWN, buff=0.18)
        assert_in_frame(strip=strip, rec=rec)

        self.cap.show(
            "On the mixed-domain sets, the gated model wins six of nine.",
            "On M1, M3 and M4 — each built from many different domains — the "
            "gated model beats N-BEATS in six of nine cases.", size=30)
        self.play(stagger([FadeIn(m) for m in strip], lag_ratio=0.14),
                  run_time=1.2)
        self.play(Write(rec), run_time=0.8)

        # The bars, driven by real series from each ensemble. Ghost ticks
        # accumulate where each bar has been, so the spread is visible.
        self.cap.show(
            "Watch the bars move from series to series.",
            "And you can see why. Watch what the gate does as you move from "
            "one series in that collection to the next. A series that is "
            "mostly trend routes almost everything to the trend expert. The "
            "next one is flat and strongly seasonal, and the weights swing "
            "right across.", size=30)
        ghosts = self.run_ensemble(D.m1_like(6), C_DATA)
        self.cap.show(
            "Every series gets a different mix.",
            "Each series gets its own mix, and the marks left behind show how "
            "far the weights travel.", size=30)
        hold(self, 1.6)

        self.cap.show(
            "On Tourism — a single domain — it loses all three.",
            "On Tourism it doesn't win. It loses all three. Tourism is a "
            "single domain, so its series look broadly alike.", size=30)
        head2 = label("single domain", 24, C_NEUT)
        head2.move_to(head)
        sub2 = label("Tourism", 19, C_NEUT).move_to(sub)
        strip2 = VGroup(*[marker(ORIGIN, C_NEUT, size=0.24, opacity=0.40)
                          for _ in D.RECORD_TOURISM])
        strip2.arrange(RIGHT, buff=0.14)
        strip2.move_to(strip)
        rec2 = label("0 of 3", 20, C_NEUT).move_to(rec)
        assert_in_frame(head2=head2, strip2=strip2, rec2=rec2)
        self.play(ReplacementTransform(head, head2),
                  ReplacementTransform(sub, sub2),
                  ReplacementTransform(strip, strip2),
                  ReplacementTransform(rec, rec2),
                  FadeOut(ghosts), run_time=1.3)

        ghosts2 = self.run_ensemble(D.tourism_like(6), C_NEUT)
        self.cap.show(
            "The gate opens to nearly the same numbers every time.",
            "Every series here is a tourism series, so the gate sees much the "
            "same features each time, and opens to nearly the same three "
            "numbers.", size=30)
        self.play(stagger([Indicate(g, color=C_NEUT, scale_factor=1.2)
                           for g in ghosts2], lag_ratio=0.05), run_time=1.2)
        self.cap.show(
            "The marks barely spread at all.",
            "The marks it leaves behind barely spread at all. Where that "
            "happens the extra weights buy you very little, and here they "
            "cost a little accuracy.", size=30)
        self.wait(0.8)

        self.cap.show(
            "The gains are real, but concentrated where the data is mixed.",
            "So the gains are real, but they are not uniform. They are "
            "concentrated where the data is mixed.", size=30)
        self.wait(1.8)

        self.ev_group = VGroup(head2, sub2, strip2, rec2)
        self.play(FadeOut(ghosts2), run_time=0.6)

    def run_ensemble(self, series, tick_color):
        """Drive the bars through real series; leave a ghost tick at each
        bar's end position so the spread across the ensemble is legible."""
        ghosts = VGroup()
        for k, s in enumerate(series):
            w = D.gate(s.window())
            hidx = np.arange(-D.N_HIST, 1)
            new_hist = polyline(self.in_panel, hidx,
                                fit_to_panel(self.in_panel, s.observed(hidx)),
                                C_DATA, width=2.0)
            ticks = [Line(np.array([BAR_X0 + wi * BAR_MAX,
                                    LANE_Y[i] - BAR_H / 2 - 0.11, 0]),
                          np.array([BAR_X0 + wi * BAR_MAX,
                                    LANE_Y[i] + BAR_H / 2 + 0.11, 0]))
                     .set_stroke(tick_color, width=2.4, opacity=0.75)
                     for i, wi in enumerate(w)]
            self.set_weights(
                w, run_time=0.75,
                extra=[Transform(self.in_curve, new_hist)]
                + [FadeIn(t) for t in ticks])
            ghosts.add(*ticks)
            self.wait(0.30)
        return ghosts

    # ── §4  The bars as a readout ────────────────────────────────────────
    def s4_readout(self):
        self.cap.show(
            "The weights are visible — so you can read them.",
            "There is a second thing you get for free. The weights are "
            "visible, so you can ask what the model thinks a series is.",
            size=30)

        head = label("STL component", 22, C_DATA)
        head.move_to(np.array([FC_C[0], 1.35, 0]))
        which = label("M3   ·   trend", 26, C_NEUT)
        which.next_to(head, DOWN, buff=0.22)
        assert_in_frame(head=head, which=which)
        self.play(ReplacementTransform(self.ev_group, VGroup(head, which)),
                  run_time=1.1)

        self.cap.show(
            "Decompose with STL, then see which expert the gate favours.",
            "Decompose each series with STL into a trend part, a seasonal "
            "part and a remainder, then check which expert the gate favours "
            "for each of them.", size=30)

        note = label("", 20, C_WIN)
        note.move_to(np.array([FC_C[0], -0.55, 0]))
        self.note = note
        self.add(note)

        for comp in ("Trend", "Seasonal"):
            self.show_alignment("M3", comp, which, aligned=True)
        self.cap.show(
            "On M3 it lines up.",
            "On M3 it lines up: trend components go to the trend expert, "
            "seasonal components to the seasonal expert.", size=30,
            color=C_WIN)
        self.wait(1.6)

        for comp in ("Trend",):
            self.show_alignment("M1", comp, which, aligned=False)
        self.cap.show(
            "On M1 it doesn't line up at all.",
            "On M1 it doesn't line up at all. Trend components get routed to "
            "the seasonal expert, more than two-thirds of the time. And M1 "
            "is where the model wins by the largest margin.", size=30,
            color=C_HOT)
        self.wait(2.6)

        self.cap.show(
            "A large weight means contribution, not amplitude.",
            "So the gate is not a component detector. A large weight doesn't "
            "mean a large output. It means that piece contributes more to "
            "getting the answer right.", size=30)
        caveat = Text("weight = contribution,\nnot amplitude",
                      font=FONT, font_size=26).set_color(C_HOT)
        caveat.move_to(np.array([FC_C[0], -1.75, 0]))
        assert_in_frame(caveat=caveat)
        assert_no_overlap([("caveat", caveat, "note", self.note)], pad=0.05)
        self.play(Write(caveat), run_time=1.4)
        self.wait(2.2)

        self.readout = VGroup(head, which, caveat)

    def show_alignment(self, dataset, comp, which_lbl, aligned):
        w = D.TABLE4[dataset][comp]
        expected = {"Trend": 1, "Seasonal": 2, "Residual": 0}[comp]
        picked = int(np.argmax(w))
        new_lbl = label(f"{dataset}   ·   {comp.lower()}", 26, C_NEUT)
        new_lbl.move_to(which_lbl)
        col = C_WIN if picked == expected else C_HOT
        txt = ("routed to the " + LANE_NAME[picked].lower() + " expert"
               + ("  ✓" if picked == expected else ""))
        new_note = label(txt, 20, col)
        new_note.move_to(self.note)
        assert_in_frame(new_lbl=new_lbl, new_note=new_note)

        self.play(ReplacementTransform(which_lbl.copy(), new_lbl),
                  FadeOut(which_lbl), run_time=0.5)
        which_lbl.become(new_lbl)
        self.remove(new_lbl)
        self.add(which_lbl)

        self.set_weights(w, run_time=1.1, color=C_GATE)
        self.play(FadeOut(self.note), run_time=0.25)
        self.remove(self.note)
        self.note = new_note
        self.add(self.note)
        self.play(FadeIn(self.note),
                  Indicate(self.bars[picked], color=col, scale_factor=1.10),
                  run_time=0.9)
        self.wait(1.5)
        _ = aligned

    # ── §5  Payoff ───────────────────────────────────────────────────────
    def s5_payoff(self):
        self.cap.clear(run_time=0.4)
        # §4's annotations have made their point; clearing them before the
        # payoff keeps the closing frame to one idea. The lanes, bars and gate
        # all survive the boundary, so nothing is being cut away.
        self.play(FadeOut(VGroup(self.readout, self.note)), run_time=0.8)
        stage = Dimmer(*self.lanes, *self.lane_curves, *self.lane_names,
                       self.in_panel, self.in_curve, self.x0_lbl,
                       self.eq_sum, self.eq_g, self.gbox, self.glbl,
                       self.a_in, self.fan, *self.bars, *self.nums)

        # Verbatim, in the styling it had at 0:35.
        q = Text(self.q_text, font=FONT, font_size=36).set_color(C_HOT)
        q.move_to(np.array([EQ_X, -1.35, 0]))
        assert_in_frame(q=q)
        assert_no_overlap([(f"q/num{i}", q, f"num{i}", m)
                           for i, m in enumerate(self.nums)], pad=0.05)
        self.play(*stage.to(0.14), FadeIn(q, shift=UP * 0.2), run_time=1.2)
        self.wait(2.8)

        ans = Text("The series does.", font=FONT, font_size=44)
        ans.set_color(WHITE).move_to(np.array([EQ_X, -1.35, 0]))
        assert_in_frame(ans=ans)
        assert_no_overlap([(f"ans/num{i}", ans, f"num{i}", m)
                           for i, m in enumerate(self.nums)], pad=0.05)
        # The stage starts returning as the question leaves, so the frame is
        # never empty between them.
        self.play(FadeOut(q, shift=UP * 0.3), *stage.to(0.30), run_time=0.7)
        self.play(Write(ans), run_time=1.5)
        self.cap.show(
            "Not the architecture. Not the dataset average.",
            "Not the architecture, and not some average taken across the "
            "whole dataset. The series in front of it, every time.", size=28)
        self.wait(1.0)

        # Point back at the object that answered it.
        self.play(*stage.restore(),
                  ans.animate.scale(0.66).move_to(np.array([EQ_X, 0.55, 0])),
                  run_time=1.3)
        self.play(stagger([Indicate(b, color=C_HOT, scale_factor=1.12)
                           for b in self.bars], lag_ratio=0.22),
                  run_time=1.4)

        self.cap.show(
            "Every sum has coefficients, chosen or not.",
            "Every forecast N-BEATS makes is a sum, and every sum has "
            "coefficients, whether or not anyone ever chose them.", size=30)

        # Close on the series it opened with, still gated.
        self.set_weights(D.gate(D.HERO.window()), run_time=1.2,
                         extra=[Transform(
                             self.in_curve,
                             polyline(self.in_panel,
                                      np.arange(-D.N_HIST, 1),
                                      D.HERO.observed(
                                          np.arange(-D.N_HIST, 1)),
                                      C_DATA, width=2.0))])
        self.cap.show(
            "The model looks them up, instead of assuming them.",
            "All this changes is that they become something the model looks "
            "up for the series in front of it, instead of something it "
            "assumes once and applies to everything.", size=30)
        self.wait(1.2)
        self.cap.clear(run_time=0.5)
        self.play(FadeOut(Group(*self.mobjects)), run_time=1.6)
        self.wait(0.6)
