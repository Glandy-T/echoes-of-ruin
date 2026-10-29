from pathlib import Path
from PIL import Image
import json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
OUT=ROOT/"assets/art/room1_wall_lamp_r13"
report={"legacy_aging_layers_used":[],"walls":{}}
for wall in ("left","right","front","rear"):
    old=Image.open(HERE/f"baseline_{wall}.png").convert("RGBA")
    new=Image.open(OUT/f"wall_{wall}.png").convert("RGBA")
    read=Image.open(HERE/f"readback_{wall}.png").convert("RGBA")
    changes=[(x,y) for y in range(272) for x in range(new.width) if old.getpixel((x,y))!=new.getpixel((x,y))]
    outside=[(x,y) for x,y in changes if not ((2<=y<=43) or (wall=="rear" and 688<=x<944 and 16<=y<272))]
    data={"changed_pixels":len(changes),"outside_lamp_or_door_bay":len(outside),"aseprite_pixel_exact":new.tobytes()==read.tobytes()}
    assert not outside and data["aseprite_pixel_exact"]
    report["walls"][wall]=data
    if wall=="rear":
        for name,im in (("rear_map_before",old),("rear_map_after",new)):
            im.crop((560,0,1072,272)).resize((1024,544),Image.Resampling.NEAREST).save(EXP/f"evidence/{name}.png")
def same(a,b):return Image.open(EXP/f"evidence/{a}.png").tobytes()==Image.open(EXP/f"evidence/{b}.png").tobytes()
report["N_roundtrip_exact"]=same("technical_after","technical_restored")
report["lamp_power_roundtrip_exact"]=same("lamp_on","lamp_on_restored")
assert report["N_roundtrip_exact"] and report["lamp_power_roundtrip_exact"]
bindings=json.loads((EXP/"evidence/rear_bindings.json").read_text())
report["rear_receiver_bindings"]=bindings
assert {b["mesh"] for b in bindings}=={"Wall_rear_left","Wall_rear_right","Wall_rear_door_header"}
assert all(b["map"]=="res://assets/art/room1_wall_lamp_r13/wall_rear.png" and b["kind"]==5 for b in bindings)
report["lamp_close_clipped_pixels"]={name:sum(max(pixel[:3])>=254 for pixel in Image.open(EXP/f"evidence/lamp_close_{name}.png").convert("RGB").get_flattened_data()) for name in ("before","after")}
report["new_usage_generations"]=sum(json.loads((EXP/f"result_{v}.json").read_text())["usage"]["generations"] for v in ("portal","lamp_a","lamp_b"))
(HERE/"quality.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
groups=[("后墙游戏效果：r12 → r13",["game_center_before","game_center_after"]),("门所在宽墙板近景",["rear_close_before","rear_close_after"]),("后墙原生贴图",["rear_map_before","rear_map_after"]),("灯带发光表面",["lamp_close_before","lamp_close_after"]),("灯带颜色诊断",["lamp_color_before","lamp_color_after"]),("灯带开启／关闭",["lamp_on","lamp_off"]),("灯带四个转角",["lamp_corner_front_left","lamp_corner_rear_left","lamp_corner_front_right","lamp_corner_rear_right"]),("整室左右",["game_left_after","game_right_after"]),("四角与前墙",["survey_front_left","survey_rear_left","survey_front_right","survey_rear_right","survey_front_full"])]
html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Room 1 后墙与灯带 r13</title><style>body{margin:28px;background:#141b1d;color:#d4dfd7;font:15px/1.5 system-ui}main{max-width:1500px;margin:auto}section{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;padding:10px;background:#202b2c}img{width:100%;display:block;image-rendering:pixelated}h2{margin-top:30px}a{color:#bcd0c4}</style><main><h1>Room 1 r13：补齐门所在后墙，细化连续灯带</h1><p>后墙原先仍是过疏的宽墙板差分；本版以PixelLab补齐。灯带由PixelLab生成灯罩与槽边细节，并压回表面过曝使纹理可见。保持原UV2环境照明。<a href="README.md">制作与验证记录</a></p>'
for title,names in groups:
    html+='<h2>'+title+'</h2><section>'
    for n in names:html+='<figure><img src="evidence/'+n+'.png"><figcaption>'+n+'</figcaption></figure>'
    html+='</section>'
(EXP/"preview.html").write_text(html+'</main></html>',encoding="utf-8")
print(json.dumps(report))
