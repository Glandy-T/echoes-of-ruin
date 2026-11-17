"""Build r31 review crops, measurements and preview.html from the Godot captures.

Run with any Python 3.11 that has Pillow + NumPy, from the repository root:
    python docs/art/experiments/room1_door_shader_r31/source/build_review.py
"""
import json, pathlib
import numpy as np
from PIL import Image, ImageFilter

HERE = pathlib.Path(__file__).resolve().parents[1]
EV = HERE / "evidence"
TEX = HERE.parents[3] / "assets/art/room1_door_window_r30/door_front.png"

def crop_pair(a, b, box, scale, out):
    ia, ib = [Image.open(EV / n).convert("RGB").crop(box) for n in (a, b)]
    ia, ib = [i.resize((i.width * scale, i.height * scale), Image.NEAREST) for i in (ia, ib)]
    c = Image.new("RGB", (ia.width * 2 + 16, ia.height), (19, 27, 28))
    c.paste(ia, (0, 0)); c.paste(ib, (ia.width + 16, 0)); c.save(EV / out)

crop_pair("1_a_game_door_closed.png", "2_b_game_door_closed.png", (440, 70, 840, 400), 2, "compare_game_door.png")
crop_pair("1_a_door_wall_front.png", "2_b_door_wall_front.png", (120, 0, 1160, 720), 1, "compare_front.png")

def bands(name):
    im = np.asarray(Image.open(EV / name).convert("RGB")).astype(float)
    door = im[130:340, 580:700]; wall = np.concatenate([im[130:340, 470:555], im[130:340, 725:790]], 1)
    return [[round(door[y:y+35, :, 1].mean(), 1), round(wall[y:y+35, :, 1].mean(), 1)] for y in range(0, 210, 35)]

def grain(name):
    g = Image.open(EV / name).convert("L"); a = np.asarray(g).astype(float)
    hp = a - np.asarray(g.filter(ImageFilter.GaussianBlur(12))).astype(float)
    return {"door_local_std": round(hp[60:600, 470:820].std(), 2), "wall_local_std": round(hp[60:600, 180:420].std(), 2),
            "door_mean": round(a[60:600, 470:820].mean(), 1), "wall_mean": round(a[60:600, 180:420].mean(), 1)}

t = np.asarray(Image.open(TEX).convert("RGB")).astype(float) @ [0.2126, 0.7152, 0.0722]
mode_value = np.bincount(t.round().astype(int).ravel()).argmax()
report = {
    "game_camera_green_by_band_top_to_bottom_[door,wall]": {"A_r30": bands("1_a_game_door_closed.png"), "B_r31": bands("2_b_game_door_closed.png")},
    "front_camera_grain": {"A_r30": grain("1_a_door_wall_front.png"), "B_r31": grain("2_b_door_wall_front.png")},
    "r30_texture_single_colour_share": round(float((t.round() == mode_value).mean()), 3),
    "r30_texture_luma_percentiles_5_25_50_75_95": [round(float(np.percentile(t, p)), 1) for p in (5, 25, 50, 75, 95)],
}
(HERE / "source/measurements.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(report, indent=1, ensure_ascii=False))

pairs = [("game_door_closed", "游戏镜头·关门"), ("door_wall_front", "门墙正面"), ("door_wall_oblique", "门墙斜侧"),
         ("door_front_close", "门近景"), ("door_oblique_close", "门斜侧近景")]
fig = lambda src, cap: f'<figure><figcaption>{cap}</figcaption><a href="evidence/{src}"><img src="evidence/{src}" loading="lazy"></a></figure>'
html = ['<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Room 1 门着色器 r31</title><style>body{background:#131b1c;color:#d9e3de;font:16px/1.6 system-ui;margin:24px auto;padding:0 20px;max-width:1600px}a{color:#a7d3d8}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:#202b2c;padding:10px}img{display:block;width:100%;height:auto;image-rendering:pixelated}h2{font-size:19px;margin-top:28px}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style>',
        '<h1>Room 1 · 门着色器 r31（只改着色器）</h1>',
        '<p>A＝r30（v3门着色器），B＝r31。贴图仍是r30原图，门形、UV、动画、认证灯、绿灯柔光与房间光照不变；PixelLab消耗0。正式F5未切换。<a href="README.md">说明与测量</a></p>',
        '<h2>先看这张：游戏镜头门区放大（左A／右B）</h2>', fig("compare_game_door.png", "A r30 ｜ B r31")]
for key, cap in pairs:
    html.append(f'<h2>{cap}</h2><div class="pair">{fig("1_a_" + key + ".png", "A · r30")}{fig("2_b_" + key + ".png", "B · r31")}</div>')
html.append('<h2>B的认证与开门状态（确认未受影响）</h2><div class="pair">')
for key, cap in [("scanning_yellow_window", "认证黄窗"), ("opening_green_reveal", "开启中绿灯"), ("game_door_open", "游戏镜头·门开"), ("open_green_soft_glow", "开门柔光")]:
    html.append(fig("2_b_" + key + ".png", cap))
html.append('</div></html>')
(HERE / "preview.html").write_text("\n".join(html), encoding="utf-8")
