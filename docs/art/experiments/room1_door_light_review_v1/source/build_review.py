"""Contact sheets and preview.html for the door light review v1.

Run from repo root with Python 3.11 + Pillow:
    python docs/art/experiments/room1_door_light_review_v1/source/build_review.py
"""
import pathlib
from PIL import Image, ImageDraw

HERE = pathlib.Path(__file__).resolve().parents[1]
EV = HERE / "evidence"

def sheet(items, box, scale, out):
    ims = [Image.open(EV / f).convert("RGB").crop(box) for f, _ in items]
    ims = [i.resize((i.width * scale, i.height * scale), Image.NEAREST) for i in ims]
    w, h = ims[0].size
    c = Image.new("RGB", (len(ims) * (w + 12) - 12, h + 28), (19, 27, 28))
    d = ImageDraw.Draw(c)
    for k, (im, (_, label)) in enumerate(zip(ims, items)):
        c.paste(im, (k * (w + 12), 28)); d.text((k * (w + 12) + 4, 6), label, fill=(217, 227, 222))
    c.save(EV / out)

sheet([("near_1_idle.png", "1 idle"), ("near_2_scanning_lit.png", "2 scanning (lit)"), ("near_3_denied_red.png", "3 denied"),
       ("near_5_open_pass_r17_core.png", "4 pass - r17 core"), ("near_5_open_pass_r18_soft.png", "5 pass - r18 soft")],
      (430, 0, 850, 720), 1, "sheet_states_near.png")
sheet([("game_5_open_pass_r17_core.png", "r17 core"), ("game_5_open_pass_r18_soft.png", "r18 soft glow")],
      (500, 80, 780, 400), 3, "sheet_pass_game_r17_r18.png")

fig = lambda s, c: f'<figure><figcaption>{c}</figcaption><a href="evidence/{s}"><img src="evidence/{s}" loading="lazy"></a></figure>'
names = [("1_idle", "待机"), ("2_scanning_lit", "认证中（黄闪亮相）"), ("3_denied_red", "拒绝（红）"),
         ("5_open_pass_r17_core", "通行 · r17 硬灯芯"), ("5_open_pass_r18_soft", "通行 · r18 柔光")]
html = ['<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Room 1 门灯审图 v1</title>',
        '<style>body{background:#131b1c;color:#d9e3de;font:16px/1.6 system-ui;margin:24px auto;padding:0 20px;max-width:1600px}a{color:#a7d3d8}.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}figure{margin:0;background:#202b2c;padding:8px}img{display:block;width:100%;height:auto;image-rendering:pixelated}h2{font-size:19px;margin-top:26px}</style>',
        '<h1>Room 1 门灯审图 v1（r32 门）</h1><p>现有 r17 内侧灯芯与 r18 柔光，在已确认的 r32 门上重新同机位截图。本页没有改动任何灯光、颜色或节奏。<a href="README.md">说明</a></p>',
        '<h2>先看：五个状态（近景）</h2>', fig("sheet_states_near.png", "待机 ｜ 认证黄闪 ｜ 拒绝红 ｜ 通行 r17 ｜ 通行 r18"),
        '<h2>通行状态，游戏镜头放大：r17 硬灯芯 vs r18 柔光</h2>', fig("sheet_pass_game_r17_r18.png", "r17 ｜ r18")]
for key, cap in names:
    html.append(f'<h2>{cap}</h2><div class="row">{fig("game_" + key + ".png", "游戏镜头")}{fig("near_" + key + ".png", "近景")}</div>')
html.append(f'<h2>开启中（斜侧）</h2><div class="row">{fig("oblique_4_opening_r17_core.png", "r17")}{fig("oblique_4_opening_r18_soft.png", "r18")}</div>')
html.append(f'<h2>认证黄闪的暗相</h2>{fig("near_2_scanning_dark_phase.png", "黄闪暗相")}</html>')
(HERE / "preview.html").write_text("\n".join(html), encoding="utf-8")
