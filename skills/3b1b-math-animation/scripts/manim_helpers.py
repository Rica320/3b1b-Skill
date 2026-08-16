"""
Reusable ManimGL helpers for 3b1b-style explainers.

Copy this next to your scene file and `from manim_helpers import *`.
ManimGL's module loader does not put the scene file's directory on sys.path,
so add this at the top of the scene file first:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))

Every helper here exists because a specific defect shipped without it. See
references/anti_patterns.md for the failure each one prevents.
"""

from manimlib import *
import numpy as np


# ─────────────────────────────────────────────────────────────────────────
# Frame geometry
# ─────────────────────────────────────────────────────────────────────────

FRAME_H = 8.0
FRAME_W = 14.222222
SAFE_X = FRAME_W / 2 - 0.35
SAFE_Y = FRAME_H / 2 - 0.35

FONT = "CMU Serif"
CAPTION_Y = 3.42          # the one band captions live in; nothing else here



# ─────────────────────────────────────────────────────────────────────────
# Safe constructors  —  ANTI-PATTERN #1
#
# ManimGL 1.7.x hard-declares fill_color / stroke_color defaults in the
# __init__ signatures of Dot, Arrow and Circle. A `color=` kwarg lands in
# **kwargs and is then overridden by the explicit default passed up to the
# parent, so it is silently discarded and the mobject renders white/grey/red.
#
#   Dot(ORIGIN, color=ORANGE)        -> RGB(253,255,253)   white
#   Dot(ORIGIN).set_color(ORANGE)    -> RGB(255,123,0)     orange
#
# Always construct through these.
# ─────────────────────────────────────────────────────────────────────────

def dot(point, color, radius=0.075, opacity=1.0):
    d = Dot(point, radius=radius)
    d.set_fill(color, opacity=opacity)
    d.set_stroke(color, width=0, opacity=0)
    return d


def arrow(start, end, color, stroke_width=3.5, buff=0.0, **kw):
    a = Arrow(start, end, buff=buff, stroke_width=stroke_width, **kw)
    a.set_fill(color, opacity=1.0)
    a.set_stroke(color, width=stroke_width, opacity=1.0)
    return a


def circle(radius, color, stroke_width=2.0, fill_opacity=0.0):
    c = Circle(radius=radius)
    c.set_stroke(color, width=stroke_width, opacity=1.0)
    c.set_fill(color, opacity=fill_opacity)
    return c


def label(text, size=24, color=GREY_A, font=FONT):
    return Text(text, font=font, font_size=size).set_color(color)


# ─────────────────────────────────────────────────────────────────────────
# Pacing
# ─────────────────────────────────────────────────────────────────────────

SPEAK_WPS = 2.55        # words per second of delivered narration

# A spoken line does not finish while the caption sits still - it carries on
# over the animations that follow it. This is the fraction of the line
# delivered during the caption's own dwell. Without it every narrated caption
# double-counts its line and the cut runs ~30% long.
NARRATION_COVERAGE = 0.57


def speak_time(narration):
    return len(narration.split()) / SPEAK_WPS + 0.35


def hold(scene, beats=1.0):
    """A comprehension hold. Pace to the eye, not to the clock.

    beats 1.0 = ~0.9s (a simple reveal), 2.0 = ~1.35s (dense frame or peak).
    """
    scene.wait(0.45 + 0.45 * beats)


def stagger(anims, lag_ratio=0.08, **kw):
    """Related elements enter in sequence, never as a simultaneous pop."""
    return LaggedStart(*anims, lag_ratio=lag_ratio, **kw)


def morph(scene, src, dst, run_time=1.0, **kw):
    """Two visuals are the same idea -> the object becomes the other.

    Use instead of FadeOut(src) + FadeIn(dst).
    """
    scene.play(ReplacementTransform(src, dst, **kw), run_time=run_time)
    return dst


