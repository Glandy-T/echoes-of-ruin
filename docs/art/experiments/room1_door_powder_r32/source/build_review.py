"""Build r32 review crops, measurements and preview.html from the Godot captures.

Run from the repository root with Python 3.11 + Pillow + NumPy:
    python docs/art/experiments/room1_door_powder_r32/source/build_review.py
"""
import json, pathlib
import numpy as np
from PIL import Image, ImageFilter

HERE = pathlib.Path(__file__).resolve().parents[1]
EV = HERE / "evidence"
ROOT = HERE.parents[3]
MODES = [("1_a", "A r30"), ("2_b", "B r31"), ("3_c", "C r32 粉末涂层")]

def crop_row(names, box, scale, out):
    ims = [Image.open(EV / n).convert("RGB").crop(box) for n in names]
    ims = [i.resize((i.width * scale, i.height * scale), Image.NEAREST) for i in ims]
    c = Image.new("RGB", (sum(i.width for i in ims) + 16 * (len(ims) - 1), ims[0].height), (19, 27, 28))
    x = 0
    for i in ims:
        c.paste(i, (x, 0)); x += i.width + 16
    c.save(EV / out)

crop_row([f"{p}_game_door_closed.png" for p, _ in MODES], (470, 80, 810, 390), 2, "compare_game_door.png")
crop_row([f"{p}_door_front_close.png" for p, _ in MODES], (380, 60, 900, 660), 1, "compare_close.png")
tex = [Image.open(ROOT / p).convert("RGB") for p in ("assets/art/room1_door_window_r30/door_front.png",
                                                      "assets/art/cryo_building_review_v1/textures/M05-L.png",
                                                      "assets/art/room1_door_powder_r32/door_front.png")]
tex[1] = tex[1].crop((12, 52, 124, 236))
c = Image.new("RGB", (112 * 3 + 32, 184), (19, 27, 28))
for k, t in enumerate(tex):
    c.paste(t, (k * 128, 0))
c.resize((c.width * 3, c.height * 3), Image.NEAREST).save(EV / "compare_textures.png")

def bands(name):
    im = np.asarray(Image.open(EV / name).convert("RGB")).astype(float)
    door = im[130:340, 580:700]; wall = np.concatenate([im[130:340, 470:555], im[130:340, 725:790]], 1)
    return [[round(door[y:y+35, :, 1].mean(), 1), round(wall[y:y+35, :, 1].mean(), 1)] for y in range(0, 210, 35)]

def grain(name):
    g = Image.open(EV / name).convert("L"); a = np.asarray(g).astype(float)
    hp = a - np.asarray(g.filter(ImageFilter.GaussianBlur(12))).astype(float)
    return {"door_local_std": round(hp[60:600, 470:820].std(), 2), "wall_local_std": round(hp[60:600, 180:420].std(), 2),
            "door_mean": round(a[60:600, 470:820].mean(), 1), "wall_mean": round(a[60:600, 180:420].mean(), 1)}

report = {
    "game_camera_green_by_band_top_to_bottom_[door,wall]": {lab: bands(f"{p}_game_door_closed.png") for p, lab in MODES},
    "front_camera_grain": {lab: grain(f"{p}_door_wall_front.png") for p, lab in MODES},
}
(HERE / "source/measurements.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(report["front_camera_grain"], ensure_ascii=False))

fig = lambda src, cap: f'<figure><figcaption>{cap}</figcaption><a href="evidence/{src}"><img src="evidence/{src}" loading="lazy"></a></figure>'
html = ['<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Room 1 门 r32 粉末涂层</title><style>body{background:#131b1c;color:#d9e3de;font:16px/1.6 system-ui;margin:24px auto;padding:0 20px;max-width:1700px}a{color:#a7d3d8}.row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}figure{margin:0;background:#202b2c;padding:8px}img{display:block;width:100%;height:auto;image-rendering:pixelated}h2{font-size:19px;margin-top:28px}@media(max-width:900px){.row{grid-template-columns:1fr}}</style>',
        '<h1>Room 1 · 门 r32：M05-L 粉末涂层钢板</h1>',
        '<p>A＝r30，B＝r31（r30贴图＋贴墙着色器），C＝r32（M05-L粉末涂层底材＋r30暗痕迹／密封边／小窗，经r31着色器以r32参数显示）。门形、UV、动画、认证灯、绿灯柔光与房间光照不变；PixelLab新生成0次。正式F5未切换。<a href="README.md">说明与测量</a></p>',
        '<h2>先看这两张：游戏镜头门区（左A／中B／右C）、近景</h2>', fig("compare_game_door.png", "A r30 ｜ B r31 ｜ C r32"),
        fig("compare_close.png", "近景 A ｜ B ｜ C"),
        '<h2>贴图原生像素（左 r30 ／中 M05-L 原生裁片 ／右 r32）</h2>', fig("compare_textures.png", "r30 ｜ M05-L (12,52) 112×184 ｜ r32")]
for key, cap in [("game_door_closed", "游戏镜头·关门"), ("door_wall_front", "门墙正面"), ("door_wall_oblique", "门墙斜侧"),
                 ("door_front_close", "门近景"), ("door_oblique_close", "门斜侧近景")]:
    html.append(f'<h2>{cap}</h2><div class="row">' + "".join(fig(f"{p}_{key}.png", lab) for p, lab in MODES) + "</div>")
html.append('<h2>C 的认证与开门状态</h2><div class="row">')
for key, cap in [("scanning_yellow_window", "认证黄窗"), ("opening_green_reveal", "开启中绿灯"), ("game_door_open", "游戏镜头·门开"), ("open_green_soft_glow", "开门柔光")]:
    html.append(fig("3_c_" + key + ".png", cap))
html.append("</div></html>")
(HERE / "preview.html").write_text("\n".join(html), encoding="utf-8")
