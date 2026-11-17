"""Package recorded local refinement and compare at the approved native scale."""
from pathlib import Path
from hashlib import sha256
import json
import struct
import shutil
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent.parent
raw_path=ROOT/'raw/front.png'
original=Image.open(raw_path).convert('RGBA')
raw=Image.open(ROOT/'front_apose.png').convert('RGBA')
refinement=json.loads((ROOT/'source/local_refinement.json').read_text(encoding='utf8'))
readback=Image.open(ROOT/'evidence/aseprite_readback.png').convert('RGBA')
guide=Image.open(ROOT/'source/apose_GUIDE.png').convert('RGBA')
assert raw.size==readback.size==guide.size==(128,128)
assert raw.getchannel('A').tobytes()==readback.getchannel('A').tobytes()
assert all(a==b for a,b in zip(raw.getdata(),readback.getdata()) if a[3])
assert original.getchannel('A').tobytes()==raw.getchannel('A').tobytes()
changed=[(i%128,i//128) for i,(a,b) in enumerate(zip(original.getdata(),raw.getdata())) if a!=b]
assert len(changed)==refinement['changed_pixels']
assert all(56<=x<=72 and 41<=y<=44 for x,y in changed)
raw.resize((512,512),Image.Resampling.NEAREST).save(ROOT/'evidence/apose_4x.png')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
preview=Image.new('RGB',(1120,650),'#273033')
draw=ImageDraw.Draw(preview)
for i,(image,title,caption) in enumerate([(guide,'已认可外形 v3','只扩左右透明画布，人物未缩放'),(raw,'本轮 A 姿势／机织收袖口','面料已确认；姿势与收袖口成图待审')]):
    draw.text((i*560+24,15),title,font=font,fill='#e4ece8')
    draw.text((i*560+24,49),caption,font=small,fill='#b8cbc4')
    magnified=image.resize((512,512),Image.Resampling.NEAREST)
    preview.paste(magnified,(i*560+24,89),magnified)
    # Registration lines are outside the artwork and only appear in the proof.
    for row,label in [(6,'头顶参考'),(123,'脚底参考')]:
        yy=89+row*4
        draw.line((i*560+20,yy,i*560+540,yy),fill='#657d71')
draw.text((24,619),'两张均为原生整数4倍，未等高重采样；绿色线只用于核对，不进入素材。',font=small,fill='#bacbc5')
preview.save(ROOT/'evidence/pose_comparison.png')
head_box=(49,5,79,29)
head_diff=sum(a!=b for a,b in zip(raw.crop(head_box).getdata(),guide.crop(head_box).getdata()))
report={'native_size':list(raw.size),'visible_bounds':list(raw.getbbox()),'visible_rgb_colours':len({p[:3] for p in raw.getdata() if p[3]}),'alpha_values':sorted(set(raw.getchannel('A').getdata())),'raw_sha256':sha256(raw_path.read_bytes()).hexdigest(),'final_byte_identical_to_raw':False,'final_sha256':sha256((ROOT/'front_apose.png').read_bytes()).hexdigest(),'local_refinement':refinement,'aseprite_visible_pixels_and_alpha_exact':True,'local_refined_pixels':len(changed),'head_region_comparison_box':list(head_box),'head_region_changed_rgba_pixels_vs_guide':head_diff,'head_difference_boundary':'This is a registration measurement only, not automatic likeness approval.','pose_review':'pending','not_verified':['side/back consistency','3D mesh openings and internal surfaces','garment fit and bone deformation','final character approval']}
binary=(ROOT/'editable/front_apose.aseprite').read_bytes()
count=struct.unpack_from('<H',binary,134)[0];off=144;layers=[]
for _ in range(count):
    size,kind=struct.unpack_from('<IH',binary,off);data=binary[off+6:off+size]
    if kind==0x2004:
        length=struct.unpack_from('<H',data,16)[0]
        layers.append({'name':data[18:18+length].decode('utf8'),'visible':bool(struct.unpack_from('<H',data)[0]&1)})
    off+=size
assert len(layers)==5 and all(not x['visible'] for x in layers if x['name'].endswith('_hidden'))
report.update(aseprite_layers=layers,final_matches_aseprite_readback=True,raw_to_final_changes_confined_to_recorded_region=True)
(ROOT/'source/validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
record=json.loads((ROOT/'source/generation_record.json').read_text(encoding='utf8'))
record.update(status='front_apose_material_cuff_candidate_user_review_pending',local_painted_pixels=len(changed),local_refinement='source/local_refinement.json',final_sha256=report['final_sha256'],raw_sha256=report['raw_sha256'],actual_size=report['native_size'],actual_visible_bounds=report['visible_bounds'],actual_visible_rgb_colours=report['visible_rgb_colours'])
(ROOT/'source/generation_record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>主角 A 姿势 v4</title><style>body{max-width:1160px;margin:24px auto;padding:0 20px;background:#1c2528;color:#dfe9e4;font:16px/1.7 system-ui}a{color:#a9dcd4}img{max-width:100%;height:auto}.native{image-rendering:pixelated;background:#273033}h1{font-size:26px}</style><h1>主角正面 A 姿势 v4 · 待审</h1><p>保留v3成人比例和像素画法；面料已确认为细密哑光、略挺的涤纶混纺机织布。袖口已收窄，成图待审。鼻子以上的阴影保留为之后的贴图修改。</p><p><a href="README.md">制作说明与3D检查顺序</a> · <a href="front_apose.png">原生PNG</a> · <a href="editable/front_apose.aseprite">分层Aseprite</a> · <a href="source/generation_record.json">请求及额度记录</a></p><img class="native" src="evidence/pose_comparison.png" alt="v3与A姿势同原生尺度对比"><p>两图均整数4倍；只是建模参考，并未生成3D、补侧背面或替换游戏角色。</p><img class="native" src="front_apose.png" width="128" height="128" alt="原生一倍"><img class="native" src="front_apose.png" width="512" height="512" alt="整数四倍"><h2>宽袖与收袖口对照</h2><img class="native" src="evidence/material_comparison.png" alt="同姿势收袖口前后"><p>最终图有独立Aseprite局部精修层，清掉胸前意外横线；官网原图另存。</p><h2>PixelLab官网原始结果</h2><img src="evidence/pixellab_result.jpg" alt="PixelLab完成截图"></html>'''
(ROOT/'preview.html').write_text(html+'\n',encoding='utf8')
(ROOT/'preview.md').write_text('# 主角 A 姿势 v4\n\n[说明与后续3D检查](README.md) · [原生PNG](front_apose.png) · [分层Aseprite](editable/front_apose.aseprite)\n\n![同原生尺度对比](evidence/pose_comparison.png)\n\n机织混纺面料已确认，收袖口A姿势成图待审；尚无新3D模型。\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))

# Material/cuff comparison: same A-pose and same native display scale.
before=Image.open(ROOT/'source/material_GUIDE.png').convert('RGBA')
material=Image.new('RGB',(1120,650),'#273033');md=ImageDraw.Draw(material)
for i,(im,title,caption) in enumerate([(before,'原宽袖 · 仅留姿势来源','用户指出接近浴衣，不作服装母版'),(raw,'收袖口 · 哑光机织休眠服','面料已确认，成图待审；同原生尺度')]):
 md.text((i*560+24,15),title,font=font,fill='#e4ece8');md.text((i*560+24,49),caption,font=small,fill='#b8cbc4')
 im=im.resize((512,512),Image.Resampling.NEAREST);material.paste(im,(i*560+24,89),im)
md.text((24,619),'两图均为原生整数4倍；保持同一A姿势与117px人物高度，鼻以上阴影尚未添加。',font=small,fill='#bacbc5')
material.save(ROOT/'evidence/material_comparison.png')
