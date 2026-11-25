"""Export the four original, unretouched PixelLab poses for review."""
import ast
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
BACKGROUND = "#414548"
SCALE = Image.Resampling.NEAREST


def read_layer(archive, project, frame, layer):
    cel = project["frames"][frame - 1]["cels"][layer - 1]
    size = ast.literal_eval(cel["image_size"].removeprefix("Vector2i"))
    offset = ast.literal_eval(cel["offset"])
    pixels = archive.read(f"image_data/frames/{frame}/layer_{layer}")
    image = Image.new("RGBA", (project["size_x"], project["size_y"]))
    image.paste(Image.frombytes("RGBA", size, pixels), offset)
    return image


def matte(image):
    canvas = Image.new("RGB", image.size, BACKGROUND)
    canvas.paste(image, mask=image.getchannel("A"))
    return canvas


def export():
    with ZipFile(ROOT / "walk_r3_pilot.pxo") as archive:
        project = json.loads(archive.read("data.json"))
        layers = [layer["name"] for layer in project["layers"]]
        assert len(project["frames"]) == 5 and project["size_x"] == project["size_y"] == 128
        ref = read_layer(archive, project, 1, layers.index("Layer 1") + 1)
        original = Image.open(ROOT.parent / "protagonist_five_idle_eyes_r3/final_90.png").convert("RGBA")
        assert matte(ref).tobytes() == matte(original).tobytes()
        poses = []
        for frame in (3, 2, 5, 4):
            pose = read_layer(archive, project, frame, layers.index("PixelLab - Generation") + 1)
            assert pose.getbbox()
            poses.append(pose)
    sheet = Image.new("RGB", (4 * 256, 280), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    for i, (frame, pose) in enumerate(zip((3, 2, 5, 4), poses)):
        sheet.paste(matte(pose).resize((256, 256), SCALE), (i * 256, 0))
        draw.text((i * 256 + 8, 260), f"{'CONTACT' if i % 2 == 0 else 'PASS'}  /  PXO {frame}", fill="white")
    sheet.save(ROOT / "poses.png")
    return original, poses


def contact_toes(pose):
    feet = np.asarray(pose)[116:, :, 3] > 127
    assert not feet[:, 58].any()
    return [int(np.nonzero(feet[:, :58])[1].min()), 58 + int(np.nonzero(feet[:, 58:])[1].min())]


def darken_far_leg(pose):
    # At the second contact the forward leg is behind the gown and near leg.
    pixels = np.array(pose)
    leg = pixels[83:, :58]
    original = leg.copy()
    for light, dark in [
        ((230, 189, 151), (175, 142, 126)),
        ((197, 168, 145), (175, 142, 126)),
        ((190, 153, 129), (153, 128, 123)),
        ((175, 142, 126), (153, 128, 123)),
    ]:
        mask = (original[:, :, :3] == light).all(axis=2) & (original[:, :, 3] == 255)
        leg[mask, :3] = dark
    return Image.fromarray(pixels)


def loop(frames, filename, period):
    ticks = [round(i * period * 100 / len(frames)) for i in range(len(frames) + 1)]
    durations = [10 * (b - a) for a, b in zip(ticks, ticks[1:])]
    frames[0].save(ROOT / filename, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, disposal=2)
    with Image.open(ROOT / filename) as saved:
        assert saved.n_frames == len(frames) and saved.info["loop"] == 0
        for i, ms in enumerate(durations):
            saved.seek(i)
            assert saved.info["duration"] == ms


def render_review():
    _, raw = export()
    front, opposite = (contact_toes(raw[i]) for i in (0, 2))
    steps = [opposite[1] - front[0], front[1] - opposite[0]]
    meters = [px * 1.65 / 125 for px in steps]
    period = sum(meters) / 1.1
    poses = raw.copy()
    poses[2] = darken_far_leg(raw[2])
    for label, images in [("pilot", poses), ("raw", raw)]:
        loop([matte(p).resize((256, 256), SCALE) for p in images], label + ".gif", period)

    # Compare drawings at matched phases; both columns use the r3 review clock.
    r2 = ROOT.parent / "protagonist_walk_side_r2"
    comparison = []
    for old_index, new in zip((1, 3, 4, 6), poses):
        old = Image.open(r2 / f"cycle_{old_index:02}.png").convert("RGBA")
        panel = Image.new("RGB", (512, 280), BACKGROUND)
        for x, pose, label in [(0, old, "r2  /  text"), (256, new, "r3  /  skeleton")]:
            panel.paste(matte(pose).resize((256, 256), SCALE), (x, 24))
            ImageDraw.Draw(panel).text((x + 10, 6), label, fill="white")
        comparison.append(panel)
    loop(comparison, "r2_r3_phases.gif", period)
    print("Contact toes, step px, step meters, period, pilot fps, 12-frame fps:")
    print(front, opposite, steps, meters, period, len(poses) / period, 12 / period)


if __name__ == "__main__":
    render_review()
