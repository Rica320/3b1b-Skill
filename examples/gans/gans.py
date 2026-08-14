"""
"What do you write down as the score, when there is no right answer?"

A six-minute explainer on generative adversarial networks, built with the
3b1b-math-animation skill in this repository. See SCRIPT.md for the narration
this render is paced against, and README.md for how to run it.

Deliberately a single Scene with one method per section, rather than eleven
separate Scenes. An earlier build rendered each beat as its own file and
concatenated them, which is why 10 of its 11 scene boundaries passed through
a blank black frame (docs/DEFECTS.md, §B1). Objects here persist across
section boundaries and are transformed, never torn down and rebuilt.

    Render:  bash ../../skills/3b1b-math-animation/scripts/render.sh gans.py GANs
    Verify:  python ../../skills/3b1b-math-animation/scripts/verify_render.py \
                 videos/GANs.mp4 --meta render_meta.json
    Audit:   GANS_AUDIT=1 manimgl gans.py GANs      # reports text overlaps
"""

from manimlib import *
from pathlib import Path
import numpy as np
import sys
import os

# ManimGL's module loader does not put the scene file's own directory on
# sys.path, so neither a sibling module nor the skill's shared helpers are
# importable without this. Standalone projects should copy manim_helpers.py
# next to the scene file instead; the examples in this repository import the
# canonical copy so the two cannot drift apart.
_HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(_HERE),
                str(_HERE.parents[1] / "skills" / "3b1b-math-animation"
                    / "scripts")]

from manim_helpers import (
    dot, arrow, label, Caption, Dimmer,
    stagger, hold, push_in, pull_back, dump_meta,
    equation, box_around, assert_in_frame, assert_no_overlap,
    audit_text_overlaps, swap_raster, FONT,
)
from landscape import Landscape

ASSETS = _HERE / "assets" / "faces"
CACHE_DIR = _HERE / "_field_cache"
META_PATH = _HERE / "render_meta.json"

# ── Colour mapping. Fixed for the entire video. See SCRIPT.md. ───────────
C_REAL = BLUE_C      # real data: real images, the real cloud, p_data
C_FAKE = ORANGE      # generated: the seed z, G's outputs, the fake cloud, p_G
C_DISC = TEAL_C      # the discriminator: its box, its surface, its height
C_GRAD = GREEN       # gradient / direction of improvement
C_HOT = YELLOW       # transient: whatever is load-bearing right now
C_NEUT = GREY_B      # neutral scaffolding

# ── Plane geometry (image space), fixed from §2 onward ───────────────────
PX0, PY0 = 0.0, 1.15
PW, PH = 10.2, 3.3
XR = (-4.0, 4.0)
YR = (-1.6, 1.6)


def c2p(x, y):
    return np.array([PX0 + (x / XR[1]) * (PW / 2),
                     PY0 + (y / YR[1]) * (PH / 2), 0.0])


# ── The two distributions. real is bimodal so §6 has two peaks to talk about
REAL_SPEC = [(-0.75, 0.20, 0.62, 0.52, 1.0),
             (1.55, -0.15, 0.62, 0.52, 1.0)]
FAKE_START = [(-2.95, -0.80, 0.62, 0.44, 1.0)]
FAKE_MID = [(-1.30, -0.30, 0.70, 0.50, 1.0)]
FAKE_NEAR = [(-0.10, 0.05, 0.85, 0.55, 1.0)]
FAKE_DONE = REAL_SPEC
FAKE_COLLAPSE = [(1.55, -0.15, 0.16, 0.14, 1.0)]
FAKE_COLLAPSE2 = [(-0.75, 0.20, 0.16, 0.14, 1.0)]

N_REAL, N_FAKE = 64, 46


def sample(spec, n, seed):
    rng = np.random.default_rng(seed)
    ws = np.array([s[4] for s in spec], dtype=float)
    ws /= ws.sum()
    which = rng.choice(len(spec), size=n, p=ws)
    out = []
    for k in which:
        cx, cy, sx, sy, _ = spec[k]
        x = np.clip(rng.normal(cx, sx), XR[0] + .05, XR[1] - .05)
        y = np.clip(rng.normal(cy, sy), YR[0] + .05, YR[1] - .05)
        out.append((x, y))
    return out


def photo(fname, color, height=0.95):
    img = ImageMobject(str(ASSETS / fname))
    img.set_height(height)
    b = Rectangle(width=img.get_width(), height=img.get_height())
    b.set_stroke(color, width=2.5, opacity=1.0)
    b.set_fill(opacity=0)
    b.move_to(img)
    return Group(img, b)