class Caption:
    """A single caption slot that never lets two lines share the band.

    ANTI-PATTERN #4: writing a new caption while fading the old one out at
    the same position draws two sentences on top of each other.

    Pass `narration` to hold for as long as the line takes to say:

      - with a `narrator=` attached, it is a **beat id** from script.yaml and
        the hold is the measured length of the synthesised wav, so the caption
        is on screen for exactly as long as the voice is talking. The cue time
        is recorded for mux_audio.py.
      - with no narrator it is the spoken line as prose, and the hold is a
        word-count estimate. Use this only for a silent render.

    Either way the holds vary with content - a uniform wait after every beat
    drags on easy frames and rushes hard ones.

    ANTI-PATTERN #13: in a 3D scene a caption that is not fixed in frame is a
    flat sheet of glyphs lying in the world's xy-plane - the camera tilt skews
    it and the geometry buries it. `fixed=None` fixes captions automatically
    inside a ThreeDScene, which is what you almost always want.
    """

    def __init__(self, scene, y=CAPTION_Y, fixed=None, narrator=None):
        self.scene = scene
        self.y = y
        self.fixed = isinstance(scene, ThreeDScene) if fixed is None else fixed
        self.narrator = narrator
        self.current = None

    def show(self, text, narration=None, size=30, color=WHITE,
             run_time=1.0, morph_from_prev=False, tail=None, hold=True):
        # The cue has to be taken BEFORE the caption is written, not after:
        # the voice starts as the words appear, so the line's clock starts at
        # the first frame of the Write, not at the end of it. Cueing after
        # would put every line ~1.3s late and the drift compounds.
        dur = None
        if narration and self.narrator is not None:
            dur = self.narrator.cue(self.scene, narration)

        new = Text(text, font=FONT, font_size=size).set_color(color)
        new.move_to(np.array([0, self.y, 0]))
        if self.fixed:
            fix(new)
        spent = run_time
        if self.current is None:
            self.scene.play(Write(new), run_time=run_time)
        elif morph_from_prev:
            self.scene.play(ReplacementTransform(self.current, new),
                            run_time=run_time)
        else:
            self.scene.play(FadeOut(self.current, shift=UP * 0.25),
                            run_time=0.35)
            self.scene.play(Write(new), run_time=run_time)
            spent += 0.35
        self.current = new

        if dur is not None:
            # hold=False cues the line and writes the caption but does NOT
            # wait it out: the caller has visuals to play under the rest of
            # the line, and calls narrator.finish() when they are done. Waiting
            # here first would push those visuals past the end of the line.
            if hold:
                t = self.narrator.tail if tail is None else tail
                self.scene.wait(max(0.0, dur + t - spent))
        elif narration and hold:
            self.scene.wait(
                max(0.3, speak_time(narration) * NARRATION_COVERAGE - spent))
        return new

    def clear(self, run_time=0.4):
        if self.current is not None:
            self.scene.play(FadeOut(self.current, shift=UP * 0.25),
                            run_time=run_time)
            self.current = None


# ─────────────────────────────────────────────────────────────────────────
# Attention
# ─────────────────────────────────────────────────────────────────────────

