from manimlib import *
from pathlib import Path
import numpy as np


# ── Beat 0: Cold open — "Can you tell which is real?" (0:00–0:45) ──────────
# Real face photos zoom out into a point-cloud. No voiceover — timing set
# for ~45 s of narration cadence.

REAL_COLOR   = BLUE_C
FAKE_COLOR   = ORANGE
BG           = BLACK
LABEL_FONT   = "CMU Serif"
ASSETS       = Path(__file__).parent / "assets" / "faces"


def photo_thumb(filename: str, color=WHITE, height: float = 0.9) -> Group:
    """A face photo with a thin colored border, standing in for one example."""
    img = ImageMobject(str(ASSETS / filename))
    img.set_height(height)
    border = Rectangle(width=img.get_width(), height=img.get_height())
    border.set_stroke(color, width=2)
    border.set_fill(opacity=0)
    border.move_to(img)
    return Group(img, border)


class ColdOpen(Scene):
    def construct(self):
        self.camera.background_color = BG

        # ── 1. Title appears ──────────────────────────────────────────────
        title = Text("GANs, Explained Visually", font=LABEL_FONT, font_size=44)
        title.set_color(WHITE)
        title.to_edge(UP)
        self.play(Write(title), run_time=1.5)
        self.wait(0.5)

        # ── 2. Six real face photos spread across screen ───────────────────
        real_files = [f"real_{i:02d}.png" for i in range(6)]
        photos = Group(*[photo_thumb(f, REAL_COLOR) for f in real_files])
        photos.arrange(RIGHT, buff=0.45)
        photos.move_to(ORIGIN)

        self.play(
            LaggedStart(*[FadeIn(p, shift=DOWN * 0.2) for p in photos],
                        lag_ratio=0.15),
            run_time=1.8
        )
        self.wait(0.6)

        # ── 3. Label: "Real examples" ─────────────────────────────────────
        real_lbl = Text("Real examples", font=LABEL_FONT, font_size=28)
        real_lbl.set_color(REAL_COLOR)
        real_lbl.next_to(photos, DOWN, buff=0.4)
        self.play(FadeIn(real_lbl), run_time=0.6)
        self.wait(0.8)

        # ── 4. Look closer at one of them ───────────────────────────────────
        self.play(FlashAround(photos[0], color=REAL_COLOR), run_time=1.0)
        self.wait(0.4)

        # ── 5. A "generated" photo slides in — looks plausible ─────────────
        fake_photo = photo_thumb("fake_blend.png", FAKE_COLOR)
        fake_photo.next_to(photos, RIGHT, buff=0.6)
        fake_lbl = Text("Generated?", font=LABEL_FONT, font_size=22)
        fake_lbl.set_color(FAKE_COLOR)
        fake_lbl.next_to(fake_photo, DOWN, buff=0.25)

        self.play(FadeIn(fake_photo, shift=LEFT * 0.3), run_time=0.7)
        self.play(Write(fake_lbl), run_time=0.5)
        self.wait(1.0)

        # ── 6. Question card ───────────────────────────────────────────────
        q1 = Text("If you had a million examples,", font=LABEL_FONT, font_size=30)
        q2 = Text("could a machine learn to make new ones?",
                  font=LABEL_FONT, font_size=30)
        q_group = VGroup(q1, q2).arrange(DOWN, buff=0.2)
        q_group.set_color(YELLOW)
        q_group.to_edge(DOWN, buff=0.7)

        self.play(Write(q1), run_time=1.2)
        self.play(Write(q2), run_time=1.4)
        self.wait(1.0)

        # ── 7. Zoom out: photos become dots in a point-cloud ──────────────
        dots = VGroup(*[
            Dot(p.get_center(), radius=0.07, color=REAL_COLOR)
            for p in photos
        ] + [Dot(fake_photo.get_center(), radius=0.07, color=FAKE_COLOR)])

        # Extra random cloud of points suggesting a large distribution
        rng = np.random.default_rng(42)
        cloud_pts = VGroup(*[
            Dot(
                np.array([rng.uniform(-5, 5), rng.uniform(-2.5, 2.5), 0]),
                radius=0.04,
                color=BLUE_A,
            )
            for _ in range(120)
        ])

        self.play(
            FadeOut(photos), FadeOut(fake_photo),
            FadeIn(dots),
            FadeOut(fake_lbl),
            FadeOut(real_lbl),
            run_time=1.5,
        )
        self.play(
            LaggedStart(*[FadeIn(p) for p in cloud_pts], lag_ratio=0.02),
            run_time=1.5,
        )
        self.wait(0.5)

        # narration beat: "the interesting question is learning the distribution"
        dist_lbl = Text(
            "The goal: learn the distribution,\nnot memorise examples.",
            font=LABEL_FONT, font_size=28,
        )
        dist_lbl.set_color(WHITE)
        dist_lbl.to_edge(DOWN, buff=0.5)

        self.play(FadeOut(q_group), run_time=0.4)
        self.play(Write(dist_lbl), run_time=1.4)
        self.wait(2.0)

        self.play(FadeOut(VGroup(title, dist_lbl, cloud_pts, dots)),
                  run_time=1.0)
        self.wait(0.3)
