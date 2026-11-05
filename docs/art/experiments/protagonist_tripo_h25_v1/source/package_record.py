"""Package actual model screenshots and provenance, without altering any artwork."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib,json

EXP=Path(__file__).resolve().parents[1];ROOT=EXP.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
front=EXP/'source/input_front.png'
assert front.read_bytes()==(ROOT/'docs/art/experiments/protagonist_turnaround_v2/views/front.png').read_bytes()
audit=json.loads((EXP/'source/mesh_audit.json').read_text('utf8'))
assert audit['mesh_objects']==1 and audit['meshes'][0]['triangles']==2943
assert audit['raw_sha256']==sha(EXP/'model/protagonist_tripo_h25_v1_raw.glb')
Image.open(EXP/'source/generated_full.jpg').crop((780,150,1200,742)).save(EXP/'evidence/web_generated.jpg',quality=95)
Image.open(EXP/'source/export_full.jpg').crop((1090,523,1400,790)).save(EXP/'evidence/free_export_menu.jpg',quality=95)
sheet=Image.new('RGB',(1280,390),(36,44,45));draw=ImageDraw.Draw(sheet)
for i,name in enumerate(['front','side','back','quarter']):
 im=Image.open(EXP/'evidence'/f'blender_{name}.png')
 assert im.size==(1280,720)
 im=im.crop((360,0,920,720));im.thumbnail((280,360))
 sheet.paste(im,(i*320+(320-im.width)//2,25));draw.text((i*320+20,6),name.upper(),fill=(220,230,225))
sheet.save(EXP/'evidence/blender_views.jpg',quality=95)
record={'date':'2026-11-05','provider':'Tripo Studio official web UI via Chrome extension','model_id':'0d9ffe69-a83a-43dc-a2cf-ec9c967dae4e','model_url':'https://studio.tripo3d.ai/workspace/generate/0d9ffe69-a83a-43dc-a2cf-ec9c967dae4e','input':{'file':'input_front.png','sha256':sha(front),'views':['front'],'NoAI_reference_uploaded':False},'settings':{'path':'HD Model','AI_model':'H2.5 Legacy','target_polygons':3000,'topology':'Triangle','Texture':False,'Generate_in_Parts':False,'8K_Texture':False,'AI_Complete':False,'privacy':'Public','generation_count':1},'credits':{'before':200,'after':185,'consumed':15,'paid_purchase':False},'download':{'method':'Official Export button, GLB','initial_free_exports_UI':15,'three_local_files_found':True,'all_three_SHA256_equal':True,'selected_raw_sha256':audit['raw_sha256'],'bytes':71604,'original_downloads_preserved':True,'notes':'Browser download event timed out while normal exports wrote files to a custom download folder. User identified folder. No internal model extraction.'},'blender':{'version':audit['blender_version'],'source':'model/protagonist_h25_inspection.blend','mesh_objects':1,'vertices':1463,'triangles':2943,'UV_layers':0,'armatures':0,'raw_geometry_modified':False,'preview_resolution':[1280,720]},'visual_review':{'views':['front','side','back','quarter'],'issues':['Jagged fragmented/folded rear hair geometry visible in back and side views','Hands reduced to coarse merged finger blocks','Body, gown and hair not semantically separated'],'user_approval':False,'ready_for_final_textures_or_animation':False},'scope':'Single free gray-model trial, actual download and Blender inspection. No scene edits, new textures, rigging or Godot replacement.'}
(EXP/'source/generation_record.json').write_text(json.dumps(record,indent=2),encoding='utf8')
page='''<!doctype html><html lang="zh"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>主角 H2.5 免费灰模：Blender 实测</title><style>body{max-width:1300px;margin:30px auto;padding:0 20px;background:#182123;color:#e2e8e4;font:16px/1.75 system-ui}a{color:#9cddda}img{display:block;max-width:100%;height:auto}h1{font-size:27px}.views{display:grid;grid-template-columns:repeat(auto-fit,minmax(470px,1fr));gap:15px}.views img{width:100%}figure{margin:0}</style><h1>主角 H2.5 免费灰模：Blender 实测</h1><p><strong>官方免费导出成功，已下载GLB并在Blender打开。</strong>只生成一次，消耗15免费点，余额185。三份重复下载文件哈希相同，本目录只留一份，原下载保留。</p><p><a href="model/protagonist_h25_inspection.blend">Blender检查工程</a> · <a href="model/protagonist_tripo_h25_v1_raw.glb">原始GLB</a> · <a href="README.md">完整检查说明</a> · <a href="source/mesh_audit.json">实际网格数据</a> · <a href="https://studio.tripo3d.ai/workspace/generate/0d9ffe69-a83a-43dc-a2cf-ec9c967dae4e">Tripo模型页</a></p><p>实际1463顶点／2943三角面、1个网格对象；没有UV、骨架或贴图。后发背面有明显碎裂尖刺状面片，手指粗糙，身体／白袍／头发未合理分件。<strong>这版仅作粗形和流程验证，不直接进入正式贴图／绑定。</strong>没有修改原始几何、Room1或4F。</p><h2>实际Blender四视图</h2><p>相同原始模型、1280×720灰模审查；下方为真实渲染，没有AI重画。背面问题须单独审看。</p><img src="evidence/blender_views.jpg"><div class="views">'''
for name,label in [('front','正面'),('side','侧面'),('back','背面：后发问题'),('quarter','斜侧')]:page+=f'<figure><figcaption>{label}</figcaption><a href="evidence/blender_{name}.png"><img src="evidence/blender_{name}.png"></a></figure>'
page+='</div><h2>网页生成与免费导出证据</h2><img src="evidence/web_generated.jpg"><img src="evidence/free_export_menu.jpg"><p>完成形体／分件／拓扑与UV后，再按既定PixelLab流程制作像素贴图。当前没有新纹理、绑定或实机角色替换。</p></html>'
(EXP/'preview.html').write_text(page,encoding='utf8')
print('PACKAGED_ACTUAL_H25_GLB_AND_BLENDER_REVIEW')
