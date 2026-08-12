from manimlib import *
import numpy as np

# ── Beat 6: Two distributions chasing each other (7:00–8:30) ──────────────
# This is the conceptual centrepiece. Real (blue) vs generated (orange)
# density curves on shared axes; the fake curve migrates toward the real one
# until D(x)=½ everywhere.

LABEL_FONT = "CMU Serif"
BG         = BLACK
REAL_C     = BLUE_C
FAKE_C     = ORANGE


def gaussian_pdf(x, mu, sigma):
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))


class DistributionsChase(Scene):
    def construct(self):
        self.camera.background_color = BG

        axes = Axes(
            x_range=(-5, 5, 1),
            y_range=(0, 0.55, 0.1),
            height=4.5, width=10.0,
        )
        axes.set_color(GREY_D)
        axes.move_to(ORIGIN + DOWN * 0.3)

        ax_title = Text("Probability density over image space",
                        font=LABEL_FONT, font_size=26)
        ax_title.set_color(WHITE)
        ax_title.to_edge(UP, buff=0.4)

        self.play(Write(axes), Write(ax_title), run_time=1.0)

        # ── Real distribution — stays fixed ──────────────────────────────
        real_curve = axes.get_graph(
            lambda x: gaussian_pdf(x, mu=1.5, sigma=0.8),
            color=REAL_C,
        )
        real_area = axes.get_area(
            real_curve, x_range=(-5, 5),
            color=REAL_C, opacity=0.15,
        )
        real_lbl = Text("real data  p_data", font=LABEL_FONT, font_size=22)
        real_lbl.set_color(REAL_C)
        real_lbl.to_corner(UL, buff=0.6).shift(DOWN * 1.0)

        self.play(ShowCreation(real_curve), FadeIn(real_area),
                  Write(real_lbl), run_time=1.2)
        self.wait(0.5)

        # ── Initial fake distribution — far from real ─────────────────────
        fake_mu_start = -2.5
        fake_curve = axes.get_graph(
            lambda x: gaussian_pdf(x, mu=fake_mu_start, sigma=1.0),
            color=FAKE_C,
        )
        fake_area = axes.get_area(
            fake_curve, x_range=(-5, 5),
            color=FAKE_C, opacity=0.15,
        )
        fake_lbl = Text("generated  p_G", font=LABEL_FONT, font_size=22)
        fake_lbl.set_color(FAKE_C)
        fake_lbl.to_corner(UR, buff=0.6).shift(DOWN * 1.0)

        self.play(ShowCreation(fake_curve), FadeIn(fake_area),
                  Write(fake_lbl), run_time=1.0)
        self.wait(0.6)

        far_lbl = Text("At first: very different distributions.",
                       font=LABEL_FONT, font_size=26)
        far_lbl.set_color(YELLOW)
        far_lbl.to_edge(DOWN, buff=0.4)
        self.play(Write(far_lbl), run_time=0.8)
        self.wait(1.0)
        self.play(FadeOut(far_lbl), run_time=0.4)

        # ── Discriminator boundary ─────────────────────────────────────────
        boundary = DashedLine(
            axes.c2p(-0.5, 0), axes.c2p(-0.5, 0.55),
            color=WHITE, dash_length=0.12, stroke_width=1.5,
        )
        d_lbl = Text("D finds the gap", font=LABEL_FONT, font_size=20)
        d_lbl.set_color(WHITE).next_to(axes.c2p(-0.5, 0.55), RIGHT, buff=0.15)

        self.play(ShowCreation(boundary), FadeIn(d_lbl), run_time=0.7)
        self.wait(0.8)
        self.play(FadeOut(VGroup(boundary, d_lbl)), run_time=0.4)

        # ── Fake curve migrates toward real — 4 interpolation steps ───────
        target_mus   = [-1.0, 0.3, 1.1, 1.5]
        target_sigmas = [0.95, 0.88, 0.82, 0.80]

        for step, (mu, sigma) in enumerate(zip(target_mus, target_sigmas)):
            new_fake = axes.get_graph(
                lambda x, m=mu, s=sigma: gaussian_pdf(x, m, s),
                color=FAKE_C,
            )
            new_area = axes.get_area(
                new_fake, x_range=(-5, 5),
                color=FAKE_C, opacity=0.15,
            )
            step_lbl = Text(
                f"Training step {step + 1}",
                font=LABEL_FONT, font_size=22,
            ).set_color(GREY_A).to_edge(DOWN, buff=0.4)

            self.play(
                Transform(fake_curve, new_fake),
                Transform(fake_area, new_area),
                FadeIn(step_lbl),
                run_time=1.0,
            )
            self.wait(0.4)
            self.play(FadeOut(step_lbl), run_time=0.3)

        self.wait(0.4)

        # ── Aha moment: curves overlap, D(x) = 1/2 ────────────────────────
        aha_lbl = Text("Curves converge: real = generated",
                       font=LABEL_FONT, font_size=28)
        aha_lbl.set_color(YELLOW)
        aha_lbl.to_edge(DOWN, buff=0.6)

        eq_half = Tex(r"D(x) = \tfrac{1}{2}", font_size=40)
        eq_half.set_color(TEAL_C)
        eq_half.next_to(aha_lbl, UP, buff=0.4)

        self.play(Write(aha_lbl), run_time=0.8)
        self.play(Write(eq_half), run_time=0.8)
        self.wait(2.0)

        self.play(
            FadeOut(VGroup(axes, ax_title,
                           real_curve, real_area, real_lbl,
                           fake_curve, fake_area, fake_lbl,
                           aha_lbl, eq_half)),
            run_time=0.8,
        )
        self.wait(0.2)
