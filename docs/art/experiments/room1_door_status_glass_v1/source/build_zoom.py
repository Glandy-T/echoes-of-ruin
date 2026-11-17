"""Zoomed status-window sheet: rows old / glass, columns idle, scanning, denied.
Run: python docs/art/experiments/room1_door_status_glass_v1/source/build_zoom.py"""
import pathlib
from PIL import Image
EV = pathlib.Path(__file__).resolve().parents[1] / "evidence"
box = (581, 243, 698, 336)
rows = []
for tag in ("old", "glass"):
    ims = [Image.open(EV / f"near_{s}_{tag}.png").convert("RGB").crop(box) for s in ("1_idle", "2_scanning", "3_denied")]
    ims = [i.resize((i.width * 4, i.height * 4), Image.NEAREST) for i in ims]
    rows.append(ims)
w, h = rows[0][0].size
c = Image.new("RGB", (w * 3 + 24, h * 2 + 12), (19, 27, 28))
for r, ims in enumerate(rows):
    for k, im in enumerate(ims):
        c.paste(im, (k * (w + 12), r * (h + 12)))
c.save(EV / "window_zoom_old_vs_glass.png")
game = [Image.open(EV / f"game_3_denied_{t}.png").convert("RGB").crop((560, 120, 720, 300)) for t in ("old", "glass")]
game = [g.resize((g.width * 4, g.height * 4), Image.NEAREST) for g in game]
c2 = Image.new("RGB", (game[0].width * 2 + 12, game[0].height), (19, 27, 28))
c2.paste(game[0], (0, 0)); c2.paste(game[1], (game[0].width + 12, 0)); c2.save(EV / "game_denied_old_vs_glass.png")