class Dimmer:
    """Push a set of mobjects back, then restore them exactly.

    ANTI-PATTERN #6: do NOT use Group.set_opacity() to dim and un-dim. It
    drives fill and stroke to the SAME value, so anything drawn as an outline
    (fill_opacity=0 - a plot frame, an empty box) returns as a solid block,
    and anything with per-element alpha (a rasterised field, a shaded group)
    is flattened. This snapshots each leaf's own opacities, so restoring is
    lossless.

    ANTI-PATTERN #16: a `Surface` is NOT a VMobject, and neither is a
    TrueDot/GlowDot/DotCloud - a VMobject-only walk skips them silently, so
    dimming a 3D stage leaves the surface at full brightness. They are handled
    here by their own opacity uniform.
    """

    def __init__(self, *mobs):
        self.items = []
        for top in mobs:
            if top is None:
                continue
            for m in top.get_family():
                if isinstance(m, ImageMobject):
                    self.items.append(
                        (m, "img", float(m.data["opacity"][0, 0])))
                elif isinstance(m, (Surface, DotCloud)) and m.has_points():
                    # Not VMobjects: no fill/stroke split, one opacity each.
                    self.items.append((m, "obj", float(m.get_opacity())))
                elif isinstance(m, VMobject) and m.has_points():
                    # get_family() also yields point-less group containers;
                    # set_fill() raises on those, so only take real leaves.
                    #
                    # The float() casts matter: get_fill_opacity() returns
                    # np.float32, which is NOT a subclass of Python float
                    # (np.float64 is). ManimGL's set_fill tests
                    # isinstance(opacity, (float, int)) to choose between a
                    # scalar and a per-point array, so np.float32 takes the
                    # array branch and dies on len() of a 0-d value.
                    self.items.append(
                        (m, "vec", (float(m.get_fill_opacity()),
                                    float(m.get_stroke_opacity()))))

    def to(self, factor):
        out = []
        for m, kind, orig in self.items:
            if kind in ("img", "obj"):
                out.append(m.animate.set_opacity(orig * factor))
            else:
                f, s = orig
                out.append(m.animate
                           .set_fill(opacity=f * factor)
                           .set_stroke(opacity=s * factor))
        return out

    def restore(self):
        return self.to(1.0)


def open_camera_window(scene):
    """Mark the camera as leaving rest. Pair with close_camera_window()."""
    if not hasattr(scene, "camera_windows"):
        scene.camera_windows = []
    if getattr(scene, "_cam_open", None) is None:
        scene._cam_open = round(scene.time, 2)


def close_camera_window(scene):
    if getattr(scene, "_cam_open", None) is not None:
        scene.camera_windows.append([scene._cam_open, round(scene.time, 2)])
        scene._cam_open = None


def push_in(scene, target, height=4.0, run_time=1.2):
    """Direct attention by moving the frame, not by adding an arrow.

    Opens a "camera not at rest" window that stays open until pull_back().
    A close-up crops the frame and produces large frame-to-frame deltas -
    from the pixels alone these are indistinguishable from "content fell off
    the edge" and "hard cut". Declaring the window lets verify_render.py stay
    strict everywhere else.
    """
    open_camera_window(scene)
    scene.play(
        scene.camera.frame.animate.move_to(target).set_height(height),
        run_time=run_time,
    )


def pull_back(scene, run_time=1.2):
    scene.play(
        scene.camera.frame.animate.move_to(ORIGIN).set_height(FRAME_H),
        run_time=run_time,
    )
    close_camera_window(scene)


def dump_meta(scene, path):
    """Write the render sidecar that verify_render.py consumes."""
    import json
    meta = {
        "duration": round(float(scene.time), 2),
        "camera_windows": getattr(scene, "camera_windows", []),
    }
    with open(path, "w") as fh:
        json.dump(meta, fh, indent=2)
    print(f"[META] wrote {path}: {meta}")


# ─────────────────────────────────────────────────────────────────────────
# Equations built from addressable terms  —  ANTI-PATTERN #5
#
# Never index into a Tex glyph array to highlight part of an equation, and
# never index it by the character length of the LaTeX source - the two are
# unrelated, and the resulting box lands on nothing. Build the equation from
# separate Tex objects: each term is then a real mobject you can move,
# colour, box, or transform on its own.
# ─────────────────────────────────────────────────────────────────────────

def equation(*parts, buff=0.22, scale=1.0):
    """equation(term_a, "+", term_b) -> VGroup where each part is addressable."""
    mobs = [Tex(p) if isinstance(p, str) else p for p in parts]
    g = VGroup(*mobs)
    g.arrange(RIGHT, buff=buff)
    g.scale(scale)
    return g


