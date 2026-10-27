"""Read actual captures and canonical Aseprite exports; no screenshot brightening."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import json,re,hashlib,html
ROOT=Path(__file__).resolve().parents[1]; PROJECT=ROOT.parents[3]
ASSETS=PROJECT/'assets/art/room1_surface_full_r5'; E=ROOT/'evidence'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
checks={}
for name,size in [('floor_aged',(1648,728)),('floor_with_leaks',(1648,728)),('wall_left',(728,272)),('wall_right',(728,272)),('wall_front',(1648,272)),('wall_rear',(1648,272))]:
    asset=ASSETS/(name+'.png'); source=ROOT/'source/readback'/(name+'.png')
    a=Image.open(asset).convert('RGBA'); b=Image.open(source).convert('RGBA')
    assert a.size==b.size==size
    assert ImageChops.difference(a,b).getbbox() is None,name
    checks[name]={'size':size,'aseprite_reopen_exact':True,'sha256':sha(asset)}
walls=[Image.open(ASSETS/('wall_'+name+'.png')).convert('RGB') for name in ['left','right','front','rear']]
edge=walls[0].crop((0,0,2,272))
for wall in walls:
    assert ImageChops.difference(edge,wall.crop((0,0,2,272))).getbbox() is None
    assert ImageChops.difference(edge,wall.crop((wall.width-2,0,wall.width,272))).getbbox() is None
    assert wall.crop((0,18,wall.width,36)).getextrema()==((204,204),(221,221),(228,228))
checks['wall_corner_and_diffuser']={'all_end_columns_equal':True,'diffuser_rgb':[204,221,228],'diffuser_rows':[18,35]}
baseline=PROJECT/'docs/art/experiments/room1_wall_age_r4/evidence/game_r4_lit.png'
for name in ['game_left_m0','game_left_m0_after_n_roundtrip']:
    a=Image.open(E/(name+'.png')).convert('RGB'); b=Image.open(baseline).convert('RGB')
    assert ImageChops.difference(a,b).getbbox() is None,name
checks['r4_and_n_roundtrip_exact']=True
record=json.loads((E/'capture_record.json').read_text(encoding='utf-8'))
survey=json.loads((ROOT/'survey/capture_record.json').read_text(encoding='utf-8'))
for row in record['captures']:
    assert Image.open(E/row['file']).size==(1280,720)
for row in survey['captures']:
    assert Image.open(ROOT/'survey'/row['file']).size==(1280,720)
checks['actual_capture_count']={'comparison':len(record['captures']),'survey':len(survey['captures']),'size':[1280,720]}
checks['scope']={'geometry_uv2_hdr_camera_lights_changed':False,'formal_main_changed':False,'new_albedo_bounce_rebaked':False,'new_ai_calls':0}
# Regenerate explanatory plan from the canonical, re-exported runtime PNG.
floor=Image.open(ASSETS/'floor_with_leaks.png').convert('RGB'); plan=floor.copy(); draw=ImageDraw.Draw(plan)
scene=(PROJECT/'scenes/dev/room1_pod_exit_animation_r3.tscn').read_text(encoding='utf-8')
for match in re.finditer(r'\[node name="(P\d+)"[^\n]*\ntransform = Transform3D\(([^\n]+)\)',scene):
    vals=list(map(float,match.group(2).split(','))); x=(vals[-3]-.2)*80; y=(vals[-1]+9.3)*80
    draw.rectangle((x-42,y-92,x+42,y+92),outline='#D3D6C9',width=2); draw.text((x-11,y-4),match.group(1),fill='#E7E7D4')
manifest=json.loads((ROOT/'source/floor_manifest.json').read_text(encoding='utf-8'))
manifest['pod_plan_bounds']='1.05x2.3m nominal footprint; runtime r5 readback measures approximately 1.05x2.294m on all four closed leak pods, consistent with placement.'
manifest['runtime_pod_aabb_readback']=record['leak_candidates']
(ROOT/'source/floor_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
wall_manifest=json.loads((ROOT/'source/wall_manifest.json').read_text(encoding='utf-8'))
for name,row in wall_manifest['walls'].items():
    if 'sha256' in row:row['source_raster_sha256']=row.pop('sha256')
    row['canonical_aseprite_export_sha256']=sha(ASSETS/('wall_'+name+'.png'))
(ROOT/'source/wall_manifest.json').write_text(json.dumps(wall_manifest,indent=2),encoding='utf-8')
for leak in manifest['leaks']:
    x,y=leak['pixel_center']; draw.text((x-23,y+98),leak['pod']+' LEAK',fill='#CCDFC6')
plan.save(E/'floor_leak_placement_plan.png')
for name,label in [('floor_aged','floor_aged_native'),('floor_with_leaks','floor_leaks_native')]:Image.open(ASSETS/(name+'.png')).convert('RGB').save(E/(label+'.png'))
sheet=Image.new('RGB',(1920,784),'#171D21'); d=ImageDraw.Draw(sheet)
for row,mode in enumerate([0,3]):
    for col,station in enumerate(['left','center','right']):
        x=col*640;y=row*392;d.text((x+12,y+8),f'{station.upper()} / '+('R4 BASELINE' if mode==0 else 'R5 FULL WALLS + AGED FLOOR + LEAKS'),fill='#D3D6C9')
        sheet.paste(Image.open(E/f'game_{station}_m{mode}.png').convert('RGB').resize((640,360),Image.Resampling.LANCZOS),(x,y+32))
sheet.save(E/'comparison_overview.png')
(ROOT/'source/quality_check.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
def fig(path,label):return f'<figure><a href="{path}"><img loading="lazy" src="{path}" alt="{html.escape(label)}"></a><figcaption>{html.escape(label)}</figcaption></figure>'
parts=['''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Room 1 · 全室表面 r5</title><style>body{margin:0;background:#151B1F;color:#D9DDD5;font:16px/1.7 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:32px}h1,h2{font-weight:600}p{max-width:1050px}a{color:#B3D9DE}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}figure{margin:0 0 18px}img{width:100%;height:auto;display:block;background:#222B30}figcaption{padding:8px 0;color:#AFBBB9}.native img{image-rendering:pixelated}.links{padding:18px;background:#20292D}@media(max-width:800px){.grid{grid-template-columns:1fr}main{padding:16px}}</style><main><p>Echoes of Ruin / 終末残響 · 2026-10-27</p><h1>Room 1 全室墙地 · r5</h1><p>沿用已暂时认可的 r4 墙面旧化，全墙增加差分；地面统一连续做旧，不加接缝。四个固定舱位 P03 / P06 / P13 / P18 增加旧漏液残迹。布局、模型、UV、舱体、灯光和游戏镜头保持。以下游戏图为实际 Godot 原照明截图，没有提亮。新候选待审。</p><p class="links"><a href="README.md">制作记录与限制</a> · <a href="editable/">六份分层 Aseprite</a> · <a href="source/quality_check.json">文件／回退校验</a> · <a href="source/floor_manifest.json">固定漏液位置</a></p><h2>相同游戏镜头：r4 局部基线 / r5 全室</h2>''',fig('evidence/comparison_overview.png','上：旧局部样段；下：全室新墙、旧化地坪和少数舱位漏液。点击看原尺寸。')]
parts.append('<h2>左、中、右：原照明下逐项比较</h2>')
for station,title in [('left','左侧'),('center','中央'),('right','右侧')]:
    parts.append(f'<h3>{title}</h3><div class="grid">')
    for mode,label in [(0,'r4 局部基线'),(1,'全墙，旧地面'),(2,'全墙＋全体旧地坪，无漏液'),(3,'全墙＋全体旧地坪＋四处漏液')]:parts.append(fig(f'evidence/game_{station}_m{mode}.png',label))
    parts.append('</div>')
parts.append('<h2>四处漏液：舱基与地面</h2><p>固定选择，运行时不随机。液体成分与剧情意义尚未确定，不代表与舱内人物状态存在关联。</p><div class="grid">')
for pod in manifest['selected_pods']:parts.append(fig(f'evidence/leak_{pod}_m3_lit.png',pod+' · 正常照明，舱底外扩旧膜与干涸沉积边'))
parts.append('</div><h2>颜色图诊断与位置图</h2><p>Base Color 用于检查绘制内容，不是实际发光效果。位置图白框和文字仅为检查标注，不进入游戏。</p>')
parts.extend([fig('evidence/overview_m3_base_color.png','全室 Base Color 诊断'),fig('evidence/floor_leak_placement_plan.png','原生地面与20个舱位标注')])
parts.append('<h2>四面墙原生贴图</h2><div class="native">')
for name in ['left','right','front','rear']:parts.append(fig('../../../../assets/art/room1_surface_full_r5/wall_'+name+'.png',name+' · 独立完整颜色图，共用灯带高度与转角边列'))
parts.append('</div><h2>整室巡检</h2><div class="grid">')
for row in survey['captures']:parts.append(fig('survey/'+row['file'],row['file'].removesuffix('.png')))
parts.append('</div><p>前墙在正常游戏中为剖切用的 Shadows Only；前墙与转角技术图临时显示实体，拍完恢复。复用已修复的 r4 UV2 与连续灯带 irradiance。新颜色图引起的间接反射尚未重新烘焙；本轮用于表面审图，不称为最终新烘焙包。80 texels/m 仅为本次沿用试值。</p></main></html>')
(ROOT/'preview.html').write_text('\n'.join(parts),encoding='utf-8')
print(json.dumps(checks,indent=2))
