"""Build the full and exhaled drawings from D. Coordinates start at zero."""
from pathlib import Path
from shutil import copyfile

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE / "45"
D = HERE.parent / "protagonist_idle_pose_45_r1/D/raw/01.png"
TIMES = [1200, 1600]


def save_loop(frames, path):
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=TIMES,
                   loop=0, disposal=2, optimize=False)


def build():
    OUT.mkdir(exist_ok=True)
    base = Image.open(D).convert("RGBA")
    rgba = np.asarray(base)
    # Broad search interval from the brief. Its unique minimum is below
    # the chest mark and above the cuff; check that before committing the cut.
    difference = {y: int(np.any(rgba[y] != rgba[y-1], axis=1).sum())
                  for y in range(34, 53)}
    cut = min(difference, key=difference.get)
    if cut != 38 or difference[cut] != 3:
        raise ValueError(f"Review cut for the new source: {difference}")
    exhaled = base.copy()
    exhaled.paste((0, 0, 0, 0), (0, 0, base.width, 1))
    exhaled.paste(base.crop((0, 0, base.width, cut)), (0, 1))
    copyfile(D, OUT / "01.png")
    exhaled.save(OUT / "02.png")

    for scale in (1, 3):
        frames = []
        for sprite in (base, exhaled):
            matte = Image.new("RGB", sprite.size, "#555b5e")
            matte.paste(sprite, mask=sprite.getchannel("A"))
            frames.append(matte.resize((128*scale, 128*scale), Image.Resampling.NEAREST))
        save_loop(frames, OUT / f"breath_{scale}x.gif")


def room_loop():
    crops = []
    for i in (1, 2):
        with Image.open(OUT / f"room_{i:02}.png") as shot:
            if shot.size != (1280, 720):
                raise ValueError("Room 1 camera output must be 1280x720")
            crops.append(shot.convert("RGB").crop((535, 244, 745, 510)))
    atlas = Image.new("RGB", (420, 266))
    for i, crop in enumerate(crops):
        atlas.paste(crop, (210*i, 0))
    palette = atlas.quantize(colors=256)
    save_loop([c.quantize(palette=palette, dither=Image.Dither.NONE) for c in crops],
              OUT / "room_native.gif")


if __name__ == "__main__":
    import sys
    if "--room" in sys.argv:
        room_loop()
    else:
        build()