def box_around(mob, color, buff=0.12, stroke_width=2.0):
    r = SurroundingRectangle(mob, buff=buff)
    r.set_stroke(color, width=stroke_width, opacity=1.0)
    r.set_fill(color, opacity=0.0)
    return r


# ─────────────────────────────────────────────────────────────────────────
# Layout safety  —  fail at build time, not in the finished render
# ─────────────────────────────────────────────────────────────────────────

def in_frame(mob, margin=0.0):
    try:
        l, r = mob.get_left()[0], mob.get_right()[0]
        b, t = mob.get_bottom()[1], mob.get_top()[1]
    except Exception:
        return True
    return (l >= -SAFE_X - margin and r <= SAFE_X + margin
            and b >= -SAFE_Y - margin and t <= SAFE_Y + margin)


def assert_in_frame(**named_mobs):
    """Call before self.play for anything positioned relative to something else.

    next_to(x, RIGHT) after x.to_corner(DR) is how content walks off the edge
    unnoticed. This turns that into a build failure with coordinates.
    """
    bad = []
    for name, m in named_mobs.items():
        if m is None:
            continue
        if not in_frame(m):
            bad.append(
                f"  {name}: x[{m.get_left()[0]:.2f},{m.get_right()[0]:.2f}] "
                f"y[{m.get_bottom()[1]:.2f},{m.get_top()[1]:.2f}] "
                f"(safe: x±{SAFE_X:.2f} y±{SAFE_Y:.2f})")
    if bad:
        raise AssertionError("Mobjects outside the safe frame area:\n"
                             + "\n".join(bad))


def overlaps(a, b, pad=0.0):
    ax1, ax2 = a.get_left()[0] - pad, a.get_right()[0] + pad
    ay1, ay2 = a.get_bottom()[1] - pad, a.get_top()[1] + pad
    bx1, bx2 = b.get_left()[0], b.get_right()[0]
    by1, by2 = b.get_bottom()[1], b.get_top()[1]
    return not (ax2 < bx1 or bx2 < ax1 or ay2 < by1 or by2 < ay1)


def assert_no_overlap(pairs, pad=0.0):
    """pairs: list of (name_a, mob_a, name_b, mob_b)

    Purely geometric: it compares bounding boxes and knows nothing about
    visibility, so a mobject you just faded out still counts. Only assert on
    pairs that are on screen at the same time.
    """
    bad = [f"  {na} overlaps {nb}"
           for na, a, nb, b in pairs if overlaps(a, b, pad)]
    if bad:
        raise AssertionError("Overlapping mobjects:\n" + "\n".join(bad))


def audit_text_overlaps(scene, pad=-0.04):
    """Report any two visible text/equation mobjects sharing screen space.

    assert_no_overlap only covers pairs you thought to declare. This walks
    everything actually on screen, so it catches collisions you did not
    predict. Wire it into Scene.wait() behind an env flag:

        def wait(self, *a, **kw):
            r = super().wait(*a, **kw)
            if os.environ.get("AUDIT"): audit_text_overlaps(self)
            return r
    """
    def visibility(m):
        # A Text/Tex container holds its glyphs as submobjects and has no
        # points of its own, so has_points()/get_fill_opacity() on the
        # container are useless - go to the leaves.
        ops = [float(s.get_fill_opacity()) for s in m.get_family()
               if isinstance(s, VMobject) and s.has_points()]
        return max(ops) if ops else 0.0

    # Walk each top-level mobject's FAMILY, not just scene.mobjects. Text and
    # Tex are routinely held inside a VGroup (labels built in a loop, an
    # equation assembled from parts) - those are invisible to a top-level-only
    # scan, which is how a real collision can pass a "0 overlaps" audit.
    live, seen = [], set()
    for top in scene.mobjects:
        for m in top.get_family():
            if (isinstance(m, (Text, Tex)) and id(m) not in seen
                    and m.get_width() > 1e-6 and m.get_height() > 1e-6
                    and visibility(m) > 0.25):
                seen.add(id(m))
                live.append(m)
    # In a 3D scene a mobject's world-space box says nothing about where it
    # lands on screen, so compare projected boxes for anything not fixed in
    # frame. Without this the audit reports a confident zero in exactly the
    # scenes where labels are hardest to place.
    # (screen_bbox returns the world box unchanged for fixed-in-frame
    # mobjects, which is what the shader does too.)
    frame = scene.camera.frame
    box = lambda m: screen_bbox(frame, m)

    hits = []
    for i in range(len(live)):
        for j in range(i + 1, len(live)):
            a, b = box(live[i]), box(live[j])
            if a is None or b is None:
                continue
            if not (a[1] + pad < b[0] or b[1] < a[0] - pad
                    or a[3] + pad < b[2] or b[3] < a[2] - pad):
                hits.append((live[i], live[j]))
    for a, b in hits:
        ta = getattr(a, "get_string", lambda: "?")()[:40]
        tb = getattr(b, "get_string", lambda: "?")()[:40]
        print(f"[OVERLAP] t={scene.time:7.2f}s  {ta!r}  <->  {tb!r}")
    return hits


