"""Paint the approved Room 1 door surface in addressable pixel layers.

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
d.rectangle((4, 126, 123, 230), fill="#C3CDC6")
d.rectangle((3, 231, 124, 255), fill="#AABAB5")
# Broad, stepped material differences read as manufactured finish, not stains.
d.polygon([(12, 26), (49, 26), (49, 29), (83, 29), (83, 85),
           (66, 85), (66, 90), (12, 90)], fill="#CAD3CB")
d.polygon([(87, 105), (114, 105), (114, 110), (120, 110),
           (120, 195), (96, 195), (96, 189), (87, 189)], fill="#BBC8C1")

structure = blank()
d = ImageDraw.Draw(structure)
# One-pixel seal in the opening, without a bright applied frame.
d.rectangle((0, 0, 0, 255), fill=(58, 78, 77, 255))
d.rectangle((127, 0, 127, 255), fill=(58, 78, 77, 255))
d.rectangle((0, 0, 127, 0), fill=(56, 76, 75, 255))
d.rectangle((0, 255, 127, 255), fill=(48, 68, 69, 255))
# The lower service joint matches the rear wall protection-band elevation.
d.line((2, 230, 125, 230), fill=(81, 107, 105, 255), width=1)
d.line((2, 231, 125, 231), fill=(158, 176, 167, 255), width=1)
# The physical status window is a small, flush inset. Color state is runtime.
d.rectangle((54, 86, 74, 99), fill=(130, 151, 146, 255))
d.rectangle((56, 88, 72, 97), fill=(47, 65, 69, 255))
d.line((56, 88, 72, 88), fill=(105, 130, 129, 255), width=1)
d.line((56, 97, 72, 97), fill=(30, 48, 54, 255), width=1)

age = blank()
d = ImageDraw.Draw(age)
# Wear follows seal, lower contact edge, and two hand-height maintenance spots.
# These are authored clusters, never a random speckle pass.
d.polygon([(3, 141), (5, 141), (5, 157), (7, 157), (7, 161),
           (5, 161), (5, 169), (3, 169)], fill=(94, 116, 111, 180))
d.polygon([(122, 122), (125, 122), (125, 150), (123, 150),
           (123, 146), (121, 146), (121, 137)], fill=(90, 110, 108, 170))
d.polygon([(2, 239), (7, 239), (7, 241), (11, 241), (11, 243),
           (2, 243)], fill=(91, 113, 108, 105))
d.polygon([(125, 240), (120, 240), (120, 242), (116, 242),
           (116, 244), (125, 244)], fill=(88, 111, 107, 100))
d.line((6, 252, 122, 252), fill=(83, 105, 103, 95), width=1)

named = [("mineral_composite_base", base),
         ("seal_and_status_window", structure),
         ("edge_and_contact_age", age)]
image = blank()
for label, layer in named:
    layer.save(LAYERS / (label + ".png"))
    image = Image.alpha_composite(image, layer)
image.save(OUT / "door_front.png")
print("DOOR_PIXEL_LAYERS_READY", SIZE, len(named))
