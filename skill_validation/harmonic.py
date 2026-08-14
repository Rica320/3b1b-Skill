"""
Skill-validation scene: "Why does the harmonic series diverge?"

Written from the 3b1b-math-animation skill alone (narrative_template.md,
animation_rules.md, anti_patterns.md, checklists.md, manim_helpers.py).

Spine
  QUESTION    the terms shrink to nothing - so why doesn't the sum settle?
  MOTIVATION  watch the partial sums; they crawl. It *looks* convergent.
              That intuition is the obvious answer, and it is wrong.
  BUILD       group the terms into blocks; every block is worth at least 1/2;
              there are infinitely many blocks, so the staircase gains 1/2
              forever.
  PAYOFF      restate the question, answer it: shrinking is not enough -
              they have to shrink FAST enough.

Carried metaphor: THE STAIRCASE of partial sums.
  a term            -> one step's height
  the partial sum   -> how high you have climbed
  "does it settle?" -> does the staircase level off?
  the blocks        -> a fixed 1/2 gain, repeatable forever
  divergence        -> a staircase with no ceiling

Colour mapping (fixed for the whole scene)
  BLUE_C   the terms of the series (the given data)
  ORANGE   the partial sum / the staircase (the thing being computed)
  TEAL_C   the comparison blocks (the second actor)
  YELLOW   transient emphasis only
  GREY_B   scaffolding: axes, braces, connectives
"""

from manimlib import *
from pathlib import Path
import sys
import os

# ManimGL's loader does not put the scene file's directory on sys.path.
sys.path.insert(0, str(Path(__file__).parent))

from manim_helpers import (
    dot, arrow, label, Caption, Dimmer, hold, stagger, morph,
    push_in, pull_back, dump_meta, equation, box_around,
    assert_in_frame, assert_no_overlap, audit_text_overlaps,
    FONT, FRAME_H,
)

C_TERM = BLUE_C      # the terms
C_SUM = ORANGE       # the partial sum / staircase
C_BLOCK = TEAL_C     # the comparison blocks
C_HOT = YELLOW       # transient emphasis
C_NEUT = GREY_B

N_STEPS = 24