# ─────────────────────────────────────────────────────────────────────────
# Scalar fields  —  ANTI-PATTERN #7
#
# A grid of translucent Rectangles cannot tile cleanly: overlapping them
# double-blends and draws a bright grid; abutting them leaves antialiasing
# hairlines and draws a dark one. Either way a smooth field renders as a bar
# chart. Rasterise to one ImageMobject instead - no seams, one mobject,
# crisp at any zoom.
# ─────────────────────────────────────────────────────────────────────────

def raster_field(func, x_range, y_range, width, height, center,
                 cache_path, color_hi=TEAL_C, color_lo=ORANGE,
                 mid=0.5, max_opacity=0.34, gamma=1.4, px=560, py=200):
    """Render scalar func(X, Y) -> [0,1] as a seamless translucent image.

    Values at `mid` are fully transparent; deviation from it is what shows.
    Keep max_opacity low - the field is a wash that data sits on top of, not
    a fill that hides it.
    """
    from PIL import Image
    import os
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    xs = np.linspace(x_range[0], x_range[1], px)
    ys = np.linspace(y_range[1], y_range[0], py)   # rows run top->bottom
    X, Y = np.meshgrid(xs, ys)
    d = func(X, Y)

    strength = np.abs(d - mid) / max(mid, 1 - mid)
    alpha = max_opacity * np.clip(strength, 0, 1) ** gamma
    hi = np.array(color_to_rgb(color_hi)) * 255.0
    lo = np.array(color_to_rgb(color_lo)) * 255.0

    rgba = np.zeros((py, px, 4), dtype=np.uint8)
    rgba[..., :3] = np.where((d >= mid)[..., None], hi, lo).astype(np.uint8)
    rgba[..., 3] = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
    Image.fromarray(rgba, mode="RGBA").save(cache_path)

    img = ImageMobject(cache_path)
    img.set_width(width, stretch=True)
    img.set_height(height, stretch=True)
    img.move_to(center)
    return img


def swap_raster(scene, old, new, run_time=1.5, extra=(), behind=()):
    """Cross-dissolve one raster field to another.

    A continuous field reads as re-forming rather than cutting. Pair it with
    a genuine Transform of some line/curve derived from the same data - that
    is what carries object identity through the change.
    """
    new.set_opacity(0.0)
    scene.add(new)
    for m in behind:
        scene.bring_to_front(m)
    scene.play(old.animate.set_opacity(0.0),
               new.animate.set_opacity(1.0),
               *extra, run_time=run_time)
    scene.remove(old)
    return new


