from manimlib import *
import numpy as np

# ── Beat 7: Why gradients are the secret weapon (8:30–10:00) ──────────────

LABEL_FONT = "CMU Serif"
BG         = BLACK


class GradientScene(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── 1. Loss landscape ─────────────────────────────────────────────
        title = Text("Loss landscape of the Generator",
                     font=LABEL_FONT, font_size=34)
        title.set_color(WHITE)
        title.to_edge(UP, buff=0.4)

        axes = Axes(
            x_range=(-3.5, 3.5, 1),
            y_range=(0, 3.2, 0.5),
            height=4.8, width=9.0,
        )
        axes.set_color(GREY_D)
        axes.move_to(DOWN * 0.2)

        # Bowl-shaped loss
        loss_curve = axes.get_graph(
            lambda x: 0.4 * x ** 2 + 0.3 * np.sin(2 * x) + 1.5,
            color=BLUE_C,
        )
        loss_lbl = Text("Generator loss  L", font=LABEL_FONT, font_size=22)
        loss_lbl.set_color(BLUE_C)
        loss_lbl.to_corner(UL, buff=0.6).shift(DOWN * 1.5)

        self.play(Write(title), run_time=0.8)
        self.play(Write(axes), run_time=0.8)
        self.play(ShowCreation(loss_curve), Write(loss_lbl), run_time=1.2)
        self.wait(0.5)

        # Glowing dot = current generator parameters
        param_x = ValueTracker(2.5)

        def dot_pos():
            x = param_x.get_value()
            return axes.c2p(x, 0.4 * x ** 2 + 0.3 * np.sin(2 * x) + 1.5)

        param_dot = Dot(dot_pos(), radius=0.14, color=YELLOW)
        param_dot.add_updater(lambda d: d.move_to(dot_pos()))

        param_label = Text("Generator\nparameters  θ",
                           font=LABEL_FONT, font_size=20)
        param_label.set_color(YELLOW)
        param_label.add_updater(
            lambda l: l.next_to(param_dot, UR, buff=0.1)
        )

        self.play(GrowFromCenter(param_dot), FadeIn(param_label), run_time=0.6)
        self.wait(0.5)

        # ── 2. Gradient arrow (direction of descent) ───────────────────────
        def grad_arrow():
            x = param_x.get_value()
            grad = 0.8 * x + 0.6 * np.cos(2 * x)   # derivative
            # arrow pointing downhill
            dx = -0.6 * np.sign(grad)
            start = axes.c2p(x, 0.4 * x ** 2 + 0.3 * np.sin(2 * x) + 1.5)
            end   = axes.c2p(x + dx,
                             0.4 * (x + dx) ** 2
                             + 0.3 * np.sin(2 * (x + dx)) + 1.5)
            return start, end

        s, e = grad_arrow()
        g_arrow = Arrow(s, e, buff=0, color=GREEN, stroke_width=3)

        g_lbl = Text("gradient  ∇L\n(direction to improve)",
                     font=LABEL_FONT, font_size=20)
        g_lbl.set_color(GREEN)
        g_lbl.to_corner(DR, buff=0.5)

        self.play(GrowArrow(g_arrow), Write(g_lbl), run_time=0.8)
        self.wait(0.6)

        # ── 3. Parameter update — dot slides downhill ─────────────────────
        update_eq = Tex(
            r"\theta \leftarrow \theta - \eta \nabla_\theta L",
            font_size=36,
        )
        update_eq.set_color(WHITE)
        update_eq.to_edge(DOWN, buff=0.4)
        self.play(Write(update_eq), run_time=0.9)
        self.wait(0.4)

        # Slide downhill in 3 steps
        for new_x in [1.5, 0.5, -0.15]:
            s, e = grad_arrow()
            new_arrow = Arrow(s, e, buff=0, color=GREEN, stroke_width=3)
            self.play(
                param_x.animate.set_value(new_x),
                Transform(g_arrow, new_arrow),
                run_time=1.0,
            )
            self.wait(0.3)

        self.wait(0.5)

        # ── 4. Backprop chain diagram ──────────────────────────────────────
        self.play(
            FadeOut(VGroup(axes, loss_curve, loss_lbl,
                           param_dot, param_label,
                           g_arrow, g_lbl, update_eq, title)),
            run_time=0.7,
        )

        chain = [
            ("Discriminator output", TEAL_C),
            ("Discriminator loss",   TEAL_C),
            ("Gradient",             GREEN),
            ("Generator parameters", YELLOW),
            ("Better image",         ORANGE),
        ]
        chain_mobs = VGroup()
        for i, (text, color) in enumerate(chain):
            t = Text(text, font=LABEL_FONT, font_size=26).set_color(color)
            t.move_to(UP * (2.0 - i * 1.0))
            chain_mobs.add(t)

        chain_arrows = VGroup()
        for i in range(len(chain_mobs) - 1):
            a = Arrow(
                chain_mobs[i].get_bottom(),
                chain_mobs[i + 1].get_top(),
                buff=0.05, color=GREY, stroke_width=2,
            )
            chain_arrows.add(a)

        chain_title = Text("Gradient flows back through D to train G",
                           font=LABEL_FONT, font_size=28)
        chain_title.set_color(WHITE)
        chain_title.to_edge(UP, buff=0.5)

        self.play(Write(chain_title), run_time=0.7)
        self.play(
            LaggedStart(*[FadeIn(t, shift=DOWN * 0.15) for t in chain_mobs],
                        lag_ratio=0.2),
            run_time=1.5,
        )
        self.play(
            LaggedStart(*[GrowArrow(a) for a in chain_arrows],
                        lag_ratio=0.2),
            run_time=1.2,
        )
        self.wait(2.0)

        self.play(
            FadeOut(VGroup(chain_title, chain_mobs, chain_arrows)),
            run_time=0.7,
        )
        self.wait(0.2)
