"""Build unmodified review sheets for the approved five-view sprite trial."""
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
B = ROOT.parent / "protagonist_front_c_raw_v2" / "B_original.png"
KEYS = ["B", "0", "45", "90", "135", "180"]
LABELS = ["B 正面参照", "0° 重画", "45° 重画", "90° 重画", "135° 重画", "180° 重画"]
SCALE = 3
CELL = 128 * SCALE
TITLE_H = 42
FONT = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 17)

def source_for(key: str) -> Path:
    return B if key == "B" else ROOT / f"final_{key}.png"

def load_sprite(key: str) -> tuple[Image.Image, tuple[int, int, int, int]]:
    image = Image.open(source_for(key)).convert("RGBA")
    if image.size != (128, 128):
        raise ValueError(f"{key} is {image.size}, expected 128x128")
    box = image.getchannel("A").getbbox()
    if box is None:
        raise ValueError(f"{key} has no visible pixels")
    return image, box

def make_sprite_sheet() -> None:
    out = Image.new("RGB", (CELL * len(KEYS), CELL + TITLE_H), "#30383a")
    draw = ImageDraw.Draw(out, "RGBA")
    boxes: dict[str, tuple[int, int, int, int]] = {}
    for index, (key, label) in enumerate(zip(KEYS, LABELS)):
        sprite, box = load_sprite(key)
        boxes[key] = box
        # Align only the transparent canvas to the bottom visible pixel. No
        # resize, registration, or pixel modification is performed.
        y = 128 - box[3]
        panel = Image.new("RGBA", (128, 128))
        panel.alpha_composite(sprite, (0, y))
        panel = panel.resize((CELL, CELL), Image.Resampling.NEAREST)
        out.paste(panel, (CELL * index, TITLE_H), panel)
        draw.text((CELL * index + CELL // 2, 11), label, fill="white", anchor="mt", font=FONT)

    # Reference lines use B's measured landmarks after bottom alignment.
    # They are review overlays and do not touch the individual PNG files.
    b = boxes["B"]
    landmark_y = {
        "头顶": 128 - b[3] + b[1],
        # B's upper silhouette begins at y=31. Its last warm-ivory gown row
        # is y=86, so the hem guide is placed at y=87 immediately below it.
        "肩": 128 - b[3] + 31,
        "下摆": 128 - b[3] + 87,
    }
    colors = [(130, 205, 190, 150), (241, 203, 116, 160), (162, 188, 230, 160)]
    for (label, y), color in zip(landmark_y.items(), colors):
        line_y = TITLE_H + y * SCALE
        draw.line((0, line_y, out.width, line_y), fill=color, width=1)
        draw.text((3, line_y - 15), label, fill=color, font=FONT)
    out.save(ROOT / "sprites_3x_guides.png")

def make_room_sheet() -> None:
    baseline = Image.open(ROOT / "room_B.png").convert("RGB")
    if baseline.size != (1280, 720):
        raise ValueError("Room capture must be 1280x720")
    crop = (501, 245, 779, 517)
    width = crop[2] - crop[0]
    height = crop[3] - crop[1]
    out = Image.new("RGB", (width * len(KEYS), height + TITLE_H), "#30383a")
    draw = ImageDraw.Draw(out)
    for index, (key, label) in enumerate(zip(KEYS, LABELS)):
        room = Image.open(ROOT / f"room_{key}.png").convert("RGB")
        if room.size != baseline.size:
            raise ValueError(f"room_{key} has unexpected size {room.size}")
        if key != "B":
            changed = ImageChops.difference(baseline, room).getbbox()
            if changed is None or not (525 < changed[0] < changed[2] < 755 and 240 < changed[1] < changed[3] < 520):
                raise ValueError(f"room_{key} changed outside hero area: {changed}")
            print(key, "room delta", changed)
        out.paste(room.crop(crop), (width * index, TITLE_H))
        draw.text((width * index + width // 2, 11), label, fill="white", anchor="mt", font=FONT)
    out.save(ROOT / "room_compare.png")

if __name__ == "__main__":
    make_sprite_sheet()
    make_room_sheet()
