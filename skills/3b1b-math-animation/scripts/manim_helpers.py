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

    Pass `narration` (the actual spoken line) to hold for as long as it takes
    to say. That makes holds vary with content - a uniform wait after every
    beat drags on easy frames and rushes hard ones.
    """

    def __init__(self, scene, y=CAPTION_Y):
        self.scene = scene
        self.y = y
        self.current = None

    def show(self, text, narration=None, size=30, color=WHITE,
             run_time=1.0, morph_from_prev=False):
        new = Text(text, font=FONT, font_size=size).set_color(color)
        new.move_to(np.array([0, self.y, 0]))
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
        if narration:
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
            if kind == "img":
                out.append(m.animate.set_opacity(orig * factor))
            else:
                f, s = orig
                out.append(m.animate
                           .set_fill(opacity=f * factor)
                           .set_stroke(opacity=s * factor))
        return out

    def restore(self):
        return self.to(1.0)


def push_in(scene, target, height=4.0, run_time=1.2):
    """Direct attention by moving the frame, not by adding an arrow.

    Opens a "camera not at rest" window that stays open until pull_back().
    A close-up crops the frame and produces large frame-to-frame deltas -
    from the pixels alone these are indistinguishable from "content fell off
    the edge" and "hard cut". Declaring the window lets verify_render.py stay
    strict everywhere else.
    """
    if not hasattr(scene, "camera_windows"):
        scene.camera_windows = []
    scene._cam_open = round(scene.time, 2)
    scene.play(
        scene.camera.frame.animate.move_to(target).set_height(height),
        run_time=run_time,
    )


def pull_back(scene, run_time=1.2):
    scene.play(
        scene.camera.frame.animate.move_to(ORIGIN).set_height(FRAME_H),
        run_time=run_time,
    )
    if getattr(scene, "_cam_open", None) is not None:
        scene.camera_windows.append([scene._cam_open, round(scene.time, 2)])
        scene._cam_open = None


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
    hits = []
    for i in range(len(live)):
        for j in range(i + 1, len(live)):
            if overlaps(live[i], live[j], pad):
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
