from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent
front=Image.open(p.parent/'protagonist_front_c_raw_v2/B_original.png').convert('RGBA')
side=Image.open(p/'side.png').convert('RGBA')
old=Image.open(p.parent/'protagonist_side_c_v1/side.png').convert('RGBA')
assert side.size==(128,128)
nn=Image.Resampling.NEAREST
def fit(im,h):
    obj=im.crop(im.getbbox())
    return obj.resize((round(obj.width*h/obj.height),h),nn)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
def pair(left,right,labels,name):
    plate=Image.new('RGB',(368,408),'#53605d')
    for i,im in enumerate((left,right)):
        sprite=fit(im,360)
        x=92+184*i
        plate.paste(sprite,(x-sprite.width//2,8),sprite)
        ImageDraw.Draw(plate).text((x,378),labels[i],font=font,anchor='mt')
    plate.save(p/name)
pair(front,side,['正面 B','新侧面'],'compare.png')
pair(old,side,['收窄前','收窄后'],'old_new.png')
frame=Image.open(p.parent/'protagonist_simplification_l123/evidence/game/game_L2_front.png')
bg=frame.crop((688,180,1008,524)).resize((160,172),nn).convert('RGB')
gain=[a/b for a,b in zip(frame.getpixel((640,360)),(218,221,216))]
sheet=Image.new('RGB',(496,198),'#293531')
for i,im in enumerate((front,old,side)):
    s=fit(im,117)
    ch=s.split()
    lit=Image.merge('RGBA',tuple(c.point(lambda v,g=g:round(v*g)) for c,g in zip(ch,gain))+(ch[3],))
    tile=bg.copy()
    tile.paste(lit,(25-s.width//2,41),lit)
    sheet.paste(tile,(168*i,0))
    ImageDraw.Draw(sheet).text((168*i+80,175),['正面 B','收窄前','收窄后'][i],font=font,anchor='mt')
sheet.save(p/'room.png')
