"""Make the door face from Room 1's actual approved r6 mineral pixel surface.

The 112x184 canvas gives about 80 texels per metre in both directions, the
same physical density as the walls. Only door-specific seal/indicator marks
are added; all broad mineral variation and low-edge aging come from r6.
"""
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
PROJECT = HERE.parents[3]
LAYERS = HERE / "source/layers"
OUT = PROJECT / "assets/art/room1_integrated_door_v3"
LAYERS.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)

SIZE = (112, 184)
WALL_SOURCE = PROJECT / "assets/art/room1_seam_contact_r6/wall_rear.png"
wall = Image.open(WALL_SOURCE).convert("RGBA")
assert wall.size == (1648, 272)
# This seam-free interval is one original wall bay. It carries the same broad
# mineral planes and the same floor-connected age contour as the room walls.
base = wall.crop((956, 65, 1068, 249))
assert base.size == SIZE

structure = Image.new("RGBA", SIZE, (0, 0, 0, 0))
d = ImageDraw.Draw(structure)
# A moving leaf needs a narrow seal, but no heavy outer frame or extra panels.
d.line((0, 0, 0, 183), fill=(105, 129, 124, 255), width=1)
d.line((111, 0, 111, 183), fill=(105, 129, 124, 255), width=1)
# The physically separate eye-height status quad sits inside this small inset.
d.rectangle((49, 62, 63, 72), fill=(131, 153, 145, 255))
d.rectangle((51, 64, 61, 70), fill=(47, 65, 69, 255))
d.line((51, 64, 61, 64), fill=(105, 130, 129, 255), width=1)
d.line((51, 70, 61, 70), fill=(30, 48, 54, 255), width=1)

age = Image.new("RGBA", SIZE, (0, 0, 0, 0))
d = ImageDraw.Draw(age)
# A sliding seal adds continuous operation wear toward its lower contacts.
# The source wall already supplies the main broad aging; do not add spots.
d.polygon([(1, 118), (2, 118), (2, 145), (3, 145),
           (3, 166), (4, 166), (4, 183), (1, 183)],
          fill=(112, 136, 129, 86))
d.polygon([(110, 138), (109, 138), (109, 158), (108, 158),
           (108, 176), (107, 176), (107, 183), (110, 183)],
          fill=(111, 134, 127, 70))

named = [("mineral_composite_base", base),
         ("seal_and_status_window", structure),
         ("edge_and_contact_age", age)]
result = Image.new("RGBA", SIZE, (0, 0, 0, 0))
for name, layer in named:
    layer.save(LAYERS / f"{name}.png")
    result = Image.alpha_composite(result, layer)
result.save(OUT / "door_front.png")  # provisional; Aseprite writes final blend
print("DOOR_PIXEL_LAYERS_FROM_R6", SIZE, "wall_crop=(956,65,1068,249)")
