from manimlib import *
import numpy as np

# ── Beat 2: The Generator — turning randomness into structure (2:00–3:30) ──

LABEL_FONT = "CMU Serif"
BG         = BLACK


def nn_layer(n_nodes: int, color=WHITE, height=2.8) -> VGroup:
    """Vertical column of circles representing a neural-network layer."""
    spacing = height / max(n_nodes - 1, 1)
    nodes = VGroup(*[
        Circle(radius=0.18)
        .set_stroke(color, width=2)
        .set_fill(color, opacity=0.15)
        .move_to(np.array([0, i * spacing - height / 2, 0]))
        for i in range(n_nodes)
    ])
    return nodes


def connect_layers(layer_a: VGroup, layer_b: VGroup, color=GREY_D) -> VGroup:
    """Draw edges between every pair of nodes in adjacent layers."""
    edges = VGroup()
    for na in layer_a:
        for nb in layer_b:
            edges.add(
                Line(na.get_right(), nb.get_left(),
                     stroke_color=color, stroke_width=0.8)
            )
    return edges


class GeneratorScene(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── 1. Diagram: z → [G] → x_fake ─────────────────────────────────
        z_dot = Dot(radius=0.15, color=ORANGE)
        z_dot.move_to(LEFT * 5.5)
        z_lbl = Tex(r"\mathbf{z}", font_size=36).set_color(ORANGE)
        z_lbl.next_to(z_dot, LEFT, buff=0.15)

        arr1 = Arrow(LEFT * 5.2, LEFT * 3.8, buff=0, color=GREY)

        g_box = Rectangle(width=1.6, height=1.0)
        g_box.set_stroke(YELLOW, width=2)
        g_box.set_fill(YELLOW, opacity=0.08)
        g_box.move_to(LEFT * 3.0)
        g_lbl = Text("G", font=LABEL_FONT, font_size=32).set_color(YELLOW)
        g_lbl.move_to(g_box)

        arr2 = Arrow(LEFT * 2.2, LEFT * 0.8, buff=0, color=GREY)

        img_box = Square(side_length=1.0)
        img_box.set_stroke(ORANGE, width=2)
        img_box.set_fill(ORANGE, opacity=0.12)
        img_box.move_to(ORIGIN + RIGHT * 0.1)
        img_lbl = Text("x̂", font=LABEL_FONT, font_size=28).set_color(ORANGE)
        img_lbl.move_to(img_box)

        self.play(FadeIn(z_dot), Write(z_lbl), run_time=0.6)
        self.play(ShowCreation(arr1), run_time=0.5)
        self.play(ShowCreation(g_box), Write(g_lbl), run_time=0.7)
        self.play(ShowCreation(arr2), run_time=0.5)
        self.play(ShowCreation(img_box), Write(img_lbl), run_time=0.6)

        caption = Text("random noise  →  [ GENERATOR G ]  →  image",
                       font=LABEL_FONT, font_size=24)
        caption.set_color(GREY_A)
        caption.to_edge(DOWN, buff=0.5)
        self.play(Write(caption), run_time=1.0)
        self.wait(1.0)

        # ── 2. Zoom into G: layered network transforming a point cloud ─────
        self.play(
            FadeOut(VGroup(z_dot, z_lbl, arr1, g_box, g_lbl,
                           arr2, img_box, img_lbl, caption)),
            run_time=0.6,
        )

        # Build a 4-layer "abstract" network
        layer_sizes  = [4, 6, 5, 3]
        layer_colors = [ORANGE, YELLOW, TEAL_C, BLUE_C]
        layer_xs     = [-4.5, -1.8, 1.0, 3.8]

        layers = []
        for n, c, x in zip(layer_sizes, layer_colors, layer_xs):
            lay = nn_layer(n, color=c)
            lay.move_to(np.array([x, 0, 0]))
            layers.append(lay)

        edge_groups = [
            connect_layers(layers[i], layers[i + 1])
            for i in range(len(layers) - 1)
        ]

        # Layer labels
        stage_lbls = [
            Text("noise\n(z)", font=LABEL_FONT, font_size=20).set_color(ORANGE),
            Text("abstract\nfeatures", font=LABEL_FONT, font_size=20).set_color(YELLOW),
            Text("shapes", font=LABEL_FONT, font_size=20).set_color(TEAL_C),
            Text("image\n(x̂)", font=LABEL_FONT, font_size=20).set_color(BLUE_C),
        ]
        for lbl, lay in zip(stage_lbls, layers):
            lbl.next_to(lay, DOWN, buff=0.4)

        for eg in edge_groups:
            self.play(LaggedStart(*[ShowCreation(e) for e in eg],
                                  lag_ratio=0.01), run_time=0.6)
        for lay, lbl in zip(layers, stage_lbls):
            self.play(
                LaggedStart(*[GrowFromCenter(n) for n in lay], lag_ratio=0.08),
                FadeIn(lbl),
                run_time=0.7,
            )
        self.wait(1.0)

        # ── 3. Equation G(z) = x_fake ─────────────────────────────────────
        eq = Tex(r"G(\mathbf{z}) = \hat{\mathbf{x}}")
        eq.scale(1.5)
        eq.set_color_by_tex(r"\mathbf{z}", ORANGE)
        eq.set_color_by_tex(r"\hat{\mathbf{x}}", BLUE_C)
        eq.to_edge(UP, buff=0.4)

        self.play(Write(eq), run_time=1.0)
        self.wait(0.6)

        # ── 4. Two nearby z-points → smoothly changing output ─────────────
        # Show latent space mini-panel on left
        lat_axes = Axes(
            x_range=(-2, 2, 1),
            y_range=(-2, 2, 1),
            height=2.8, width=2.8,
        )
        lat_axes.set_color(GREY_D)
        lat_axes.to_corner(DL, buff=0.6)
        lat_title = Text("Latent space", font=LABEL_FONT, font_size=18)
        lat_title.set_color(GREY)
        lat_title.next_to(lat_axes, UP, buff=0.15)

        self.play(Write(lat_axes), FadeIn(lat_title), run_time=0.8)

        z1 = Dot(lat_axes.c2p(-0.6, 0.4), radius=0.1, color=ORANGE)
        z2 = Dot(lat_axes.c2p(0.5, -0.3), radius=0.1, color=YELLOW)
        conn = DashedLine(z1.get_center(), z2.get_center(), color=GREY_B)

        self.play(GrowFromCenter(z1), GrowFromCenter(z2),
                  ShowCreation(conn), run_time=0.8)

        # Two output "image" squares on right
        img1 = Square(side_length=1.0).set_stroke(ORANGE, 2)
        img1.set_fill(ORANGE, opacity=0.12)
        img1_lbl = Tex(r"\hat{x}_1", font_size=28).set_color(ORANGE)
        img1_lbl.move_to(img1)

        img2 = Square(side_length=1.0).set_stroke(YELLOW, 2)
        img2.set_fill(YELLOW, opacity=0.12)
        img2_lbl = Tex(r"\hat{x}_2", font_size=28).set_color(YELLOW)
        img2_lbl.move_to(img2)

        img1.to_corner(DR, buff=0.8).shift(UP * 1.0)
        img2.next_to(img1, RIGHT, buff=0.5)
        img1_lbl.move_to(img1)
        img2_lbl.move_to(img2)

        nearby_lbl = Text(
            "Nearby points in latent space\n→ similar generated images.",
            font=LABEL_FONT, font_size=22,
        )
        nearby_lbl.set_color(GREY_A)
        nearby_lbl.to_edge(DOWN, buff=0.4)

        self.play(
            FadeIn(img1), Write(img1_lbl),
            FadeIn(img2), Write(img2_lbl),
            Write(nearby_lbl),
            run_time=1.2,
        )
        self.wait(2.0)

        self.play(
            FadeOut(VGroup(*layers, *edge_groups, *stage_lbls,
                           eq, lat_axes, lat_title,
                           z1, z2, conn,
                           img1, img1_lbl, img2, img2_lbl,
                           nearby_lbl)),
            run_time=0.8,
        )
        self.wait(0.2)
