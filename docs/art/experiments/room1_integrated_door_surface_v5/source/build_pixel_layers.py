"""Build a door-specific wear map from Room 1's approved r6 wall palette.

The wall's broad mineral variation is reused at 80 texels/m. Its floor-height
grime silhouette is deliberately excluded: that silhouette describes a fixed
wall touching the floor, not a moving door leaf. New aging follows seals and
the inset status window, with only a narrow bottom contact line.
"""
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[3]
SOURCE = ROOT / "docs/art/experiments/room1_seam_contact_r6/source/wall_layers"
LAYERS = HERE / "source/layers"
OUT = ROOT / "assets/art/room1_integrated_door_surface_v5"
LAYERS.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
SIZE = (112, 184)
REGION = (956, 65, 1068, 249)

base = Image.new("RGBA", SIZE, (0, 0, 0, 0))
for name in ("base", "quiet_mineral_plane", "structure", "joints", "top_deposit", "joint_seal_film", "base_contact"):
    layer = Image.open(SOURCE / f"rear_{name}.png").convert("RGBA").crop(REGION)
    assert layer.size == SIZE
    base = Image.alpha_composite(base, layer)

# The approved door's 1-pixel moving edges and functional status inset remain.
details = Image.open(ROOT / "docs/art/experiments/room1_integrated_door_v3/source/layers/seal_and_status_window.png").convert("RGBA")
assert details.size == SIZE

age = Image.new("RGBA", SIZE, (0, 0, 0, 0))
d = ImageDraw.Draw(age)
# Seal compression and past sliding contact leave small, directional marks.
# These live on the edge, never as floating random stains on the panel face.
d.polygon([(1, 24), (2, 24), (2, 62), (3, 62), (3, 79), (1, 79)],
          fill=(102, 125, 119, 90))
d.polygon([(109, 74), (110, 74), (110, 122), (108, 122), (108, 139), (110, 139), (110, 156), (109, 156)],
          fill=(104, 127, 121, 82))
d.polygon([(1, 127), (3, 127), (3, 162), (4, 162), (4, 181), (1, 181)],
          fill=(110, 132, 126, 66))
# Dust can remain in the recess of the status inset without marking its screen.
d.line((48, 73, 64, 73), fill=(113, 133, 125, 100), width=1)
d.line((64, 62, 64, 72), fill=(116, 137, 129, 70), width=1)
# Bottom gasket touches the floor; a slim contact band is plausible, not a
# diffuse dark stain rising up the entire leaf.
d.rectangle((3, 181, 108, 182), fill=(126, 145, 135, 76))

named = (("mineral_panel", base), ("seal_and_status", details), ("localized_contact_age", age))
composed = Image.new("RGBA", SIZE, (0, 0, 0, 0))
for name, layer in named:
    layer.save(LAYERS / f"{name}.png")
    composed = Image.alpha_composite(composed, layer)
composed.save(OUT / "door_front.png")  # provisional; Aseprite writes final
print("DOOR_V5_LAYERS", SIZE, "source_region", REGION)
