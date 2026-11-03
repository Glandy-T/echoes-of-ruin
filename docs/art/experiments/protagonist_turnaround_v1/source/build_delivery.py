"""Mechanical layout, annotations and verification; no asset pixels painted or resized."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,shutil,hashlib,base64
import numpy as np
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
for name in ['side','back']:shutil.copyfile(EXP/'raw'/f'{name}.png',EXP/'views'/f'{name}.png')
shutil.copyfile(ROOT/'docs/art/experiments/protagonist_front_v2/editable/front_design_v2.aseprite',EXP/'editable/front.aseprite')
names=['front','side','back'];bounds={};checks={};usage=0
for name in names:
 im=Image.open(EXP/'views'/f'{name}.png').convert('RGBA');bounds[name]=im.getbbox()
 checks[name+'_native192x256']=im.size==(192,256)
 if name!='front':
  readback=Image.open(HERE/f'readback_{name}.png').convert('RGBA');a=np.array(im);b=np.array(readback);visible=a[:,:,3]>0
  checks[name+'_ASE_visible_and_alpha_exact']=np.array_equal(a[visible],b[visible]) and np.array_equal(a[:,:,3],b[:,:,3])
  r=json.loads((EXP/f'result_{name}.json').read_text(encoding='utf8'));checks[name+'_real_completed_job']=r['status']=='completed';usage+=r['usage']['generations']
original=ROOT/'docs/art/experiments/protagonist_front_v2/front_design_v2.png'
checks['front_v2_file_exact']=(EXP/'views/front.png').read_bytes()==original.read_bytes()
checks['head_top_and_floor_aligned']=len({b[1] for b in bounds.values()})==1 and len({b[3] for b in bounds.values()})==1
sheet=Image.new('RGB',(640,320),(128,138,134));d=ImageDraw.Draw(sheet)
for y in [11,60,139,211,244]:d.line((8,32+y,632,32+y),fill=(105,117,113),width=1)
for i,name in enumerate(names):
 im=Image.open(EXP/'views'/f'{name}.png').convert('RGBA');x=16+i*208;d.text((x,8),name.upper(),fill=(238,241,232));sheet.paste(im,(x,32),im)
d.text((16,300),'Native 192x256 per view; no scaling. Design reference, not CAD.',fill=(238,241,232))
sheet.save(EXP/'turnaround_sheet.png')
def data(name):return 'data:image/png;base64,'+base64.b64encode((EXP/'views'/f'{name}.png').read_bytes()).decode()
svg='''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="650" viewBox="0 0 1000 650"><rect width="1000" height="650" fill="#25302f"/><style>text{font:19px 'Microsoft YaHei',sans-serif;fill:#ecf0e6}.small{font-size:15px}.line{stroke:#aec6b9;stroke-width:2;fill:none}circle{fill:#aec6b9}</style><text x="30" y="35">主角部件拆分建议 · 三视图阶段的工程标注</text>'''
svg+=f'<image href="{data("front")}" x="130" y="70" width="384" height="512" style="image-rendering:pixelated"/><image href="{data("back")}" x="590" y="70" width="384" height="512" style="image-rendering:pixelated"/>'
svg+='''<text x="280" y="64">正面</text><text x="750" y="64">背面</text><text x="26" y="146">H1 前发／侧束</text><path class="line" d="M170 140 L250 140 L288 157"/><circle cx="288" cy="157" r="4"/><text x="30" y="274">B1 身体体系</text><text class="small" x="30" y="299">头颈、手、脚</text><path class="line" d="M160 270 L238 270 L320 138"/><circle cx="320" cy="138" r="4"/><path class="line" d="M160 292 L240 348"/><circle cx="240" cy="348" r="4"/><text x="30" y="437">C1 白色休眠袍</text><text class="small" x="30" y="463">独立衣物网格</text><path class="line" d="M174 430 L320 370"/><circle cx="320" cy="370" r="4"/><text x="554" y="280">H2 后发体块</text><path class="line" d="M688 274 L782 220"/><circle cx="782" cy="220" r="4"/><text class="small" x="30" y="606">袍身与袖子连续；头发少量实心低模体块；一个骨架共同驱动。当前只是拆分计划，尚未生成3D或分离网格。</text><text class="small" x="30" y="632">被衣物遮挡的人体需要建模时补足必要体积；图中未展示裸体或虚构的内部结构。</text></svg>'''
(EXP/'parts.svg').write_text(svg,encoding='utf8')
report={'result':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'alpha_bounds_xy_exclusive':bounds,'head_top_y':bounds['front'][1],'soles_last_y':bounds['front'][3]-1,'new_PixelLab_requests':2,'actual_generations':usage,'creative_resizing':False,'manual_art_refinement_pixels':0,'new_3D_models':0,'user_turnaround_approval':False,'boundary':'matching alpha endpoints does not prove every hidden joint or hair contour metrically identical; back hair and back garment are inferred design candidates'}
(HERE/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');assert report['result']=='PASS',report
print('TURNAROUND_SOURCE_PASS',len(checks),'checks;',usage,'generations;3views native and head/floor aligned')
page='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>主角三视图 v1</title><style>body{background:#172020;color:#e2e5dd;font:16px/1.7 system-ui;max-width:1300px;margin:30px auto;padding:0 20px}a{color:#a6d5d3}img{display:block;max-width:100%;height:auto;image-rendering:pixelated}.views{display:flex;gap:24px;flex-wrap:wrap}figure{margin:0}figure img{background:#808a86}h1{font-size:25px}h2{font-size:21px}</style><h1>主角三视图 v1 · 正面v2＋右侧面＋背面</h1><p>正面沿用已认可v2原文件。侧／背由PixelLab分别以该图为唯一图像输入生成，两次请求，实际18 generations。每张192×256原生，头顶y11、脚底最后一行y244，未缩放或拉伸；白袍、弱五官、浅肤色与低A姿势作为共同依据。</p><p>本轮交付是造型三视图和部件建议，尚未建模。后发、衣服背面等首次可见结构是候选设计，3D阶段继续检查体积、遮挡与动作。头顶／脚底对齐不代表所有隐藏关节或衣物褶皱都达到CAD精度。</p><p><a href="README.md">来源与检查</a> · <a href="turnaround_sheet.png">并排PNG</a> · <a href="parts.svg">部件标注SVG</a> · <a href="editable/front.aseprite">正面Aseprite</a> · <a href="editable/side.aseprite">侧面Aseprite</a> · <a href="editable/back.aseprite">背面Aseprite</a></p><h2>三视图（并排原生排版）</h2><img width="1280" height="640" src="turnaround_sheet.png"><h2>部件拆分建议</h2><img src="parts.svg"><h2>原生独立图</h2><div class="views">'''
for name,label in [('front','正面 · 已认可v2'),('side','右侧面 · 朝画面右方'),('back','背面')]:page+=f'<figure><figcaption>{label}</figcaption><a href="views/{name}.png"><img width="192" height="256" src="views/{name}.png"></a></figure>'
page+='</div><p>完整人物参考用于统一造型。身体、白袍和头发在后续Blender阶段保留可独立编辑的网格／分组；不能假设AI自动生成可动画的服装分层。</p></html>'
(EXP/'preview.html').write_text(page,encoding='utf8')
