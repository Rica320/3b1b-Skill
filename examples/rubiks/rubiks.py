"""
"What does somebody who can solve a Rubik's cube actually know?"

A 3D, narrated explainer: the skill's worked example for the audio pipeline
(script.yaml -> tts.py -> Narrator -> mux_audio.py) and its second 3D one.

    TTS:     ../../skills/3b1b-math-animation/scripts/tts.py script.yaml --out audio
    Render:  bash ../../skills/3b1b-math-animation/scripts/render.sh rubiks.py Rubiks
    Mux:     python ../../skills/3b1b-math-animation/scripts/mux_audio.py \
                 videos/Rubiks.mp4 --cues narration_cues.json
    Verify:  python ../../skills/3b1b-math-animation/scripts/verify_render.py \
                 videos/Rubiks.mp4 --meta render_meta.json
             python ../../skills/3b1b-math-animation/scripts/verify_audio.py \
                 videos/Rubiks_narrated.mp4 --cues narration_cues.json
             python verify_cube.py          # every claim the narration makes

Spine
  QUESTION    43,252,003,274,489,856,000 arrangements. Nobody memorises a way
              out of each one, so what is it a solver actually knows?
  MOTIVATION  the obvious answer - learn where each piece goes and put it
              there - dies on the first move, because every turn moves nine
              cubies at once. The one method that always works, retracing the
              scramble backwards, is correct and useless.
  BUILD       but retracing works because a move and its undo cancel. Keep
              that and drop the memory: R, then something, then R inverse.
              Everything R disturbed comes back except what changed while it
              was away - one corner and one edge. That is a detour, and
              because a detour returns, six of them return the whole cube.
  PAYOFF      the method is nothing but detours spent in the right order. Not
              positions: seven short sequences.

Carried metaphor: THE DETOUR - leave by a road, come back by the same road.
  R ... R'               -> the road out and the road home
  the U turn between     -> the errand you left to run
  the untouched pieces   -> the town you drove around
  (R U R' U')^6 = solved -> the detour is a closed loop
  the solved bottom layer-> the town you must not disturb
  the whole method       -> a short list of detours

Colour
  The cube's six face colours belong to the cube, the way a photograph's
  colours do; nothing else in the scene is allowed to use them. Attention is
  directed by DIMMING (Dimmer) rather than by tinting, which is the only way
  to highlight part of an object whose colours are already its meaning.
  TEAL_C is the single added colour - not a cube colour, and used only to
  outline the one piece being followed.
  GREY_A / WHITE for captions and the HUD.
"""

import os
import sys
from pathlib import Path

import numpy as np
from manimlib import *

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parents[1] / "skills" / "3b1b-math-animation"
                      / "scripts"))

import cube_model as cm                                    # noqa: E402
import solver as sv                                        # noqa: E402
from cube_view import CubeView                             # noqa: E402
from manim_helpers import (                                # noqa: E402
    Caption, Dimmer, hold, dump_meta, audit_text_overlaps,
    assert_in_frame_3d, fix, orient, orbit, spin, FONT,
)
from narration import Narrator                             # noqa: E402

C_TRACK = TEAL_C          # the one added colour: the piece being followed
C_HUD = GREY_A
HUD_X = -6.2               # the left column: move label, counter, tally
C_TEXT = WHITE

CUBE_SIZE = 3.6
SCRAMBLE_SEED = 30

THETA, PHI = -32, 68      # a three-quarter view: up, front and right faces
PHI_UNDER = 112           # from below, where the white layer is

STATES = 43252003274489856000
QUESTION = "What does somebody who can solve this actually know?"

# The one sequence the whole video is about.
DETOUR = cm.parse("R U R' U'")


