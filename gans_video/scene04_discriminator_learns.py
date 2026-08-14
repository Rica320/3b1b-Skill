from manimlib import *
import numpy as np

# ── Beat 4: The Discriminator learns the rules (4:15–5:30) ────────────────

LABEL_FONT = "CMU Serif"
BG         = BLACK


class DiscriminatorLearns(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── 1. Dial: 0=fake, 1=real ────────────────────────────────────────
        dial_title = Text("Discriminator output", font=LABEL_FONT, font_size=30)
        dial_title.set_color(WHITE)
        dial_title.to_edge(UP, buff=0.5)

        # Number line 0 → 1
        line = Line(LEFT * 4.5, RIGHT * 4.5, color=GREY)
        line.move_to(ORIGIN + UP * 0.6)
        tick0 = Line(DOWN * 0.15, UP * 0.15, color=GREY).move_to(line.get_start())
        tick1 = Line(DOWN * 0.15, UP * 0.15, color=GREY).move_to(line.get_end())
        lbl0 = Text("0 — fake", font=LABEL_FONT, font_size=22)
        lbl0.set_color(ORANGE)
        lbl0.next_to(tick0, DOWN, buff=0.2)
        lbl1 = Text("1 — real", font=LABEL_FONT, font_size=22)
        lbl1.set_color(BLUE_C)
        lbl1.next_to(tick1, DOWN, buff=0.2)
        lbl_half = Text("0.5", font=LABEL_FONT, font_size=20)
        lbl_half.set_color(GREY)
        lbl_half.next_to(line.get_center(), DOWN, buff=0.25)

        dial_group = VGroup(line, tick0, tick1, lbl0, lbl1, lbl_half)

        self.play(Write(dial_title), run_time=0.7)
        self.play(ShowCreation(dial_group), run_time=1.0)
        self.wait(0.5)

        # Needle (dot) moving along the line
        needle = Dot(radius=0.14, color=YELLOW)
        needle.move_to(line.point_from_proportion(0.5))  # start center

        cases = [
            ("Real face",      0.92, BLUE_C),
            ("Random noise",   0.05, ORANGE),
            ("Bad fake face",  0.12, ORANGE),
            ("Good fake face", 0.55, YELLOW),
        ]

        case_lbl = Text("", font=LABEL_FONT, font_size=26)
        case_lbl.move_to(DOWN * 1.5)

        self.play(GrowFromCenter(needle), run_time=0.5)

        for name, val, color in cases:
            new_lbl = Text(name, font=LABEL_FONT, font_size=26)
            new_lbl.set_color(color)
            new_lbl.move_to(DOWN * 1.5)
            self.play(
                needle.animate.move_to(line.point_from_proportion(val)),
                FadeOut(case_lbl),
                FadeIn(new_lbl),
                run_time=0.9,
            )
            case_lbl = new_lbl
            self.wait(0.5)

        self.play(FadeOut(VGroup(dial_title, dial_group, needle, case_lbl)),
                  run_time=0.7)

        # ── 2. Key insight: D learns a boundary ───────────────────────────
        insight = Text(
            "The discriminator doesn't need to understand\n"
            '"what a face is."\n'
            "It only needs a boundary separating real from fake.",
            font=LABEL_FONT, font_size=28,
        )
        insight.set_color(YELLOW)
        insight.move_to(UP * 1.5)
        self.play(Write(insight), run_time=2.0)
        self.wait(1.2)
        self.play(FadeOut(insight), run_time=0.6)

        # ── 3. Animated boundary in 2-D toy dataset ────────────────────────
        axes = Axes(
            x_range=(-3, 3, 1),
            y_range=(-2.5, 2.5, 1),
            height=5.0, width=7.0,
        )
        axes.set_color(GREY_D)
        axes.move_to(ORIGIN)
        ax_lbl = Text("2-D toy example  (each point = one image)",
                      font=LABEL_FONT, font_size=20)
        ax_lbl.set_color(GREY)
        ax_lbl.to_edge(UP, buff=0.4)

        self.play(Write(axes), Write(ax_lbl), run_time=0.8)

        rng = np.random.default_rng(22)
        real_pts = VGroup(*[
            Dot(axes.c2p(rng.normal(1.2, 0.5), rng.normal(0.6, 0.5)),
                radius=0.09, color=BLUE_C)
            for _ in range(25)
        ])
        fake_pts = VGroup(*[
            Dot(axes.c2p(rng.normal(-1.3, 0.6), rng.normal(-0.8, 0.5)),
                radius=0.09, color=ORANGE)
            for _ in range(25)
        ])

        self.play(
            LaggedStart(*[GrowFromCenter(d) for d in real_pts], lag_ratio=0.04),
            LaggedStart(*[GrowFromCenter(d) for d in fake_pts], lag_ratio=0.04),
            run_time=1.2,
        )

        real_legend = VGroup(
            Dot(radius=0.09, color=BLUE_C),
            Text("real", font=LABEL_FONT, font_size=20).set_color(BLUE_C),
        ).arrange(RIGHT, buff=0.15)
        fake_legend = VGroup(
            Dot(radius=0.09, color=ORANGE),
            Text("generated", font=LABEL_FONT, font_size=20).set_color(ORANGE),
        ).arrange(RIGHT, buff=0.15)
        legend = VGroup(real_legend, fake_legend).arrange(DOWN, buff=0.2, aligned_edge=LEFT)
        legend.to_corner(UR, buff=0.4)
        self.play(FadeIn(legend), run_time=0.5)
        self.wait(0.5)

        # Boundary line: starts diagonal, adjusts
        def boundary(t: float) -> np.ndarray:
            # parametric: vertical line shifting from left to center
            x_pos = -2.5 + t * 2.5   # moves right as t: 0→1
            return axes.c2p(x_pos, 0)

        boundary_line = Line(
            axes.c2p(-2.5, -2.5), axes.c2p(-2.5, 2.5),
            color=WHITE, stroke_width=2,
        )

        self.play(ShowCreation(boundary_line), run_time=0.7)

        # Animate boundary sweeping right to separate the clouds
        final_line = Line(
            axes.c2p(-0.1, -2.5), axes.c2p(-0.1, 2.5),
            color=WHITE, stroke_width=2,
        )
        self.play(Transform(boundary_line, final_line), run_time=1.5)

        sep_lbl = Text("Decision boundary", font=LABEL_FONT, font_size=20)
        sep_lbl.set_color(WHITE)
        sep_lbl.next_to(axes.c2p(-0.1, 2.5), RIGHT, buff=0.2)
        self.play(FadeIn(sep_lbl), run_time=0.5)
        self.wait(2.0)

        self.play(
            FadeOut(VGroup(axes, ax_lbl, real_pts, fake_pts,
                           legend, boundary_line, sep_lbl)),
            run_time=0.8,
        )
        self.wait(0.2)
