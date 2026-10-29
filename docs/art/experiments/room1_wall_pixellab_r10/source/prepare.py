"""Crop the existing wall and prepare a structure-preserving PixelLab mask."""
from pathlib import Path
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
full = Image.open(ROOT / "assets/art/room1_seam_contact_r6/wall_left.png").convert("RGBA")
sample = full.crop((128, 16, 384, 272))
sample.save(HERE / "guide.png")
full.save(HERE / "wall_left_baseline.png")
mask = Image.new("L", sample.size, 0)
d = ImageDraw.Draw(mask)
d.rectangle((8,28,247,232), fill=255)
for x in (48,176):
    d.rectangle((x-1,28,x,232), fill=0)
mask.save(HERE / "mask.png")
print("Wall sample", sample.size, "global columns 128:384 rows16:272; light, seal cores and boundaries preserved")
