"""Mask-align PixelLab's raw texture to the fixed UV and status insert.

No aging marks are drawn here. PixelLab supplies every new material pixel;
the third layer replaces the legacy header while retaining the status insert.
"""
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
ROOT = HERE.parents[4]
OUT = ROOT / "assets/art/room1_integrated_door_pixellab_v7"
OUT.mkdir(parents=True, exist_ok=True)
guide = Image.open(HERE / "guide.png").convert("RGBA")
raw = Image.open(EXPERIMENT / "raw/pixellab_inpaint_v3_revision.png").convert("RGBA")
request_mask = Image.open(HERE / "mask.png").convert("L")
assert guide.size == raw.size == request_mask.size == (112, 184)

# PixelLab created a larger bezel around the status window. Keep the existing
# small functional inset intact; the material detail remains PixelLab output.
final_mask = Image.new("L", guide.size, 0)
cut = ImageDraw.Draw(final_mask)
# The Pro result expanded some fine deposits beyond the submitted narrow mask.
# Keep its complete native clusters instead of chopping them into straight
# vertical strips; only the approved top, outer seal and status stay locked.
cut.rectangle((5, 20, 106, 183), fill=255)
cut.rectangle((38, 54, 74, 84), fill=0)
final_mask.save(HERE / "composite_mask.png")
detail = raw.copy()
detail.putalpha(final_mask)
detail.save(HERE / "pixellab_material_layer.png")
result = Image.alpha_composite(guide, detail)
header_path = EXPERIMENT / "raw/pixellab_inpaint_v3_header.png"
if header_path.exists():
    header = Image.open(header_path).convert("RGBA")
    header_mask = Image.open(HERE / "header_mask.png").convert("L")
    assert header.size == header_mask.size == result.size
    header.putalpha(header_mask)
    header.save(HERE / "pixellab_header_layer.png")
    result = Image.alpha_composite(result, header)
result.save(OUT / "door_front.png")  # Aseprite roundtrip will export the master
print("PIXELLAB_ASSEMBLED", result.size, "pixel_detail_from=PixelLab", "status=original")