# ═════════════════════════════════════════════════════════════════════════
# 3D
#
# Everything below is for scenes rendered from a tilted camera. Subclass
# ThreeDScene, not Scene: it turns on 4x multisampling (3D edges alias badly
# without it), depth-tests everything it adds, and starts the frame at
# theta=-30, phi=70. A plain Scene with a reoriented frame draws in add-order
# instead of depth order, so a curve behind a surface is painted on top of it.
#
# Each helper here was verified against rendered pixels; the measurements are
# in references/anti_patterns.md #13-#17.
# ═════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────
# Fixing 2D overlays into the frame  —  ANTI-PATTERN #13 / #14
# ─────────────────────────────────────────────────────────────────────────

def fix(*mobs):
    """Pin mobjects to the screen: they ignore the camera entirely.

    Two separate things have to happen, and doing only the first is the
    single most common 3D defect:

      1. fix_in_frame()        - the mobject stops living in world space, so
                                 the camera tilt no longer skews it.
      2. deactivate_depth_test() - otherwise the surface in front of it eats
                                 it. Measured: a caption fixed AFTER being
                                 added to a ThreeDScene rendered with its
                                 first four characters missing, because
                                 ThreeDScene.add() had already switched depth
                                 testing on.

    Use for every caption, title, axis-legend and HUD element in a 3D scene.
    Returns the single mobject, or the tuple, so it composes inline.
    """
    for m in mobs:
        m.fix_in_frame()
        m.deactivate_depth_test()
    return mobs[0] if len(mobs) == 1 else mobs


def flat(*mobs):
    """Let a flat 2D mobject sit on top of another one inside a 3D scene.

    ANTI-PATTERN #14: under depth testing an opaque VMobject fill swallows
    anything drawn over it, no matter how far in front it is - a label on a
    filled box vanishes completely, and nudging it 1.0 units toward the
    camera does not bring it back. Turn the depth test off for the layer that
    must stay on top (or for both, if neither has real depth).
    """
    for m in mobs:
        m.deactivate_depth_test()
    return mobs[0] if len(mobs) == 1 else mobs


# ─────────────────────────────────────────────────────────────────────────
# Where does a world point actually land on screen?  —  ANTI-PATTERN #15
#
# assert_in_frame() compares world coordinates against the frame rectangle.
# That is meaningless once the camera is tilted: a label at world x=6.5 can
# be dead centre on screen, and a label at world ORIGIN can be off the edge.
# project() reproduces ManimGL's own projection (view matrix, then the
# perspective divide from emit_gl_Position.glsl) and was checked against
# rendered pixels - four probe points landed within 1px of prediction.
# ─────────────────────────────────────────────────────────────────────────

def project(frame, point):
    """World point -> on-screen coords, in the same units as FRAME_W/FRAME_H.

    Returns (x, y, w). w <= 0 means the point is behind the camera; x and y
    are meaningless there.
    """
    v = frame.to_fixed_frame_point(np.asarray(point, dtype=float))
    w = 1.0 - v[2] * frame.get_scale() / frame.get_focal_distance()
    if w <= 1e-6:
        return np.array([np.nan, np.nan, w])
    return np.array([v[0] / w, v[1] / w, w])


def screen_bbox(frame, mob):
    """(x_min, x_max, y_min, y_max) on screen for a mobject's bounding box.

    Projects the eight corners. Projection is projective, so the projected
    corners contain the projected object - the box is conservative, never
    optimistic.

    A mobject that is fixed in frame skips the view matrix in the shader, so
    its coordinates ARE screen coordinates; projecting it would give a
    confident wrong answer. Those are returned as-is.
    """
    if mob.is_fixed_in_frame():
        return (mob.get_left()[0], mob.get_right()[0],
                mob.get_bottom()[1], mob.get_top()[1])
    pts = np.array([project(frame, c)[:2] for c in mob.get_all_corners()])
    if np.isnan(pts).any():
        return None
    return (pts[:, 0].min(), pts[:, 0].max(),
            pts[:, 1].min(), pts[:, 1].max())


