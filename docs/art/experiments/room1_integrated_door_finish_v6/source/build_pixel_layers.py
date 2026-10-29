"""Create a legible, construction-led Room 1 door age map at 80 texels/m.

Uses the existing room's mineral palette and pixel clusters. The coarse upper
deposit is remapped from the wall's header seam to the door's upper gasket;
seal contact stays on side edges. The face is not filled with random spots.
"""
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[3]
LAYERS = HERE / "source/layers"
OUT = ROOT / "assets/art/room1_integrated_door_finish_v6"
WALL_LAYERS = ROOT / "docs/art/experiments/room1_seam_contact_r6/source/wall_layers"
V5_LAYERS = ROOT / "docs/art/experiments/room1_integrated_door_surface_v5/source/layers"
LAYERS.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
SIZE = (112, 184)

base = Image.open(V5_LAYERS / "mineral_panel.png").convert("RGBA")
details = Image.open(V5_LAYERS / "seal_and_status.png").convert("RGBA")
assert base.size == details.size == SIZE

# The original r6 wall has a pixel-cluster deposit directly under its top
# construction seam. Use that existing language at the door's upper gasket,
# at reduced strength. It does not travel down the face as a drip.
header = Image.new("RGBA", SIZE, (0, 0, 0, 0))
upper = Image.open(WALL_LAYERS / "rear_top_deposit.png").convert("RGBA").crop((956, 44, 1068, 64))
assert upper.size == (112, 20)
upper.putalpha(upper.getchannel("A").point(lambda value: round(value * 0.90)))
header.paste(upper, (0, 0))

wear = Image.new("RGBA", SIZE, (0, 0, 0, 0))
d = ImageDraw.Draw(wear)
# The moving seals and upper gasket retain broad, stepped mineral deposits.
# Larger clusters are intentional: at the fixed game camera a 1-3 px mark on
# this 80 texel/m map vanishes after Room 1's dark emergency-light falloff.
d.polygon([(3, 20), (11, 20), (11, 35), (9, 35), (9, 48), (7, 48),
           (7, 69), (5, 69), (5, 89), (3, 89)], fill=(86, 109, 103, 92))
d.polygon([(3, 23), (7, 23), (7, 62), (5, 62), (5, 105), (3, 105)],
          fill=(67, 88, 82, 92))
d.polygon([(101, 43), (108, 43), (108, 85), (106, 85), (106, 112),
           (103, 112), (103, 125), (101, 125)], fill=(84, 104, 98, 86))
d.polygon([(106, 78), (110, 78), (110, 151), (108, 151), (108, 163),
           (106, 163)], fill=(66, 83, 79, 88))
d.polygon([(3, 123), (7, 123), (7, 145), (10, 145), (10, 165),
           (7, 165), (7, 177), (3, 177)], fill=(78, 98, 91, 104))
# Where the upper gasket meets the sliding leaf, a little settled material
# follows its edge. This is related to the approved wall header, not a random
# patch in the middle of the panel.
d.polygon([(5, 13), (18, 13), (18, 17), (31, 17), (31, 20),
           (48, 20), (48, 22), (62, 22), (62, 19), (77, 19),
           (77, 16), (97, 16), (97, 12), (107, 12), (107, 26),
           (100, 26), (100, 24), (91, 24), (91, 27), (73, 27),
           (73, 29), (49, 29), (49, 26), (30, 26), (30, 24),
           (17, 24), (17, 23), (5, 23)], fill=(98, 119, 111, 76))
# Status insert: dust is retained in the recess and a narrow adjacent strip,
# while the glass itself stays clear enough to read the yellow/green/red state.
d.polygon([(45, 60), (67, 60), (67, 64), (65, 64), (65, 75),
           (46, 75), (46, 72), (43, 72), (43, 63), (45, 63)],
          fill=(87, 105, 99, 88))
d.line((47, 75, 65, 75), fill=(58, 75, 71, 130), width=1)
# Only a narrow lower seal line; the moving leaf does not inherit the fixed
# wall's entire floor-height grime silhouette.
d.polygon([(4, 177), (21, 177), (21, 179), (92, 179),
           (92, 177), (108, 177), (108, 183), (4, 183)],
          fill=(75, 94, 87, 112))

named = (("mineral_panel", base), ("upper_gasket_deposit", header),
         ("seal_and_status", details), ("directional_contact_wear", wear))
composed = Image.new("RGBA", SIZE, (0, 0, 0, 0))
for name, layer in named:
    layer.save(LAYERS / f"{name}.png")
    composed = Image.alpha_composite(composed, layer)
composed.save(OUT / "door_front.png")  # provisional; Aseprite exports final
print("DOOR_V6_LAYERS", SIZE, "upper_original_r6=(956,44,1068,64)")
