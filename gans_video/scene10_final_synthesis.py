from manimlib import *
from pathlib import Path
import numpy as np

# ── Beat 10: Final synthesis — "A GAN is a feedback loop" (12:30–13:30) ───

LABEL_FONT = "CMU Serif"
BG         = BLACK
ASSETS     = Path(__file__).parent / "assets" / "faces"


def photo_thumb(filename: str, color=WHITE, height: float = 0.55) -> Group:
    """A face photo with a thin colored border, standing in for one example."""
    img = ImageMobject(str(ASSETS / filename))
    img.set_height(height)
    border = Rectangle(width=img.get_width(), height=img.get_height())
    border.set_stroke(color, width=2)
    border.set_fill(opacity=0)
    border.move_to(img)
    return Group(img, border)


class FinalSynthesis(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── 1. Full annotated diagram ─────────────────────────────────────
        # Boxes
        g_box = Rectangle(width=2.2, height=1.0)
        g_box.set_stroke(YELLOW, 2.5)
        g_box.set_fill(YELLOW, opacity=0.08)
        g_box.move_to(LEFT * 0.5 + UP * 1.8)
        g_lbl = Text("GENERATOR", font=LABEL_FONT, font_size=22).set_color(YELLOW)
        g_lbl.move_to(g_box)

        d_box = Rectangle(width=2.6, height=1.0)
        d_box.set_stroke(TEAL_C, 2.5)
        d_box.set_fill(TEAL_C, opacity=0.08)
        d_box.move_to(RIGHT * 0.3 + DOWN * 0.5)
        d_lbl = Text("DISCRIMINATOR", font=LABEL_FONT, font_size=20).set_color(TEAL_C)
        d_lbl.move_to(d_box)

        # z input
        z_dot = Dot(radius=0.1, color=ORANGE)
        z_dot.move_to(LEFT * 4.0 + UP * 1.8)
        z_lbl = Tex(r"\mathbf{z}", font_size=30).set_color(ORANGE)
        z_lbl.next_to(z_dot, LEFT, buff=0.1)

        # real data input
        real_dot = photo_thumb("real_00.png", BLUE_C)
        real_dot.move_to(LEFT * 4.0 + DOWN * 0.5)
        real_lbl = Text("real data", font=LABEL_FONT, font_size=20)
        real_lbl.set_color(BLUE_C).next_to(real_dot, LEFT, buff=0.15)

        # fake data: a small photo icon on the G -> D path
        fake_icon = photo_thumb("fake_blend.png", ORANGE)
        fake_icon.move_to(g_box.get_bottom() + DOWN * 0.6)
        fake_lbl = Text("fake data", font=LABEL_FONT, font_size=20)
        fake_lbl.set_color(ORANGE).move_to(RIGHT * 0.3 + UP * 0.7)

        # Arrows
        arr_z_g   = Arrow(z_dot.get_right(), g_box.get_left(),
                          buff=0.05, color=GREY)
        arr_g_fake = Arrow(g_box.get_bottom(),
                           g_box.get_bottom() + DOWN * 0.6,
                           buff=0.3, color=ORANGE)
        arr_fake_d = Arrow(g_box.get_bottom() + DOWN * 0.6,
                           d_box.get_top() + LEFT * 0.3,
                           buff=0.3, color=ORANGE)
        arr_real_d = Arrow(real_dot.get_right(),
                           d_box.get_left(),
                           buff=0.3, color=BLUE_C)

        # feedback path: D → bottom → back up to G
        feedback_pts = [
            d_box.get_bottom(),
            d_box.get_bottom() + DOWN * 1.0,
            g_box.get_bottom() + LEFT * 3.0 + DOWN * 1.0,
            g_box.get_bottom() + LEFT * 3.0,
            g_box.get_left(),
        ]
        feedback_path = VMobject()
        feedback_path.set_points_as_corners(feedback_pts)
        feedback_path.set_stroke(GREEN, 2.0)

        feedback_lbl = Text("feedback", font=LABEL_FONT, font_size=20)
        feedback_lbl.set_color(GREEN)
        feedback_lbl.move_to(
            (feedback_pts[1] + feedback_pts[2]) / 2 + DOWN * 0.25
        )

        objs = Group(
            z_dot, z_lbl, g_box, g_lbl,
            d_box, d_lbl, real_dot, real_lbl,
            fake_icon, fake_lbl,
            arr_z_g, arr_g_fake, arr_fake_d, arr_real_d,
            feedback_path, feedback_lbl,
        )

        self.play(
            FadeIn(z_dot), Write(z_lbl),
            FadeIn(real_dot), Write(real_lbl),
            run_time=0.7,
        )
        self.play(ShowCreation(g_box), Write(g_lbl), run_time=0.6)
        self.play(ShowCreation(d_box), Write(d_lbl), run_time=0.6)
        self.play(
            GrowArrow(arr_z_g),
            GrowArrow(arr_g_fake),
            GrowArrow(arr_fake_d),
            GrowArrow(arr_real_d),
            FadeIn(fake_icon), FadeIn(fake_lbl),
            run_time=0.9,
        )
        self.play(ShowCreation(feedback_path), Write(feedback_lbl),
                  run_time=0.9)
        self.wait(1.5)

        # ── 2. Strip labels progressively until only the loop remains ─────
        self.play(
            FadeOut(Group(z_dot, z_lbl, real_dot, real_lbl,
                          fake_icon, fake_lbl, feedback_lbl)),
            run_time=0.8,
        )
        self.wait(0.5)
        self.play(
            FadeOut(VGroup(g_lbl, d_lbl)),
            g_box.animate.set_stroke(GREY, 1.5).set_fill(BLACK, 0),
            d_box.animate.set_stroke(GREY, 1.5).set_fill(BLACK, 0),
            run_time=0.9,
        )
        self.wait(0.5)
        self.play(
            FadeOut(VGroup(arr_z_g, arr_real_d, arr_g_fake, arr_fake_d)),
            run_time=0.6,
        )
        # Only the loop arrow remains
        self.wait(1.0)

        # ── 3. Closing thought ────────────────────────────────────────────
        closing = Text(
            "Nobody ever tells the generator\nwhat a good image looks like.",
            font=LABEL_FONT, font_size=30,
        )
        closing.set_color(WHITE)
        closing.to_edge(UP, buff=0.5)

        closing2 = Text(
            "It learns because another network\n"
            "is constantly trying to prove\n"
            "that its images are fake.",
            font=LABEL_FONT, font_size=30,
        )
        closing2.set_color(YELLOW)
        closing2.next_to(closing, DOWN, buff=0.5)

        self.play(Write(closing), run_time=1.8)
        self.play(Write(closing2), run_time=2.2)
        self.wait(3.0)

        self.play(
            FadeOut(VGroup(g_box, d_box, feedback_path, closing, closing2)),
            run_time=1.2,
        )
        self.wait(0.5)
