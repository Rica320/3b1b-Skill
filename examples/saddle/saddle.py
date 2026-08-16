"""
"Is the origin a maximum or a minimum of z = x^2 - y^2?"

A 1:35 3D scene: the worked example for the skill's three_d.md rules.
Every 3D-specific helper in manim_helpers.py is exercised here, and the
camera move is the argument rather than the decoration.

    Render:  bash ../../skills/3b1b-math-animation/scripts/render.sh \
                 saddle.py Saddle
    Verify:  python ../../skills/3b1b-math-animation/scripts/verify_render.py \
                 videos/Saddle.mp4 --meta render_meta.json
    Audit:   AUDIT=1 manimgl saddle.py Saddle     # reports text overlaps

Spine
  QUESTION    seen from directly above, the origin of z = x^2 - y^2 is just a
              point on a flat-looking sheet. Peak or valley?
  MOTIVATION  the obvious answer is to slice. Along x the slice says minimum.
              Along y the slice says maximum. Both slices are correct, and
              they contradict each other.
  BUILD       the contradiction is not in the algebra, it is in the viewpoint.
              Tilt the camera: the two slices lift out of the plane into two
              parabolas crossing at the origin, and the surface between them
              is a pass.
  PAYOFF      restate the question, answer it: neither - a saddle, where
              every direction you walk disagrees with its neighbour.

Carried metaphor: THE MOUNTAIN PASS.
  the surface        -> the terrain
  the x-slice        -> the trail that climbs out of the pass
  the y-slice        -> the ridge that falls away from it
  the origin         -> the pass itself
  "max or min?"      -> "is the pass a summit or a basin?"

Colour mapping (fixed for the whole scene)
  BLUE_C   the x direction and its slice - the one that says "minimum"
  ORANGE   the y direction and its slice - the one that says "maximum"
  TEAL_C   the surface itself
  YELLOW   transient emphasis only
  GREY_B   scaffolding: axes, captions, connectives
"""

from manimlib import *
from pathlib import Path
import sys
import os

# ManimGL's loader does not put the scene file's directory on sys.path, so the
# skill's shared helpers are not importable without this. Standalone projects
# should copy manim_helpers.py next to the scene file instead; the examples in
# this repository import the canonical copy so the two cannot drift apart.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1] / "skills" / "3b1b-math-animation"
                       / "scripts"))

from manim_helpers import (
    Caption, Dimmer, hold, stagger, dump_meta,
    audit_text_overlaps, assert_in_frame_3d,
    fix, orient, orbit, spin, surface, mesh_for, dot3d, slice_curve,
    FONT,
)

C_X = BLUE_C         # the x direction: the slice that says "minimum"
C_Y = ORANGE         # the y direction: the slice that says "maximum"
C_SURF = TEAL_C      # the terrain
C_HOT = YELLOW       # transient emphasis
C_NEUT = GREY_B

R = 2.2              # domain half-width
K = 0.6              # vertical scale, chosen so the surface fits z_range


def f(x, y):
    return K * (x * x - y * y)


