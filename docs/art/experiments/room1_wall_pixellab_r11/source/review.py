from pathlib import Path
from PIL import Image
import json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
OUT=ROOT/"assets/art/room1_wall_pixellab_r11"
report={"legacy_aging_layers_used":[],"new_pixel_source":"PixelLab inpaint-v3","walls":{}}
for wall in ("left","right","front","rear"):
    base=Image.open(HERE/f"clean_{wall}.png").convert("RGBA")
    final=Image.open(OUT/f"wall_{wall}.png").convert("RGBA")
    read=Image.open(HERE/f"readback_{wall}.png").convert("RGBA")
    overlays=Image.open(HERE/f"{wall}_pixellab_layer.png").convert("RGBA")
    source=ROOT/"docs/art/experiments/room1_seam_contact_r6/source/wall_layers"
    expected=Image.open(source/f"{wall}_base.png").convert("RGBA")
    for part in ("structure","joints"):
        expected=Image.alpha_composite(expected,Image.open(source/f"{wall}_{part}.png").convert("RGBA"))
    if wall=="rear":
        from PIL import ImageDraw
        ImageDraw.Draw(expected).rectangle((812,44,819,248),fill=(211,214,201,255))
    corner_ok=all(base.getpixel((x,y))==final.getpixel((x,y)) for x in (0,1,base.width-2,base.width-1) for y in range(272))
    light_ok=base.crop((0,18,base.width,36)).tobytes()==final.crop((0,18,base.width,36)).tobytes()
    diff=sum(base.getpixel((x,y))!=final.getpixel((x,y)) for y in range(272) for x in range(base.width))
    data={"size":list(final.size),"clean_base_matches_structure_only":base.tobytes()==expected.tobytes(),"changed_from_clean":diff,"aseprite_pixel_exact":final.tobytes()==read.tobytes(),"light_strip_exact":light_ok,"corners_exact":corner_ok}
    report["walls"][wall]=data
    assert data["clean_base_matches_structure_only"] and data["aseprite_pixel_exact"] and light_ok and corner_ok
    # Show full wall native layout plus a 2x material crop.
    final.save(EXP/f"evidence/map_{wall}.png")
    if wall=="left":
        final.crop((48,16,304,272)).resize((512,512),Image.Resampling.NEAREST).save(EXP/"evidence/material_new_2x.png")
        base.crop((48,16,304,272)).resize((512,512),Image.Resampling.NEAREST).save(EXP/"evidence/clean_guide_2x.png")
report["N_roundtrip_exact"]=Image.open(EXP/"evidence/technical_after.png").tobytes()==Image.open(EXP/"evidence/technical_restored.png").tobytes()
assert report["N_roundtrip_exact"]
report["usage_generations"]=sum(json.loads((EXP/f"result_{v}.json").read_text())["usage"]["generations"] for v in ("a","b","c","d","portal","portal2"))
(HERE/"quality.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
groups=[("干净输入 → PixelLab 新材质",["clean_guide_2x","material_new_2x"]),("游戏左／中／右，修前 → 修后",[f"game_{s}_{v}" for s in ("left","center","right") for v in ("before","after")]),("近景修前 → 修后",["technical_before","technical_after"]),("颜色诊断修前 → 修后",["base_color_before","base_color_after"]),("四墙新贴图",["map_left","map_right","map_front","map_rear"]),("四角与前墙巡检",["survey_front_left","survey_rear_left","survey_front_right","survey_rear_right","survey_front_full"])]
html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Room 1 四墙全新 PixelLab 材质 r11</title><style>body{margin:28px;background:#141b1d;color:#d3ded6;font:15px/1.5 system-ui}main{max-width:1500px;margin:auto}section{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;padding:10px;background:#202a2b}img{width:100%;display:block;image-rendering:pixelated}h2{margin-top:30px}a{color:#bfd4c4}</style><main><h1>Room 1 四墙 r11：清除旧做旧后，用 PixelLab 统一重做</h1><p>只保留配色与建筑结构。新母版没有旧上沿、墙脚、矩形膜或大块色差图层。<a href="README.md">来源与限制</a>。B键仅切换历史对照。</p>'
for title,names in groups:
    html+='<h2>'+title+'</h2><section>'
    for n in names:html+='<figure><img src="evidence/'+n+'.png"><figcaption>'+n+'</figcaption></figure>'
    html+='</section>'
(EXP/"preview.html").write_text(html+'</main></html>',encoding="utf-8")
print(json.dumps(report))
