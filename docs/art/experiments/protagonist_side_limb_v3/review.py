from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent
paths=[p.parent/'protagonist_side_c_v1/side.png',p.parent/'protagonist_side_limb_v2/side.png',p/'side.png']
images=[Image.open(f).convert('RGBA') for f in paths]
labels=['原侧面','收窄版（退回）','新版 · 轻收']
bounds=images[0].getbbox()
assert all(im.getbbox()==bounds for im in images)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
nn=Image.Resampling.NEAREST
frame=Image.open(p.parent/'protagonist_simplification_l123/evidence/game/game_L2_front.png')
bg=frame.crop((688,180,1008,524)).resize((160,172),nn).convert('RGB')
gain=[a/b for a,b in zip(frame.getpixel((640,360)),(218,221,216))]
detail=Image.new('RGB',(504,414),'#53605d')
room=Image.new('RGB',(496,198),'#293531')
for i,(im,label) in enumerate(zip(images,labels)):
    obj=im.crop(bounds)
    big=obj.resize((obj.width*3,obj.height*3),nn)
    x=i*168
    detail.paste(big,(x+84-big.width//2,8),big)
    ImageDraw.Draw(detail).text((x+84,387),label,font=font,anchor='mt')
    sprite=obj.resize((round(obj.width*117/obj.height),117),nn)
    channels=sprite.split()
    lit=Image.merge('RGBA',tuple(c.point(lambda v,g=g:round(v*g)) for c,g in zip(channels,gain))+(channels[3],))
    tile=bg.copy()
    tile.paste(lit,(25-lit.width//2,41),lit)
    room.paste(tile,(x,0))
    ImageDraw.Draw(room).text((x+80,175),label,font=font,anchor='mt')
detail.save(p/'compare.png')
room.save(p/'room.png')
for y in range(128):
    a,b=images[0],images[2]
    if 88<=y<=118:
        left,_,right,_=a.crop((0,y,128,y+1)).getbbox()
        new_left,_,new_right,_=b.crop((0,y,128,y+1)).getbbox()
        assert new_left==left and right-new_right in (1,2)
        assert a.crop((0,y,new_right-1,y+1)).tobytes()==b.crop((0,y,new_right-1,y+1)).tobytes()
    elif not 45<=y<=67:
        assert a.crop((0,y,128,y+1)).tobytes()==b.crop((0,y,128,y+1)).tobytes()
