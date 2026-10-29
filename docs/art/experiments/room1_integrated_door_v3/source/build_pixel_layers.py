"""Paint the Room 1 door review surface in addressable pixel layers.

The rejected free-form PixelLab swatch is intentionally not an input. Geometry
and the interactive light states stay separate from this opaque color map.
"""
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
LAYERS = HERE / "source" / "layers"
OUT = HERE.parents[3] / "assets" / "art" / "room1_integrated_door_v3"
LAYERS.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
SIZE = (128, 256)


def blank():
    return Image.new("RGBA", SIZE, (0, 0, 0, 0))


base = Image.new("RGBA", SIZE, "#C2CCC5")
d = ImageDraw.Draw(base)
d.rectangle((3, 3, 124, 125), fill="#C8D0C9")
d.rectangle((4, 126, 123, 255), fill="#C3CDC6")
# The wall's skirting stops at the opening. The moving leaf has a continuous
# face and only a mild, low-level material shift at its floor contact.
d.rectangle((4, 222, 123, 255), fill="#BDC9C2")
d.rectangle((4, 247, 123, 255), fill="#B8C5BE")
# Broad, stepped material differences read as manufactured finish, not stains.
d.polygon([(12, 26), (49, 26), (49, 29), (83, 29), (83, 85),
           (66, 85), (66, 90), (12, 90)], fill="#CAD3CB")
d.polygon([(87, 105), (114, 105), (114, 110), (120, 110),
           (120, 195), (96, 195), (96, 189), (87, 189)], fill="#BBC8C1")

structure = blank()
d = ImageDraw.Draw(structure)
# The narrow moving-leaf seal is carried mainly by model depth. Its painted
# border is a near-tone transition, without a second black outline.
d.rectangle((0, 0, 0, 255), fill=(121, 143, 136, 255))
d.rectangle((127, 0, 127, 255), fill=(121, 143, 136, 255))
# The physical status window is a small, flush inset. Color state is runtime.
d.rectangle((54, 86, 74, 99), fill=(130, 151, 146, 255))
d.rectangle((56, 88, 72, 97), fill=(47, 65, 69, 255))
d.line((56, 88, 72, 88), fill=(105, 130, 129, 255), width=1)
d.line((56, 97, 72, 97), fill=(30, 48, 54, 255), width=1)

age = blank()
d = ImageDraw.Draw(age)
# Continuous edge deposits collect where the leaf rubs its seal; they grow
# toward the floor, then taper inward. No isolated stain blocks at mid-height.
d.polygon([(1, 190), (2, 190), (2, 212), (3, 212), (3, 230),
           (5, 230), (5, 246), (9, 246), (9, 253), (1, 253)],
          fill=(101, 125, 120, 110))
d.polygon([(126, 203), (125, 203), (125, 226), (123, 226),
           (123, 241), (119, 241), (119, 250), (126, 250)],
          fill=(100, 123, 118, 92))
d.line((11, 253, 50, 253), fill=(90, 111, 109, 65), width=1)
d.line((77, 253, 119, 253), fill=(90, 111, 109, 58), width=1)

named = [("mineral_composite_base", base),
         ("seal_and_status_window", structure),
         ("edge_and_contact_age", age)]
image = blank()
for label, layer in named:
    layer.save(LAYERS / (label + ".png"))
    image = Image.alpha_composite(image, layer)
image.save(OUT / "door_front.png")
print("DOOR_PIXEL_LAYERS_READY", SIZE, len(named))
