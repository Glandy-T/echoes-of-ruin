"""Align walk inputs to the standing sole line and quantize to B's actual palette."""
from pathlib import Path
import numpy as np
from PIL import Image

root = Path(__file__).resolve().parent
reference = np.asarray(Image.open(root.parent / "protagonist_front_c_raw_v2/B_original.png").convert("RGBA"))
palette = np.unique(reference[reference[:, :, 3] == 255, :3], axis=0)
assert len(palette) == 17
for index in range(1, 9):
    original = Image.open(root / f"render_{index:02}.png").convert("RGBA")
    left, top, right, bottom = original.getbbox()
    crop = original.crop((left, top, right, bottom))
    height = min(125, max(123, crop.height))
    crop = crop.resize((crop.width, height), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (128, 128))
    canvas.paste(crop, (left, 127 - height))
    pixels = np.array(canvas)
    assert set(np.unique(pixels[:, :, 3])) == {0, 255}
    visible = pixels[:, :, 3] == 255
    delta = pixels[visible, :3].astype("int32")[:, None, :] - palette
    pixels[visible, :3] = palette[(delta ** 2).sum(axis=2).argmin(axis=1)]
    pixels[~visible] = 0
    Image.fromarray(pixels).save(root / f"input_{index:02}.png")
