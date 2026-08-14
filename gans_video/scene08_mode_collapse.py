from manimlib import *
from pathlib import Path
import numpy as np

# ── Beat 8: Mode collapse (10:00–11:15) ───────────────────────────────────

LABEL_FONT = "CMU Serif"
BG         = BLACK
ASSETS     = Path(__file__).parent / "assets" / "faces"


def photo_thumb(filename: str, color=WHITE, height: float = 0.65) -> Group:
    """A face photo with a thin colored border, standing in for one example."""
    img = ImageMobject(str(ASSETS / filename))
    img.set_height(height)
    border = Rectangle(width=img.get_width(), height=img.get_height())
    border.set_stroke(color, width=2)
    border.set_fill(opacity=0)
    border.move_to(img)
    return Group(img, border)


def gaussian_pdf(x, mu, sigma):
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))


class ModeCollapse(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── 1. Introduce the problem ───────────────────────────────────────
        title = Text("A subtle problem: the generator can cheat",
                     font=LABEL_FONT, font_size=32)
        title.set_color(WHITE)
        title.to_edge(UP, buff=0.5)

        self.play(Write(title), run_time=1.0)
        self.wait(0.5)

        # ── 2. Show diverse output first, then collapse ────────────────────
        diverse_lbl = Text(
            "Good training: diverse faces",
            font=LABEL_FONT, font_size=26,
        ).set_color(GREEN)
        diverse_lbl.move_to(UP * 1.5)
        self.play(Write(diverse_lbl), run_time=0.7)

        real_files = [f"real_{i:02d}.png" for i in range(8)]
        diverse_photos = Group()
        for i, fname in enumerate(real_files):
            thumb = photo_thumb(fname, BLUE_C)
            thumb.move_to(LEFT * 3.5 + RIGHT * i * 1.0 + ORIGIN)
            diverse_photos.add(thumb)

        self.play(
            LaggedStart(*[FadeIn(d, shift=UP * 0.15) for d in diverse_photos],
                        lag_ratio=0.08),
            run_time=1.2,
        )
        self.wait(0.8)

        # ── 3. Collapse to the same fake face everywhere ────────────────────
        collapse_lbl = Text(
            "Mode collapse: generator always outputs the same face",
            font=LABEL_FONT, font_size=26,
        ).set_color(ORANGE)
        collapse_lbl.move_to(UP * 1.5)

        collapsed_photos = Group()
        for i in range(8):
            thumb = photo_thumb("fake_blend.png", ORANGE)
            thumb.move_to(LEFT * 3.5 + RIGHT * i * 1.0 + ORIGIN)
            collapsed_photos.add(thumb)

        self.play(
            FadeOut(diverse_lbl),
            Write(collapse_lbl),
            FadeOut(diverse_photos),
            FadeIn(collapsed_photos),
            run_time=1.5,
        )
        self.wait(1.0)

        # ── 4. Latent-space cloud collapses ───────────────────────────────
        self.play(
            FadeOut(Group(diverse_photos, collapsed_photos, collapse_lbl)),
            run_time=0.6,
        )

        lat_box = Square(side_length=4.0)
        lat_box.set_stroke(GREY_D, 1)
        lat_box.move_to(ORIGIN + DOWN * 0.2)
        lat_lbl = Text("Latent space  z", font=LABEL_FONT, font_size=20)
        lat_lbl.set_color(GREY).next_to(lat_box, DOWN, buff=0.2)
        self.play(ShowCreation(lat_box), Write(lat_lbl), run_time=0.6)

        # Spread cloud
        rng = np.random.default_rng(3)
        spread_dots = VGroup(*[
            Dot(np.array([rng.uniform(-1.8, 1.8),
                          -0.2 + rng.uniform(-1.8, 1.8), 0]),
                radius=0.07, color=ORANGE)
            for _ in range(60)
        ])
        self.play(
            LaggedStart(*[GrowFromCenter(d) for d in spread_dots],
                        lag_ratio=0.02),
            run_time=1.0,
        )
        self.wait(0.5)

        spread_lbl = Text("Before: spread across latent space",
                          font=LABEL_FONT, font_size=22).set_color(GREY_A)
        spread_lbl.to_edge(DOWN, buff=0.5)
        self.play(Write(spread_lbl), run_time=0.5)
        self.wait(0.5)

        # Collapse cloud to a tiny cluster
        collapsed_dots = VGroup(*[
            Dot(np.array([rng.uniform(-0.15, 0.15),
                          -0.2 + rng.uniform(-0.15, 0.15), 0]),
                radius=0.07, color=ORANGE)
            for _ in range(60)
        ])
        collapse_lbl2 = Text("After: collapsed to one mode",
                             font=LABEL_FONT, font_size=22).set_color(ORANGE)
        collapse_lbl2.to_edge(DOWN, buff=0.5)

        self.play(
            *[Transform(spread_dots[i], collapsed_dots[i])
              for i in range(60)],
            FadeOut(spread_lbl),
            Write(collapse_lbl2),
            run_time=1.8,
        )
        self.wait(1.0)

        # ── 5. Why it's bad ───────────────────────────────────────────────
        why_bad = Text(
            "Discriminator is fooled → positive feedback\n"
            "→ generator never improves diversity.",
            font=LABEL_FONT, font_size=24,
        )
        why_bad.set_color(YELLOW)
        why_bad.to_edge(DOWN, buff=0.3)
        self.play(FadeOut(collapse_lbl2), Write(why_bad), run_time=1.2)
        self.wait(2.0)

        self.play(
            FadeOut(VGroup(title, lat_box, lat_lbl,
                           spread_dots, why_bad)),
            run_time=0.8,
        )
        self.wait(0.2)
