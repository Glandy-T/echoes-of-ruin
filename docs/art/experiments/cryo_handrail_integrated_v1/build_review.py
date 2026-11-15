"""Assemble and verify actual Godot screenshots for the shape review."""
from html.parser import HTMLParser
import json
from pathlib import Path

from PIL import Image, ImageDraw

folder = Path(__file__).resolve().parent
evidence = folder / "evidence"
records = json.loads((evidence / "capture_record.json").read_text(encoding="utf8"))
assert len(records) == 12
keys = ("resolution", "camera", "ortho_m", "light_energy", "ambient_energy", "zone_factors", "point_light_energies", "albedo", "cut")
for view in ("overview", "grip", "turn", "hero"):
    shots = [record for record in records if record["view"] == view]
    assert len(shots) == 3
    assert {shot["sample"] for shot in shots} == {"A", "B", "C"}
    assert all(shot[key] == shots[0][key] for key in keys for shot in shots)
    for shot in shots:
        with Image.open(evidence / shot["file"]) as image:
            assert image.size == (1280, 720)
            image.verify()

titles = {"a": "A · 原杆件", "b": "B · 原折板", "c": "C · 一体化握持槽"}
markdown = [
    "# 一体化护栏灰模对比", "",
    "三款使用同一灰色和光照，点图查看 1280×720 原图。", "",
    "| A · 原杆件 | B · 原折板 | C · 一体化握持槽 |", "|---|---|---|",
]
web = [
    '<!doctype html><html lang="zh-CN"><meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    '<title>一体化护栏灰模对比</title>',
    '<style>body{max-width:1800px;margin:auto;padding:24px;background:#182226;color:#e2e7e3;font:16px/1.6 system-ui,sans-serif}a{color:#b6dfd5}h1{font-size:clamp(24px,3vw,40px)}h2{margin:36px 0 12px}.row{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}figure{margin:0;background:#263438;padding:8px;border-radius:8px}img{display:block;width:100%;height:auto}figcaption{padding:4px}p{max-width:1000px}@media(max-width:700px){body{padding:12px}.row{grid-template-columns:1fr}}</style>',
    '<h1>一体化护栏｜灰模轮廓对比</h1>',
    '<p>A 为原杆件，B 为原折板，C 为本轮一体化栏体。先比较构件数量、握持凹槽与转角。C 的厚度暂试 80 mm，握持边高 0.90 m，栏顶高 1.10 m。点图看原尺寸。</p>',
    '<p><a href="model/handrail_integrated_v1.blend">Blender 工程</a> · <a href="README.md">尺寸、验证与待看项</a></p>',
]
for view, title in (("overview", "单段轮廓"), ("grip", "握持位置"), ("turn", "折返截段"), ("hero", "游戏方向与人物尺度")):
    web.extend([f"<h2>{title}</h2>", '<div class="row">'])
    if view != "overview":
        markdown.extend(["", f"## {title}", "", "| A | B | C |", "|---|---|---|"])
    markdown.append("| " + " | ".join(
        f'[![{titles[key]}](evidence/{key}_{view}.png)](evidence/{key}_{view}.png)'
        for key in ("a", "b", "c")
    ) + " |")
    for key in ("a", "b", "c"):
        name = f"evidence/{key}_{view}.png"
        web.append(f'<figure><figcaption>{titles[key]}</figcaption><a href="{name}"><img src="{name}" alt="{titles[key]}" width="1280" height="720" loading="lazy"></a></figure>')
    web.append("</div>")
web.extend([
    "<p>前三组是统一剖切的技术视图，最后一组补看人物和遮挡。样段在梯井中心截断。完整净宽、墙侧握轨与双跑安装仍待后续整合检查。</p>",
    '<p><a href="evidence/capture_record.json">Godot 相机与光照记录</a> · <a href="model_manifest.json">模型检查</a></p></html>',
])
markdown.extend(["", "C 是形体候选。完整净宽、墙侧握轨和双跑安装仍待整合检查。",
                 "", "[Blender 工程](model/handrail_integrated_v1.blend) · [尺寸与说明](README.md)"])
(folder / "preview.html").write_text("\n".join(web) + "\n", encoding="utf8")
(folder / "preview.md").write_text("\n".join(markdown) + "\n", encoding="utf8")

sheet = Image.new("RGB", (1440, 300), "#182226")
draw = ImageDraw.Draw(sheet)
for index, key in enumerate(("a", "b", "c")):
    draw.text((index * 480 + 10, 8), key.upper(), fill="#e2e7e3")
    with Image.open(evidence / f"{key}_overview.png") as image:
        sheet.paste(image.convert("RGB").resize((480, 270), Image.Resampling.LANCZOS), (index * 480, 30))
sheet.save(evidence / "overview_comparison.png", optimize=True)

class Links(HTMLParser):
    def handle_starttag(self, tag, attributes):
        for key, value in attributes:
            if key in ("src", "href"):
                assert (folder / value).exists(), value

Links().feed("\n".join(web))
print("12 Godot captures verified. Camera, light and material settings match across all three samples.")
