from manimlib import *
import numpy as np

# ── Beat 5: Now the game begins (5:30–7:00) ────────────────────────────────

LABEL_FONT = "CMU Serif"
BG         = BLACK


class TheGame(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── 1. Two characters on screen ────────────────────────────────────
        g_box = Rectangle(width=2.2, height=1.1)
        g_box.set_stroke(YELLOW, 2.5)
        g_box.set_fill(YELLOW, opacity=0.10)
        g_box.move_to(LEFT * 3.5 + UP * 0.5)
        g_lbl = Text("GENERATOR", font=LABEL_FONT, font_size=24).set_color(YELLOW)
        g_lbl.move_to(g_box)

        d_box = Rectangle(width=2.6, height=1.1)
        d_box.set_stroke(TEAL_C, 2.5)
        d_box.set_fill(TEAL_C, opacity=0.10)
        d_box.move_to(RIGHT * 3.5 + UP * 0.5)
        d_lbl = Text("DISCRIMINATOR", font=LABEL_FONT, font_size=22).set_color(TEAL_C)
        d_lbl.move_to(d_box)

        g_speech = Text('"I\'ll make fake images."', font=LABEL_FONT, font_size=22)
        g_speech.set_color(YELLOW)
        g_speech.next_to(g_box, DOWN, buff=0.3)

        d_speech = Text('"I\'ll catch them."', font=LABEL_FONT, font_size=22)
        d_speech.set_color(TEAL_C)
        d_speech.next_to(d_box, DOWN, buff=0.3)

        self.play(FadeIn(g_box), Write(g_lbl), run_time=0.7)
        self.play(FadeIn(d_box), Write(d_lbl), run_time=0.7)
        self.play(Write(g_speech), run_time=0.7)
        self.play(Write(d_speech), run_time=0.7)
        self.wait(1.0)

        # ── 2. Training loop diagram ───────────────────────────────────────
        self.play(
            FadeOut(VGroup(g_speech, d_speech)),
            g_box.animate.move_to(LEFT * 4.5 + ORIGIN),
            g_lbl.animate.move_to(LEFT * 4.5 + ORIGIN),
            d_box.animate.move_to(RIGHT * 4.5 + ORIGIN),
            d_lbl.animate.move_to(RIGHT * 4.5 + ORIGIN),
            run_time=0.8,
        )
        # re-center labels after move
        self.play(
            g_lbl.animate.move_to(g_box.get_center()),
            d_lbl.animate.move_to(d_box.get_center()),
            run_time=0.1,
        )

        steps = [
            "generate", "fake images", "discriminator", "feedback", "generator"
        ]
        step_colors = [YELLOW, ORANGE, TEAL_C, WHITE, YELLOW]
        step_mobs = VGroup()
        for i, (s, c) in enumerate(zip(steps, step_colors)):
            t = Text(s, font=LABEL_FONT, font_size=24).set_color(c)
            t.move_to(DOWN * (i * 0.65 - 1.2))
            step_mobs.add(t)

        arrows_loop = VGroup()
        for i in range(len(step_mobs) - 1):
            arr = Arrow(
                step_mobs[i].get_bottom(),
                step_mobs[i + 1].get_top(),
                buff=0.05, color=GREY, stroke_width=2,
            )
            arrows_loop.add(arr)

        loop_label = Text("↺", font=LABEL_FONT, font_size=40)
        loop_label.set_color(GREY)
        loop_label.next_to(step_mobs[-1], DOWN, buff=0.1)

        self.play(
            LaggedStart(*[FadeIn(s, shift=RIGHT * 0.2) for s in step_mobs],
                        lag_ratio=0.15),
            run_time=1.5,
        )
        self.play(
            LaggedStart(*[ShowCreation(a) for a in arrows_loop], lag_ratio=0.15),
            FadeIn(loop_label),
            run_time=1.0,
        )
        self.wait(1.2)

        self.play(
            FadeOut(VGroup(step_mobs, arrows_loop, loop_label,
                           g_box, g_lbl, d_box, d_lbl)),
            run_time=0.6,
        )

        # ── 3. Minimax objective — build term by term ──────────────────────
        min_max = Tex(
            r"\min_G \max_D",
            font_size=48,
        )
        min_max.set_color(WHITE)
        min_max.move_to(UP * 2.8)
        self.play(Write(min_max), run_time=1.0)
        self.wait(0.5)

        # Annotation: D maximises
        d_ann = Text("D tries to distinguish", font=LABEL_FONT, font_size=22)
        d_ann.set_color(TEAL_C)
        d_ann.next_to(min_max, DOWN, buff=0.5)
        self.play(Write(d_ann), run_time=0.7)
        self.wait(0.5)

        g_ann = Text("G tries to fool D", font=LABEL_FONT, font_size=22)
        g_ann.set_color(YELLOW)
        g_ann.next_to(d_ann, DOWN, buff=0.3)
        self.play(Write(g_ann), run_time=0.7)
        self.wait(0.8)

        # ── 4. Full objective — each term highlighted in turn ──────────────
        self.play(FadeOut(VGroup(d_ann, g_ann)), run_time=0.4)

        full_obj = Tex(
            r"\min_G \max_D \,"
            r"\mathbb{E}_{x \sim p_{\text{data}}}[\log D(x)]"
            r" + "
            r"\mathbb{E}_{z \sim p_z}[\log(1 - D(G(z)))]",
            font_size=32,
        )
        full_obj.move_to(ORIGIN + UP * 1.0)
        self.play(Write(full_obj), run_time=2.5)
        self.wait(0.6)

        # Highlight term 1: real data
        term1_box = SurroundingRectangle(
            full_obj[0][len(r"\min_G \max_D \,"):len(r"\min_G \max_D \,") + 30],
            color=BLUE_C, buff=0.06,
        )
        t1_lbl = Text(
            "D assigns high probability\nto real images",
            font=LABEL_FONT, font_size=20,
        ).set_color(BLUE_C).to_edge(DOWN, buff=0.8)

        self.play(ShowCreation(term1_box), Write(t1_lbl), run_time=0.9)
        self.wait(1.0)

        # Highlight term 2: fake data
        term2_box = SurroundingRectangle(
            full_obj,   # approximate — whole eq as fallback
            color=ORANGE, buff=0.06,
        )
        t2_lbl = Text(
            "G minimises D's confidence\nin its fake images",
            font=LABEL_FONT, font_size=20,
        ).set_color(ORANGE).to_edge(DOWN, buff=0.8)

        self.play(
            ReplacementTransform(term1_box, term2_box),
            FadeOut(t1_lbl),
            Write(t2_lbl),
            run_time=0.9,
        )
        self.wait(1.5)

        self.play(
            FadeOut(VGroup(min_max, full_obj, term2_box, t2_lbl)),
            run_time=0.8,
        )
        self.wait(0.2)