class Harmonic(Scene):

    def wait(self, *args, **kwargs):
        r = super().wait(*args, **kwargs)
        if os.environ.get("AUDIT"):
            audit_text_overlaps(self)
        return r

    def construct(self):
        self.camera.background_color = BLACK
        self.cap = Caption(self)
        for name, fn in [("s0", self.s0_question), ("s1", self.s1_crawl),
                         ("s2", self.s2_blocks), ("s3", self.s3_payoff)]:
            t0 = self.time
            fn()
            print(f"[TIMING] {name} start={t0:6.1f}s dur={self.time - t0:5.1f}s")
        dump_meta(self, str(Path(__file__).parent / "render_meta.json"))

    # ── §0  The question ─────────────────────────────────────────────────
    def s0_question(self):
        series = Tex(r"1 + \tfrac12 + \tfrac13 + \tfrac14 + \tfrac15 + \cdots")
        series.scale(1.25).set_color(C_TERM)
        series.move_to(np.array([0, 0.9, 0]))
        assert_in_frame(series=series)
        self.play(Write(series), run_time=2.0)
        hold(self, 1.5)

        self.cap.show(
            "The terms shrink to nothing.",
            "Add up one, plus a half, plus a third, plus a quarter, "
            "and keep going forever. The terms shrink to nothing.",
            size=30)

        shrink = Tex(r"\tfrac{1}{n} \to 0").scale(1.0).set_color(C_HOT)
        shrink.move_to(np.array([0, -0.6, 0]))
        assert_in_frame(shrink=shrink)
        self.play(Write(shrink), run_time=1.0)
        hold(self, 1.5)

        # the driving question, anchored to what is on screen
        question = Text("So why doesn't the sum settle down?",
                        font=FONT, font_size=36).set_color(C_HOT)
        question.move_to(np.array([0, -2.3, 0]))
        assert_no_overlap([("shrink", shrink, "question", question)], pad=0.05)
        assert_in_frame(question=question)
        self.play(Write(question), run_time=1.8)
        self.wait(3.4)

        self.series = series
        self.shrink = shrink
        self.question = question

    # ── §1  The obvious expectation, tried and failed ────────────────────
    def s1_crawl(self):
        self.cap.show(
            "Watch the running total.",
            "The obvious guess is that it settles. Watch the running total "
            "and it certainly looks that way.",
            size=30)

        # The series becomes the staircase - the carried object enters by
        # transformation, not by appearing alongside.
        axes = Axes(x_range=(0, N_STEPS, 4), y_range=(0, 4.4, 1),
                    width=9.4, height=4.0)
        axes.set_stroke(GREY_D, width=1.6)
        axes.move_to(np.array([0.35, -0.35, 0]))
        y_lbl = label("running total", 22, C_SUM)
        y_lbl.next_to(axes, LEFT, buff=0.0).shift(RIGHT * 0.35 + UP * 1.7)
        # sits at the right end: the comparison braces claim the band directly
        # under the first two-thirds of the axis
        x_lbl = label("how many terms", 22, C_NEUT)
        x_lbl.next_to(axes.c2p(20, 0), DOWN, buff=0.22)
        assert_in_frame(axes=axes, y_lbl=y_lbl, x_lbl=x_lbl)

        self.play(
            FadeOut(self.shrink, shift=UP * 0.25),
            FadeOut(self.question, shift=DOWN * 0.25),
            self.series.animate.scale(0.62).move_to(np.array([0, 3.0, 0]))
                       .set_opacity(0.45),
            run_time=1.2,
        )
        self.play(ShowCreation(axes), FadeIn(y_lbl), FadeIn(x_lbl),
                  run_time=1.1)

        partial, steps, tops = 0.0, VGroup(), []
        for n in range(1, N_STEPS + 1):
            prev = partial
            partial += 1.0 / n
            riser = Line(axes.c2p(n - 1, prev), axes.c2p(n - 1, partial))
            tread = Line(axes.c2p(n - 1, partial), axes.c2p(n, partial))
            for seg in (riser, tread):
                seg.set_stroke(C_SUM, width=3.0)
            steps.add(riser, tread)
            tops.append((n, partial))

        self.play(stagger([ShowCreation(s) for s in steps], lag_ratio=0.035),
                  run_time=3.2)
        hold(self, 1.5)

        self.cap.show(
            "Each step is flatter than the last.",
            "Each new step is flatter than the one before it. After "
            "twenty-four terms we are barely climbing at all. Everything "
            "about this picture says it is levelling off.",
            size=30)
        self.wait(2.6)

        self.axes = axes
        self.steps = steps
        self.y_lbl = y_lbl
        self.x_lbl = x_lbl

    # ── §2  Why that intuition fails: the blocks ─────────────────────────
    def s2_blocks(self):
        self.cap.show(
            "But group the terms, and something else appears.",
            "But it isn't. Group the terms instead, and something else "
            "appears.",
            size=30)

        # brackets under 1/2 | 1/3+1/4 | 1/5..1/8 | 1/9..1/16
        groups = [(2, 2), (3, 4), (5, 8), (9, 16)]
        braces, brace_lbls = VGroup(), VGroup()
        for lo, hi in groups:
            y0 = 0.0
            br = Line(self.axes.c2p(lo - 1, y0), self.axes.c2p(hi, y0))
            br.set_stroke(C_BLOCK, width=5.0)
            br.shift(DOWN * 0.16)
            braces.add(br)
            t = Tex(r"\geq \tfrac12").scale(0.62).set_color(C_BLOCK)
            t.next_to(br, DOWN, buff=0.12)
            brace_lbls.add(t)
        assert_in_frame(braces=braces, brace_lbls=brace_lbls)

        # one block at a time, so the claim is earned before it is repeated
        self.play(ShowCreation(braces[0]), Write(brace_lbls[0]), run_time=0.9)
        self.cap.show(
            "A half is a half.",
            "The first block is just one half.",
            size=30, color=C_BLOCK)

        self.play(ShowCreation(braces[1]), Write(brace_lbls[1]), run_time=0.9)
        self.cap.show(
            "A third plus a quarter beats a half.",
            "A third plus a quarter is more than a quarter plus a quarter, "
            "which is a half.",
            size=30, color=C_BLOCK)

        self.play(
            stagger([AnimationGroup(ShowCreation(b), Write(t))
                     for b, t in zip(braces[2:], brace_lbls[2:])],
                    lag_ratio=0.5),
            run_time=1.8,
        )
        self.cap.show(
            "And it never stops working.",
            "Four terms down to an eighth beat a half. Eight terms down to a "
            "sixteenth beat a half. You can always take the next block, and "
            "it is always worth at least a half.",
            size=30, color=C_BLOCK)
        self.wait(2.4)

        # the consequence, on the staircase itself
        self.cap.show(
            "So the staircase gains a half, forever.",
            "Which means the staircase gains half a unit, over and over, "
            "with no end.",
            size=30, color=C_HOT)
        ladder = VGroup()
        for k in range(1, 5):
            ln = DashedLine(self.axes.c2p(0, 0.5 * k),
                            self.axes.c2p(N_STEPS, 0.5 * k),
                            dash_length=0.1)
            ln.set_stroke(C_HOT, width=1.4, opacity=0.55)
            ladder.add(ln)
        self.play(stagger([ShowCreation(l) for l in ladder], lag_ratio=0.25),
                  run_time=1.4)
        hold(self, 2.0)
        self.wait(1.6)

        self.braces = braces
        self.brace_lbls = brace_lbls
        self.ladder = ladder

    # ── §3  Payoff ───────────────────────────────────────────────────────
    def s3_payoff(self):
        # one idea on screen: dim the working, restate the question
        self.cap.clear(run_time=0.4)
        stage = Dimmer(self.axes, self.steps, self.braces, self.brace_lbls,
                       self.ladder, self.y_lbl, self.x_lbl, self.series)
        q = Text("So why doesn't the sum settle down?",
                 font=FONT, font_size=38).set_color(C_HOT)
        q.move_to(np.array([0, 0.7, 0]))
        assert_in_frame(q=q)
        # dim and reveal together - dimming first leaves a near-empty frame
        self.play(*stage.to(0.15), FadeIn(q, shift=UP * 0.2), run_time=1.1)
        self.wait(2.6)

        ans = Text("Shrinking isn't enough.\nThey have to shrink fast enough.",
                   font=FONT, font_size=38).set_color(WHITE)
        ans.move_to(np.array([0, 0.7, 0]))
        # the picture starts coming back as the question leaves, so the frame
        # is never empty between them
        self.play(FadeOut(q, shift=UP * 0.3), *stage.to(0.34), run_time=0.6)
        self.play(Write(ans), run_time=1.8)
        self.wait(2.8)

        # point back at the object that answered it. The series line vacates
        # the top band the answer is moving into.
        self.play(*stage.restore(),
                  FadeOut(self.series, shift=UP * 0.3),
                  ans.animate.move_to(np.array([0, 3.05, 0])).scale(0.72),
                  run_time=1.2)
        self.play(stagger([Indicate(l, color=C_HOT) for l in self.ladder],
                          lag_ratio=0.18),
                  run_time=1.4)
        hold(self, 2.0)

        diverge = Tex(r"\sum_{n=1}^{\infty} \tfrac{1}{n} = \infty")
        diverge.scale(0.95).set_color(C_SUM)
        diverge.move_to(np.array([0, -3.0, 0]))
        assert_in_frame(diverge=diverge)
        # the band under the axis is vacated for the result: the "≥ ½" labels
        # have made their point, and the braces alone still show the grouping
        # (no assert_no_overlap here: it is geometric, so it would still see
        #  the faded-out mobjects' bounding boxes)
        self.play(FadeOut(self.x_lbl, shift=DOWN * 0.2),
                  FadeOut(self.brace_lbls, shift=DOWN * 0.15),
                  Write(diverge), run_time=1.4)
        self.wait(3.0)

        self.play(
            FadeOut(Group(ans, diverge, self.axes, self.steps, self.braces,
                          self.brace_lbls, self.ladder, self.y_lbl)),
            run_time=1.5,
        )
        self.wait(0.6)
