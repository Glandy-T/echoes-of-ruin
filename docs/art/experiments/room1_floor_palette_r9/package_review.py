from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib,runpy,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=ROOT/'assets/art/room1_floor_palette_r9';OLD=ROOT/'assets/art/room1_floor_contact_r8'
runpy.run_path(str(HERE/'source/check_palette.py'),run_name='__main__')
E=HERE/'evidence'
def exact(a,b):
    a=Image.open(a).convert('RGB');b=Image.open(b).convert('RGB');assert a.size==b.size==(1280,720)
    assert ImageChops.difference(a,b).getbbox() is None
exact(E/'game_r8_original.png',ROOT/'docs/art/experiments/room1_floor_contact_r8/evidence/game_right_baseline_C.png')
for key in ['n','f','i']:exact(E/'game_r9_final.png',E/('game_r9_after_'+key+'.png'))
for name in ['room1_baked_uv2_r3.glb','mesh_mapping.json','uv2_layout_record.json']:assert (OUT/name).read_bytes()==(OLD/name).read_bytes()
for name in ['room1_baked_uv2_r3.glb.import','strip_irradiance_denoised.exr.import']:assert (OUT/name).read_text().split('[params]',1)[1].strip()==(OLD/name).read_text().split('[params]',1)[1].strip()
manifest=json.loads((OUT/'bake_manifest.json').read_text(encoding='utf-8'))
for row in manifest['albedo_sources']:assert hashlib.sha256((ROOT/row['color_map']).read_bytes()).hexdigest()==row['sha256']
record=json.loads((E/'capture_record.json').read_text())
for row in record:assert Image.open(E/row['file']).size==(1280,720)
quality={'palette':json.loads((HERE/'source/palette_check.json').read_text()),'old_r8_baseline_exact':True,'n_f_i_restoration_exact':True,'glb_mapping_uv_exact_r8':True,'import_params_exact_r8':True,'baked_albedo_source_hashes_current':True,'captures':len(record),'size':[1280,720]}
(HERE/'quality_check.json').write_text(json.dumps(quality,indent=2),encoding='utf-8')
fig=lambda p,t:f'<figure><a href="{p}"><img src="{p}" loading="lazy"></a><figcaption>{t}</figcaption></figure>'
parts=['''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Room 1 去黄修色 r9</title><style>body{background:#171D21;color:#D9DDD5;font:16px/1.7 system-ui;margin:0}main{max-width:1500px;margin:auto;padding:30px}a{color:#B3D9DE}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0 0 20px}img{width:100%;display:block}figcaption{padding:8px}@media(max-width:800px){.grid{grid-template-columns:1fr}}</style><main><h1>地面去黄修色 · r9</h1><p>保留全部沉积形状与位置，只把偏黄绿色亮部改成贴近地坪的低饱和冷灰蓝。主地坪底色、墙图、模型、光强与曝光保持。以下均为实际Godot截图，没有截图提亮或全局调色。</p><p><a href="README.md">说明与源</a> · <a href="editable/">分层Aseprite</a> · <a href="room1_floor_palette_r9_packed.blend">打包Blender工程</a> · <a href="quality_check.json">验证记录</a></p><h2>同一光照：旧r8 / 新r9配色</h2><div class="grid">''',fig('evidence/pod_r8_original.png','旧色：偏黄绿的沉积亮部'),fig('evidence/pod_r9_same_light.png','新色：冷灰蓝，同一r8光照'),fig('evidence/game_r8_original.png','旧r8颜色与光照'),fig('evidence/game_r9_same_light.png','新r9颜色，光照与旧版相同'),'</div><h2>当前配套光照下的新色</h2><div class="grid">',fig('evidence/pod_r9_final.png','r9最终近景'),fig('evidence/game_r9_final.png','r9游戏镜头'),fig('evidence/leak_r9_final.png','原漏液浅色边同步去黄，形状与位置不变'),'</div><h2>颜色诊断：原生配色差异</h2><p>以下是Base Color诊断，不是正式发光效果。</p><div class="grid">',fig('evidence/floor_r8_base_color.png','r8旧地面'),fig('evidence/floor_r9_base_color.png','r9冷灰蓝地面'),'</div><p>四边和20舱接触逻辑保留。新候选等待美术审查，不将颜色检查等同最终自然度通过。</p></main></html>']
s='\n'.join(parts);(HERE/'preview.html').write_text(s,encoding='utf-8');assert not [p for p in re.findall(r'(?:src|href)="([^"]+)"',s) if not (HERE/p).exists()]
print(json.dumps({k:v for k,v in quality.items() if k!='palette'}))