def assert_in_frame_3d(scene, margin=0.0, **named_mobs):
    """assert_in_frame(), but for a scene whose camera is not at rest.

    Call it after the camera reaches the orientation the mobject is meant to
    be read at - a label that is perfectly placed at theta=-30 can be off the
    edge at theta=+40, and only the projection knows.

    Use it on labels, markers and small groups. On a large curved body it
    projects bounding-box corners the body never reaches and reports a false
    positive: measured, a saddle surface whose real pixels stayed well inside
    the frame projected to y=-4.25 against a safe limit of 3.65. Let
    verify_render.py check [1] police the geometry instead.
    """
    frame = scene.camera.frame
    bad = []
    for name, m in named_mobs.items():
        if m is None:
            continue
        box = screen_bbox(frame, m)
        if box is None:
            bad.append(f"  {name}: behind the camera")
            continue
        x0, x1, y0, y1 = box
        if (x0 < -SAFE_X - margin or x1 > SAFE_X + margin
                or y0 < -SAFE_Y - margin or y1 > SAFE_Y + margin):
            bad.append(f"  {name}: screen x[{x0:.2f},{x1:.2f}] "
                       f"y[{y0:.2f},{y1:.2f}] "
                       f"(safe: x±{SAFE_X:.2f} y±{SAFE_Y:.2f})")
    if bad:
        theta, phi, gamma = frame.get_euler_angles() / DEG
        raise AssertionError(
            f"Mobjects outside the safe frame area at "
            f"theta={theta:.0f} phi={phi:.0f} gamma={gamma:.0f}:\n"
            + "\n".join(bad))


# ─────────────────────────────────────────────────────────────────────────
# Camera moves that are arguments  —  ANTI-PATTERN #17
#
# In this style the camera move is not decoration: rotating from top-down to
# oblique is what proves the flat picture was hiding something. Both helpers
# record a camera-motion window into render_meta.json, because a rotating 3D
# frame produces exactly the pixel signature (edge content, big deltas) that
# verify_render.py's checks [1] and [4] are built to catch.
# ─────────────────────────────────────────────────────────────────────────

def orient(scene, theta=None, phi=None, gamma=None, center=None, height=None):
    """Set the viewpoint instantly. Only for the first frame of a scene."""
    scene.camera.frame.reorient(theta, phi, gamma, center, height)


def orbit(scene, theta=None, phi=None, gamma=None, center=None, height=None,
          run_time=2.5, rate_func=smooth):
    """Animate the viewpoint. Angles in degrees; None keeps the current one.

    `phi` is the payload: 0 is straight down (a 3D scene that reads as 2D),
    ~70 is the standard oblique view. Moving between them is the reveal.
    """
    open_camera_window(scene)
    scene.play(
        scene.camera.frame.animate.reorient(theta, phi, gamma, center, height),
        run_time=run_time, rate_func=rate_func,
    )
    close_camera_window(scene)


def spin(scene, seconds, speed=6.0, **play_kwargs):
    """Slow ambient rotation while something else happens (or nothing does).

    speed is degrees per second; keep it under ~10 or the viewer tracks the
    motion instead of the object. Pass animations as `anims=[...]` to run
    them during the spin instead of waiting.
    """
    frame = scene.camera.frame
    open_camera_window(scene)
    frame.add_ambient_rotation(speed * DEG)
    anims = play_kwargs.pop("anims", None)
    if anims:
        scene.play(*anims, run_time=seconds, **play_kwargs)
    else:
        scene.wait(seconds)
    frame.clear_updaters()
    close_camera_window(scene)


# ─────────────────────────────────────────────────────────────────────────
# 3D mobjects
# ─────────────────────────────────────────────────────────────────────────

