"""
Reusable ManimGL helpers for 3b1b-style explainers.

Everything here exists because building the GANs video surfaced a specific
failure. See DEFECTS.md for the render evidence behind each one.
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

CAPTION_Y = 3.42          # the one band captions live in; nothing else goes here


# ─────────────────────────────────────────────────────────────────────────
# Safe constructors
#
# ManimGL 1.7.x hard-declares fill_color / stroke_color defaults in the
# __init__ signatures of Dot, Arrow and Circle. A `color=` kwarg lands in
# **kwargs and is then overridden by the explicit default passed up to the
# parent, so it is silently discarded and the mobject renders white/grey/red.
# Verified: Dot(color=ORANGE) -> RGB(253,255,253).
# Always go through these.
# ─────────────────────────────────────────────────────────────────────────

def dot(point, color, radius=0.075, opacity=1.0):
    """A Dot whose colour actually takes."""
    d = Dot(point, radius=radius)
    d.set_fill(color, opacity=opacity)
    d.set_stroke(color, width=0, opacity=0)
    return d


def arrow(start, end, color, stroke_width=3.5, buff=0.0, **kw):
    """An Arrow whose colour actually takes (tip included)."""
    a = Arrow(start, end, buff=buff, stroke_width=stroke_width, **kw)
    a.set_fill(color, opacity=1.0)
    a.set_stroke(color, width=stroke_width, opacity=1.0)
    return a


def circle(radius, color, stroke_width=2.0, fill_opacity=0.0):
    c = Circle(radius=radius)
    c.set_stroke(color, width=stroke_width, opacity=1.0)
    c.set_fill(color, opacity=fill_opacity)
    return c


# ─────────────────────────────────────────────────────────────────────────
# Typography
# ─────────────────────────────────────────────────────────────────────────

FONT = "CMU Serif"


def label(text, size=24, color=GREY_A, font=FONT):
    return Text(text, font=font, font_size=size).set_color(color)


def caption_text(text, size=30, color=WHITE):
    t = Text(text, font=FONT, font_size=size).set_color(color)
    t.move_to(np.array([0, CAPTION_Y, 0]))
    return t


# ─────────────────────────────────────────────────────────────────────────
# Motion grammar
# ─────────────────────────────────────────────────────────────────────────

def stagger(anims, lag_ratio=0.08, **kw):
    """Related elements enter in sequence, never as a simultaneous pop."""
    return LaggedStart(*anims, lag_ratio=lag_ratio, **kw)


SPEAK_WPS = 2.55        # words per second of delivered narration

# A spoken line does not finish while the caption sits still - it carries on
# over the animations that follow it. This is the fraction of the line
# delivered during the caption's own dwell; the rest plays over the next few
# beats. Without it every narrated caption double-counts its own line and the
# cut runs ~30% long.
NARRATION_COVERAGE = 0.57


def speak_time(narration):
    """Seconds it takes to say a line aloud, with a breath at the end."""
    return len(narration.split()) / SPEAK_WPS + 0.35


def hold(scene, beats=1.0):
    """A comprehension hold. Pace to the eye, not to the clock.

    beats: 1.0 = ~0.9s, enough for a simple reveal to land.
           2.0 = ~1.5s, for a dense frame or an emotional peak.
    """
    scene.wait(0.45 + 0.45 * beats)


def morph(scene, src, dst, run_time=1.0, **kw):
    """Two visuals represent the same idea -> the object becomes the other.

    Use instead of FadeOut(src) + FadeIn(dst). Continuity of object identity
    is what makes a sequence read as an argument rather than a slideshow.
    """
    scene.play(ReplacementTransform(src, dst, **kw), run_time=run_time)
    return dst


class Caption:
    """A single caption slot that morphs between lines.

    Fixes the overlap defect: writing a new caption while fading the old one
    out at the same position draws two sentences on top of each other. This
    either transforms glyph-to-glyph (similar text) or clears before writing.
    """

    def __init__(self, scene, y=CAPTION_Y):
        self.scene = scene
        self.y = y
        self.current = None

    def show(self, text, narration=None, size=30, color=WHITE,
             run_time=1.0, morph_from_prev=False):
        """Show a caption, then hold for as long as its narration takes.

        `narration` is the actual spoken line from the script. Passing it
        keeps the cut locked to the voiceover and, more importantly, makes
        the holds *vary with content* - a uniform self.wait(2.0) after every
        beat is what makes a video drag on the easy frames and rush the
        hard ones.
        """
        new = Text(text, font=FONT, font_size=size).set_color(color)
        new.move_to(np.array([0, self.y, 0]))
        spent = run_time
        if self.current is None:
            self.scene.play(Write(new), run_time=run_time)
        elif morph_from_prev:
            self.scene.play(ReplacementTransform(self.current, new),
                            run_time=run_time)
        else:
            # clear first, then write - the two never coexist in the band
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


def focus(scene, spotlight, others, dim=0.22, run_time=0.6):
    """One idea on screen at a time: dim everything not load-bearing.

    Prefer this over deleting context and rebuilding it later.
    """
    anims = []
    for m in others:
        if m is not None and m not in spotlight:
            anims.append(m.animate.set_opacity(dim))
    for m in spotlight:
        if m is not None:
            anims.append(m.animate.set_opacity(1.0))
    if anims:
        scene.play(*anims, run_time=run_time)


def undim(scene, mobs, run_time=0.5):
    anims = [m.animate.set_opacity(1.0) for m in mobs if m is not None]
    if anims:
        scene.play(*anims, run_time=run_time)


class Dimmer:
    """Push a set of mobjects back, then restore them exactly.

    Do NOT use Group.set_opacity() to dim and un-dim. It drives fill and
    stroke to the *same* value, so anything drawn as an outline
    (fill_opacity=0) - a plot frame, an empty box - returns as a solid
    block, and anything with a per-element alpha (a rasterised field) is
    flattened. This snapshots each leaf's own fill/stroke opacity and scales
    it, so restoring is lossless.
    """

    def __init__(self, *mobs):
        self.items = []
        for top in mobs:
            if top is None:
                continue
            for m in top.get_family():
                if isinstance(m, ImageMobject):
                    self.items.append((m, "img", float(m.data["opacity"][0, 0])))
                elif isinstance(m, VMobject) and m.has_points():
                    # get_family() also yields point-less group containers;
                    # set_fill() raises on those, so only take real leaves.
                    #
                    # The float() casts matter: get_fill_opacity() returns
                    # np.float32, which is NOT a subclass of Python float
                    # (np.float64 is). ManimGL's set_fill tests
                    # isinstance(opacity, (float, int)) to decide between a
                    # scalar and a per-point array, so an np.float32 falls
                    # into the array branch and dies on len() of a 0-d value.
                    self.items.append(
                        (m, "vec", (float(m.get_fill_opacity()),
                                    float(m.get_stroke_opacity()))))

    def to(self, factor):
        """Animations scaling every leaf's own opacity by `factor`."""
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

    Opens a "camera is not at rest" window that stays open until pull_back.
    A deliberate close-up crops the frame and produces large frame-to-frame
    deltas - both of which look identical, from the pixels alone, to
    "content fell off the edge" and "hard cut". Declaring the window lets
    post-render checks stay strict everywhere else.
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
        "duration": round(scene.time, 2),
        "camera_windows": getattr(scene, "camera_windows", []),
    }
    with open(path, "w") as fh:
        json.dump(meta, fh, indent=2)
    print(f"[META] wrote {path}: {meta}")


