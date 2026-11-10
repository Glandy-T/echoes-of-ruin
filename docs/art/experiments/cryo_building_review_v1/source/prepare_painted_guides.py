"""Prepare nonblank native-size guides from owned inherited/PixelLab maps.

These are ONLY generation inputs. No transformed legacy crop is promoted as a
new PixelLab material. No resizing, procedural grain, or synthetic ageing.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import json

S=Path(__file__).resolve().parent; E=S.parent; R=S.parents[4];T=R/'assets/art/cryo_building_review_v1/textures'; J=S/'jobs'
seed=Image.open(T/'M03.png').convert('RGB'); assert seed.size==(192,256)
base=Image.new('RGB',(256,256));base.paste(seed,(0,0));base.paste(seed.crop((128,0,192,256)),(192,0))
def adjust(image, target):
    median=(124,131,128)
    values=tuple(int(target[i:i+2],16) for i in (0,2,4))
    channels=[ch.point([max(0,min(255,round((x-med)*.60+t))) for x in range(256)]) for ch,med,t in zip(image.split(),median,values)]
    return Image.merge('RGB',channels)
ids={'M05-L':'A7B0AA','M05-D':'4D6065','M07':'71858A','M06-01':'B9BDB2','M06-02':'B9BDB2','M06-03':'B9BDB2','M06-J':'B9BDB2','M06-R':'B9BDB2'}
for i,(name,color) in enumerate(ids.items()):
    s=base if i%2==0 else base.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    q=adjust(s,color)
    if name in ['M06-J','M06-R']:
        d=ImageDraw.Draw(q)
        if name=='M06-J':d.line((0,0,0,255),fill='#687771',width=1)
        else:d.line((118,0,150,0),fill='#687771',width=1)
    q.save(J/name/'painted_input.png')
for row in json.loads((S/'requests.json').read_text(encoding='utf-8')):
    name=row['name']
    if row['group']!='J05':continue
    dark=name.startswith('EL') or name=='EN-B'; m='M05-D' if dark else 'M05-L'; p=J/name
    guide=Image.open(p/'guide.png').convert('RGB'); mask=Image.open(p/'edit_mask.png').convert('L')
    img=Image.open(J/m/'painted_input.png').convert('RGB').crop((0,0,*guide.size))
    Image.composite(img,guide,mask).save(p/'painted_input.png')
print('Prepared native underpainted guides for 14 texture tasks')
