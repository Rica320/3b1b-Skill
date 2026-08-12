from manimlib import *
import numpy as np

# ── Beat 3: Introducing the Discriminator (3:30–4:15) ─────────────────────

LABEL_FONT = "CMU Serif"
BG         = BLACK


class DiscriminatorIntro(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── 1. Problem statement ───────────────────────────────────────────
        prob1 = Text("The generator has a problem:", font=LABEL_FONT, font_size=32)
        prob1.set_color(WHITE)
        prob1.move_to(UP * 2.5)

        prob2 = Text("Nobody is telling it whether its image is good.",
                     font=LABEL_FONT, font_size=30)
        prob2.set_color(YELLOW)
        prob2.next_to(prob1, DOWN, buff=0.4)

        self.play(Write(prob1), run_time=1.0)
        self.play(Write(prob2), run_time=1.2)
        self.wait(1.2)

        self.play(FadeOut(VGroup(prob1, prob2)), run_time=0.6)

        # ── 2. A new character appears: the Discriminator ──────────────────
        d_box = Rectangle(width=2.8, height=1.2)
        d_box.set_stroke(TEAL_C, width=2.5)
        d_box.set_fill(TEAL_C, opacity=0.10)
        d_box.move_to(ORIGIN)

        d_lbl = Text("DISCRIMINATOR", font=LABEL_FONT, font_size=24)
        d_lbl.set_color(TEAL_C)
        d_lbl.move_to(d_box)

        question = Text("Real or Fake?", font=LABEL_FONT, font_size=28)
        question.set_color(YELLOW)
        question.next_to(d_box, UP, buff=0.5)

        self.play(ShowCreation(d_box), Write(d_lbl), run_time=0.9)
        self.play(Write(question), run_time=0.7)
        self.wait(0.7)

        # ── 3. Full diagram ────────────────────────────────────────────────
        # real path
        real_box = Square(side_length=0.8)
        real_box.set_stroke(BLUE_C, 2)
        real_box.set_fill(BLUE_C, opacity=0.15)
        real_box.move_to(LEFT * 5.5 + UP * 1.4)
        real_lbl = Text("real", font=LABEL_FONT, font_size=20)
        real_lbl.set_color(BLUE_C).move_to(real_box)

        # fake path
        z_dot = Dot(radius=0.1, color=ORANGE)
        z_dot.move_to(LEFT * 5.5 + DOWN * 1.4)
        z_lbl = Tex(r"\mathbf{z}", font_size=30).set_color(ORANGE)
        z_lbl.next_to(z_dot, LEFT, buff=0.1)

        g_box = Rectangle(width=1.4, height=0.7)
        g_box.set_stroke(YELLOW, 2)
        g_box.set_fill(YELLOW, opacity=0.08)
        g_box.move_to(LEFT * 3.2 + DOWN * 1.4)
        g_lbl = Text("G", font=LABEL_FONT, font_size=22).set_color(YELLOW)
        g_lbl.move_to(g_box)

        fake_box = Square(side_length=0.8)
        fake_box.set_stroke(ORANGE, 2)
        fake_box.set_fill(ORANGE, opacity=0.15)
        fake_box.move_to(LEFT * 1.2 + DOWN * 1.4)
        fake_lbl = Text("fake", font=LABEL_FONT, font_size=20)
        fake_lbl.set_color(ORANGE).move_to(fake_box)

        # merge arrows
        d_box.move_to(RIGHT * 1.8)
        d_lbl.move_to(d_box)
        question.next_to(d_box, UP, buff=0.4)

        arr_real = Arrow(real_box.get_right(), d_box.get_left() + UP * 0.3,
                         buff=0.08, color=GREY)
        arr_z   = Arrow(z_dot.get_right(), g_box.get_left(), buff=0.08, color=GREY)
        arr_gf  = Arrow(g_box.get_right(), fake_box.get_left(), buff=0.08, color=GREY)
        arr_fake = Arrow(fake_box.get_right(), d_box.get_left() + DOWN * 0.3,
                         buff=0.08, color=GREY)

        # output arrow
        output = Text("real / fake", font=LABEL_FONT, font_size=22)
        output.set_color(TEAL_C)
        output.move_to(RIGHT * 4.5)
        arr_out = Arrow(d_box.get_right(), output.get_left(), buff=0.1, color=GREY)

        self.play(
            FadeIn(real_box), Write(real_lbl),
            FadeIn(z_dot), Write(z_lbl),
            run_time=0.7,
        )
        self.play(
            ShowCreation(arr_z), ShowCreation(g_box), Write(g_lbl),
            run_time=0.7,
        )
        self.play(ShowCreation(arr_gf), FadeIn(fake_box), Write(fake_lbl),
                  run_time=0.6)
        self.play(
            ShowCreation(arr_real),
            ShowCreation(arr_fake),
            run_time=0.6,
        )
        self.play(ShowCreation(arr_out), Write(output), run_time=0.6)
        self.wait(2.0)

        self.play(
            FadeOut(VGroup(d_box, d_lbl, question,
                           real_box, real_lbl,
                           z_dot, z_lbl,
                           g_box, g_lbl,
                           fake_box, fake_lbl,
                           arr_real, arr_z, arr_gf, arr_fake,
                           arr_out, output)),
            run_time=0.8,
        )
        self.wait(0.2)