class Saddle(ThreeDScene):

    def wait(self, *args, **kwargs):
        r = super().wait(*args, **kwargs)
        if os.environ.get("AUDIT"):
            audit_text_overlaps(self)
        return r

    def construct(self):
        self.camera.background_color = BLACK
        self.cap = Caption(self)          # fixes itself in frame: ThreeDScene
        for name, fn in [("s0", self.s0_question), ("s1", self.s1_slices),
                         ("s2", self.s2_tilt), ("s3", self.s3_payoff)]:
            t0 = self.time
            fn()
            print(f"[TIMING] {name} start={t0:6.1f}s dur={self.time - t0:5.1f}s")
        dump_meta(self, str(_HERE / "render_meta.json"))

    # ── §0  The question, asked from a viewpoint that cannot answer it ───
    def s0_question(self):
        # phi = 0 is straight down. A 3D scene deliberately opened as a 2D one:
        # the whole video is the cost of that missing dimension.
        orient(self, theta=0, phi=0, height=8.0)

        axes = ThreeDAxes(
            x_range=(-R, R, 1), y_range=(-R, R, 1), z_range=(-3, 3, 1),
            width=5.6, height=5.6, depth=3.4,
        )
        axes.set_stroke(GREY_D, width=1.6)
        axes.move_to(ORIGIN)

        surf = surface(f, axes=axes, color=C_SURF, opacity=0.85,
                       resolution=(72, 72))
        # The mesh is the depth cue. A single-colour surface with no wireframe
        # reads as a coloured blob until the camera moves; with one, the fold
        # is legible in a still frame.
        mesh = mesh_for(surf, resolution=(19, 19), color=WHITE,
                        width=1.0, opacity=0.5)

        formula = Tex(r"z = x^2 - y^2").scale(0.95).set_color(C_NEUT)
        fix(formula.move_to(np.array([-4.6, 3.0, 0])))

        self.play(ShowCreation(axes), run_time=1.2)
        self.play(ShowCreation(surf), run_time=1.6)
        self.play(ShowCreation(mesh), FadeIn(formula), run_time=1.2)

        self.cap.show(
            "A surface, seen from straight above.",
            "Here is the surface z equals x squared minus y squared, seen "
            "from straight above.",
            size=30)

        # Lifted a hair off the surface for the same reason slice_curve lifts
        # its curves: a marker at exactly the surface's own height loses the
        # depth test to it about half the time.
        origin_dot = dot3d(axes.c2p(0, 0, 0.08), C_HOT, radius=0.075)
        self.play(FadeIn(origin_dot, scale=0.4), run_time=0.7)
        hold(self, 1.0)

        question = Text("Is the origin a maximum or a minimum?",
                        font=FONT, font_size=34).set_color(C_HOT)
        fix(question.move_to(np.array([0, -3.05, 0])))
        assert_in_frame_3d(self, question=question, formula=formula)
        self.play(Write(question), run_time=1.8)
        self.wait(2.6)

        self.axes, self.surf, self.mesh = axes, surf, mesh
        self.origin_dot, self.formula, self.question = (
            origin_dot, formula, question)

    # ── §1  The obvious answer: slice it. Twice. ─────────────────────────
    def s1_slices(self):
        self.cap.show(
            "The obvious move: take a slice.",
            "The obvious move is to take a slice through the origin and read "
            "off the shape of the curve you get.",
            size=30)

        axes, ax_f = self.axes, f

        # From directly above, both slices are still just lines through the
        # origin - which is exactly the point. The claim they support is a
        # caption, not a picture, and that is what §2 has to repair.
        cut_x = slice_curve(axes, ax_f, (-R, R), direction="x", color=C_X,
                            width=5.0)
        cut_y = slice_curve(axes, ax_f, (-R, R), direction="y", color=C_Y,
                            width=5.0)

        claim_x = Tex(r"z = x^2 \quad\Rightarrow\quad \text{minimum}")
        claim_x.scale(0.7).set_color(C_X)
        fix(claim_x.move_to(np.array([-4.2, -1.5, 0])))
        claim_y = Tex(r"z = -y^2 \quad\Rightarrow\quad \text{maximum}")
        claim_y.scale(0.7).set_color(C_Y)
        fix(claim_y.move_to(np.array([-4.2, -2.3, 0])))

        self.play(
            FadeOut(self.question, shift=DOWN * 0.2),
            ShowCreation(cut_x), run_time=1.4)
        self.play(Write(claim_x), run_time=1.1)
        self.wait(1.4)

        self.play(ShowCreation(cut_y), run_time=1.2)
        self.play(Write(claim_y), run_time=1.1)
        assert_in_frame_3d(self, claim_x=claim_x, claim_y=claim_y)
        self.wait(1.2)

        self.cap.show(
            "Both slices are correct. They disagree.",
            "Walk along x and the origin is the bottom of a valley. Walk "
            "along y and it is the top of a hill. Both of those are correct, "
            "and they cannot both describe a maximum or a minimum.",
            size=30)
        self.wait(1.6)

        self.cut_x, self.cut_y = cut_x, cut_y
        self.claim_x, self.claim_y = claim_x, claim_y

    # ── §2  The camera move that resolves it ─────────────────────────────
    def s2_tilt(self):
        self.cap.show(
            "The contradiction is in the viewpoint.",
            "The contradiction is not in the algebra. It is in the viewpoint.",
            size=30)

        # The reveal. Nothing on the stage changes; only phi does. The two
        # slices lift out of the plane into the two parabolas they always
        # were, and the flat sheet becomes a pass.
        orbit(self, theta=-30, phi=68, run_time=3.4)
        # Checked at the orientation it will be read at, and on a mobject that
        # lives in the world: this is the assertion that has to go through the
        # projection, since world coordinates say nothing at this angle. Not
        # asserted on the surface itself - it is a large curved body, and the
        # check projects bounding-box corners the surface never reaches, so it
        # reports a false positive. Check [1] of verify_render.py polices the
        # geometry against the real pixels.
        assert_in_frame_3d(self, origin=self.origin_dot)
        hold(self, 2.0)

        self.cap.show(
            "Both curves were parabolas all along.",
            "Both curves were parabolas all along. One opens upward, the "
            "other opens downward, and they cross at the origin.",
            size=30)
        self.wait(1.2)

        # Dim the terrain so the two curves carry the frame on their own.
        # Dimmer, not set_opacity: the surface is not a VMobject and the mesh
        # is a stroke-only one, and a flat set_opacity would flatten both.
        stage = Dimmer(self.surf, self.mesh, self.axes)
        self.play(*stage.to(0.28), run_time=1.0)
        # A pulse travelling along each curve says "walk this way" without
        # moving the mobject. Indicate() would scale the curve about its own
        # centre, which in 3D reads as the geometry jumping off the surface.
        self.play(
            stagger([ShowPassingFlash(self.cut_x.copy()
                                      .set_stroke(C_HOT, 7), time_width=0.45),
                     ShowPassingFlash(self.cut_y.copy()
                                      .set_stroke(C_HOT, 7), time_width=0.45)],
                    lag_ratio=0.45),
            run_time=2.4)
        hold(self, 1.5)
        self.play(*stage.restore(), run_time=1.0)

        self.cap.show(
            "The surface between them is a mountain pass.",
            "And the surface stretched between them is a mountain pass: the "
            "trail climbs out of it in one direction and the ridge falls "
            "away in the other.",
            size=30)
        # Negative: the sweep stays inside the informative arc
        # (theta -30 to -60). Spinning the other way passes through
        # theta = 0, where the near fold hides the far one and the
        # saddle reads as a plain bowl.
        spin(self, 3.0, speed=-5.0)
        self.cap.show(
            "Up the trail one way, down the ridge the other.",
            "Walk out along the blue trail and you climb. Walk out along the "
            "orange ridge and you fall away. The pass is both of those at "
            "once.",
            size=30)
        spin(self, 3.0, speed=-5.0)

    # ── §3  Payoff: the opening question, restated and answered ──────────
    def s3_payoff(self):
        stage = Dimmer(self.surf, self.mesh, self.axes, self.cut_x, self.cut_y)
        self.play(*stage.to(0.5),
                  FadeOut(self.claim_x), FadeOut(self.claim_y),
                  run_time=1.0)

        # Restate the opening question verbatim, then answer it.
        question = Text("Is the origin a maximum or a minimum?",
                        font=FONT, font_size=34).set_color(C_NEUT)
        fix(question.move_to(np.array([0, -2.75, 0])))
        answer = Text("Neither. It is a saddle.",
                      font=FONT, font_size=40).set_color(C_HOT)
        fix(answer.move_to(np.array([0, -3.45, 0])))
        assert_in_frame_3d(self, question=question, answer=answer)

        self.play(Write(question), run_time=1.5)
        self.wait(1.4)
        self.play(*stage.restore(), Write(answer), run_time=1.6)

        # A ring lying on the surface at the pass. Flash() would draw its
        # spokes in the world xy-plane and be swallowed by the terrain; a ring
        # with a non-flat stroke is a 3D object and tilts with the camera.
        ring = Circle(radius=0.34)
        ring.set_stroke(C_HOT, width=3.0, opacity=1.0)
        ring.set_fill(opacity=0.0)
        ring.set_flat_stroke(False)
        ring.move_to(self.axes.c2p(0, 0, 0.1))
        self.play(ShowCreation(ring), run_time=0.6)
        self.play(ring.animate.scale(2.1).set_stroke(opacity=0.0),
                  run_time=0.9)
        self.remove(ring)

        self.cap.show(
            "No single slice can see it.",
            "Every direction you walk away from the origin disagrees with "
            "the one next to it. No single slice can see that. Only the "
            "third dimension can.",
            size=30)
        spin(self, 6.0, speed=5.0)   # back the way it came
        self.play(FadeOut(question), FadeOut(answer), run_time=1.0)
        self.cap.clear(run_time=0.8)
        self.wait(0.8)
