"""Preserve the current v7 baseline and prepare a top-only PixelLab mask."""
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
image = Image.open(ROOT / "assets/art/room1_integrated_door_pixellab_v7/door_front.png").convert("RGBA")
assert image.size == (112, 184)
target = HERE / "header_guide.png"
if target.exists():
    raise RuntimeError("Header baseline already exists; do not overwrite provenance")
image.save(target)
mask = Image.new("L", image.size, 0)
ImageDraw.Draw(mask).rectangle((1, 0, 110, 31), fill=255)
mask.save(HERE / "header_mask.png")
