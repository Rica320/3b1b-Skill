from manimlib import *
import numpy as np

# ── Beat 1: What does "generating" mean? (0:45–2:00) ──────────────────────
# 1-D probability curve → 2-D landscape → latent vector z ~ N(0,I)

LABEL_FONT = "CMU Serif"
BG         = BLACK


class GeneratingMeaning(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── 1. 1-D number line with a Gaussian curve ──────────────────────
        axes_1d = Axes(
            x_range=(-4, 4, 1),
            y_range=(0, 0.45, 0.1),
            height=3.5,
            width=9,
        )
        axes_1d.set_color(GREY)
        axes_1d.move_to(ORIGIN + UP * 0.3)

        x_lbl = Text("possible images  →", font=LABEL_FONT, font_size=22)
        x_lbl.set_color(GREY)
        x_lbl.next_to(axes_1d, DOWN, buff=0.2).to_edge(RIGHT, buff=0.3)

        curve = axes_1d.get_graph(
            lambda x: 0.4 * np.exp(-0.5 * (x - 1) ** 2)
                    + 0.25 * np.exp(-0.5 * ((x + 1.5) / 0.7) ** 2),
            color=BLUE_C,
        )
        curve_lbl = Text("probability", font=LABEL_FONT, font_size=22)
        curve_lbl.set_color(BLUE_C)
        curve_lbl.to_corner(UL, buff=0.5)

        self.play(Write(axes_1d), run_time=1.0)
        self.play(Write(x_lbl), run_time=0.6)
        self.play(ShowCreation(curve), run_time=1.5)
        self.play(Write(curve_lbl), run_time=0.6)
        self.wait(0.8)

        # dots near the high-probability region
        rng = np.random.default_rng(7)
        sample_xs = np.concatenate([
            rng.normal(1.0, 0.35, 8),
            rng.normal(-1.5, 0.45, 5),
        ])
        sample_dots = VGroup(*[
            Dot(axes_1d.c2p(x, 0), radius=0.08, color=YELLOW)
            for x in sample_xs
        ])
        self.play(
            LaggedStart(*[GrowFromCenter(d) for d in sample_dots],
                        lag_ratio=0.08),
            run_time=1.2,
        )
        self.wait(0.6)

        title_beat = Text(
            "Common examples cluster near the high-probability regions.",
            font=LABEL_FONT, font_size=26,
        )
        title_beat.set_color(WHITE)
        title_beat.to_edge(DOWN, buff=0.5)
        self.play(Write(title_beat), run_time=1.2)
        self.wait(1.0)

        # ── 2. Fade → 2-D landscape ───────────────────────────────────────
        self.play(
            FadeOut(VGroup(axes_1d, curve, curve_lbl, x_lbl,
                           sample_dots, title_beat)),
            run_time=0.8,
        )

        axes_2d = Axes(
            x_range=(-4, 4, 1),
            y_range=(-3, 3, 1),
            height=5.5,
            width=8,
        )
        axes_2d.set_color(GREY_D)
        axes_2d.move_to(ORIGIN)

        lbl_2d = Text("Image space  (each point = one possible image)",
                      font=LABEL_FONT, font_size=22)
        lbl_2d.set_color(GREY)
        lbl_2d.to_edge(UP, buff=0.3)

        self.play(Write(axes_2d), Write(lbl_2d), run_time=1.0)

        # draw 2-D "density blobs"
        blob_centers = [(1.2, 0.8), (-1.5, -1.0), (0.2, -1.8)]
        blob_colors  = [BLUE_C, TEAL_C, BLUE_B]
        blobs = VGroup()
        for (cx, cy), bc in zip(blob_centers, blob_colors):
            blob = Ellipse(width=1.6, height=1.1)
            blob.set_fill(bc, opacity=0.25)
            blob.set_stroke(bc, width=1.5)
            blob.move_to(axes_2d.c2p(cx, cy))
            blobs.add(blob)

        self.play(
            LaggedStart(*[ShowCreation(b) for b in blobs], lag_ratio=0.25),
            run_time=1.5,
        )

        blob_lbl = Text("High-density\nregions", font=LABEL_FONT, font_size=22)
        blob_lbl.set_color(BLUE_C)
        blob_lbl.next_to(blobs[0], RIGHT, buff=0.3)
        self.play(Write(blob_lbl), run_time=0.6)
        self.wait(0.6)

        goal_lbl = Text(
            "A generative model learns\nwhere the interesting regions are.",
            font=LABEL_FONT, font_size=26,
        )
        goal_lbl.set_color(YELLOW)
        goal_lbl.to_edge(DOWN, buff=0.4)
        self.play(Write(goal_lbl), run_time=1.2)
        self.wait(1.0)

        # ── 3. Introduce z ~ N(0, I): latent vector ───────────────────────
        self.play(
            FadeOut(VGroup(axes_2d, blobs, blob_lbl, goal_lbl, lbl_2d)),
            run_time=0.7,
        )

        z_eq = Tex(r"\mathbf{z} \sim \mathcal{N}(\mathbf{0},\, \mathbf{I})")
        z_eq.scale(1.6)
        z_eq.set_color(WHITE)
        z_eq.move_to(ORIGIN + UP * 1.2)

        z_lbl = Text("A random seed — a point in latent space.",
                     font=LABEL_FONT, font_size=28)
        z_lbl.set_color(GREY_A)
        z_lbl.next_to(z_eq, DOWN, buff=0.45)

        self.play(Write(z_eq), run_time=1.2)
        self.play(FadeIn(z_lbl), run_time=0.7)
        self.wait(0.8)

        # random dots appearing in a small latent-space square
        lat_box = Square(side_length=3.0)
        lat_box.set_stroke(GREY_D, width=1)
        lat_box.move_to(ORIGIN + DOWN * 1.2)
        lat_lbl = Text("Latent space  z", font=LABEL_FONT, font_size=20)
        lat_lbl.set_color(GREY)
        lat_lbl.next_to(lat_box, DOWN, buff=0.2)

        self.play(ShowCreation(lat_box), FadeIn(lat_lbl), run_time=0.8)

        rng2 = np.random.default_rng(99)
        lat_dots = VGroup(*[
            Dot(
                np.array([rng2.uniform(-1.3, 1.3),
                          -1.2 + rng2.uniform(-1.3, 1.3), 0]),
                radius=0.07, color=ORANGE,
            )
            for _ in range(30)
        ])
        self.play(
            LaggedStart(*[GrowFromCenter(d) for d in lat_dots], lag_ratio=0.04),
            run_time=1.4,
        )
        self.wait(0.6)

        key_line = Text(
            '"Give the network a random seed.\nAsk it to turn that seed into an image."',
            font=LABEL_FONT, font_size=26,
        )
        key_line.set_color(YELLOW)
        key_line.to_edge(DOWN, buff=0.35)
        self.play(Write(key_line), run_time=1.6)
        self.wait(2.0)

        self.play(
            FadeOut(VGroup(z_eq, z_lbl, lat_box, lat_lbl, lat_dots, key_line)),
            run_time=0.8,
        )
        self.wait(0.2)
