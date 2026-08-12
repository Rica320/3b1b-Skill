from manimlib import *
import numpy as np


# ── Beat 0: Cold open — "Can you tell which is real?" (0:00–0:45) ──────────
# Digits represented as glowing pixel-grid squares; images zoom out into a
# point-cloud.  No voiceover — timing set for ~45 s of narration cadence.

REAL_COLOR   = BLUE_C
FAKE_COLOR   = ORANGE
BG           = BLACK
LABEL_FONT   = "CMU Serif"


def digit_square(val: int, color=WHITE, side=0.7) -> VGroup:
    """Tiny labeled square that stands in for a handwritten digit."""
    sq = Square(side_length=side)
    sq.set_stroke(color, width=2)
    sq.set_fill(color, opacity=0.12)
    num = Text(str(val), font=LABEL_FONT, font_size=22).set_color(color)
    num.move_to(sq)
    return VGroup(sq, num)


class ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── 1. Title appears ──────────────────────────────────────────────
        title = Text("GANs, Explained Visually", font=LABEL_FONT, font_size=44)
        title.set_color(WHITE)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)
        self.wait(0.5)

        # ── 2. Six real digits spread across screen ───────────────────────
        digits_vals = [3, 7, 1, 9, 4, 0]
        digits = VGroup(*[
            digit_square(v, REAL_COLOR) for v in digits_vals
        ])
        digits.arrange(RIGHT, buff=0.45)
        digits.move_to(ORIGIN)

        self.play(
            LaggedStart(*[FadeIn(d, shift=DOWN * 0.2) for d in digits],
                        lag_ratio=0.15),
            run_time=1.8
        )
        self.wait(0.6)

        # ── 3. Label: "Real examples" ─────────────────────────────────────
        real_lbl = Text("Real examples", font=LABEL_FONT, font_size=28)
        real_lbl.set_color(REAL_COLOR)
        real_lbl.next_to(digits, DOWN, buff=0.4)
        self.play(FadeIn(real_lbl), run_time=0.6)
        self.wait(0.8)

        # ── 4. One digit morphs into another  ─────────────────────────────
        morph_src = digit_square(3, REAL_COLOR, side=1.1)
        morph_tgt = digit_square(8, REAL_COLOR, side=1.1)
        morph_src.move_to(digits[0])
        morph_tgt.move_to(digits[0])

        self.play(Transform(digits[0], morph_src), run_time=0.4)
        self.play(Transform(digits[0], morph_tgt), run_time=1.2)
        self.wait(0.4)

        # ── 5. A "generated" image slides in — looks plausible ─────────────
        fake_d = digit_square(3, FAKE_COLOR, side=0.7)
        fake_d.next_to(digits, RIGHT, buff=0.6)
        fake_lbl = Text("Generated?", font=LABEL_FONT, font_size=22)
        fake_lbl.set_color(FAKE_COLOR)
        fake_lbl.next_to(fake_d, DOWN, buff=0.25)

        self.play(FadeIn(fake_d, shift=LEFT * 0.3), run_time=0.7)
        self.play(Write(fake_lbl), run_time=0.5)
        self.wait(1.0)

        # ── 6. Question card ───────────────────────────────────────────────
        q1 = Text("If you had a million examples,", font=LABEL_FONT, font_size=30)
        q2 = Text("could a machine learn to make new ones?",
                  font=LABEL_FONT, font_size=30)
        q_group = VGroup(q1, q2).arrange(DOWN, buff=0.2)
        q_group.set_color(YELLOW)
        q_group.to_edge(DOWN, buff=0.7)

        self.play(Write(q1), run_time=1.2)
        self.play(Write(q2), run_time=1.4)
        self.wait(1.0)

        # ── 7. Zoom out: digits become dots in a point-cloud ──────────────
        all_shown = VGroup(digits, fake_d, fake_lbl, real_lbl)
        dots = VGroup(*[
            Dot(d.get_center(), radius=0.07, color=REAL_COLOR)
            for d in digits
        ] + [Dot(fake_d.get_center(), radius=0.07, color=FAKE_COLOR)])

        # Extra random cloud of points suggesting a large distribution
        rng = np.random.default_rng(42)
        cloud_pts = VGroup(*[
            Dot(
                np.array([rng.uniform(-5, 5), rng.uniform(-2.5, 2.5), 0]),
                radius=0.04,
                color=BLUE_A,
            )
            for _ in range(120)
        ])

        self.play(
            *[Transform(d, dots[i]) for i, d in enumerate(digits)],
            Transform(fake_d, dots[-1]),
            FadeOut(fake_lbl),
            FadeOut(real_lbl),
            run_time=1.5,
        )
        self.play(
            LaggedStart(*[FadeIn(p) for p in cloud_pts], lag_ratio=0.02),
            run_time=1.5,
        )
        self.wait(0.5)

        # narration beat: "the interesting question is learning the distribution"
        dist_lbl = Text(
            "The goal: learn the distribution,\nnot memorise examples.",
            font=LABEL_FONT, font_size=28,
        )
        dist_lbl.set_color(WHITE)
        dist_lbl.to_edge(DOWN, buff=0.5)

        self.play(FadeOut(q_group), run_time=0.4)
        self.play(Write(dist_lbl), run_time=1.4)
        self.wait(2.0)

        self.play(FadeOut(VGroup(title, dist_lbl, cloud_pts, dots, fake_d, digits)),
                  run_time=1.0)
        self.wait(0.3)
