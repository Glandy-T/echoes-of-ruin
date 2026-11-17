"""Front-only two-value block study inside the approved immutable L2 mask.

This is the brief's silhouette -> two-value -> final-colour approval stage,
not production texture painting or procedural ageing. No generation calls.
"""
from pathlib import Path
from hashlib import sha256
import json, shutil
from PIL import Image, ImageDraw, ImageChops, ImageFont

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT.parent/'protagonist_l2_front_silhouette_v1'
for folder in ['source/parts','editable','evidence']:
    (ROOT/folder).mkdir(parents=True,exist_ok=True)
source=BASE/'front_silhouette.png'
shutil.copyfile(source,ROOT/'source/APPROVED_front_silhouette.png')
approved=Image.open(source).convert('RGBA')
alpha=approved.getchannel('A')
record=json.loads((BASE/'source/shape_record.json').read_text(encoding='utf8'))
old=record['old_geometry']
# The two neutral study values match the selected L2 comparison, not a new
# skin/hair/fabric palette. Deliberately no eyes, face shadow or identity marks.
LIGHT=(218,221,216,255)
DARK=(79,94,99,255)

def poly(points):
    out=Image.new('L',(128,128));ImageDraw.Draw(out).polygon(points,fill=255)
    return out
def union(*masks):
    out=Image.new('L',(128,128))
    for m in masks: out=ImageChops.lighter(out,m)
    return out
def intersect(a,b): return ImageChops.multiply(a,b)
def paint(mask,colour):
    out=Image.new('RGBA',(128,128),colour);out.putalpha(mask);return out

gown=poly(record['candidate_gown_vertices'])
hair=poly(record['candidate_hair_vertices'])
face_clear=poly(old['face_clear'])
hair_visible=ImageChops.subtract(hair,face_clear)
# Broad connected planes only. The gown shadow follows its mild A-line edge;
# no narrow waist stripe, belt, decorative folds, ageing or outlines are added.
gown_shadow_points=[(72,33),(76,35),(75,56),(76,64),(78,77),(79,86),
                    (74,86),(73,77),(72,64),(71,55)]
gown_shadow=intersect(poly(gown_shadow_points),gown)
sleeves=union(poly(old['sleeve']),poly([(128-x,y) for x,y in old['sleeve']]))
sleeve_planes=intersect(union(poly([(47,39),(54,40),(52,44),(47,42)]),
                                    poly([(74,35),(78,36),(81,41),(76,44),(74,41)])),sleeves)
skin=union(*[poly(old[k]) for k in ['arm','hand','leg','foot']],
           *[poly([(128-x,y) for x,y in old[k]]) for k in ['arm','hand','leg','foot']])
skin_planes=intersect(union(
    poly([(51,44),(52,44),(49,65),(47,68),(46,76),(45,76),(46,66),(48,55)]),
    poly([(79,44),(80,44),(84,64),(86,69),(86,75),(84,76),(83,68),(82,64)]),
    poly([(59,87),(61,87),(61,122),(59,122)]),
    poly([(71,87),(73,87),(72,116),(72,119),(77,120),(77,122),(71,122)])),skin)
shade=intersect(union(hair_visible,gown_shadow,sleeve_planes,skin_planes),alpha)
base=paint(alpha,LIGHT)
shadow=paint(shade,DARK)
two=Image.alpha_composite(base,shadow)
assert two.getchannel('A').tobytes()==alpha.tobytes()
assert set(two.getchannel('A').getdata())=={0,255}
assert {p for p in two.getdata() if p[3]}=={LIGHT,DARK}
# Face opening is deliberately one flat light value, without eye-band shadow.
face_test=intersect(face_clear,poly(old['face']))
assert all(two.getpixel((x,y))==LIGHT for y in range(128) for x in range(128) if face_test.getpixel((x,y)))
two.save(ROOT/'front_twotone.png')
base.save(ROOT/'source/parts/base_light.png')
shadow.save(ROOT/'source/parts/shadow_dark.png')
two.resize((512,512),Image.Resampling.NEAREST).save(ROOT/'evidence/twotone_4x.png')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
sheet=Image.new('RGB',(1120,680),'#a9b2ad');draw=ImageDraw.Draw(sheet)
for i,(im,title,caption) in enumerate([
    (approved,'已认可 · L2正面剪影','微A字衣身、弧形发顶；作为锁定外形'),
    (two,'正面两色体块 · 待审','仅亮暗两色；无脸部阴影、无标记')]):
    draw.text((i*560+24,15),title,font=font,fill='#202a2c')
    draw.text((i*560+24,51),caption,font=small,fill='#344540')
    enlarged=im.resize((512,512),Image.Resampling.NEAREST)
    sheet.paste(enlarged,(i*560+24,94),enlarged)
draw.text((24,628),'128×128原生画布 · 同尺寸整数4倍 · 外轮廓逐像素一致 · 亮暗体块研究，尚非成品配色',font=small,fill='#344540')
sheet.save(ROOT/'evidence/silhouette_twotone.png')
detail=Image.new('RGB',(800,400),'#a9b2ad');dd=ImageDraw.Draw(detail)
for i,(box,title) in enumerate([((53,3,75,32),'头部：保留单色面部'),((47,27,82,89),'衣身：简洁连续亮暗面')]):
    factor=8 if i==0 else 5
    crop=two.crop(box).resize(((box[2]-box[0])*factor,(box[3]-box[1])*factor),Image.Resampling.NEAREST)
    dd.text((i*400+20,12),title,font=small,fill='#202a2c')
    detail.paste(crop,(i*400+100,65),crop)
detail.save(ROOT/'evidence/details.png')
manifest={'date':'2026-11-17','stage':'L2 front two-value block study; pending user approval',
    'approved_silhouette':'../protagonist_l2_front_silhouette_v1/front_silhouette.png',
    'approved_source_sha256':sha256(source.read_bytes()).hexdigest(),
    'native_canvas':[128,128],'visible_height_px':117,'alpha_equal':True,
    'changed_silhouette_pixels':0,'neutral_study_palette':{'light':list(LIGHT),'dark':list(DARK)},
    'gown_shadow_vertices':gown_shadow_points,'face_opening_single_light_value':True,
    'method':'Editable flat block study, same two neutral values as selected L2, intersected with approved silhouette. Not a final texture.',
    'services':{'PixelLab':0,'Tripo':0,'other_generation':0},
    'not_added':['face shadow','eyes or other facial features','P12','wristband','stage two costume','ageing texture'],
    'not_made':['final colour palette','side','back','3D','Godot character replacement']}
(ROOT/'source/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PASS: exactly two neutral colours; 0 silhouette pixels changed; face opening remains flat light.')
