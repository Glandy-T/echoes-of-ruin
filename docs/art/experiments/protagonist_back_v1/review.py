from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
p=Path(__file__).resolve().parent
def load(path):
    return Image.open(path).convert('RGBA')
front=load(p.parent/'protagonist_front_c_raw_v2/B_original.png')
side=load(p.parent/'protagonist_side_eye_v4/side.png')
mirror=load(p/'raw/mirror.png')
assert mirror.tobytes()==ImageOps.mirror(front).tobytes()
back=load(p/'back.png')
views=[front,side,mirror,back]
labels=['正面 B','侧面 eye_v4','正面水平翻转','背面']
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
nn=Image.Resampling.NEAREST
plate=Image.new('RGB',(768,437),'#53605d')
d=ImageDraw.Draw(plate)
for y in [3,30,86,127]:
    d.line((0,8+3*y,767,8+3*y),fill='#69756f')
for i,(im,label) in enumerate(zip(views,labels)):
    assert im.size==(128,128)
    shift=128-im.getbbox()[3]
    sprite=im.crop((32,0,96,128)).resize((192,384),nn)
    plate.paste(sprite,(i*192,8+3*shift),sprite)
    d.text((i*192+96,401),label,font=font,anchor='mt')
plate.save(p/'compare.png')
frame=load(p.parent/'protagonist_simplification_l123/evidence/game/game_L2_front.png')
bg=frame.crop((688,180,1008,524)).resize((160,172),nn).convert('RGB')
gain=[a/b for a,b in zip(frame.getpixel((640,360))[:3],(218,221,216))]
room=Image.new('RGB',(496,198),'#293531')
for i,(im,label) in enumerate(zip([front,side,back],['正面 B','侧面','背面'])):
    obj=im.crop(im.getbbox())
    s=obj.resize((round(obj.width*117/obj.height),117),nn)
    ch=s.split()
    lit=Image.merge('RGBA',tuple(c.point(lambda v,g=g: round(v*g)) for c,g in zip(ch,gain))+(ch[3],))
    tile=bg.copy()
    tile.paste(lit,(25-lit.width//2,41),lit)
    room.paste(tile,(168*i,0))
    ImageDraw.Draw(room).text((168*i+80,175),label,font=font,anchor='mt')
room.save(p/'room.png')
