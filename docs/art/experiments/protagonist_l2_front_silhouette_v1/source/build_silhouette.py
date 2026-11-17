"""Front-only L2 silhouette revision; no painting, generation service or3D."""
from pathlib import Path
from hashlib import sha256
import json,shutil
from PIL import Image,ImageDraw,ImageChops,ImageFont

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT.parent/'protagonist_simplification_l123'
for folder in ['source/parts','editable','evidence']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
source=BASE/'silhouette/L2_front.png'
shutil.copyfile(source,ROOT/'source/L2_front_APPROVED.png')
all_geometry=json.loads((BASE/'source/geometry.json').read_text(encoding='utf8'))
old=all_geometry['views']['L2_front']['geometry']
new_gown=[(55,30),(59,29),(62,31),(66,31),(69,29),(73,30),(76,34),(76,45),(75,56),(76,64),(78,77),(79,86),(49,86),(50,77),(52,64),(53,56),(52,45),(52,34)]
new_hair=[(61,7),(63,6),(65,6),(67,7),(69,8),(71,10),(72,12),(72,17),(73,20),(72,23),(73,25),(70,25),(70,28),(68,26),(67,25),(61,25),(59,28),(58,26),(55,27),(56,24),(55,22),(56,18),(55,15),(56,12),(58,9)]

def poly(points):
    out=Image.new('L',(128,128));ImageDraw.Draw(out).polygon(points,fill=255);return out
def union(*masks):
    out=Image.new('L',(128,128))
    for m in masks:out=ImageChops.lighter(out,m)
    return out
def black(mask):
    image=Image.new('RGBA',(128,128),(0,0,0,255));image.putalpha(mask);return image

unchanged=[poly([(61,22),(67,22),(67,32),(61,32)]),poly(old['face'])]
for key in ['sleeve','arm','hand','leg','foot']:
    unchanged += [poly(old[key]),poly([(128-x,y) for x,y in old[key]])]
fixed=union(*unchanged)
baseline=Image.open(source).convert('RGBA')
reconstructed=union(fixed,poly(old['torso']),poly(old['hair']))
assert reconstructed.tobytes()==baseline.getchannel('A').tobytes()
gown=poly(new_gown);hair=poly(new_hair)
candidate=union(fixed,gown,hair)
new=black(candidate);new.save(ROOT/'front_silhouette.png')
parts={'unchanged_L2':fixed,'gown_A_line':gown,'short_hair_rounded':hair,'old_gown':poly(old['torso']),'old_hair':poly(old['hair'])}
for name,mask in parts.items():black(mask).save(ROOT/f'source/parts/{name}.png')
assert candidate.getbbox()[1]==6 and candidate.getbbox()[3]==123
assert set(new.getchannel('A').getdata())=={0,255}
assert {p[:3] for p in new.getdata() if p[3]}=={(0,0,0)}
# Differences must belong solely to the two editable shape domains.
domain=union(poly(old['torso']),gown,poly(old['hair']),hair)
changed=[]
for y in range(128):
    for x in range(128):
        if candidate.getpixel((x,y))!=reconstructed.getpixel((x,y)):
            assert domain.getpixel((x,y))
            changed.append([x,y])
def width(mask,y):
    xs=[x for x in range(128) if mask.getpixel((x,y))]
    return {'y':y,'x_min':min(xs),'x_max_inclusive':max(xs),'width_px':max(xs)-min(xs)+1}
measure={name:{'before':width(poly(old['torso']),y),'candidate':width(gown,y)} for name,y in [('chest',44),('waist',55),('hip',64),('lower_body',77),('hem',86)]}
assert measure['waist']['before']['width_px']==measure['waist']['candidate']['width_px']==23
assert measure['hem']['before']['width_px']==27 and measure['hem']['candidate']['width_px']==31
# A three-pixel crown and stepped arc replace the former seven-pixel flat top.
old_top=[x for x in range(128) if poly(old['hair']).getpixel((x,6))]
new_top=[x for x in range(128) if hair.getpixel((x,6))]
assert len(old_top)==7 and len(new_top)==3

manifest={'date':'2026-11-17','brief':'docs/art/PROTAGONIST_REDESIGN_BRIEF.md#4','status':'FRONT_SILHOUETTE_USER_REVIEW_PENDING',
    'approved_base':'../protagonist_simplification_l123/silhouette/L2_front.png','approved_base_sha256':sha256(source.read_bytes()).hexdigest(),
    'native_canvas':[128,128],'crown_y':6,'sole_y_exclusive':123,'visible_height_px':117,'chin_y_last':25,'head_height_px':20,'heads_high':117/20,
    'old_geometry':old,'candidate_gown_vertices':new_gown,'candidate_hair_vertices':new_hair,
    'unchanged':'Existing L2 face/jaw, neck, sleeves, arms, mitten-plus-thumb hands, legs, block feet, stance and knee-height hem. No side/back changes.',
    'changes':'Only front gown flare and short-hair outer contour. Crown apex narrowed 7px to 3px, same total head height and hair width.',
    'gown_measurements':measure,'crown_top_row_width_before':len(old_top),'crown_top_row_width_candidate':len(new_top),
    'silhouette_changed_pixels':len(changed),'silhouette_changed_coordinates':changed,
    'candidate_sha256':sha256((ROOT/'front_silhouette.png').read_bytes()).hexdigest(),
    'service_calls':{'PixelLab':0,'Tripo':0,'other_generation':0},
    'not_performed':['Two-tone rendering','Colour rendering','Face shadow','P12 or wristband','Side/back drawings','Stage-two costume','3D','Godot character replacement']}
(ROOT/'source/shape_record.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
review=Image.new('RGB',(1120,680),'#e6e5dc');d=ImageDraw.Draw(review)
for i,(image,title,caption) in enumerate([(baseline,'已选L2 · 原剪影','保留作基线，原文件不改'),(new,'L2正面 · 剪影修订待审','衣身微A字；弧形发顶与少量乱发梢')]):
    d.text((i*560+24,15),title,font=font,fill='#202a2c');d.text((i*560+24,51),caption,font=small,fill='#53615e')
    image=image.resize((512,512),Image.Resampling.NEAREST)
    review.paste(image,(i*560+24,94),image)
d.text((24,628),'两图均为128×128原生整数4倍；头顶、脚底、头身和站姿一致。这里只审黑剪影。',font=small,fill='#53615e')
review.save(ROOT/'evidence/before_after.png')
new.resize((512,512),Image.Resampling.NEAREST).save(ROOT/'evidence/candidate_4x.png')
# Local close-up proves hair curvature without showing unapproved face details.
hairproof=Image.new('RGB',(800,350),'#e6e5dc');hd=ImageDraw.Draw(hairproof)
for i,(im,title) in enumerate([(baseline,'原L2发顶'),(new,'修订：顶端弧度／乱发梢')]):
    hd.text((i*400+20,12),title,font=small,fill='#202a2c')
    crop=im.crop((51,3,77,32)).resize((208,232),Image.Resampling.NEAREST)
    hairproof.paste(crop,(i*400+88,62),crop)
hd.text((20,315),'同一区域整数8倍；只改外轮廓，不绘五官或脸部阴影。',font=small,fill='#53615e')
hairproof.save(ROOT/'evidence/hair_closeup.png')
print('Front-only silhouette candidate:',len(changed),'outline pixels changed; hem27→31; crown apex7→3.')