# ─────────────────────────────────────────────────────────────────────────
# Equations built from addressable terms
#
# Never index into a Tex glyph array to highlight part of an equation, and
# never index it by the character length of the LaTeX source - the two are
# unrelated, and the resulting SurroundingRectangle lands on nothing.
# Build the equation from separate Tex objects instead: each term is then a
# real mobject you can move, colour, box or fly across the frame.
# ─────────────────────────────────────────────────────────────────────────

def equation(*parts, buff=0.22, scale=1.0):
    """Assemble Tex parts into one row; each part stays addressable.

    equation(r"\\min_G \\max_D", term_a, "+", term_b) -> VGroup of Tex
    """
    mobs = []
    for p in parts:
        mobs.append(Tex(p) if isinstance(p, str) else p)
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
# Layout safety
# ─────────────────────────────────────────────────────────────────────────

def in_frame(mob, margin=0.0):
    """True if the mobject's bounding box is fully inside the safe area."""
    try:
        l, r = mob.get_left()[0], mob.get_right()[0]
        b, t = mob.get_bottom()[1], mob.get_top()[1]
    except Exception:
        return True
    return (l >= -SAFE_X - margin and r <= SAFE_X + margin
            and b >= -SAFE_Y - margin and t <= SAFE_Y + margin)


