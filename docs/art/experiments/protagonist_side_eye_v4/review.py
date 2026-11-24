from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent
paths=[p.parent/'protagonist_front_c_raw_v2/B_original.png',p.parent/'protagonist_side_limb_v3/side.png',p/'side.png']
images=[Image.open(f).convert('RGBA') for f in paths]
labels=['正面 B','侧面 · 改前','侧面 · 改后']
bounds=images[0].getbbox()
assert images[1].getbbox()==images[2].getbbox()
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
nn=Image.Resampling.NEAREST
frame=Image.open(p.parent/'protagonist_simplification_l123/evidence/game/game_L2_front.png')
bg=frame.crop((688,180,1008,524)).resize((160,172),nn).convert('RGB')
gain=[a/b for a,b in zip(frame.getpixel((640,360)),(218,221,216))]
detail=Image.new('RGB',(768,292),'#53605d')
room=Image.new('RGB',(496,198),'#293531')
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
changes=[(x,y) for y in range(128) for x in range(128) if images[1].getpixel((x,y))!=images[2].getpixel((x,y))]
assert set(changes)=={(70,16),(71,16),(69,17),(70,17),(71,17),(71,18)}
assert images[1].getchannel('A').tobytes()==images[2].getchannel('A').tobytes()
