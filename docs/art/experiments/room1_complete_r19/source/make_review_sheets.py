"""Arrange actual Godot screenshots for QA; never modifies the original frames."""
from pathlib import Path
from PIL import Image, ImageDraw

base = Path(__file__).resolve().parents[1]
frames = base / "evidence" / "complete"

def sheet(names, columns, output):
    width, height = 400, 248
    canvas = Image.new("RGB", (columns*width, ((len(names)+columns-1)//columns)*height), "#171f21")
    draw = ImageDraw.Draw(canvas)
    for index, name in enumerate(names):
        x, y = (index % columns)*width, (index // columns)*height
        original = Image.open(frames / f"{name}.png").convert("RGB")
        original.thumbnail((400, 225), Image.Resampling.NEAREST)
        canvas.paste(original, (x, y+23))
        draw.text((x+8, y+5), name, fill="#dde2df")
    canvas.save(base / "evidence" / output)

sheet([f"pod_P{number:02d}" for number in range(1,21)], 4, "pods_all_20.png")
sheet(["corner_rear_left","corner_rear_right","corner_front_left","corner_front_right",
       "door_header","front_wall_lamp","floor_contacts","glass_closed_tubes_on",
       "glass_hidden","glass_tubes_off","raw_corner","denoised_corner"], 3, "lighting_checks.png")
