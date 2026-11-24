from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent
paths=[p.parent/'protagonist_front_c_raw_v2/B_original.png',p.parent/'protagonist_side_eye_v4/side.png',p/'variant_1.png',p/'variant_2.png']
images=[Image.open(f).convert('RGBA') for f in paths]
labels=['正面 B','eye_v4','变体 1','变体 2']
bounds=images[0].getbbox()
assert images[1].getbbox()==images[2].getbbox()
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
nn=Image.Resampling.NEAREST
frame=Image.open(p.parent/'protagonist_simplification_l123/evidence/game/game_L2_front.png')
bg=frame.crop((688,180,1008,524)).resize((160,172),nn).convert('RGB')
gain=[a/b for a,b in zip(frame.getpixel((640,360)),(218,221,216))]
detail=Image.new('RGB',(1024,292),'#53605d')
room=Image.new('RGB',(664,198),'#293531')
for i,(im,label) in enumerate(zip(images,labels)):
    obj=im.crop(im.getbbox())
    big=im.crop((48,0,80,32)).resize((256,256),nn)
    x=i*168
    detail.paste(big,(i*256,0),big)
    ImageDraw.Draw(detail).text((i*256+128,264),label,font=font,anchor='mt')
    sprite=obj.resize((round(obj.width*117/obj.height),117),nn)
    channels=sprite.split()
    lit=Image.merge('RGBA',tuple(c.point(lambda v,g=g:round(v*g)) for c,g in zip(channels,gain))+(channels[3],))
    tile=bg.copy()
    tile.paste(lit,(25-lit.width//2,41),lit)
    room.paste(tile,(x,0))
    ImageDraw.Draw(room).text((x+80,175),label,font=font,anchor='mt')
detail.save(p/'compare.png')
room.save(p/'room.png')
def differences(a,b):
    return {(x,y) for y in range(128) for x in range(128) if a.getpixel((x,y))!=b.getpixel((x,y))}
assert differences(images[1],images[2])=={(69,17),(70,17),(69,18),(70,18),(71,18)}
assert differences(images[2],images[3])=={(70,16),(71,16),(72,16)}
