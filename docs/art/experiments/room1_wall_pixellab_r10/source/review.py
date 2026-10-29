from pathlib import Path
from PIL import Image
import json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
old=Image.open(HERE/"wall_left_baseline.png").convert("RGBA")
new=Image.open(ROOT/"assets/art/room1_wall_pixellab_r10/wall_left.png").convert("RGBA")
read=Image.open(HERE/"readback.png").convert("RGBA")
mask=Image.open(HERE/"composite_mask.png").convert("L")
changed=[(x,y) for y in range(272) for x in range(728) if old.getpixel((x,y))!=new.getpixel((x,y))]
outside=[(x,y) for x,y in changed if not(128<=x<384 and 16<=y<272) or mask.getpixel((x-128,y-16))==0]
def same(a,b):return Image.open(a).convert("RGBA").tobytes()==Image.open(b).convert("RGBA").tobytes()
report={"changed_pixels":len(changed),"outside_mask":len(outside),"aseprite_pixel_exact":new.tobytes()==read.tobytes(),"light_strip_unchanged":old.crop((0,18,728,36)).tobytes()==new.crop((0,18,728,36)).tobytes(),"technical_after_N_roundtrip_exact":same(EXP/"evidence/technical_after.png",EXP/"evidence/technical_restored.png"),"sample_world":{"x":0.2,"z":[-5.0,-1.8],"height":[0.0,3.2]},"new_light_bake":False}
(HERE/"quality.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
for name,im in (("texture_before",old), ("texture_after",new)):
    im.crop((128,16,384,272)).resize((512,512),Image.Resampling.NEAREST).save(EXP/"evidence"/(name+".png"))
groups=[("原生纹理最近邻2倍",["texture_before","texture_after"]),("实际游戏镜头",["game_left_before","game_left_after"]),("技术近景，原灯光",["technical_before","technical_after"]),("Base Color诊断",["base_color_before","base_color_after"]),("全室四角巡检（旧墙面仍保留）",["survey_front_left","survey_rear_left","survey_front_right","survey_rear_right"])]
html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Room 1 墙面 PixelLab r10</title><style>body{background:#131b1d;color:#d5dfd8;font:15px/1.5 system-ui;margin:28px}main{max-width:1500px;margin:auto}section{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:#202b2c;padding:10px}img{width:100%;display:block;image-rendering:pixelated}h2{margin-top:32px}a{color:#bdd1c3}</style><main><h1>Room 1 墙面 PixelLab 返修 r10</h1><p>左墙中间两块墙板的独立候选。比较顺序：修前 → 修后。保留原灯带、接缝芯、布局与光照；其他墙仍为原r6。<a href="README.md">来源与限制</a></p>'
for title,names in groups:
    html+='<h2>'+title+'</h2><section>'
    for n in names:html+='<figure><img src="evidence/'+n+'.png"><figcaption>'+n+'</figcaption></figure>'
    html+='</section>'
(EXP/"preview.html").write_text(html+'</main></html>',encoding="utf-8")
print(json.dumps(report))
assert not outside and report["aseprite_pixel_exact"] and report["light_strip_unchanged"] and report["technical_after_N_roundtrip_exact"]
