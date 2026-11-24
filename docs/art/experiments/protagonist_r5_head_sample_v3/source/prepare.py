"""Register the approved B expression, and isolate PixelLab hair texels for Aseprite."""
from pathlib import Path
import sys
from PIL import Image,ImageDraw
import numpy as np
p=Path(__file__).resolve().parent.parent
v2=p.parent/'protagonist_r5_face_v2'
sys.path.insert(0,str(p.parent/'protagonist_r5_pixel_skin_v1/source'))
from model import Model
ref=Image.open(p.parent/'protagonist_front_c_raw_v2/B_original.png').convert('RGBA')
skin=Image.open(v2/'skin.png').convert('RGB')
face=Image.open(v2/'source/face_overlay.png')
layer=Image.new('RGBA',skin.size)
for y in range(52,71):
    for x in range(45,72):
        if not face.getpixel((x,y))[3]:continue
        u=round(64+(x-58)*.82)
        row=round(17+(y-62)*.88)
        col=ref.getpixel((u,row))
        # Hair falling across the 2D face supplies the cast-shadow shape.
        # Keep that shadow softer than real 3D hair.
        if not col[3]:continue
        if max(col[:3])<115 and not (row==17 and 60<=u<=68):
            col=(146,124,113,255) if row<20 else (172,145,130,255)
        if 14<=row<=16 and u>=65 and max(col[:3])<180:
            col=(194,161,141,255)
        if row in (17,18) and u in (60,61,67,68):
            col=(112,98,87,255) if u<64 else (76,78,71,255)
            if row==18:col=(178,148,129,255)
        if row==18 and u==67:
            col=(109,99,87,255)
        if row==17 and u in (66,67):
            col=(72,77,70,255)
        if 20<=row<=22 and 63<=u<=65 and col[:3]!=(234,193,157):
            col=(208,173,147,255)
        if col[:3]!=skin.getpixel((x,y)):layer.putpixel((x,y),col)
layer.save(p/'source/expression.png')
m=Model(v2/'walk_pixel.glb');f=m.faces()
pos=m.attribute('POSITION')
_,ids=np.unique(pos.round(6),axis=0,return_inverse=True)
neighbors=[set() for _ in range(max(ids)+1)]
for a,b,c in ids[f]:
    neighbors[a].update((b,c));neighbors[b].update((a,c));neighbors[c].update((a,b))
top=ids[pos[:,1].argmax()]
seen={top};todo=[top]
while todo:
    new=neighbors[todo.pop()]-seen
    todo.extend(new);seen.update(new)
uv=m.attribute('TEXCOORD_0')
mask=Image.new('1',(512,512));draw=ImageDraw.Draw(mask)
for t in f[np.isin(ids[f[:,0]],list(seen))]:
    draw.polygon([tuple(pt) for pt in uv[t]*512],fill=1)
mask=mask.convert('L').resize((128,128),Image.Resampling.BOX)
hair=Image.new('RGBA',skin.size)
tones={(28,39,35):(43,53,51),(46,57,51):(50,60,57),(82,86,85):(61,72,66),(100,97,87):(71,82,74),(112,125,115):(78,89,79),(136,150,138):(84,95,85)}
for y in range(128):
    for x in range(128):
        rgb=skin.getpixel((x,y))
        if mask.getpixel((x,y))>0 and rgb in tones:hair.putpixel((x,y),(*tones[rgb],255))
hair.save(p/'source/hair.png')


