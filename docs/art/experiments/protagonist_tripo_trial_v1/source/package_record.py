"""Mechanical screenshot cropping and provenance only; no model extraction."""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
crop=(800,160,1180,742);files=[]
(EXP/'evidence').mkdir(exist_ok=True)
for name in ['front','side','back','quarter']:
 source=HERE/f'{name}_full.jpg';im=Image.open(source);assert im.size==(1920,855)
 out=EXP/'evidence'/f'{name}.jpg';im.crop(crop).save(out,quality=95);files.append(out)
Image.open(HERE/'front_full.jpg').crop((1450,60,1580,150)).save(EXP/'evidence/viewer_statistics.jpg',quality=95)
sheet=Image.new('RGB',(4*380,618),(37,42,43));d=ImageDraw.Draw(sheet)
for i,name in enumerate(['front','side','back','quarter']):
 d.text((i*380+15,10),name.upper(),fill=(225,230,223));sheet.paste(Image.open(EXP/'evidence'/f'{name}.jpg'),(i*380,30))
sheet.save(EXP/'evidence/views_sheet.jpg',quality=95)
input_path='docs/art/experiments/protagonist_turnaround_v2/views/front.png'
assert (HERE/'input_front.png').read_bytes()==(ROOT/input_path).read_bytes()
record={'date':'2026-11-05','provider':'Tripo Studio','generation_channel':'Chrome extension controlled official web UI, not API','model_url':'https://studio.tripo3d.ai/workspace/generate/7407fbd8-8ff0-4ae7-bca8-2223e003c137','model_id':'7407fbd8-8ff0-4ae7-bca8-2223e003c137','input':{'path':input_path,'sha256':hashlib.sha256((HERE/'input_front.png').read_bytes()).hexdigest(),'size':[192,256],'used_views':['front'],'uploaded_NoAI_reference':False},'requested':{'mode':'Smart Mesh','AI_model':'P2.0','topology':'Quad','target_polygons':3000,'number_of_generation':1,'privacy':'Public','textures_generated':False},'observed_UI':{'faces':3211,'vertices':3161,'topology':'Quad','credits_before':200,'credits_after':200,'trial_count_before':2,'trial_count_after':1,'charged_credits_observed':0},'export':{'attempted_format':'GLB','filename':'protagonist_tripo_trial_v1_raw','result':'Upgrade to export ready-to-use 3D assets in multiple formats','model_file_downloaded':False,'paid_subscription_purchased':False,'local_Blender_source_created':False},'review':{'front_side_back_and_quarter_seen':True,'positive':['Recognizable clothed figure and natural body volume','Gown, sleeves and hair are volumetric rather than only image planes'],'issues':['Back hair inferred too long with pointed jagged ends compared with working back reference','Upper gown follows chest form more closely than simple loose garment reference','Thin raised strand-like shapes near forehead/hair need cleanup'],'not_verified':['Actual mesh connectivity or body/clothing/hair separation','UVs, normals, manifoldness and deformation topology','Physical scale, rigging and Godot import','Raw mesh statistics independent of UI report'],'user_art_approval':False},'screenshot_capture':{'original_UI_size':[1920,855],'same_crop_xy_exclusive':list(crop),'model_images_rescaled':False,'full_UI_screenshots':'Local only, excluded from Git to omit account UI and unrelated asset thumbnails'},'scope':'One free untextured cloud-model trial. No new PixelLab generations, no game scene or lighting changes.'}
(HERE/'generation_record.json').write_text(json.dumps(record,indent=2),encoding='utf8')
print('TRIPO_TRIAL_RECORD_SAVED;4actualmodelviews;noGLBdownload')
page='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>主角Tripo免费灰模试作 v1</title><style>body{background:#172020;color:#e1e7df;font:16px/1.7 system-ui;max-width:1400px;margin:30px auto;padding:0 24px}a{color:#a6d5d3}img{display:block;max-width:100%;height:auto}.grid{display:flex;flex-wrap:wrap;gap:18px}figure{margin:0}h1{font-size:26px}</style><h1>主角Tripo免费灰模试作 v1</h1><p>已在Tripo网页生成一个无纹理灰模。P2.0 Smart Mesh免费试用一次，目标3000四边面，界面统计3211面、3161顶点；没有扣减200点余额，试用2→1。只输入正面v2，后方结构由服务推断。</p><p><strong>GLB导出出现升级提示，未下载网格文件。</strong>当前可在<a href="https://studio.tripo3d.ai/workspace/generate/7407fbd8-8ff0-4ae7-bca8-2223e003c137">Tripo模型页</a>旋转查看。这里保存真实网页截图和来源，没有本地Blender工程／可导入Godot的角色资产。</p><p>后发偏长且发尾偏尖，上衣胸前较贴身，发际有细薄突起；这是需要进一步修整的初稿，不是最终模型。取得可编辑网格后先整理部件、比例、拓扑和UV，再用PixelLab制作像素贴图。<a href="README.md">来源、使用限制与下一步</a> · <a href="source/generation_record.json">实际设置与结果记录</a></p><div class="grid">'''
for name,label in [('front','正面'),('side','侧面'),('back','背面'),('quarter','斜侧')]:page+=f'<figure><figcaption>{label}</figcaption><a href="evidence/{name}.jpg"><img width="380" height="582" src="evidence/{name}.jpg"></a></figure>'
page+='</div><h2>网页统计（不是本地网格审计）</h2><img src="evidence/viewer_statistics.jpg"><h2>实际输入</h2><img width="192" height="256" src="source/input_front.png"></html>'
(EXP/'preview.html').write_text(page,encoding='utf8')
