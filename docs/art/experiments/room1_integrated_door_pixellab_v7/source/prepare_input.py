"""Prepare only a structural guide and edit mask; PixelLab creates texture detail."""
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
V5 = ROOT / "docs/art/experiments/room1_integrated_door_surface_v5/source/layers"
V6 = ROOT / "docs/art/experiments/room1_integrated_door_finish_v6/source/layers"
SIZE = (112, 184)

# Keep the approved rear-wall mineral palette, fine upper accumulation, and
# functional status recess. Do not recreate the v6 hand-drawn coarse polygons.
guide = Image.new("RGBA", SIZE, (0, 0, 0, 0))
for path in (V5 / "mineral_panel.png", V6 / "upper_gasket_deposit.png",
             V5 / "seal_and_status.png"):
    layer = Image.open(path).convert("RGBA")
    assert layer.size == SIZE
    guide = Image.alpha_composite(guide, layer)
guide.save(HERE / "guide.png")

# White = PixelLab may redraw. Preserve the fine header, status glass, the
# external seal and the otherwise quiet central ceramic face.
mask = Image.new("RGB", SIZE, "black")
d = ImageDraw.Draw(mask)
for rect in ((5, 22, 106, 38), (5, 39, 17, 169),
             (94, 39, 106, 169), (5, 162, 106, 176),
             (39, 55, 73, 81)):
    d.rectangle(rect, fill="white")
d.rectangle((45, 61, 66, 74), fill="black")
mask.save(HERE / "mask.png")
print("PIXELLAB_INPUT", SIZE, "guide=project-owned", "mask=localized")
