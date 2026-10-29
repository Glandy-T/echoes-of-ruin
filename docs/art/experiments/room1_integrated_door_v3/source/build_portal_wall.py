"""Recompose the Room 1 rear wall around its existing central door opening.

The r6 mineral/age layers stay intact outside the door bay. Only the joint
that ran through the door header is replaced by joints at the actual jambs
and a shallow header-to-jamb construction seam. No room geometry moves.
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/art/experiments/room1_seam_contact_r6/source/wall_layers"
LAYERS = HERE / "source/portal_wall_layers"
OUT = ROOT / "assets/art/room1_integrated_door_v3/wall_rear_portal.png"
LAYERS.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)

ORDER = ["base", "quiet_mineral_plane", "structure", "joints", "top_deposit",
         "lower_accumulation", "joint_seal_film", "base_contact"]
layers = {name: Image.open(SOURCE / f"rear_{name}.png").convert("RGBA") for name in ORDER}
assert all(layer.size == (1648, 272) for layer in layers.values())

# World mapping is 80 texels/m: x=(world_x-0.2)*80. The real wall opening is
# x=9.8..11.2 m, so its jambs land at texels 768 and 880. The old repetitive
# seam at 816 bisected the 1.4 m header and made the opening look cut later.
opening_left, opening_right, obsolete_joint = 768, 880, 816
joint = layers["joints"]
film = layers["joint_seal_film"]
for layer, start, end in ((joint, 812, 820), (film, 800, 832)):
    ImageDraw.Draw(layer).rectangle((start, 44, end, 248), fill=(0, 0, 0, 0))

dj = ImageDraw.Draw(joint)
for center in (opening_left, opening_right):
    # Half-width structural joint at the jamb, joined to the existing wall
    # panel rhythm without a second applied border around the moving leaf.
    for dx, color in ((-2, "#A5B4A8"), (-1, "#647C7A"),
                      (0, "#536B6B"), (1, "#94A8A0")):
        dj.line((center + dx, 44, center + dx, 248), fill=color)

# The header bottom is at world y=2.4 m, v=(1-2.4/3.4)*272 ≈ 80. This shallow
# horizontal construction seam physically meets both jambs, instead of
# running a vertical panel joint through the middle of the door.
dj.line((opening_left, 79, opening_right, 79), fill="#738986", width=1)
dj.line((opening_left, 80, opening_right, 80), fill="#BBC6B8", width=1)

df = ImageDraw.Draw(film)
# Deposits remain attached to the new jamb seals and grow toward the floor.
# The two sides differ to avoid mirrored grime or detached dark patches.
df.polygon([(opening_left-1, 172), (opening_left-5, 172),
            (opening_left-5, 205), (opening_left-8, 205),
            (opening_left-8, 243), (opening_left-1, 243)], fill="#AAB7AA")
df.polygon([(opening_right+1, 186), (opening_right+5, 186),
            (opening_right+5, 216), (opening_right+8, 216),
            (opening_right+8, 246), (opening_right+1, 246)], fill="#ADB9AB")

result = Image.new("RGBA", (1648, 272), (0, 0, 0, 0))
for name in ORDER:
    layers[name].save(LAYERS / f"{name}.png")
    result = Image.alpha_composite(result, layers[name])
# Use the exact running r6 raster as the base. Re-compositing every pixel in
# Pillow changes a few far corner pixels by 1 RGB step versus the Aseprite
# readback, which would risk the previously fixed four-wall corner continuity.
baseline = Image.open(ROOT / "assets/art/room1_seam_contact_r6/wall_rear.png").convert("RGB")
candidate = result.convert("RGB")
patch = Image.new("RGBA", baseline.size, (0, 0, 0, 0))
bp, cp, pp = baseline.load(), candidate.load(), patch.load()
for y in range(44, 249):
    for x in range(752, 897):
        if cp[x, y] != bp[x, y]:
            pp[x, y] = (*cp[x, y], 255)
finished = Image.alpha_composite(baseline.convert("RGBA"), patch).convert("RGB")
assert finished.crop((0, 0, 752, 272)).tobytes() == baseline.crop((0, 0, 752, 272)).tobytes()
assert finished.crop((897, 0, 1648, 272)).tobytes() == baseline.crop((897, 0, 1648, 272)).tobytes()
assert finished.crop((0, 0, 1648, 44)).tobytes() == baseline.crop((0, 0, 1648, 44)).tobytes()
assert finished.crop((0, 249, 1648, 272)).tobytes() == baseline.crop((0, 249, 1648, 272)).tobytes()
baseline.convert("RGBA").save(LAYERS / "baseline_rear.png")
patch.save(LAYERS / "portal_bay_overlay.png")
finished.save(OUT)
print("PORTAL_WALL_READY", OUT, "opening_px", opening_left, opening_right)
