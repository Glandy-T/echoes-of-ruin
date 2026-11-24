from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent
raw=Image.open(p.parent/'protagonist_front_color_c_v1/raw/master.png').convert('RGBA')
frame=Image.open(p.parent/'protagonist_simplification_l123/evidence/game/game_L2_front.png')
plate=frame.crop((688,180,1008,524)).resize((160,172),Image.Resampling.NEAREST).convert('RGB')
gain=[a/b for a,b in zip(frame.getpixel((640,360)),(218,221,216))]
sheet=Image.new('RGB',(648,205),'#293531')
face=Image.new('RGB',(320,192),'#52605b')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
for i,(name,label) in enumerate([('A_original','A 微暖 · 原脸'),('B_original','B 再暖一点 · 原脸'),('B_original','B 原脸'),('B_adult','B 稍成熟')]):
 im=Image.open(p/(name+'.png')).convert('RGBA')
 assert im.getchannel('A').tobytes()==raw.getchannel('A').tobytes()
 s=im.crop(im.getbbox()).resize((37,117),Image.Resampling.NEAREST)
 ch=s.split()
 lit=Image.merge('RGBA',tuple(c.point(lambda v,g=g:round(v*g)) for c,g in zip(ch,gain))+(ch[3],))
 tile=plate.copy();tile.paste(lit,(6,41),lit)
 x=160*i+(8 if i>=2 else 0)
 sheet.paste(tile,(x,0));ImageDraw.Draw(sheet).text((x+10,178),label,font=font)
 if i>=2:
  s=im.crop((50,2,80,34)).resize((150,160),Image.Resampling.NEAREST)
  face.paste(s,((i-2)*160,0),s);ImageDraw.Draw(face).text(((i-2)*160+30,168),label,font=font)
sheet.save(p/'room.png');face.save(p/'face.png')
