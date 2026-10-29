"""Place the existing Room 1 door in a wider, original rear-wall panel bay.

The r6 wall already has a 3.2 m panel span between joints around the door.
Only the repetitive joint drawn through the small header is removed. The
surrounding wall, lamp, lower guard and aged surface stay pixel-identical.
"""
from pathlib import Path
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/art/experiments/room1_seam_contact_r6/source/wall_layers"
LAYERS = HERE / "source/portal_wall_layers"
OUT = ROOT / "assets/art/room1_integrated_door_v3/wall_rear_portal.png"
LAYERS.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)

baseline = Image.open(ROOT / "assets/art/room1_seam_contact_r6/wall_rear.png").convert("RGB")
assert baseline.size == (1648, 272)

# Reconstruct the original mineral surface without its seam/film layers. The
# nearest remaining original joints are x=688 and x=944, making a 3.2 m-wide
# construction bay with the 1.4 m personnel door near its center. No new
# jamb-to-ceiling lines or foreign colors are painted.
plain_layers = ["base", "quiet_mineral_plane", "structure",
                "top_deposit", "lower_accumulation", "base_contact"]
plain = Image.new("RGBA", baseline.size, (0, 0, 0, 0))
for name in plain_layers:
    layer = Image.open(SOURCE / f"rear_{name}.png").convert("RGBA")
    assert layer.size == baseline.size
    plain = Image.alpha_composite(plain, layer)
plain = plain.convert("RGB")

# x=816 was a regular panel seam through the separate header. The header
# occupies world y=2.4..3.4 m (texture rows 0..80). Restore only that patch;
# the door opening below it has no front wall face to repaint.
patch = Image.new("RGBA", baseline.size, (0, 0, 0, 0))
old, clear, overlay = baseline.load(), plain.load(), patch.load()
for y in range(44, 81):
    for x in range(799, 834):
        if old[x, y] != clear[x, y]:
            overlay[x, y] = (*clear[x, y], 255)
finished = Image.alpha_composite(baseline.convert("RGBA"), patch).convert("RGB")
diff_box = ImageChops.difference(baseline, finished).getbbox()
assert diff_box and diff_box[0] >= 799 and diff_box[2] <= 834
assert diff_box[1] >= 44 and diff_box[3] <= 81

baseline.convert("RGBA").save(LAYERS / "baseline_rear.png")
patch.save(LAYERS / "portal_bay_overlay.png")
finished.save(OUT)
print("DOOR_BAY_READY", OUT, "original_seam_x", 816, "changed", diff_box)
