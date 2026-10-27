from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib,re,runpy
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];OUT=ROOT/'assets/art/room1_floor_contact_r8';OLD=ROOT/'assets/art/room1_surface_lighting_r7'
runpy.run_path(str(HERE/'source/check_floor.py'),run_name='__main__')
E=HERE/'evidence';S=HERE/'survey'
def exact(a,b):
    a=Image.open(a).convert('RGB');b=Image.open(b).convert('RGB');assert a.size==b.size==(1280,720)
    assert ImageChops.difference(a,b).getbbox() is None
exact(E/'game_right_baseline_A_exact.png',ROOT/'docs/art/experiments/room1_surface_lighting_r7/evidence/game_right_before_n.png')
for name in ['n','f','i']:exact(E/'game_right_baseline_C.png',E/('game_right_after_'+name+'.png'))
for name in ['room1_baked_uv2_r3.glb','mesh_mapping.json','uv2_layout_record.json']:assert (OUT/name).read_bytes()==(OLD/name).read_bytes()
for name in ['room1_baked_uv2_r3.glb.import','strip_irradiance_denoised.exr.import']:
    assert (OUT/name).read_text().split('[params]',1)[1].strip()==(OLD/name).read_text().split('[params]',1)[1].strip()
manifest=json.loads((OUT/'bake_manifest.json').read_text(encoding='utf-8'))
for material in manifest['albedo_sources']:assert hashlib.sha256((ROOT/material['color_map']).read_bytes()).hexdigest()==material['sha256']
comparison=json.loads((E/'capture_record.json').read_text());survey=json.loads((S/'capture_record.json').read_text())
for folder,record in [(E,comparison),(S,survey)]:
    for row in record['captures']:assert Image.open(folder/row['file']).size==(1280,720)
floor=json.loads((HERE/'source/floor_quality.json').read_text());source=json.loads((HERE/'source_readback.json').read_text())
quality={'floor':floor,'matching_bake_source_hashes':True,'r7_baseline_exact':True,'n_f_i_roundtrip_exact':True,'glb_mapping_uv2_exact_r7':True,'godot_import_params_exact_r7':True,'capture_counts':{'comparison':len(comparison['captures']),'survey':len(survey['captures']),'size':[1280,720]},'hdr':source['hdr_stats'],'scope':'New floor contact aging only; r6 wall PNGs, model, layout, emitters, UV and gameplay camera retained. Matching floor-color bounce rebaked.'}
(HERE/'quality_check.json').write_text(json.dumps(quality,indent=2),encoding='utf-8')
fig=lambda p,t:f'<figure><a href="{p}"><img loading="lazy" src="{p}"></a><figcaption>{t}</figcaption></figure>'
s=['''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Room 1 地坪接触旧化 r8</title><style>body{background:#171D21;color:#D9DDD5;font:16px/1.7 system-ui;margin:0}main{max-width:1500px;margin:auto;padding:30px}p{max-width:1100px}a{color:#B3D9DE}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}figure{margin:0 0 20px}img{width:100%;height:auto;display:block}figcaption{padding:8px}.native img{image-rendering:pixelated}@media(max-width:800px){.grid{grid-template-columns:1fr}}</style><main><p>Echoes of Ruin / 終末残響 · 2026-10-27</p><h1>地面边界与舱底接触 · r8</h1><p>四面墙脚与20个舱基的真实接触线增加连片沉积，边角加宽、外侧断续；保持蓝灰连续主面与原四处漏液，不增加地砖或路线。新地面配套重烘光照，原灯带、曝光、模型和布局保持。</p><p><a href="README.md">制作与导入记录</a> · <a href="editable/">7层／10层Aseprite</a> · <a href="room1_floor_contact_r8_packed.blend">当前 Blender 工程</a> · <a href="quality_check.json">验证结果</a></p><h2>原r7 / 新r8 · 同机位原照明</h2>''']
for station in ['left_front','center_front','right_front','left_back','center_back','right_back']:
    s.append('<h3>'+station+'</h3><div class="grid">')
    for tag,label in [('A_r7floor_r7gi','A 原地面／原配套光照'),('C_r8floor_r8gi','C 接触旧化地面／新配套光照')]:s.append(fig('evidence/game_'+station+'_'+tag+'.png',label))
    s.append('</div>')
s.append('<h2>材质隔离：只换地面，保留r7光照</h2><div class="grid">')
for station in ['left','center','right']:s.append(fig(f'evidence/game_{station}_B_r8floor_r7gi.png','B '+station))
s.append('</div><h2>普通休眠舱：真实接触线与边角</h2><div class="grid">')
for pod in ['P01','P05','P15','P20']:s.append(fig(f'evidence/pod_contact_{pod}_C.png',pod+' · 实际落地轮廓'))
s.append('</div><h2>原四处漏液保持</h2><div class="grid">')
for pod in ['P03','P06','P13','P18']:s.append(fig(f'evidence/leak_contact_{pod}_C.png',pod))
s.append('</div><h2>颜色图与20舱位置核对</h2><p>Base Color是颜色诊断，文字标注仅供检查，不进入游戏。</p>')
s.extend([fig('evidence/floor_basecolor_overview.png','实际Godot Base Color 总览'),fig('evidence/floor_contact_plan.png','原生贴图及20舱标注')])
s.append('<h2>整室巡检</h2><p>前墙和角点技术图临时显示剖切墙，拍后恢复；游戏视角不改变。全部游戏截图原曝光，无提亮。</p><div class="grid">')
for row in survey['captures']:s.append(fig('survey/'+row['file'],row['file'].removesuffix('.png')))
s.append('</div><p>所有新增沉积分量都与实际墙脚／舱基连接，原漏液源层保持。新候选的沉积强度与整体观感等待审图。</p></main></html>')
(HERE/'preview.html').write_text('\n'.join(s),encoding='utf-8')
assert not [p for p in re.findall(r'(?:src|href)="([^"]+)"','\n'.join(s)) if not (HERE/p).exists()]
print(json.dumps(quality,indent=2))