def assert_in_frame(**named_mobs):
    """Fail loudly at build time rather than shipping off-frame content.

    Call before self.play for anything positioned relative to another
    mobject - next_to(x, RIGHT) after x.to_corner(DR) is how content walks
    off the edge unnoticed.
    """
    bad = []
    for name, m in named_mobs.items():
        if m is None:
            continue
        if not in_frame(m):
            bad.append(
                f"  {name}: x[{m.get_left()[0]:.2f},{m.get_right()[0]:.2f}] "
                f"y[{m.get_bottom()[1]:.2f},{m.get_top()[1]:.2f}] "
                f"(safe: x±{SAFE_X:.2f} y±{SAFE_Y:.2f})"
            )
    if bad:
        raise AssertionError("Mobjects outside the safe frame area:\n"
                             + "\n".join(bad))


def audit_text_overlaps(scene, pad=-0.04):
    """Report any two text/equation mobjects currently sharing screen space.

    Build-time assert_no_overlap only covers pairs you thought to declare.
    This walks everything actually on screen, so it catches the collisions
    you did not predict - a caption swap landing on a label, an equation
    drifting into a plot. Slightly negative pad tolerates glyph bboxes that
    touch without visually colliding.
    """
    from manimlib import Text, Tex

    def visibility(m):
        # A Text/Tex container holds its glyphs as submobjects and has no
        # points of its own, so m.has_points()/m.get_fill_opacity() on the
        # container are useless - go to the leaves.
        ops = [float(s.get_fill_opacity()) for s in m.get_family()
               if isinstance(s, VMobject) and s.has_points()]
        return max(ops) if ops else 0.0

    # Walk each top-level mobject's FAMILY, not just scene.mobjects. Text and
    # Tex are routinely held inside a VGroup, and those are invisible to a
    # top-level-only scan - which is how a real collision passes a "0
    # overlaps" audit.
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
    if hits:
        for a, b in hits:
            ta = getattr(a, "get_string", lambda: "?")()[:40]
            tb = getattr(b, "get_string", lambda: "?")()[:40]
            print(f"[OVERLAP] t={scene.time:7.2f}s  {ta!r}  <->  {tb!r}")
    return hits


def overlaps(a, b, pad=0.0):
    """Axis-aligned bounding-box overlap test."""
    ax1, ax2 = a.get_left()[0] - pad, a.get_right()[0] + pad
    ay1, ay2 = a.get_bottom()[1] - pad, a.get_top()[1] + pad
    bx1, bx2 = b.get_left()[0], b.get_right()[0]
    by1, by2 = b.get_bottom()[1], b.get_top()[1]
    return not (ax2 < bx1 or bx2 < ax1 or ay2 < by1 or by2 < ay1)


