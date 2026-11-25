"""Compare the first 96×128 old idle cell with the approved sprite and raw draws."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OLD = HERE.parents[3] / "assets/characters/idle.png"
REF = HERE.parent / "protagonist_five_idle_eyes_r3/final_45.png"


def comparison(selections):
    items = [("旧待机首帧", Image.open(OLD).convert("RGBA").crop((0, 0, 96, 128))),
             ("定稿 45°", Image.open(REF).convert("RGBA"))]
    for key, frame in selections:
        path = HERE / key / "raw" / f"{int(frame):02}.png"
        items.append((f"候选 {key}", Image.open(path).convert("RGBA")))
    for scale in (1, 3):
        width = 86 * scale
        sheet = Image.new("RGB", (width * len(items), 134 * scale + 26), "#53595b")
        draw = ImageDraw.Draw(sheet)
        font = ImageFont.truetype("msyh.ttc", 13 if scale == 1 else 19)
        for col, (name, im) in enumerate(items):
            art = im.crop(im.getbbox())
            art = art.resize((art.width * scale, art.height * scale), Image.Resampling.NEAREST)
            left = col * width + (width - art.width) // 2
            bottom = sheet.height - 4 * scale
            sheet.paste(art, (left, bottom - art.height), art)
            draw.text((col * width + width // 2, 3), name, font=font, fill="#f3eee3", anchor="mt")
        sheet.save(HERE / f"compare_{scale}x.png")


if __name__ == "__main__":
    comparison([arg.split("/") for arg in sys.argv[1:]] or [(key, 1) for key in "ABCD"])
