"""One-time asset prep: turn the Olivetti faces dataset into PNGs the
gans_video Manim scenes can load as ImageMobject.

Run once from the gans_video/ directory:
    ../env/bin/python assets/prepare_faces.py

Produces (all under assets/faces/):
    real_00.png .. real_07.png   8 distinct real identities
    fake_blend.png                two identities blended + noise, stands in
                                   for "an imperfect generator output" (there
                                   is no trained GAN in this repo)
    interp_00.png .. interp_08.png  alpha walk between two real identities
                                   (9 frames, t = 0, 1/8, .. 1), for the
                                   latent-interpolation scene's steps=8 loop

Images are upscaled with nearest-neighbor (not smoothed) to keep the
low-res pixelated look, matching the pixel-grid aesthetic already used in
scene00's digit_square().
"""
import numpy as np
from PIL import Image
from sklearn.datasets import fetch_olivetti_faces

OUT_DIR = "assets/faces"
UPSCALE = 6  # 64x64 -> 384x384, nearest-neighbor


def to_png(arr: np.ndarray, path: str) -> None:
    """arr: float64 in [0, 1], shape (64, 64) -> upscaled grayscale PNG."""
    img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), mode="L")
    img = img.resize((64 * UPSCALE, 64 * UPSCALE), Image.NEAREST)
    img.save(path)


def main() -> None:
    import os
    os.makedirs(OUT_DIR, exist_ok=True)

    data = fetch_olivetti_faces()
    images, targets = data.images, data.target

    # 8 distinct identities, first pose each, spread across the id range
    # for visual variety (different people, not different photos of one).
    chosen_ids = np.linspace(0, 39, 8, dtype=int)
    real_faces = []
    for i, pid in enumerate(chosen_ids):
        idx = np.where(targets == pid)[0][0]
        face = images[idx]
        real_faces.append(face)
        to_png(face, f"{OUT_DIR}/real_{i:02d}.png")

    # "Fake": blend two different identities + light gaussian noise.
    # Illustrative only -- there's no trained generator in this repo, this
    # stands in for "a plausible but imperfect generator output."
    rng = np.random.default_rng(0)
    face_a, face_b = real_faces[0], real_faces[3]
    blend = 0.5 * face_a + 0.5 * face_b
    blend = blend + rng.normal(0, 0.03, blend.shape)
    to_png(blend, f"{OUT_DIR}/fake_blend.png")

    # Interpolation walk between two real identities (z1 -> z2), 9 frames
    # (t = 0, 1/8, .. 1) to match scene09's steps=8 loop (range(steps + 1)).
    z1_face, z2_face = real_faces[1], real_faces[5]
    for i, t in enumerate(np.linspace(0, 1, 9)):
        frame = (1 - t) * z1_face + t * z2_face
        to_png(frame, f"{OUT_DIR}/interp_{i:02d}.png")

    print(f"Wrote {8 + 1 + 9} PNGs to {OUT_DIR}/")


if __name__ == "__main__":
    main()