def assert_no_overlap(pairs, pad=0.0):
    """pairs: list of (name_a, mob_a, name_b, mob_b)"""
    bad = [f"  {na} overlaps {nb}"
           for na, a, nb, b in pairs if overlaps(a, b, pad)]
    if bad:
        raise AssertionError("Overlapping mobjects:\n" + "\n".join(bad))


# ─────────────────────────────────────────────────────────────────────────
# The landscape: a scalar field over a plane, plus a 1-D slice through it
#
# This is the carried metaphor object for the GANs video. It is built once
# and transformed for the rest of the run - never torn down and rebuilt.
# ─────────────────────────────────────────────────────────────────────────

def gaussian2(x, y, cx, cy, sx, sy):
    return np.exp(-0.5 * (((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2))


class Landscape:
    """D(x) as a shaded field over image space, with a cross-section below.

    The field is literally the optimal discriminator

        D*(x) = p_data(x) / (p_data(x) + p_G(x))

    so when the generated cloud slides onto the real one, the field flattens
    to 1/2 everywhere as a mathematical consequence, not as an animation
    cheat. The convergence beat is therefore honest.
    """

    # eps is a uniform density floor. It is what stops D from snapping to a
    # hard 0/1 two-tone split away from the clouds: where neither density
    # beats the floor, D sits at 1/2 and the field is transparent. Too small
    # and the "landscape" renders as a flat poster with a knife-edge border.
    def __init__(self, plane, slice_axes, n_cols=56, n_rows=20,
                 slice_y=0.0, eps=0.13):
        self.plane = plane
        self.slice_axes = slice_axes
        self.n_cols, self.n_rows = n_cols, n_rows
        self.slice_y = slice_y
        self.eps = eps
        self.x_min, self.x_max = plane["x_range"]
        self.y_min, self.y_max = plane["y_range"]
        self.cells = None
        self.profile = None

    # -- the model ------------------------------------------------------
    def D(self, x, y, real, fake):
        """real / fake: (cx, cy, sx, sy, weight) tuples or lists of them."""
        pr = self._density(x, y, real)
        pf = self._density(x, y, fake)
        return (pr + self.eps) / (pr + pf + 2 * self.eps)

    @staticmethod
    def _density(x, y, spec):
        if isinstance(spec, tuple):
            spec = [spec]
        return sum(w * gaussian2(x, y, cx, cy, sx, sy)
                   for (cx, cy, sx, sy, w) in spec)

    # -- the field, as a single smooth raster ---------------------------
    #
    # A grid of translucent Rectangles cannot tile cleanly: overlapping them
    # double-blends and draws a bright grid, abutting them leaves
    # antialiasing hairlines and draws a dark one. Either way a smooth
    # height map renders as a bar chart. One rasterised ImageMobject has no
    # seams, is a single mobject, and costs nothing to redraw.
    def field_image(self, real, fake, tag, cache_dir,
                    color_hi=TEAL_C, color_lo=ORANGE, w=560, h=200):
        from PIL import Image
        import os
        os.makedirs(cache_dir, exist_ok=True)
        path = os.path.join(cache_dir, f"field_{tag}.png")

        xs = np.linspace(self.x_min, self.x_max, w)
        ys = np.linspace(self.y_max, self.y_min, h)   # rows run top->bottom
        X, Y = np.meshgrid(xs, ys)
        pr = self._density_arr(X, Y, real)
        pf = self._density_arr(X, Y, fake)
        d = (pr + self.eps) / (pr + pf + 2 * self.eps)

        strength = np.abs(d - 0.5) * 2.0
        alpha = 0.34 * strength ** 1.4
        hi = np.array(color_to_rgb(color_hi)) * 255.0
        lo = np.array(color_to_rgb(color_lo)) * 255.0
        rgb = np.where((d >= 0.5)[..., None], hi, lo)

        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        rgba[..., :3] = rgb.astype(np.uint8)
        rgba[..., 3] = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
        Image.fromarray(rgba, mode="RGBA").save(path)

        img = ImageMobject(path)
        img.set_width(self.plane["width"], stretch=True)
        img.set_height(self.plane["height"], stretch=True)
        img.move_to(self.plane["center"])
        return img

    @staticmethod
    def _density_arr(X, Y, spec):
        if isinstance(spec, tuple):
            spec = [spec]
        tot = np.zeros_like(X, dtype=float)
        for (cx, cy, sx, sy, wt) in spec:
            tot += wt * np.exp(-0.5 * (((X - cx) / sx) ** 2
                                       + ((Y - cy) / sy) ** 2))
        return tot

    # -- legacy cell-grid field (kept for reference; prefer field_image) --
    def build_field(self, real, fake, color_hi=TEAL_C, color_lo=ORANGE):
        cw = (self.x_max - self.x_min) / self.n_cols
        ch = (self.y_max - self.y_min) / self.n_rows
        cells = VGroup()
        for i in range(self.n_cols):
            for j in range(self.n_rows):
                x = self.x_min + (i + 0.5) * cw
                y = self.y_min + (j + 0.5) * ch
                # Cells must abut exactly. Overlapping translucent fills
                # double-blend and draw a bright grid; leaving gaps draws a
                # dark one. Either way the "field" reads as a bar chart.
                r = Rectangle(width=cw, height=ch)
                r.move_to(self.plane["c2p"](x, y))
                r.set_stroke(width=0, opacity=0)
                col, op = self._cell_style(x, y, real, fake,
                                           color_hi, color_lo)
                r.set_fill(col, opacity=op)
                r.gan_xy = (x, y)
                r.gan_color = col          # remembered for the reveal
                r.gan_target = op
                cells.add(r)
        self.cells = cells
        return cells

    def field_reveal(self, lag_ratio=0.018):
        """Wash the field in, column by column, preserving per-cell values.

        Do NOT reveal a field with group.set_opacity(0) -> set_opacity(1):
        that overwrites every cell's individually computed opacity with a
        flat 1.0 (and re-enables stroke, which produces seams between
        cells), turning a soft height map into a hard two-tone poster.
        """
        for r in self.cells:
            r.set_fill(r.gan_color, opacity=0.0)
        cols = []
        for i in range(self.n_cols):
            col_cells = [self.cells[i * self.n_rows + j]
                         for j in range(self.n_rows)]
            cols.append(AnimationGroup(*[
                c.animate.set_fill(c.gan_color, opacity=c.gan_target)
                for c in col_cells
            ]))
        return LaggedStart(*cols, lag_ratio=lag_ratio)

    def _cell_style(self, x, y, real, fake, color_hi, color_lo):
        d = self.D(x, y, real, fake)
        # 0.5 is "undecided" -> invisible. Deviation from 0.5 is what shows.
        # Keep the ceiling low: the field is a wash the data points sit on
        # top of, not a fill that hides them.
        strength = abs(d - 0.5) * 2.0
        col = color_hi if d >= 0.5 else color_lo
        return col, 0.34 * strength ** 1.4

    def field_retarget(self, real, fake, color_hi=TEAL_C, color_lo=ORANGE):
        """Animations that reshape the existing field in place."""
        anims = []
        for r in self.cells:
            x, y = r.gan_xy
            col, op = self._cell_style(x, y, real, fake, color_hi, color_lo)
            r.gan_color, r.gan_target = col, op
            anims.append(r.animate.set_fill(col, opacity=op))
        return anims

    # -- the slice ------------------------------------------------------
    def profile_curve(self, real, fake, color=TEAL_C, stroke_width=4.0):
        ax = self.slice_axes
        g = ax.get_graph(
            lambda x: self.D(x, self.slice_y, real, fake),
            x_range=(self.x_min, self.x_max, 0.05),
        )
        g.set_stroke(color, width=stroke_width, opacity=1.0)
        g.set_fill(opacity=0)
        return g
