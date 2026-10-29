from pathlib import Path
from PIL import Image
import json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
PREV=ROOT/"docs/art/experiments/room1_wall_pixellab_r11"
OUT=ROOT/"assets/art/room1_wall_pixellab_r12"
manifest=json.loads((HERE/"assembly.json").read_text())
report={"legacy_aging_layers_used":[],"pool_size":16,"mirrored_or_scaled":False,"walls":{},"new_usage_generations":sum(json.loads((EXP/f"result_{k}.json").read_text())["usage"]["generations"] for k in ("e","f","g","h","e2"))}
hashes={}
for k in "abcdefgh":
    source_key="e2" if k=="e" else k
    tile=Image.open((PREV if k in "abcd" else EXP)/f"raw/wall_{source_key}.png").convert("RGBA")
    for half in (0,1):
        panel=tile.crop((half*128,0,(half+1)*128,256))
        hashes[f"{k}{half}"]=hashlib.sha256(panel.tobytes()).hexdigest()
        panel.resize((256,512),Image.Resampling.NEAREST).save(EXP/f"evidence/panel_{k}{half}.png")
assert len(set(hashes.values()))==16
report["unique_pixel_panel_hashes"]=16
for wall in ("left","right","front","rear"):
    clean=Image.open(HERE/f"clean_{wall}.png").convert("RGBA")
    assert clean.tobytes()==Image.open(PREV/f"source/clean_{wall}.png").convert("RGBA").tobytes()
    new=Image.open(OUT/f"wall_{wall}.png").convert("RGBA")
    read=Image.open(HERE/f"readback_{wall}.png").convert("RGBA")
    previous=Image.open(ROOT/f"assets/art/room1_wall_pixellab_r11/wall_{wall}.png").convert("RGBA")
    seq=[key for _,key in manifest["walls"][wall]["placements"]]
    data={"size":list(new.size),"unique_assignments_within_wall":len(seq)==len(set(seq)),"neighboring_parent_variants_differ":all(a[0]!=b[0] for a,b in zip(seq,seq[1:])),"aseprite_pixel_exact":new.tobytes()==read.tobytes(),"light_strip_exact":new.crop((0,18,new.width,36)).tobytes()==clean.crop((0,18,new.width,36)).tobytes(),"corners_exact":all(new.getpixel((x,y))==clean.getpixel((x,y)) for x in (0,1,new.width-2,new.width-1) for y in range(272))}
    if wall=="rear":
        data["approved_door_bay_exact"]=new.crop((688,0,944,272)).tobytes()==previous.crop((688,0,944,272)).tobytes()
    assert all(v for v in data.values() if isinstance(v,bool))
    report["walls"][wall]=data
    new.save(EXP/f"evidence/map_{wall}_after.png");previous.save(EXP/f"evidence/map_{wall}_before.png")
report["N_roundtrip_exact"]=Image.open(EXP/"evidence/technical_after.png").tobytes()==Image.open(EXP/"evidence/technical_restored.png").tobytes()
assert report["N_roundtrip_exact"]
(HERE/"quality.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Room 1 墙面差分 r12</title><style>body{margin:28px;background:#141b1d;color:#d4dfd7;font:15px/1.5 system-ui}main{max-width:1500px;margin:auto}section{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;padding:10px;background:#202b2c}img{width:100%;display:block;image-rendering:pixelated}h2{margin-top:30px}a{color:#bcd0c4}.panels{grid-template-columns:repeat(8,1fr)}@media(max-width:900px){.panels{grid-template-columns:repeat(4,1fr)}}</style><main><h1>Room 1 r12：更多 PixelLab 墙面差分</h1><p>保持r11已认可的材质基调，增加4张PixelLab差分，拆分为16种原生墙板细节；同面墙不重复使用同一个墙板。B比较r11／r12。<a href="README.md">来源与用量</a></p>'
groups=[("游戏左／中／右，r11 → r12",[f"game_{s}_{v}" for s in ("left","center","right") for v in ("before","after")]),("近景比较",["technical_before","technical_after"]),("四墙安排，r11 → r12",[f"map_{w}_{v}" for w in ("left","right","front","rear") for v in ("before","after")]),("四角与前墙巡检",["survey_front_left","survey_rear_left","survey_front_right","survey_rear_right","survey_front_full"])]
for title,names in groups:
    html+='<h2>'+title+'</h2><section>'
    for n in names:html+='<figure><img src="evidence/'+n+'.png"><figcaption>'+n+'</figcaption></figure>'
    html+='</section>'
html+='<h2>16种原生墙板像素（2倍最近邻）</h2><section class="panels">'
for key in hashes:html+='<figure><img src="evidence/panel_'+key+'.png"><figcaption>'+key+'</figcaption></figure>'
(EXP/"preview.html").write_text(html+'</section></main></html>',encoding="utf-8")
print(json.dumps(report))
