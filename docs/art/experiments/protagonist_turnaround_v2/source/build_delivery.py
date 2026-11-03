from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib,base64,xml.etree.ElementTree as ET
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4];OLD=ROOT/'docs/art/experiments/protagonist_turnaround_v1'
provenance=json.loads((HERE/'provenance.json').read_text(encoding='utf8'));checks={}
for p,h in provenance['baseline_hashes'].items():checks['frozen_v1_'+p]=hashlib.sha256((OLD/p).read_bytes()).hexdigest()==h
for name in ['front','side']:
 checks[name+'_PNG_exact']=(EXP/'views'/f'{name}.png').read_bytes()==(OLD/'views'/f'{name}.png').read_bytes()
 checks[name+'_ASE_exact']=(EXP/'editable'/f'{name}.aseprite').read_bytes()==(OLD/'editable'/f'{name}.aseprite').read_bytes()
base=np.array(Image.open(HERE/'back_v1.png').convert('RGBA'));out=np.array(Image.open(EXP/'views/back.png').convert('RGBA'));mask=np.array(Image.open(HERE/'repair_mask.png'))>0
ase=np.array(Image.open(HERE/'readback_back.png').convert('RGBA'));visible=out[:,:,3]>0
checks['back_outside4regions_exact']=np.array_equal(base[~mask],out[~mask]);checks['ASE_visible_and_alpha_exact']=np.array_equal(out[visible],ase[visible]) and np.array_equal(out[:,:,3],ase[:,:,3]);checks['all_native192x256']=all(Image.open(EXP/'views'/f'{n}.png').size==(192,256) for n in ['front','side','back'])
result=json.loads((EXP/'result_back.json').read_text(encoding='utf8'));checks['real_completed_PixelLab_job']=result['status']=='completed'
sheet=Image.new('RGB',(640,320),(128,138,134));d=ImageDraw.Draw(sheet)
for y in [11,60,139,211,244]:d.line((8,32+y,632,32+y),fill=(105,117,113))
bounds={}
for i,name in enumerate(['front','side','back']):
 im=Image.open(EXP/'views'/f'{name}.png').convert('RGBA');bounds[name]=im.getbbox();x=16+i*208;d.text((x,8),name.upper(),fill=(238,241,232));sheet.paste(im,(x,32),im)
d.text((16,300),'Back v2: posterior hands and heels repaired. Native view layout.',fill=(238,241,232));sheet.save(EXP/'turnaround_sheet.png')
# Update the self-contained technical diagram's embedded back view, not just the HTML.
tree=ET.parse(OLD/'parts.svg');root=tree.getroot();images=root.findall('{http://www.w3.org/2000/svg}image');assert len(images)==2
images[1].set('href','data:image/png;base64,'+base64.b64encode((EXP/'views/back.png').read_bytes()).decode());tree.write(EXP/'parts.svg',encoding='utf-8',xml_declaration=True)
regions=list(provenance['repair_regions_xy_inclusive'].items())
for label,path in [('before',HERE/'back_v1.png'),('after',EXP/'views/back.png')]:
 im=Image.open(path).convert('RGBA');strip=Image.new('RGB',(216,58),(128,138,134));draw=ImageDraw.Draw(strip)
 for i,(name,box) in enumerate(regions):
  x0,y0,x1,y1=box;crop=im.crop((x0,y0,x1+1,y1+1));x=i*54+(54-crop.width)//2;draw.text((i*54+5,2),['HAND-L','HAND-R','HEEL-L','HEEL-R'][i],fill=(238,241,232));strip.paste(crop,(x,21),crop)
 strip.save(EXP/f'limbs_{label}.png')
report={'result':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'bounds_xy_exclusive':bounds,'new_PixelLab_requests':1,'actual_generations':result['usage'],'creative_resize':False,'manual_art_refinement_pixels':0,'silhouette_alpha_changes_allowed_only_inside4limb_boxes':True,'anatomy_visual_review':'Recorded separately; hashes and matching bbox do not verify posterior anatomy.','user_approval':False}
(HERE/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');assert report['result']=='PASS',report
page='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>主角三视图 v2 · 背面手脚返修</title><style>body{background:#172020;color:#e2e5dd;font:16px/1.7 system-ui;max-width:1300px;margin:30px auto;padding:0 20px}a{color:#a6d5d3}img{display:block;max-width:100%;height:auto;image-rendering:pixelated}.pair{display:flex;gap:24px;flex-wrap:wrap}figure{margin:0}figure img{background:#808a86}h1{font-size:25px}h2{font-size:21px}</style><h1>主角三视图 v2 · 背面手脚方向返修</h1><p>v1背面错误沿用正面手脚，用户指出后本轮仅开放两手、脚踝与脚跟四个区域给PixelLab重画，包含必要透明轮廓。正面、侧面和背面其余部分保持原像素。这里是待审候选，不是已批准3D资产。</p><p><a href="README.md">来源与检查</a> · <a href="turnaround_sheet.png">完整三视图PNG</a> · <a href="parts.svg">更新部件图</a> · <a href="editable/back.aseprite">背面分层Aseprite</a></p><h2>背面修前／修后（2倍查看）</h2><div class="pair"><figure><figcaption>A · v1 错误手脚</figcaption><img width="384" height="512" src="source/back_v1.png"></figure><figure><figcaption>B · v2 后侧手脚候选</figcaption><img width="384" height="512" src="views/back.png"></figure></div><h2>四处局部（3倍查看）</h2><p>这里只是原生裁片排版，完整姿态见上方。</p><figure><figcaption>A · 修前</figcaption><img width="648" height="174" src="limbs_before.png"></figure><figure><figcaption>B · 修后</figcaption><img width="648" height="174" src="limbs_after.png"></figure><h2>当前三视图</h2><img width="1280" height="640" src="turnaround_sheet.png"><h2>部件标注</h2><img src="parts.svg"><p>身体、独立白袍、少量头发体块的拆分计划沿用；3D建模、分网格、绑定和Godot导入尚未开始。</p></html>'''
(EXP/'preview.html').write_text(page,encoding='utf8');print('TURNAROUND_V2_TECH_PASS',len(checks),'checks')