def surface(func, u_range=None, v_range=None, axes=None, color=BLUE_D,
            opacity=0.85, resolution=(64, 64), shading=(0.3, 0.2, 0.5)):
    """z = func(x, y) as a shaded surface.

    Pass `axes` (a ThreeDAxes) and the surface is built in that axes' units,
    so it lines up with the ticks and with anything from slice_curve(); the
    ranges then default to the axes' own. Without `axes` it is built directly
    in world coordinates.

    Shading is what makes a surface read as a surface: at (0, 0, 0) it renders
    as a flat silhouette and every fold in it disappears. Keep opacity below
    1.0 so the axis behind it stays legible.
    """
    if axes is not None:
        s = axes.get_graph(
            func, color=color, opacity=opacity, resolution=resolution,
            u_range=u_range or tuple(axes.x_range[:2]),
            v_range=v_range or tuple(axes.y_range[:2]),
        )
    else:
        s = ParametricSurface(
            lambda u, v: np.array([u, v, func(u, v)]),
            u_range=u_range, v_range=v_range, resolution=resolution,
        )
        s.set_color(color, opacity=opacity)
    s.set_shading(*shading)
    return s


def mesh_for(surf, resolution=(21, 21), color=GREY_B, width=0.5, opacity=0.4):
    """A wireframe over a surface. This is what gives the eye its depth cue.

    A single-colour surface with no mesh and no moving camera is nearly
    unreadable as a 3D object - the gradient alone does not say which way it
    folds. Keep the mesh faint; it is a texture, not content.
    """
    m = SurfaceMesh(surf, resolution=resolution)
    m.set_stroke(color, width=width, opacity=opacity)
    return m


def dot3d(point, color, radius=0.06, glow=0.0):
    """A dot that stays a dot from any angle.  —  ANTI-PATTERN #13

    A `Dot` is a flat disc lying in the world xy-plane: seen from the default
    3D viewpoint it renders as an ellipse (measured 19x6px, aspect 3.2) and
    from the side it disappears to a line. TrueDot is a true billboard and
    also scales correctly with distance.
    """
    d = TrueDot(np.asarray(point, dtype=float), radius=radius,
                glow_factor=glow)
    d.set_color(color)
    return d


def path3d(func, t_range, color, width=3.0, samples=200):
    """A parametric curve in space, drawn so it does not flatten with the view.

    `t_range` is (start, end) or ManimGL's own (start, end, step).

    set_flat_stroke(False) makes the stroke a ribbon that always turns to face
    the camera; a flat stroke is a flat ribbon lying in a fixed plane, so a
    curve drawn on a surface thins and flickers at grazing angles.
    ThreeDScene.add() applies this too - doing it here means the curve is
    already right before any animation touches it.
    """
    if len(t_range) == 2:
        t_range = (t_range[0], t_range[1], (t_range[1] - t_range[0]) / samples)
    c = ParametricCurve(func, t_range=t_range)
    c.set_stroke(color, width=width, opacity=1.0)
    c.set_flat_stroke(False)
    return c


def slice_curve(axes, func, t_range, direction="x", const=0.0,
                color=YELLOW, width=4.0, lift=0.05):
    """One cross-section of z = func(x, y), as a curve in the axes' 3D space.

    direction="x" traces (t, const, func(t, const)); "y" traces
    (const, t, func(const, t)). Two of these crossing at a point are the whole
    argument for why a 2D slice cannot classify a critical point.

    ANTI-PATTERN #17: a slice curve is by construction coincident with the
    surface it slices, so under the depth test the two fight for every pixel
    and the curve renders in patches or vanishes entirely - measured: the
    y-slice was invisible for its whole 9s on screen. `lift` raises it by that
    many axis units in z, which is always clear of a graph surface because the
    surface has exactly one height per (x, y). Set lift=0 only if the curve is
    not drawn on a surface.
    """
    if direction == "x":
        f = lambda t: axes.c2p(t, const, func(t, const) + lift)
    else:
        f = lambda t: axes.c2p(const, t, func(const, t) + lift)
    return path3d(f, t_range, color, width=width)
