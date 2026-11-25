"""Assign run8's skin ramp to the two visible limbs by anatomical side."""
import csv
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from scipy.ndimage import distance_transform_edt, label

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
sys.path.insert(0, str(BASE))
from export_advisor import NEAREST, matte, save_gif
from finish import SKIN

Y, X = np.indices((128, 128))
GROUND = 125
PHASES = ("触地", "下沉", "蹬地", "腾空")


def apply_depth(source, frame):
    original = np.array(source)
    out = original.copy()
    rgb = original[:, :, :3].astype(int)
    red, green, blue = rgb.transpose(2, 0, 1)
    # Bare-limb skin, including the cooler shadow edge in the run8 ramp.
    skin = ((red - green >= 14) | ((red == 111) & (green == 99) & (blue == 93)))
    skin &= original[:, :, 3] > 0
    stats = {}
    for part, region, far_left in (
        ("arm", (Y >= 37) & (Y < 74), frame in (1, 2, 7, 8)),
        ("leg", Y >= 74, frame in (3, 4, 5, 6)),
    ):
        eligible = skin & region
        ids, count = label(eligible, np.ones((3, 3)))
        largest = sorted(range(1, count + 1), key=lambda i: (ids == i).sum(), reverse=True)[:2]
        assert len(largest) == 2 and (ids == largest[1]).sum() >= 15, (frame, part)
        left, right = sorted(largest, key=lambda i: X[ids == i].mean())
        far, near = (left, right) if far_left else (right, left)
        # Small separated edge islands inherit the closest major painted limb.
        is_far = distance_transform_edt(ids != far) < distance_transform_edt(ids != near)
        for side, mask, target, low, high in (
            ("far", eligible & is_far, 4, 1, 5),
            ("near", eligible & ~is_far, 9, 3, 9),
        ):
            tones = np.square(rgb[mask, None, :] - SKIN.astype(int)).sum(axis=2).argmin(axis=1)
            anchor = int(np.quantile(tones, .75, method="nearest"))
            mapped = np.clip(tones + target - anchor, low, high)
            if side == "far" or anchor != target:
                out[mask, :3] = SKIN[mapped]
            stats[f"{side}_{part}_q75"] = int(np.quantile(mapped, .75, method="nearest"))
        assert stats[f"far_{part}_q75"] == 4 and stats[f"near_{part}_q75"] == 9
    assert np.array_equal(out[:, :, 3], original[:, :, 3])
    outside = ~(skin & (Y >= 37))
    assert np.array_equal(out[outside], original[outside])
    return Image.fromarray(out), stats


def pixels(path):
    return Image.open(path).convert("RGBA")


def export():
    folder = HERE / "frames"
    folder.mkdir(exist_ok=True)
    joints = json.loads((BASE.parent / "advisor_lean_mock/joints_rotated.json").read_text(encoding="utf-8-sig"))
    records, frames = [], []
    for n in range(1, 9):
        path = HERE.parent / "frames" / f"{n:02}.png"
        src = pixels(path)
        im, stats = apply_depth(src, n)
        im.save(folder / f"{n:02}.png")
        alpha = np.array(im)[:, :, 3]
        hip = joints[str(n)]["LEFT HIP"][1]
        foot = np.where(alpha[90:, 82:] > 0)[0] if n in (2, 6) else []
        records.append(dict(frame=n, source=path.relative_to(HERE.parent).as_posix(),
                            crown_y=im.getbbox()[1], rig_hip_y=hip,
                            folded_foot_clearance=GROUND - (90 + int(max(foot))) if len(foot) else "",
                            **stats))
        frames.append(im)
    assert [row["crown_y"] for row in records] == [6, 8, 5, 4, 5, 9, 5, 4]
    assert abs(records[1]["folded_foot_clearance"] - records[5]["folded_foot_clearance"]) <= 1
    with (HERE / "measurements.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=records[0])
        w.writeheader()
        w.writerows(records)

    period = 2 * 60 * 1.65 / 125 / 2.5
    for scale in (1, 3):
        side = 128 * scale
        tiles = [matte(im).resize((side, side), NEAREST) for im in frames]
        target = HERE / f"run_{scale}x.gif"
        save_gif(tiles, target, period)
        with Image.open(target) as a, Image.open(HERE.parent / "run_1x.gif") as b:
            assert a.n_frames == 8 and a.info["loop"] == 0
            assert [i.info["duration"] for i in ImageSequence.Iterator(a)] == [i.info["duration"] for i in ImageSequence.Iterator(b)]

    font = ImageFont.truetype("msyh.ttc", 16)
    sheet = Image.new("RGB", (464, 4 * 282), "#414548")
    pen = ImageDraw.Draw(sheet)
    for i, im in enumerate(frames):
        col, row = divmod(i, 4)
        x, y = col * 232, row * 282
        tile = matte(im).crop((17, 0, 127, 128)).resize((220, 256), NEAREST)
        sheet.paste(tile, (x + 5, y + 24))
        pen.text((x + 8, y + 1), f"{i+1:02}  {PHASES[row]}   头顶 y={records[i]['crown_y']}", font=font, fill="white")
    sheet.save(HERE / "paired_steps.png")
    return records


if __name__ == "__main__":
    export()
