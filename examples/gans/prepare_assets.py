#!/usr/bin/env python3
"""Generate the face PNGs that `gans.py` loads as `ImageMobject`s.

The images are derived from the Olivetti faces dataset (AT&T Laboratories
Cambridge), fetched at runtime by scikit-learn. They are *not* committed to
this repository — run this script once before rendering:

    python prepare_assets.py

Output (all under assets/faces/, ~150 KB total):

    real_00.png .. real_07.png    eight distinct identities, one pose each
    mean_face.png                 the pixel-wise mean of the whole dataset
    interp_00.png .. interp_08.png  a nine-frame alpha walk between two
                                  identities (t = 0, 1/8, ... 1)

`mean_face.png` is the point of §1 of the script: it is the literal
minimiser of mean pixel-wise distance to the dataset, and it is fog. The
video does not assert that — it shows the actual arithmetic mean.

There is no trained generator anywhere in this repository. The interpolation
walk is a linear blend between two real faces, standing in for what a latent
walk would produce. See docs/DEFECTS.md for why that substitution is honest
here: the beat is about *continuity* of the space, not about sample quality.

Images are upscaled with nearest-neighbour resampling, not smoothing, so the
64x64 source stays visibly pixelated rather than pretending to be hi-res.
"""

from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.datasets import fetch_olivetti_faces

OUT_DIR = Path(__file__).resolve().parent / "assets" / "faces"
UPSCALE = 6          # 64x64 -> 384x384
N_IDENTITIES = 8     # gans.py loads real_00 .. real_07
N_INTERP = 9         # gans.py loads interp_02, interp_04 and interp_08


def to_png(arr: np.ndarray, path: Path) -> None:
    """Write a float array in [0, 1], shape (64, 64), as an upscaled PNG."""
    img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), mode="L")
    img = img.resize((64 * UPSCALE, 64 * UPSCALE), Image.NEAREST)
    img.save(path)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    data = fetch_olivetti_faces()
    images, targets = data.images, data.target

    # Eight distinct people, spread across the id range — different
    # identities, not eight photos of the same person. The video's claim is
    # that real faces occupy a *region*, which needs genuine variety.
    chosen_ids = np.linspace(0, targets.max(), N_IDENTITIES, dtype=int)
    faces = []
    for i, pid in enumerate(chosen_ids):
        face = images[np.where(targets == pid)[0][0]]
        faces.append(face)
        to_png(face, OUT_DIR / f"real_{i:02d}.png")

    # The lowest-loss answer under a pixel-wise score, computed rather than
    # illustrated.
    to_png(images.mean(axis=0), OUT_DIR / "mean_face.png")

    # A straight-line walk between two identities.
    src, dst = faces[1], faces[5]
    for i, t in enumerate(np.linspace(0, 1, N_INTERP)):
        to_png((1 - t) * src + t * dst, OUT_DIR / f"interp_{i:02d}.png")

    print(f"Wrote {N_IDENTITIES + 1 + N_INTERP} PNGs to {OUT_DIR}")


if __name__ == "__main__":
    main()