class Rubiks(ThreeDScene):

    def wait(self, *args, **kwargs):
        r = super().wait(*args, **kwargs)
        if os.environ.get("AUDIT"):
            audit_text_overlaps(self)
        return r

    def construct(self):
        self.camera.background_color = BLACK
        self.nar = Narrator(_HERE / "script.yaml", _HERE / "audio")
        self.cap = Caption(self, narrator=self.nar)

        self.scramble = cm.scramble(20, seed=SCRAMBLE_SEED)
        self.solution = sv.solve(cm.apply(cm.SOLVED, self.scramble))

        for name, fn in [("s0", self.s0_question), ("s1", self.s1_obvious),
                         ("s2", self.s2_detour), ("s3", self.s3_loop),
                         ("s4", self.s4_method), ("s5", self.s5_payoff)]:
            t0 = self.time
            fn()
            print(f"[TIMING] {name} start={t0:6.1f}s dur={self.time - t0:5.1f}s")

        dump_meta(self, str(_HERE / "render_meta.json"))
        self.nar.dump(_HERE / "narration_cues.json", scene=self)
        self.nar.report()

    # ── §0  the question ─────────────────────────────────────────────────
    def s0_question(self):
        orient(self, theta=THETA, phi=PHI, height=8.0)
        self.cube = CubeView(size=CUBE_SIZE)
        self.cube.check("§0 build")

        self.play(FadeIn(self.cube.group, scale=0.85), run_time=1.4)
        self.cap.show("A solved cube.", "s0.open")

        # The scramble is the same twenty turns the solver is handed, so the
        # cube the viewer watches being wrecked is the cube that gets solved
        # in §4 -- not a different one that merely looks similar.
        self.nar.cue(self, "s0.count")
        self.play(self.cube.run_anim(self.scramble, per_move=0.24),
                  run_time=0.24 * len(self.scramble))
        self.cube.check("§0 scrambled")

        count = Tex(r"43{,}252{,}003{,}274{,}489{,}856{,}000")
        count.scale(0.62).set_color(C_HUD)
        fix(count.move_to(np.array([0, -3.25, 0])))
        assert_in_frame_3d(self, count=count)
        self.play(Write(count), run_time=1.6)
        self.nar.finish(self)

        self.cap.show("Nobody memorises a way out of each one.", "s0.question",
                      size=30)
        question = Text(QUESTION, font=FONT, font_size=30).set_color(C_TEXT)
        fix(question.move_to(np.array([0, -3.25, 0])))
        self.play(FadeOut(count, shift=DOWN * 0.2), run_time=0.4)
        self.play(Write(question), run_time=1.6)
        self.nar.finish(self)
        # A deliberate wordless beat. The question is the thing the viewer has
        # to carry for four minutes; talking over it does not help them hold
        # it. Silence has to be spent on purpose, or the coverage check in
        # verify_audio.py is right that there is nowhere to look.
        spin(self, 4.0, speed=-5.0)
        self.play(FadeOut(question, shift=DOWN * 0.2), run_time=0.5)

    # ── §1  the obvious answer, and the one method that always works ─────
    def s1_obvious(self):
        cube = self.cube
        self.cap.show("Put each piece where it belongs.", "s1.obvious")

        # The white-orange edge, wherever the scramble left it, and the single
        # turn that takes it home. Both are computed from the state rather than
        # written down, so editing the scramble cannot make the narration lie.
        target = (1, -1, 0)                       # the DR slot: white on orange
        here = cm.find_piece(cube.state, target)
        first = sv.ida(cube.state, lambda s: sv.solved_at(s, [target]), 3)
        assert len(first) == 1, f"expected a one-turn placement, got {first}"

        self.nar.cue(self, "s1.place")
        ring = cube.mark(here, C_TRACK)
        ring.set_stroke(opacity=0.0)
        # One Dimmer instance, dimmed and restored. Building a second one to
        # restore with would snapshot the *dimmed* opacities and restore the
        # stage to them - the cube would stay dark for the rest of the video.
        dim = Dimmer(cube.others([here]))
        self.play(*dim.to(0.3), ring.animate.set_stroke(opacity=1.0),
                  run_time=0.8)
        hold(self, 1.0)
        self.play(*dim.restore(), run_time=0.5)
        self.play(cube.turn_anim(first[0], run_time=0.9))
        cube.check("§1 first edge placed")
        assert cube.state[cm.SLOT_INDEX[target]] == cm.IDENT
        self.nar.finish(self)

        # The next white edge, and the shortest way to fetch it.
        second_slot = (0, -1, -1)                 # DB: white on blue
        fetch = sv.ida(cube.state,
                       lambda s: sv.solved_at(s, [second_slot]), 4)
        source = cm.find_piece(cube.state, second_slot)

        self.nar.cue(self, "s1.next")
        dim = Dimmer(cube.others([source, target]))
        self.play(*dim.to(0.28), run_time=0.8)
        hold(self, 1.0)
        self.play(*dim.restore(), run_time=0.5)
        self.nar.finish(self)

        # ...and it costs the piece that was already finished. Verified before
        # it is shown: a demonstration of a failure that does not fail is worse
        # than no demonstration.
        after = cm.apply(cube.state, fetch)
        assert after[cm.SLOT_INDEX[target]] != cm.IDENT, (
            "the fetch does not disturb the placed edge; §1 has no failure "
            "to show")
        self.nar.cue(self, "s1.break")
        self.play(cube.run_anim(fetch, per_move=0.75),
                  run_time=0.75 * len(fetch))
        cube.check("§1 first edge broken")
        self.nar.finish(self)

        # Fifteen seconds of narration over a frozen cube is the longest
        # still frame in the video, and verify_render.py check [3] called it:
        # 14.2s frozen. So show the claim rather than saying it -- one layer
        # lit, turned, and turned back. It costs nothing (the state is exactly
        # where it was) and it is the first sight of §2's whole idea.
        self.cap.show("Every turn moves nine cubies at once.", "s1.lesson",
                      hold=False)
        layer = [sl for sl in cm.SLOTS if sl[0] == 1]
        rest = Dimmer(cube.others(layer))
        self.play(*rest.to(0.2), run_time=1.0)
        self.play(cube.turn_anim("R", run_time=1.6))
        self.wait(0.8)
        self.play(cube.turn_anim("R'", run_time=1.6))
        self.play(*rest.restore(), run_time=1.0)
        self.nar.finish(self)

        # The one method that always works, and the reason it is worth
        # nothing: it needs a memory of the scramble. Retracing it is also the
        # first sight of the idea the rest of the video is built on.
        undo = cm.invert(self.scramble + first + fetch)
        self.cap.show("So retrace every move, backwards.", "s1.rewind",
                      hold=False)
        self.play(cube.run_anim(undo, per_move=0.16),
                  run_time=0.16 * len(undo))
        cube.unmark((1, -1, 0))
        cube.check("§1 rewound")
        assert cube.state == cm.SOLVED, "the rewind did not land on solved"
        self.nar.finish(self)

        self.cap.show("Correct, and useless.", "s1.useless")
        spin(self, 2.5, speed=-5.0)

    # ── §2  the detour ───────────────────────────────────────────────────
    def s2_detour(self):
        cube = self.cube
        self.cap.show("A move and its undo cancel.", "s2.idea", hold=False)
        self.play(cube.turn_anim("R", run_time=0.7))
        self.play(cube.turn_anim("R'", run_time=0.7))
        assert cube.state == cm.SOLVED
        self.nar.finish(self)

        corner = (1, -1, 1)          # DFR: the corner that goes out and back
        edge = (1, 0, 1)             # FR: the edge that goes with it
        ring = cube.mark(corner, C_TRACK)
        ring.set_stroke(opacity=0.0)

        move_label = Tex("R").scale(1.1).set_color(C_HUD)
        fix(move_label.move_to(np.array([HUD_X, 2.2, 0]), aligned_edge=LEFT))
        assert_in_frame_3d(self, move_label=move_label)

        self.nar.cue(self, "s2.out")
        self.play(FadeIn(move_label, shift=RIGHT * 0.2),
                  ring.animate.set_stroke(opacity=1.0), run_time=0.5)
        self.play(cube.turn_anim("R", run_time=1.1))
        self.nar.finish(self)

        self.nar.cue(self, "s2.errand")
        move_label = self._relabel(move_label, r"R\;U")
        self.play(cube.turn_anim("U", run_time=1.1))
        self.nar.finish(self)

        self.nar.cue(self, "s2.back")
        move_label = self._relabel(move_label, r"R\;U\;R'")
        self.play(cube.turn_anim("R'", run_time=1.1))
        cube.check("§2 after R U R'")
        self.nar.finish(self)

        # The claim of the section, checked against the model before it is
        # made: exactly these two pieces are not where they started.
        disturbed = [s for s in cm.SLOTS
                     if cube.state[cm.SLOT_INDEX[s]] != cm.IDENT
                     and s[1] != 1]
        assert set(disturbed) == {corner, edge}, (
            f"expected only {corner} and {edge} disturbed below the top "
            f"layer, got {disturbed}")

        self.nar.cue(self, "s2.damage")
        rest = Dimmer(cube.others([corner, edge]))
        self.play(*rest.to(0.16), run_time=1.2)
        # A long dwell on purpose: this frame IS the argument of the section,
        # and it is the only moment in the video where the viewer can count
        # the damage. The line running over it is eleven seconds long.
        self.wait(4.6)
        self.play(*rest.restore(), run_time=1.2)
        self.nar.finish(self)

        self.cap.show("Out, do something, back.", "s2.name", hold=False)
        spin(self, 4.0, speed=-6.0)
        self.nar.finish(self)

        self.nar.cue(self, "s2.four")
        move_label = self._relabel(move_label, r"R\;U\;R'\;U'")
        self.play(cube.turn_anim("U'", run_time=1.0))
        cube.check("§2 after the detour")
        self.nar.finish(self)
        spin(self, 2.5, speed=-5.0)
        self.move_label = move_label
        self.marked_corner = corner

    def _relabel(self, old, tex):
        """Grow the move label a term at a time, in place.

        A new Tex each time, replacement-transformed: repeatedly Transforming
        onto one Tex whose glyph count keeps changing is ANTI-PATTERN #9 and
        smears the letters into each other.
        """
        new = Tex(tex).scale(1.1).set_color(C_HUD)
        fix(new.move_to(np.array([HUD_X, 2.2, 0]), aligned_edge=LEFT))
        assert_in_frame_3d(self, move_label=new)
        self.play(ReplacementTransform(old, new), run_time=0.5)
        return new

    # ── §3  a detour is a loop ───────────────────────────────────────────
    def s3_loop(self):
        cube = self.cube
        counter = Text("1", font=FONT, font_size=54).set_color(C_TRACK)
        fix(counter.move_to(np.array([HUD_X + 0.25, 1.05, 0])))
        times = Text("times", font=FONT, font_size=22).set_color(C_HUD)
        fix(times.next_to(counter, DOWN, buff=0.18))
        assert_in_frame_3d(self, counter=counter, times=times)

        self.nar.cue(self, "s3.claim")
        self.play(FadeIn(counter, scale=0.7), FadeIn(times), run_time=0.6)
        spin(self, 5.0, speed=-5.0)
        self.nar.finish(self)

        n = 1

        def run(n_reps, per_move, beat):
            nonlocal counter, n
            self.nar.cue(self, beat)
            for _ in range(n_reps):
                self.play(cube.run_anim(DETOUR, per_move=per_move),
                          run_time=per_move * len(DETOUR))
                n += 1
                counter = self._recount(counter, n)
            self.nar.finish(self)

        run(2, 0.28, "s3.run")
        run(3, 0.28, "s3.solved")
        assert n == 6, f"the narration says six times; ran {n}"

        # The claim: not nearly solved, solved.
        cube.check("§3 six detours")
        assert cube.state == cm.SOLVED, (
            "(R U R' U') six times did not return the cube")
        spin(self, 4.5, speed=-5.0)      # let it be solved, with nothing said

        self.play(FadeOut(self.move_label), FadeOut(counter), FadeOut(times),
                  run_time=0.6)
        cube.unmark(self.marked_corner)
        self.cap.clear(run_time=0.5)

    def _recount(self, old, n):
        """Advance the tally. The count is carried as an int by the caller.

        Reading the number back out of the mobject and adding one would make
        the picture the source of truth for the picture, which is exactly the
        kind of loop that lets a display drift away from what happened.
        """
        new = Text(str(n), font=FONT, font_size=54).set_color(C_TRACK)
        fix(new.move_to(old))
        self.play(ReplacementTransform(old, new), run_time=0.25)
        return new

    # ── §4  the method ───────────────────────────────────────────────────
    def s4_method(self):
        cube = self.cube
        self.nar.cue(self, "s4.plan")
        self.play(cube.run_anim(self.scramble, per_move=0.13),
                  run_time=0.13 * len(self.scramble))
        cube.check("§4 rescrambled")

        # "Build the bottom layer by hand, then never touch it again" is the
        # whole plan, so show which layer that is. The camera goes underneath
        # once, here, and stays there for the cross -- the white face is the
        # one thing the standard three-quarter view cannot show, and this is
        # the section that is about it.
        #
        # This beat also exists because verify_render.py check [3] found a
        # 12.6s still frame here. Worth recording why it took a second pass to
        # find: under the previous geometry the z-fighting itself churned
        # enough pixels to keep the frame-to-frame delta above the freeze
        # threshold. Fixing the seams is what let the real defect show up.
        orbit(self, theta=THETA, phi=PHI_UNDER, run_time=1.8)
        bottom = [sl for sl in cm.SLOTS if sl[1] == -1]
        upstairs = Dimmer(cube.others(bottom))
        self.play(*upstairs.to(0.2), run_time=1.0)
        hold(self, 2.0)
        self.play(*upstairs.restore(), run_time=1.0)
        spin(self, 3.0, speed=-5.0)
        self.nar.finish(self)

        counter = Text("0 moves", font=FONT, font_size=26).set_color(C_HUD)
        fix(counter.move_to(np.array([HUD_X, -3.3, 0]), aligned_edge=LEFT))
        assert_in_frame_3d(self, counter=counter)
        self.play(FadeIn(counter), run_time=0.4)

        # One caption, one camera instruction and one pace per stage. The
        # solution is the solver's, unedited: this is a real 99-move
        # layer-by-layer solve of the scramble in §0.
        plan = [
            ("cross", "s4.cross", "The white cross.", 0.40, None),
            ("corners", "s4.corners", "The four white corners.", 0.42, PHI),
            ("middle", "s4.middle", "The middle layer.", 0.30, None),
            ("yellow-cross", "s4.yellowcross", "The yellow cross.", 0.24, None),
            ("yellow-face", "s4.yellowface", "The whole yellow face.", 0.26,
             None),
            ("place-corners", "s4.place", "Into place.", 0.22, None),
        ]
        stages = {key: moves for key, _, moves in self.solution}
        done = 0
        for key, beat, text, pace, phi in plan:
            moves = list(stages[key])
            if key == "place-corners":       # the last two stages share a line
                moves += stages["place-edges"]

            self.cap.show(text, beat, hold=False)
            if phi is not None:
                orbit(self, theta=THETA, phi=phi, run_time=1.5)
            self.play(cube.run_anim(moves, per_move=pace),
                      run_time=pace * len(moves))
            cube.check(f"§4 {key}")
            done += len(moves)
            counter = self._retally(counter, done)
            self.nar.finish(self)

        assert cube.state == cm.SOLVED, "the solve did not solve the cube"
        self.play(FadeOut(counter), run_time=0.5)
        self.counter_total = done

    def _retally(self, old, n):
        new = Text(f"{n} moves", font=FONT, font_size=26).set_color(C_HUD)
        fix(new.move_to(old, aligned_edge=LEFT))
        self.play(ReplacementTransform(old, new), run_time=0.35)
        return new

    # ── §5  payoff ───────────────────────────────────────────────────────
    def s5_payoff(self):
        total = sum(len(m) for _, _, m in self.solution)
        assert total == 99, f"the narration says 99 moves; the solve is {total}"

        self.cap.show("Ninety-nine moves.", "s5.count", hold=False)
        spin(self, 4.0, speed=-6.0)
        self.nar.finish(self)

        # Restate the opening question verbatim, in the styling it had then.
        question = Text(QUESTION, font=FONT, font_size=30).set_color(C_TEXT)
        fix(question.move_to(np.array([0, -3.25, 0])))
        assert_in_frame_3d(self, question=question)
        self.cap.clear(run_time=0.4)
        self.nar.cue(self, "s5.restate")
        self.play(Write(question), run_time=1.6)
        self.nar.finish(self)

        answer = Text("Not positions.  Detours.", font=FONT, font_size=38)
        answer.set_color(C_TRACK)
        fix(answer.move_to(np.array([0, 3.25, 0])))
        assert_in_frame_3d(self, answer=answer)
        self.nar.cue(self, "s5.answer")
        self.play(Write(answer), run_time=1.6)
        self.nar.finish(self)

        # Close on the image the video opened with: the count, and now the
        # thing that is actually small.
        count = Tex(r"43{,}252{,}003{,}274{,}489{,}856{,}000")
        count.scale(0.62).set_color(C_HUD)
        fix(count.move_to(np.array([0, -3.25, 0])))
        seven = Text("7 sequences", font=FONT, font_size=30).set_color(C_TRACK)
        fix(seven.move_to(np.array([0, -2.55, 0])))
        assert_in_frame_3d(self, count=count, seven=seven)

        self.nar.cue(self, "s5.close")
        self.play(FadeOut(question, shift=DOWN * 0.2), run_time=0.5)
        self.play(Write(count), run_time=1.4)
        self.play(FadeIn(seven, shift=UP * 0.2), run_time=0.8)
        self.nar.finish(self)

        spin(self, 5.0, speed=-5.0)
        self.play(FadeOut(answer), FadeOut(count), FadeOut(seven),
                  FadeOut(self.cube.group, scale=0.9), run_time=1.4)
        self.wait(0.6)
