from manimlib import *
from pathlib import Path
import numpy as np

# ── Beat 9: What happens when training succeeds? (11:15–12:30) ────────────
# Latent-space interpolation z(t) = (1-t)z1 + t*z2
# Shows the learned map: random latent → image manifold.

LABEL_FONT = "CMU Serif"
BG         = BLACK
ASSETS     = Path(__file__).parent / "assets" / "faces"


class LatentInterpolation(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── 1. Two latent points ──────────────────────────────────────────
        lat_box = Square(side_length=3.2)
        lat_box.set_stroke(GREY_D, 1.2)
        lat_box.move_to(LEFT * 3.5 + DOWN * 0.2)
        lat_title = Text("Latent space", font=LABEL_FONT, font_size=22)
        lat_title.set_color(GREY).next_to(lat_box, UP, buff=0.2)

        self.play(ShowCreation(lat_box), Write(lat_title), run_time=0.7)

        z1_pos = np.array([-4.3, 0.7, 0])
        z2_pos = np.array([-2.7, -0.9, 0])

        z1_dot = Dot(z1_pos, radius=0.12, color=ORANGE)
        z2_dot = Dot(z2_pos, radius=0.12, color=YELLOW)
        z1_lbl = Tex(r"\mathbf{z}_1", font_size=28).set_color(ORANGE)
        z1_lbl.next_to(z1_dot, UL, buff=0.08)
        z2_lbl = Tex(r"\mathbf{z}_2", font_size=28).set_color(YELLOW)
        z2_lbl.next_to(z2_dot, DR, buff=0.08)

        self.play(GrowFromCenter(z1_dot), Write(z1_lbl),
                  GrowFromCenter(z2_dot), Write(z2_lbl), run_time=0.8)
        self.wait(0.5)

        # ── 2. Interpolation formula ──────────────────────────────────────
        interp_eq = Tex(
            r"\mathbf{z}(t) = (1-t)\,\mathbf{z}_1 + t\,\mathbf{z}_2",
            font_size=36,
        )
        interp_eq.set_color(WHITE)
        interp_eq.to_edge(UP, buff=0.5)
        self.play(Write(interp_eq), run_time=1.0)
        self.wait(0.5)

        # ── 3. Interpolated dot sweeps the path ───────────────────────────
        path_line = DashedLine(z1_pos, z2_pos, color=GREY_B,
                               stroke_width=1.5, dash_length=0.15)
        self.play(ShowCreation(path_line), run_time=0.6)

        interp_dot = Dot(z1_pos, radius=0.1, color=WHITE)
        self.play(GrowFromCenter(interp_dot), run_time=0.3)

        # Right side: image output column
        img_title = Text("Generated image", font=LABEL_FONT, font_size=22)
        img_title.set_color(GREY)
        img_title.move_to(RIGHT * 3.5 + UP * 2.5)
        self.play(Write(img_title), run_time=0.5)

        img_box = Square(side_length=2.0)
        img_box.set_stroke(WHITE, 1.5)
        img_box.move_to(RIGHT * 3.5 + DOWN * 0.2)

        steps = 8  # 9 precomputed frames: interp_00.png .. interp_08.png,
                   # a real pixel-level alpha blend between two faces at
                   # each t, not a simulated color/label change.

        for step in range(steps + 1):
            t = step / steps
            z_t = (1 - t) * z1_pos + t * z2_pos

            # border lerp: orange → yellow, tracks progress along the walk
            col = interpolate_color(ORANGE, YELLOW, t)
            new_img = ImageMobject(str(ASSETS / f"interp_{step:02d}.png"))
            new_img.set_height(1.8)
            new_img.move_to(RIGHT * 3.5 + DOWN * 0.2)
            new_border = Rectangle(width=new_img.get_width(), height=new_img.get_height())
            new_border.set_stroke(col, 2)
            new_border.move_to(new_img)

            t_lbl = Tex(f"t = {t:.2f}", font_size=28).set_color(GREY_A)
            t_lbl.next_to(img_box, DOWN, buff=0.25)

            if step == 0:
                self.play(ShowCreation(img_box), run_time=0.4)
                cur_img = Group(new_img, new_border)
                cur_t   = t_lbl
                self.play(FadeIn(cur_img), Write(cur_t), run_time=0.5)
            else:
                prev_img = cur_img
                cur_img = Group(new_img, new_border)
                self.play(
                    interp_dot.animate.move_to(z_t),
                    FadeOut(prev_img),
                    FadeIn(cur_img),
                    Transform(cur_t, t_lbl),
                    run_time=0.55,
                )
            self.wait(0.1)

        self.wait(0.8)

        # ── 4. Pull camera back — full pipeline ───────────────────────────
        self.play(
            FadeOut(VGroup(interp_dot, path_line, z1_dot, z2_dot,
                           z1_lbl, z2_lbl, interp_eq, cur_t)),
            run_time=0.5,
        )

        pipe_lbl = Text(
            "random z  →  latent space  →  Generator  →  image manifold",
            font=LABEL_FONT, font_size=24,
        )
        pipe_lbl.set_color(YELLOW)
        pipe_lbl.to_edge(DOWN, buff=0.5)
        self.play(Write(pipe_lbl), run_time=1.2)
        self.wait(2.0)

        self.play(
            FadeOut(Group(lat_box, lat_title, img_box, cur_img,
                          img_title, pipe_lbl)),
            run_time=0.8,
        )
        self.wait(0.2)
