"""Validate the delivered source/runtime match and actual screenshot regressions."""
from pathlib import Path
from PIL import Image,ImageChops
import numpy as np,json,hashlib,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=ROOT/'assets/art/room1_surface_lighting_r7';OLD=ROOT/'assets/art/room1_wall_finish_r4'
def exact(a,b):
    a=Image.open(a).convert('RGB');b=Image.open(b).convert('RGB')
    assert a.size==b.size==(1280,720)
    assert ImageChops.difference(a,b).getbbox() is None,(a,b)
E=HERE/'evidence';S=HERE/'survey'
exact(E/'base_color_r7.png',E/'base_color_r4.png')
exact(E/'game_right_before_n.png',E/'game_right_after_n.png')
exact(E/'game_right_before_n.png',E/'game_right_after_i.png')
exact(E/'game_right_r4_roundtrip_mid.png',ROOT/'docs/art/experiments/room1_seam_contact_r6/evidence/game_right_r6.png')
for file in ['room1_baked_uv2_r3.glb','mesh_mapping.json','uv2_layout_record.json']:assert (OUT/file).read_bytes()==(OLD/file).read_bytes()
manifest=json.loads((OUT/'bake_manifest.json').read_text(encoding='utf-8'))
for material in manifest['albedo_sources']:assert hashlib.sha256((ROOT/material['color_map']).read_bytes()).hexdigest()==material['sha256']
for file in ['room1_baked_uv2_r3.glb.import','strip_irradiance_denoised.exr.import']:
    old=(OLD/file).read_text().split('[params]',1)[1];new=(OUT/file).read_text().split('[params]',1)[1]
    assert old.strip()==new.strip(),file
record=json.loads((E/'capture_record.json').read_text());survey=json.loads((S/'capture_record.json').read_text())
for folder,rows in [(E,record['captures']),(S,survey['captures'])]:
    for row in rows:assert Image.open(folder/row['file']).size==(1280,720)
on=np.array(Image.open(S/'strip_on.png').convert('RGB'));restored=np.array(Image.open(S/'strip_on_restored.png').convert('RGB'))
changed=np.any(on!=restored,axis=2);ys,xs=np.where(changed)
if len(xs):
    assert xs.min()>=968 and xs.max()<1019 and ys.min()>=376 and ys.max()<404,'lamp restore changed outside animated red screen'
lamp={'changed_pixels':int(changed.sum()),'bbox':list(ImageChops.difference(Image.fromarray(on),Image.fromarray(restored)).getbbox()) if len(xs) else None,'outside_p17_screen_exact':True,'reason':'P17 animated red display changes with time; strip and room restore exactly outside this screen rectangle.'}
source=json.loads((HERE/'source_readback.json').read_text(encoding='utf-8'))
quality={'base_color_old_new_exact':True,'n_roundtrip_exact':True,'i_roundtrip_exact':True,'old_gi_matches_r6_exact':True,'glb_mapping_uv2_record_exact_r4':True,'albedo_source_hashes_match':True,'godot_import_params_exact_r4':True,'lamp_restoration':lamp,'captures':{'comparison':len(record['captures']),'survey':len(survey['captures']),'size':[1280,720]},'source_hdr_stats':source['hdr_stats'],'geometry_uv_unchanged':True,'scope':'New indirect irradiance from latest albedo; no albedo art edits, geometry, emitter, camera or exposure change.'}
(HERE/'quality_check.json').write_text(json.dumps(quality,ensure_ascii=False,indent=2),encoding='utf-8')
def fig(path,label):return f'<figure><a href="{path}"><img loading="lazy" src="{path}"></a><figcaption>{label}</figcaption></figure>'
s=['''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Room 1 配套烘焙 r7</title><style>body{margin:0;background:#171D21;color:#D9DDD5;font:16px/1.7 system-ui}main{max-width:1500px;margin:auto;padding:30px}p{max-width:1100px}a{color:#B3D9DE}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0 0 20px}img{width:100%;height:auto;display:block}figcaption{padding:8px}@media(max-width:800px){.grid{grid-template-columns:1fr}}</style><main><p>Echoes of Ruin / 終末残響 · 2026-10-27</p><h1>当前墙地与配套光照 · r7</h1><p>r6四墙与r5连续旧地坪／固定漏液接入Blender母版，重烘配套间接光。模型、UV、原灯带、光强、镜头和贴图设计保持。不是新增提亮方案；旧新光照差别很小，重点是颜色图与烘焙源对应、整室回归。</p><p><a href="README.md">制作／导入说明</a> · <a href="room1_surface_lighting_r7_packed.blend">最新打包 Blender 工程</a> · <a href="quality_check.json">精确校验记录</a></p><h2>同机位比较：左旧r4光照，右配套r7</h2>''']
for station in ['left_front','center_front','right_front','left_back','center_back','right_back']:
    s.append('<h3>'+station+'</h3><div class="grid">')
    for v in ['r4','r7']:s.append(fig(f'evidence/game_{station}_{v}.png',v+' · 同一套当前颜色图，原照明参数'))
    s.append('</div>')
s.append('<h2>原始1024样本 / 降噪后</h2><p>只处理线性光照图，不降噪原生像素颜色图。以下截图没有提亮。</p><div class="grid">')
for file,label in [('raw_left_corner','raw 1024'),('denoised_left_corner','denoised')]:s.append(fig('evidence/'+file+'.png',label))
s.append('</div><h2>四处既有漏液</h2><div class="grid">')
for pod in ['P03','P06','P13','P18']:s.append(fig(f'evidence/leak_{pod}_r7.png',pod))
s.append('</div><h2>整室巡检与灯带开关</h2><p>前墙和转角技术图临时显示剖切墙，拍后恢复。游戏镜头不改。灯带恢复仅P17动态红屏有时间差，屏幕范围外逐像素一致。</p><div class="grid">')
for row in survey['captures']:s.append(fig('survey/'+row['file'],row['file'].removesuffix('.png')))
s.append('</div><p>本轮完成配套烘焙与导入检查，仍等待整体美术审图。没有为主门、人物、玻璃或剧情痕迹新增设计。</p></main></html>')
(HERE/'preview.html').write_text('\n'.join(s),encoding='utf-8')
missing=[p for p in re.findall(r'(?:src|href)="([^"]+)"','\n'.join(s)) if not (HERE/p).exists()]
assert not missing,missing
print(json.dumps(quality,ensure_ascii=False,indent=2))