class GANs(Scene):

    def construct(self):
        self.camera.background_color = BLACK
        self.cap = Caption(self)
        for name, fn in [
            ("s0 question", self.s0_question),
            ("s1 blur", self.s1_blur),
            ("s2 space", self.s2_space),
            ("s3 landscape", self.s3_landscape),
            ("s4 uphill", self.s4_uphill),
            ("s5 chase", self.s5_chase),
            ("s6 collapse", self.s6_collapse),
            ("s7 payoff", self.s7_payoff),
        ]:
            t0 = self.time
            fn()
            print(f"[TIMING] {name:14s} start={t0:7.1f}s  "
                  f"dur={self.time - t0:6.1f}s")
        dump_meta(self, str(META_PATH))

    # Set GANS_AUDIT=1 to check, at every hold, that no two visible text or
    # equation mobjects share screen space. Findings print as [OVERLAP].
    def wait(self, *args, **kwargs):
        result = super().wait(*args, **kwargs)
        if os.environ.get("GANS_AUDIT"):
            audit_text_overlaps(self)
        return result

    # ── helpers bound to this scene's persistent objects ─────────────────
    def _front(self):
        """Keep the data points and scaffolding above the field raster."""
        for grp in (self.real_dots, self.fake_dots, self.seed_pt):
            if grp is not None:
                self.bring_to_front(grp)

    def swap_field(self, real, fake, tag, run_time=1.5, extra=()):
        """Cross-dissolve the height field to a new state.

        The field is a continuous scalar surface, so a dissolve reads as the
        surface re-forming rather than as a cut. The *profile* curve below it
        is genuinely Transformed at the same time (passed in via `extra`),
        and that is what carries object identity through the change.
        """
        new = self.land.field_image(real, fake, tag, CACHE_DIR)
        self.field = swap_raster(
            self, self.field, new, run_time=run_time, extra=extra,
            behind=[m for m in (self.real_dots, self.fake_dots, self.seed_pt)
                    if m is not None],
        )

    # ── §0  The question ─────────────────────────────────────────────────
    def s0_question(self):
        face = photo("interp_04.png", C_NEUT, height=5.2)
        face.move_to(ORIGIN)
        self.play(FadeIn(face), run_time=1.6)
        hold(self, 2.0)

        # the face becomes one node of the training loop
        self.cap.show(
            "This face was never photographed.",
            "This face was never photographed. There's no such person; "
            "a network invented it.",
            size=32, color=WHITE, run_time=1.4)

        node_y = -0.2
        guess = photo("interp_04.png", C_NEUT, height=1.05)
        guess.move_to(np.array([-3.6, node_y, 0]))
        g_lbl = label("guess", 24, C_NEUT)
        g_lbl.next_to(guess, DOWN, buff=0.25)

        self.play(
            face.animate.set_height(1.05).move_to(np.array([-3.6, node_y, 0])),
            run_time=1.3,
        )
        self.remove(face)
        self.add(guess)
        self.play(Write(g_lbl), run_time=0.5)

        score_box = Rectangle(width=2.3, height=1.05)
        score_box.set_stroke(C_NEUT, width=2.0, opacity=1.0)
        score_box.set_fill(BLACK, opacity=1.0)
        score_box.move_to(np.array([0.0, node_y, 0]))
        s_lbl = label("score", 26, C_NEUT)
        s_lbl.move_to(score_box)

        adj_box = Rectangle(width=2.3, height=1.05)
        adj_box.set_stroke(C_NEUT, width=2.0, opacity=1.0)
        adj_box.set_fill(BLACK, opacity=1.0)
        adj_box.move_to(np.array([3.6, node_y, 0]))
        a_lbl = label("adjust", 26, C_NEUT)
        a_lbl.move_to(adj_box)

        a1 = arrow(guess.get_right() + RIGHT * 0.08,
                   score_box.get_left() + LEFT * 0.08, C_NEUT, 3.0)
        a2 = arrow(score_box.get_right() + RIGHT * 0.08,
                   adj_box.get_left() + LEFT * 0.08, C_NEUT, 3.0)

        loop = VMobject()
        loop.set_points_as_corners([
            adj_box.get_bottom() + DOWN * 0.02,
            adj_box.get_bottom() + DOWN * 0.95,
            guess.get_bottom() + DOWN * 0.95,
            guess.get_bottom() + DOWN * 0.62,
        ])
        loop.set_stroke(C_NEUT, width=3.0, opacity=1.0)
        loop_tip = arrow(guess.get_bottom() + DOWN * 0.80,
                         guess.get_bottom() + DOWN * 0.55, C_NEUT, 3.0)

        assert_in_frame(guess=guess, score=score_box, adjust=adj_box,
                        loop=loop, g_lbl=g_lbl)

        self.play(
            stagger([
                GrowArrow(a1),
                AnimationGroup(ShowCreation(score_box), Write(s_lbl)),
                GrowArrow(a2),
                AnimationGroup(ShowCreation(adj_box), Write(a_lbl)),
            ], lag_ratio=0.45),
            run_time=2.0,
        )
        self.play(ShowCreation(loop), GrowArrow(loop_tip), run_time=0.9)
        hold(self, 1.0)

        self.cap.show(
            "Training is: guess, get graded, adjust.",
            "But to train that network, something had to score its guesses. "
            "That's what training is — guess, get graded, adjust.",
            size=32)

        # the score node is the missing piece
        self.play(
            score_box.animate.set_stroke(C_HOT, width=3.0),
            s_lbl.animate.set_color(C_HOT),
            run_time=0.7,
        )
        hold(self, 1.0)

        qmark = Tex("?").scale(1.9).set_color(C_HOT)
        qmark.move_to(score_box)
        self.play(ReplacementTransform(s_lbl, qmark), run_time=0.8)
        hold(self, 1.0)

        question = Text(
            "What do you write down as the score,\n"
            "when there is no right answer?",
            font=FONT, font_size=34,
        ).set_color(C_HOT)
        question.move_to(np.array([0, -2.55, 0]))
        assert_in_frame(question=question)
        self.play(Write(question), run_time=2.2)
        # the driving question lands at ~0:18 and gets a long hold
        self.wait(4.4)

        self.q_text = question
        self.loop_group = Group(guess, g_lbl, score_box, adj_box, a_lbl,
                                a1, a2, loop, loop_tip)
        self.qmark = qmark

    # ── §1  Why the obvious answer fails ─────────────────────────────────
    def s1_blur(self):
        # the question mark is what survives into §1 - grow it to centre as
        # the loop leaves, so the frame is never empty across the boundary
        self.play(
            FadeOut(self.loop_group, shift=UP * 0.3),
            FadeOut(self.q_text, shift=DOWN * 0.3),
            self.qmark.animate.scale(1.6).move_to(np.array([0, 0.15, 0])),
            run_time=1.0,
        )
        self.cap.show(
            "The obvious score: distance to a real face.",
            "The obvious thing to try: take a real face, measure how far "
            "your guess is from it, pixel by pixel, and punish the distance.",
            size=30)

        # the ? becomes the generator's output square
        out = Square(side_length=1.9)
        out.set_stroke(C_FAKE, width=2.5, opacity=1.0)
        out.set_fill(C_FAKE, opacity=0.10)
        out.move_to(np.array([-2.8, 0.15, 0]))
        out_lbl = label("output", 22, C_FAKE)
        out_lbl.next_to(out, DOWN, buff=0.22)

        self.play(ReplacementTransform(self.qmark, out), run_time=1.0)
        self.play(FadeIn(out_lbl, shift=UP * 0.15), run_time=0.5)

        real = photo("real_00.png", C_REAL, height=1.9)
        real.move_to(np.array([2.8, 0.15, 0]))
        real_lbl = label("a real face", 22, C_REAL)
        real_lbl.next_to(real, DOWN, buff=0.22)

        self.play(FadeIn(real, shift=LEFT * 0.3), run_time=0.7)
        self.play(FadeIn(real_lbl, shift=UP * 0.15), run_time=0.5)

        dline = DashedLine(out.get_right(), real.get_left(),
                           dash_length=0.13)
        dline.set_stroke(C_NEUT, width=2.0, opacity=1.0)
        d_lbl = label("distance", 22, C_NEUT)
        d_lbl.next_to(dline, UP, buff=0.18)
        self.play(ShowCreation(dline), FadeIn(d_lbl), run_time=0.8)
        hold(self, 1.5)

        # ...but it is graded against every face at once
        self.cap.show(
            "But it is graded against every face at once.",
            "Watch what that gives you. If a network is graded on its "
            "average distance to every face in the dataset, then the output "
            "that scores best is the one closest to all of them at once.",
            size=30)
        self.play(FadeOut(VGroup(d_lbl), shift=UP * 0.2),
                  FadeOut(real_lbl, shift=DOWN * 0.2), run_time=0.5)

        grid = Group()
        for i in range(8):
            p = photo(f"real_{i:02d}.png", C_REAL, height=0.92)
            grid.add(p)
        grid.arrange_in_grid(2, 4, buff=0.28)
        grid.move_to(np.array([2.9, 0.15, 0]))

        spokes = VGroup()
        for p in grid:
            ln = Line(out.get_right(), p.get_left())
            ln.set_stroke(C_NEUT, width=1.0, opacity=0.55)
            spokes.add(ln)

        assert_in_frame(grid=grid, out=out)
        self.play(
            FadeOut(dline, run_time=0.4),
            ReplacementTransform(real, grid[0], run_time=1.0),
        )
        self.play(
            stagger([FadeIn(p, shift=LEFT * 0.2) for p in grid[1:]],
                    lag_ratio=0.10),
            run_time=1.4,
        )
        self.play(stagger([ShowCreation(s) for s in spokes], lag_ratio=0.06),
                  run_time=1.1)
        hold(self, 1.5)

        # the lowest-loss answer is their average
        self.cap.show(
            "The lowest-loss answer is their average.",
            "Which is their average. And the average of ten thousand "
            "faces is fog.",
            size=30)
        blur = ImageMobject(str(ASSETS / "mean_face.png"))
        blur.set_height(1.9)
        blur.move_to(out)
        blur_border = Square(side_length=1.9)
        blur_border.set_stroke(C_FAKE, width=2.5, opacity=1.0)
        blur_border.move_to(out)

        self.play(
            *[p.animate.scale(0.12).move_to(out.get_center()).set_opacity(0.0)
              for p in grid],
            *[s.animate.set_opacity(0.0) for s in spokes],
            FadeIn(blur),
            out.animate.set_fill(C_FAKE, opacity=0.0),
            run_time=1.8,
        )
        self.remove(grid, spokes, out)
        self.add(blur, blur_border)
        hold(self, 1.0)

        # centre it and let it land
        self.play(
            Group(blur, blur_border).animate.move_to(np.array([0, 0.15, 0]))
                                    .set_height(2.6),
            FadeOut(out_lbl, shift=DOWN * 0.2),
            run_time=1.1,
        )
        fog = label("the lowest-loss face", 26, C_FAKE)
        fog.next_to(blur_border, DOWN, buff=0.3)
        self.play(FadeIn(fog, shift=UP * 0.15), run_time=0.6)
        hold(self, 2.0)

        self.cap.show(
            'A face is not one answer. It is a space of them.',
            "So the obvious score doesn't merely work badly. It points the "
            "wrong way — it rewards the blur. Every pixel-wise score has "
            "this problem. It wants a single answer, and a face isn't a "
            "single answer. It's a whole space of them.",
            size=30, color=C_HOT)

        self.blur = blur
        self.blur_border = blur_border
        self.fog = fog

    # ── §2  Image space, and two clouds ──────────────────────────────────
    def s2_space(self):
        self.play(FadeOut(self.fog, shift=DOWN * 0.2), run_time=0.5)
        self.cap.show(
            "So take that literally: every image is one point.",
            "A whole space of them. Let's take that literally. Flatten every "
            "image down to a single point. Pictures that look alike sit near "
            "each other; pictures that look nothing alike sit far apart.",
            size=30)

        # the plane
        frame_rect = Rectangle(width=PW, height=PH)
        frame_rect.set_stroke(GREY_D, width=1.6, opacity=1.0)
        frame_rect.set_fill(opacity=0)
        frame_rect.move_to(np.array([PX0, PY0, 0]))
        plane_lbl = label("image space   (every point is a picture)", 21, GREY)
        plane_lbl.next_to(frame_rect, UP, buff=0.22)

        self.play(ShowCreation(frame_rect), FadeIn(plane_lbl), run_time=1.1)

        # the blur shrinks and becomes a single point - the hinge of the video
        seed_pt = dot(c2p(-2.95, -0.80), C_FAKE, radius=0.075)
        self.play(
            Group(self.blur, self.blur_border).animate
                .set_height(0.30).move_to(c2p(-2.95, -0.80)).set_opacity(0.0),
            run_time=1.5,
        )
        self.remove(self.blur, self.blur_border)
        self.add(seed_pt)
        self.play(FlashAround(seed_pt, color=C_FAKE), run_time=0.9)
        hold(self, 1.5)

        # the real cloud
        self.cap.show(
            "The real faces are bunched in one small region.",
            "This whole plane is every image that could exist — and almost "
            "all of it is noise. The real faces aren't scattered across it. "
            "They're bunched, in one small bright region. That region is "
            "the thing we actually want.",
            size=30)
        real_xy = sample(REAL_SPEC, N_REAL, seed=11)
        real_dots = VGroup(*[dot(c2p(x, y), C_REAL, 0.062)
                             for x, y in real_xy])
        self.play(stagger([GrowFromCenter(d) for d in real_dots],
                          lag_ratio=0.022),
                  run_time=1.9)
        hold(self, 1.0)

        # prove the correspondence: three points bloom back into faces
        picks = [3, 27, 51]
        thumbs = Group()
        for k, idx in enumerate(picks):
            x, y = real_xy[idx]
            th = photo(f"real_{k:02d}.png", C_REAL, height=0.85)
            th.move_to(c2p(x, y) + np.array([0, 0.62, 0]))
            thumbs.add(th)
        self.play(stagger([FadeIn(t, scale=0.4) for t in thumbs],
                          lag_ratio=0.18),
                  run_time=1.2)
        hold(self, 1.5)
        self.play(stagger([FadeOut(t, scale=0.25) for t in thumbs],
                          lag_ratio=0.12),
                  run_time=0.9)
        self.wait(3.0)          # narration budget: see SCRIPT.md §2

        # the generator drops points
        self.cap.show(
            "A generator turns a random seed into a point.",
            "Now — a generator is just a machine that takes a random seed "
            "and drops it somewhere on this plane. Untrained, it drops "
            "points wherever. Over here. Far from the good region.",
            size=30)
        g_box = Rectangle(width=1.5, height=0.8)
        g_box.set_stroke(C_FAKE, width=2.2, opacity=1.0)
        g_box.set_fill(BLACK, opacity=1.0)
        g_box.move_to(np.array([-4.45, -2.45, 0]))
        g_lbl = Tex("G").scale(0.95).set_color(C_FAKE)
        g_lbl.move_to(g_box)
        z_dot = dot(np.array([-6.05, -2.45, 0]), C_NEUT, 0.09)
        z_lbl = Tex(r"\mathbf{z}").scale(0.8).set_color(C_NEUT)
        z_lbl.next_to(z_dot, LEFT, buff=0.18)
        z_arr = arrow(z_dot.get_right() + RIGHT * 0.08,
                      g_box.get_left() + LEFT * 0.06, C_NEUT, 3.0)

        assert_in_frame(g_box=g_box, z_lbl=z_lbl)
        self.play(FadeIn(z_dot), Write(z_lbl), run_time=0.6)
        self.play(GrowArrow(z_arr), ShowCreation(g_box), Write(g_lbl),
                  run_time=0.8)

        fake_xy = sample(FAKE_START, N_FAKE, seed=5)
        fake_dots = VGroup(*[dot(c2p(x, y), C_FAKE, 0.062)
                             for x, y in fake_xy])

        # first three travel visibly from G, the rest stagger in
        for i in range(3):
            trav = dot(g_box.get_right(), C_FAKE, 0.062)
            self.add(trav)
            self.play(trav.animate.move_to(fake_dots[i].get_center()),
                      run_time=0.55)
            self.remove(trav)
            self.add(fake_dots[i])
        self.play(stagger([GrowFromCenter(d) for d in fake_dots[3:]],
                          lag_ratio=0.028),
                  run_time=1.6)
        self.play(FadeOut(VGroup(z_dot, z_lbl, z_arr, g_box, g_lbl),
                          shift=DOWN * 0.2),
                  run_time=0.7)
        hold(self, 1.5)

        self.cap.show(
            "The goal: move the orange cloud onto the blue one.",
            "So the goal stops being 'make a good image', and becomes "
            "something concrete: move the orange cloud onto the blue one. "
            "Which is real progress.",
            size=30, color=C_HOT)
        self.wait(3.2)          # let the restated goal sit before the turn

        # ...but which way is "toward blue"?
        self.cap.show(
            "But standing on an orange point — which way?",
            "But it hands us a new problem. Standing on an orange point — "
            "which direction is toward blue? Nothing about the plane tells "
            "you. The blue region isn't labelled. There's no arrow.",
            size=30)
        anchor_i = 7
        anchor = fake_dots[anchor_i]
        push_in(self, anchor.get_center(), height=3.0, run_time=1.4)

        rays = VGroup()
        for k in range(8):
            th = k * TAU / 8
            v = np.array([np.cos(th), np.sin(th), 0])
            rays.add(arrow(anchor.get_center() + v * 0.16,
                           anchor.get_center() + v * 0.62, C_NEUT, 2.2))
        self.play(stagger([GrowArrow(a) for a in rays], lag_ratio=0.07),
                  run_time=1.2)
        hold(self, 1.5)
        self.play(FadeOut(rays), run_time=0.8)
        hold(self, 1.0)

        self.frame_rect = frame_rect
        self.plane_lbl = plane_lbl
        self.real_dots = real_dots
        self.fake_dots = fake_dots
        self.fake_xy = fake_xy
        self.anchor = anchor
        self.seed_pt = seed_pt

    # ── §3  The critic paints the landscape ──────────────────────────────
    def s3_landscape(self):
        pull_back(self, run_time=1.4)
        self.cap.show(
            "Train a second network to tell us.",
            "Here's the move. We can't write down which way is toward blue. "
            "But we can train a second network to tell us — because that "
            "job, unlike generating, is an ordinary supervised problem.",
            size=30)

        # D is an ordinary supervised problem: it has labels
        d_box = Rectangle(width=3.0, height=0.9)
        d_box.set_stroke(C_DISC, width=2.5, opacity=1.0)
        d_box.set_fill(BLACK, opacity=1.0)
        d_box.move_to(np.array([0.0, -2.45, 0]))
        d_lbl = label("DISCRIMINATOR", 22, C_DISC)
        d_lbl.move_to(d_box)
        self.play(ShowCreation(d_box), Write(d_lbl), run_time=0.9)
        hold(self, 1.0)

        self.cap.show(
            "Blue is labelled real. Orange is labelled fake.",
            "It has right answers. Blue points are labelled real. Orange "
            "points are labelled fake. Any classifier can learn that.",
            size=30)

        # the field: what D learns, as a height over the plane
        self.cap.show(
            "What it learns is a height over every point.",
            "Call it the discriminator. And picture what it learns as a "
            "surface lying over the plane: a height at every point, for "
            "how real that point looks.",
            size=30)
        self.play(FadeOut(VGroup(d_box, d_lbl), shift=DOWN * 0.3),
                  run_time=0.7)

        plane_spec = {"x_range": XR, "y_range": YR, "c2p": c2p,
                      "width": PW, "height": PH,
                      "center": np.array([PX0, PY0, 0])}
        slice_ax = Axes(x_range=(XR[0], XR[1], 1.0), y_range=(0, 1, 0.5),
                        width=PW, height=1.55)
        slice_ax.set_stroke(GREY_D, width=1.4, opacity=1.0)
        slice_ax.move_to(np.array([0.0, -2.45, 0]))

        land = Landscape(plane_spec, slice_ax, slice_y=0.0)
        self.land = land

        field = land.field_image(REAL_SPEC, FAKE_START, "start", CACHE_DIR)
        field.set_opacity(0.0)
        self.add(field)
        self.field = field
        self._front()                      # field sits under the points
        self.play(field.animate.set_opacity(1.0), run_time=2.0)
        hold(self, 1.5)

        # the slice
        self.cap.show(
            "Read it as a cross-section through both clouds.",
            "High ground over the blue cloud. Low ground over the orange.",
            size=30)
        slice_line = DashedLine(c2p(XR[0], 0.0), c2p(XR[1], 0.0),
                                dash_length=0.11)
        slice_line.set_stroke(WHITE, width=1.6, opacity=0.75)
        self.play(ShowCreation(slice_line), run_time=0.8)
        self.play(ShowCreation(slice_ax), run_time=0.8)

        profile = land.profile_curve(REAL_SPEC, FAKE_START, color=C_DISC)
        self.play(ShowCreation(profile), run_time=1.6)
        hold(self, 1.5)

        d_tex = Tex(r"D(\mathbf{x})").scale(0.95).set_color(C_DISC)
        d_tex.next_to(slice_ax, LEFT, buff=0.0)
        d_tex.shift(RIGHT * 0.55 + UP * 0.72)
        assert_in_frame(d_tex=d_tex)
        self.play(Write(d_tex), run_time=0.9)
        hold(self, 1.5)
        self.wait(3.4)          # narration budget: see SCRIPT.md §3

        self.cap.show(
            "It never learns what a face is — only which side is higher.",
            "Now notice what we've got. The discriminator never learns what "
            "a face is. It only has to be higher over there than over here.",
            size=28)

        # a surface has slope, and a slope is a direction
        self.cap.show(
            "And a slope is a direction.",
            "But that's enough — because a surface has slope. And a slope "
            "is a direction.",
            size=30, color=C_HOT)
        push_in(self, self.anchor.get_center(), height=3.0, run_time=1.4)

        rays = VGroup()
        up_idx = 0
        best = -1e9
        for k in range(8):
            th = k * TAU / 8
            v = np.array([np.cos(th), np.sin(th), 0])
            rays.add(arrow(self.anchor.get_center() + v * 0.16,
                           self.anchor.get_center() + v * 0.62, C_NEUT, 2.2))
            ax, ay = self.fake_xy[7]
            probe = land.D(ax + np.cos(th) * 0.35, ay + np.sin(th) * 0.35,
                           REAL_SPEC, FAKE_START)
            if probe > best:
                best, up_idx = probe, k
        self.play(stagger([GrowArrow(a) for a in rays], lag_ratio=0.07),
                  run_time=1.0)
        hold(self, 1.0)

        th = up_idx * TAU / 8
        v = np.array([np.cos(th), np.sin(th), 0])
        up_arrow = arrow(self.anchor.get_center() + v * 0.16,
                         self.anchor.get_center() + v * 0.95, C_GRAD, 3.5)
        self.play(
            *[a.animate.set_opacity(0.12) for a in rays],
            ReplacementTransform(rays[up_idx].copy(), up_arrow),
            run_time=1.0,
        )
        hold(self, 2.0)
        self.play(FadeOut(rays), FadeOut(up_arrow), run_time=0.7)

        self.profile = profile
        self.slice_ax = slice_ax
        self.slice_line = slice_line
        self.d_tex = d_tex

    # ── §4  Walking uphill ───────────────────────────────────────────────
    def s4_uphill(self):
        pull_back(self, run_time=1.3)
        self.cap.show(
            "The generator reads the slope and steps up it.",
            "So the generator stops guessing. It reads the slope beneath "
            "its own output, and nudges its weights so that next time, that "
            "output lands a little further up the hill.",
            size=30)

        # a marker on the profile tracks the anchor point's x
        ax0, ay0 = self.fake_xy[7]
        pm = dot(self.slice_ax.c2p(ax0, self.land.D(ax0, 0.0, REAL_SPEC,
                                                    FAKE_START)),
                 C_FAKE, 0.085)
        drop = DashedLine(self.anchor.get_center(), pm.get_center(),
                          dash_length=0.09)
        drop.set_stroke(GREY_D, width=1.3, opacity=0.8)
        self.play(ShowCreation(drop), GrowFromCenter(pm), run_time=0.9)
        hold(self, 1.0)

        # step it uphill three times
        for tx in (-2.2, -1.5, -0.9):
            newp = self.slice_ax.c2p(
                tx, self.land.D(tx, 0.0, REAL_SPEC, FAKE_START))
            top = c2p(tx, ay0 * 0.6)
            # DashedLine is a VGroup of dashes with no points of its own, so
            # put_start_and_end_on cannot be animated on it - rebuild + Transform.
            new_drop = DashedLine(top, newp, dash_length=0.09)
            new_drop.set_stroke(GREY_D, width=1.3, opacity=0.8)
            self.play(
                self.anchor.animate.move_to(top),
                pm.animate.move_to(newp),
                Transform(drop, new_drop),
                run_time=0.85,
            )
        hold(self, 1.5)

        self.cap.show(
            "Not “here is the correct face.” Just: up is that way.",
            "That's the entire training signal. Not 'here is the correct "
            "face' — there isn't one. Just: from where you're standing, "
            "up is that way.",
            size=28, color=C_HOT)
        self.play(FadeOut(VGroup(drop, pm)), run_time=0.6)

        # the objective, built from separately addressable terms
        self.cap.show(
            "The objective is then only bookkeeping.",
            "And with that, the objective function is only bookkeeping.",
            size=30)
        t_real = Tex(r"\mathbb{E}_{x\sim p_{\text{data}}}"
                     r"\big[\log D(x)\big]").set_color(C_REAL)
        t_plus = Tex("+").set_color(WHITE)
        t_fake = Tex(r"\mathbb{E}_{z\sim p_z}"
                     r"\big[\log\big(1-D(G(z))\big)\big]").set_color(C_FAKE)
        obj = equation(t_real, t_plus, t_fake, buff=0.24, scale=0.78)
        obj.move_to(np.array([0.0, -2.45, 0]))
        assert_in_frame(obj=obj)

        self.play(
            FadeOut(VGroup(self.slice_ax, self.profile, self.d_tex),
                    shift=DOWN * 0.25),
            run_time=0.7,
        )
        self.play(Write(obj), run_time=2.2)
        hold(self, 2.0)

        # Each term is tied to its cloud by COLOUR, not by position: flying
        # the terms onto the plane puts dense LaTeX on top of a dot cloud and
        # neither survives. Box the term where it already sits and flash the
        # region it governs at the same time.
        self.cap.show(
            "Each term is about one of the two clouds.",
            "The discriminator wants to raise the surface over real points, "
            "and lower it over fake ones — that's its two terms.",
            size=30)

        r_box = box_around(t_real, C_REAL)
        self.play(ShowCreation(r_box),
                  FlashAround(self.real_dots, color=C_REAL, buff=0.12),
                  run_time=1.2)
        self.cap.show("D raises the surface here…",
                      "It wants the surface high over the real points.",
                      size=30, color=C_REAL)

        f_box = box_around(t_fake, C_FAKE)
        self.play(ReplacementTransform(r_box, f_box),
                  FlashAround(self.fake_dots, color=C_FAKE, buff=0.12),
                  run_time=1.2)
        self.cap.show(
            "…and lowers it here. G wants that to fail.",
            "The generator wants exactly one of those terms to fail. "
            "It wants its own points high.",
            size=30, color=C_FAKE)

        minimax = Tex(r"\min_G \max_D").scale(1.15)
        minimax.set_color(WHITE)
        minimax.move_to(np.array([0.0, -2.45, 0]))
        self.play(
            FadeOut(f_box, scale=1.1),
            ReplacementTransform(VGroup(t_real, t_plus, t_fake), minimax),
            run_time=1.4,
        )
        hold(self, 2.0)

        self.cap.show(
            "One surface. One player pulling it apart, one pushing it flat.",
            "One surface. One player pushing it apart, the other pushing "
            "it flat.",
            size=28, color=C_HOT)
        self.play(FadeOut(minimax, shift=DOWN * 0.25), run_time=0.7)

        # restore the slice for §5
        self.play(
            FadeIn(self.slice_ax, shift=UP * 0.2),
            FadeIn(self.profile, shift=UP * 0.2),
            FadeIn(self.d_tex, shift=UP * 0.2),
            run_time=0.8,
        )

    # ── §5  The landscape fights back ────────────────────────────────────
    def s5_chase(self):
        self.cap.show("But the surface is not fixed.",
                      "Except the surface isn't fixed.", size=30)

        stages = [
            (FAKE_MID, "The cloud climbs — so D repaints the landscape.",
             "Every time the orange cloud climbs, the discriminator gets "
             "retrained — and it repaints the landscape to separate them "
             "again."),
            (FAKE_NEAR, "It climbs again. The hill moves again.",
             "The hill moves. The generator climbs. The hill moves again. "
             "That's the whole loop. And it's why the two networks have to "
             "improve together: the grader is only ever as good as it needs "
             "to be to catch the current forger."),
        ]
        for k, (spec, line, narr) in enumerate(stages):
            self.cap.show(line, narr, size=30)
            new_xy = sample(spec, N_FAKE, seed=5)
            self.play(
                stagger([d.animate.move_to(c2p(x, y))
                         for d, (x, y) in zip(self.fake_dots, new_xy)],
                        lag_ratio=0.012),
                run_time=1.6,
            )
            new_profile = self.land.profile_curve(REAL_SPEC, spec,
                                                  color=C_DISC)
            self.swap_field(
                REAL_SPEC, spec, f"chase{k}", run_time=1.5,
                extra=[Transform(self.profile, new_profile)],
            )
            hold(self, 1.5)

        # convergence
        self.cap.show(
            "There is less and less left to separate.",
            "Now watch where this ends. As the orange cloud spreads over "
            "the blue one, the discriminator's job gets harder — there's "
            "less and less left to separate. The high ground comes down. "
            "The low ground comes up.",
            size=30)
        final_xy = sample(FAKE_DONE, N_FAKE, seed=77)
        self.play(
            stagger([d.animate.move_to(c2p(x, y))
                     for d, (x, y) in zip(self.fake_dots, final_xy)],
                    lag_ratio=0.012),
            run_time=2.0,
        )
        flat_profile = self.land.profile_curve(REAL_SPEC, FAKE_DONE,
                                               color=C_DISC)
        self.swap_field(
            REAL_SPEC, FAKE_DONE, "converged", run_time=2.0,
            extra=[Transform(self.profile, flat_profile)],
        )
        hold(self, 1.5)

        self.cap.show(
            "No surface can separate them. It goes flat.",
            "Until the two clouds coincide, and no surface can separate "
            "them at all. The landscape goes flat. D of x is one-half, "
            "everywhere. A coin flip.",
            size=30, color=C_HOT)
        half = Tex(r"D(\mathbf{x}) = \tfrac{1}{2}").scale(0.95)
        half.set_color(C_DISC)
        half.next_to(self.slice_ax, UP, buff=0.0)
        half.shift(DOWN * 0.30 + RIGHT * 3.4)
        assert_in_frame(half=half)
        self.play(Write(half), run_time=1.2)
        hold(self, 2.0)

        self.cap.show(
            "The grader has been rendered useless. That was the goal.",
            "The grader has been rendered useless. That was the goal.",
            size=28, color=C_HOT)
        # the emotional peak of the video gets the longest hold in it
        self.wait(2.2)
        self.half = half
        self.fake_final_xy = final_xy

    # ── §6  When it goes wrong ───────────────────────────────────────────
    def s6_collapse(self):
        self.cap.show(
            "Nothing here ever told the cloud to spread.",
            "One failure mode falls straight out of this picture. Nothing "
            "here ever told the orange cloud to spread. It was only told "
            "to get high.",
            size=30)
        self.play(FadeOut(self.half, shift=UP * 0.2), run_time=0.5)

        # rewind to a mid-training landscape with two visible peaks
        mid_profile = self.land.profile_curve(REAL_SPEC, FAKE_MID,
                                              color=C_DISC)
        self.swap_field(
            REAL_SPEC, FAKE_MID, "rewind", run_time=1.2,
            extra=[Transform(self.profile, mid_profile)],
        )

        self.cap.show(
            "It can pile every point onto one peak — and be satisfied.",
            "So if it finds one peak, it can pile every point it has onto "
            "that one peak — and be perfectly satisfied.",
            size=28)
        col_xy = sample(FAKE_COLLAPSE, N_FAKE, seed=9)
        self.play(
            stagger([d.animate.move_to(c2p(x, y))
                     for d, (x, y) in zip(self.fake_dots, col_xy)],
                    lag_ratio=0.010),
            run_time=1.8,
        )
        hold(self, 1.0)

        same = Group()
        for _ in range(6):
            same.add(photo("interp_08.png", C_FAKE, height=0.78))
        same.arrange(RIGHT, buff=0.16)
        same.move_to(np.array([0.0, -2.45, 0]))
        assert_in_frame(same=same)
        self.play(
            FadeOut(VGroup(self.slice_ax, self.profile, self.d_tex),
                    shift=DOWN * 0.2),
            run_time=0.6,
        )
        self.play(stagger([FadeIn(p, shift=UP * 0.2) for p in same],
                          lag_ratio=0.10),
                  run_time=1.3)
        hold(self, 2.0)
        self.wait(3.6)          # narration budget: see SCRIPT.md §6

        # D flattens that peak, and the pile just migrates
        self.cap.show(
            "D flattens that peak — so the pile moves to the next one.",
            "The discriminator will eventually notice, and flatten that "
            "peak. But the generator just moves the pile to the next one. "
            "It never learns to cover the region, because covering the "
            "region was never what we asked for.",
            size=28)
        col2_xy = sample(FAKE_COLLAPSE2, N_FAKE, seed=13)
        same2 = Group()
        for _ in range(6):
            same2.add(photo("interp_02.png", C_FAKE, height=0.78))
        same2.arrange(RIGHT, buff=0.16)
        same2.move_to(np.array([0.0, -2.45, 0]))

        self.swap_field(
            REAL_SPEC, FAKE_COLLAPSE, "collapse", run_time=1.8,
            extra=[
                stagger([d.animate.move_to(c2p(x, y))
                         for d, (x, y) in zip(self.fake_dots, col2_xy)],
                        lag_ratio=0.010),
                FadeOut(same, shift=DOWN * 0.2),
                FadeIn(same2, shift=DOWN * 0.2),
            ],
        )
        hold(self, 1.5)

        self.cap.show(
            "Mode collapse. Not a bug in the code — a gap in the objective.",
            "That's mode collapse. It isn't a bug in the code. It's a gap "
            "in the objective.",
            size=28, color=C_HOT)
        self.wait(3.4)          # the section's closing claim needs to land
        self.play(FadeOut(same2, shift=DOWN * 0.25), run_time=0.7)
        self.same_faces = same2

    # ── §7  Payoff ───────────────────────────────────────────────────────
    def s7_payoff(self):
        # restore the converged, flat landscape
        self.cap.show("So — back to the question.",
                      "So. Back to the question.", size=30)
        flat_profile = self.land.profile_curve(REAL_SPEC, FAKE_DONE,
                                               color=C_DISC)
        self.swap_field(
            REAL_SPEC, FAKE_DONE, "restore", run_time=1.8,
            extra=[stagger([d.animate.move_to(c2p(x, y))
                            for d, (x, y) in zip(self.fake_dots,
                                                 self.fake_final_xy)],
                           lag_ratio=0.010)],
        )
        self.play(
            FadeIn(self.slice_ax), FadeIn(self.d_tex),
            ShowCreation(flat_profile), run_time=1.0,
        )
        self.profile = flat_profile
        hold(self, 1.0)

        # The opening question returns as its own moment. The landscape dims
        # rather than being cleared - it has to still be there when the
        # answer points back at it.
        self.cap.clear(run_time=0.5)
        stage = Dimmer(self.field, self.real_dots, self.fake_dots,
                       self.seed_pt, self.frame_rect, self.plane_lbl,
                       self.slice_ax, self.profile, self.d_tex,
                       self.slice_line)
        self.play(*stage.to(0.16), run_time=0.9)

        q = Text(
            "What do you write down as the score,\n"
            "when there is no right answer?",
            font=FONT, font_size=40,
        ).set_color(C_HOT)
        q.move_to(np.array([0, 0.6, 0]))
        assert_in_frame(q=q)
        self.play(Write(q), run_time=2.0)
        self.wait(3.2)

        ans = Text("Nothing. You don't write it down.",
                   font=FONT, font_size=40).set_color(WHITE)
        ans.move_to(np.array([0, 0.6, 0]))
        self.play(FadeOut(q, shift=UP * 0.3), run_time=0.6)
        self.play(Write(ans), run_time=1.4)
        self.wait(2.4)

        # ...and the thing it points at comes back up
        self.play(
            FadeOut(ans, shift=UP * 0.3),
            *stage.restore(),
            run_time=1.1,
        )
        self.play(
            FlashAround(self.profile, color=C_DISC, run_time=1.4),
        )
        self.cap.show(
            "You let the data sculpt it.",
            "You let the data sculpt it. The score is a surface that the "
            "real examples raise up and the fake ones wear down; that "
            "reshapes itself every time the generator improves; and that "
            "flattens into nothing at the exact moment the generator gets "
            "it right.",
            size=30, color=C_HOT)

        # close on the same face the video opened with
        self.cap.clear(run_time=0.5)
        self.play(
            FadeOut(VGroup(self.slice_ax, self.profile, self.d_tex),
                    shift=DOWN * 0.3),
            FadeOut(self.slice_line),
            FadeOut(self.plane_lbl),
            run_time=1.0,
        )
        closing = Text(
            "Nobody ever tells this network\nwhat a good face looks like.",
            font=FONT, font_size=34,
        ).set_color(WHITE)
        closing.move_to(np.array([0, 1.55, 0]))

        closing2 = Text(
            "It learns because a second network keeps\n"
            "rebuilding the hill it has to climb.",
            font=FONT, font_size=34,
        ).set_color(C_HOT)
        closing2.move_to(np.array([0, -0.55, 0]))
        assert_no_overlap([("closing", closing, "closing2", closing2)],
                          pad=0.05)

        # the picture dissolves *into* the closing statement - the two cross
        # over rather than the frame emptying between them
        self.play(
            self.field.animate.set_opacity(0.0),
            stagger([FadeOut(d, scale=0.3) for d in self.fake_dots],
                    lag_ratio=0.008),
            stagger([FadeOut(d, scale=0.3) for d in self.real_dots],
                    lag_ratio=0.008),
            FadeOut(self.seed_pt, scale=0.3),
            FadeOut(self.frame_rect),
            FadeIn(closing, shift=UP * 0.25),
            run_time=1.8,
        )
        self.wait(2.2)
        self.play(Write(closing2), run_time=2.2)
        self.wait(3.0)

        face = photo("interp_04.png", C_NEUT, height=2.3)
        face.move_to(np.array([0, -2.35, 0]))
        assert_in_frame(face=face)
        self.play(
            closing.animate.move_to(np.array([0, 2.75, 0])),
            closing2.animate.move_to(np.array([0, 1.05, 0])),
            run_time=0.9,
        )
        self.play(FadeIn(face, scale=0.85), run_time=1.4)
        hold(self, 2.0)
        self.play(FadeOut(Group(closing, closing2, face)), run_time=1.6)
        self.wait(0.8)
