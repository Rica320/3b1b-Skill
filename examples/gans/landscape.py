"""The carried metaphor of the GANs video: D(x) as a landscape over image space.

Everything general — safe constructors, `Caption`, `Dimmer`, `raster_field`,
the frame assertions — lives in the skill's `manim_helpers.py` and is imported
from there. This module holds only what is specific to *this* video: the
discriminator model, and the two ways it is drawn.
"""

from manimlib import *
import numpy as np

from manim_helpers import raster_field

# A uniform density floor added to both sides of the ratio below. It is what
# stops D from snapping to a hard 0/1 two-tone split away from the clouds:
# where neither density beats the floor, D sits at 1/2 and the field is
# transparent. Too small and the "landscape" renders as a flat poster with a
# knife-edge border.
DENSITY_FLOOR = 0.13

# Gaussian components are described as (cx, cy, sigma_x, sigma_y, weight).
Component = tuple


class Landscape:
    """D(x) as a shaded field over image space, with a cross-section below.

    The field is literally the optimal discriminator

        D*(x) = p_data(x) / (p_data(x) + p_G(x))

    so when the generated cloud slides onto the real one, the field flattens
    to 1/2 everywhere as a mathematical consequence, not as an animation
    cheat. The convergence beat is therefore honest: nothing is keyframed,
    the picture follows from moving the cloud.

    `plane` describes the region of screen the field covers:
        {"x_range", "y_range", "width", "height", "center", "c2p"}
    `slice_axes` is the Axes the 1-D profile is drawn on.
    """

    def __init__(self, plane, slice_axes, slice_y=0.0, eps=DENSITY_FLOOR):
        self.plane = plane
        self.slice_axes = slice_axes
        self.slice_y = slice_y
        self.eps = eps
        self.x_min, self.x_max = plane["x_range"]
        self.y_min, self.y_max = plane["y_range"]

    # -- the model ------------------------------------------------------
    def D(self, x, y, real, fake):
        """Optimal discriminator at (x, y). Accepts scalars or arrays.

        real / fake: a Gaussian component tuple, or a list of them.
        """
        pr = self._density(x, y, real)
        pf = self._density(x, y, fake)
        return (pr + self.eps) / (pr + pf + 2 * self.eps)

    @staticmethod
    def _density(x, y, spec):
        if isinstance(spec, tuple):
            spec = [spec]
        total = np.zeros_like(np.asarray(x, dtype=float))
        for cx, cy, sx, sy, weight in spec:
            total = total + weight * np.exp(
                -0.5 * (((x - cx) / sx) ** 2 + ((y - cy) / sy) ** 2))
        return total

    # -- the field, as a single seamless raster -------------------------
    def field_image(self, real, fake, tag, cache_dir,
                    color_hi=TEAL_C, color_lo=ORANGE):
        """The field over the whole plane, as one `ImageMobject`.

        Rasterised rather than tiled from Rectangles — see ANTI-PATTERN #7
        in the skill: a grid of translucent cells cannot tile without either
        double-blending into a bright grid or leaving antialiasing seams.
        """
        return raster_field(
            lambda X, Y: self.D(X, Y, real, fake),
            x_range=(self.x_min, self.x_max),
            y_range=(self.y_min, self.y_max),
            width=self.plane["width"],
            height=self.plane["height"],
            center=self.plane["center"],
            cache_path=f"{cache_dir}/field_{tag}.png",
            color_hi=color_hi, color_lo=color_lo,
        )

    # -- the slice ------------------------------------------------------
    def profile_curve(self, real, fake, color=TEAL_C, stroke_width=4.0):
        """The same D, along the horizontal line y = slice_y."""
        graph = self.slice_axes.get_graph(
            lambda x: float(self.D(x, self.slice_y, real, fake)),
            x_range=(self.x_min, self.x_max, 0.05),
        )
        graph.set_stroke(color, width=stroke_width, opacity=1.0)
        graph.set_fill(opacity=0)
        return graph
