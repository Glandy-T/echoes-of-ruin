from PIL import Image,ImageDraw,ImageFont,ImageChops
from pathlib import Path
p=Path(__file__).resolve().parents[1]
e=p.parent
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
game=Image.open(e/'protagonist_simplification_l123/evidence/game/game_L2_front.png').convert('RGB')
plate=game.crop((688,180,1008,524)).resize((160,172),Image.Resampling.NEAREST)
ref=game.getpixel((640,360))
gain=[a/b for a,b in zip(ref,(218,221,216))]
sheet=Image.new('RGB',(324,200),'#293531')
board=Image.new('RGB',(640,420),'#56615e')
draw=ImageDraw.Draw(board)
base=Image.open(e/'protagonist_l2_front_twotone_v1/front_twotone.png').convert('RGBA')
variants=[Image.open(p/f'front_{v}.png').convert('RGBA') for v in 'AB']
mask=Image.open(p/'source/cloth.png').convert('L')
differences=0
for x in range(128):
 for y in range(128):
  a,b=[im.getpixel((x,y)) for im in variants]
  assert a[3]==b[3]==base.getpixel((x,y))[3]
  if a[3] and a!=b:
   assert mask.getpixel((x,y))
   differences+=1
assert differences>0
for i,im in enumerate(variants):
 sh=im.crop(im.getbbox())
 channels=sh.split()
 lit=Image.merge('RGBA',tuple(c.point(lambda v,g=g:round(v*g)) for c,g in zip(channels,gain))+(channels[3],))
 panel=plate.copy()
 panel.paste(lit,(24-lit.width//2,158-117),lit)
 sheet.paste(panel,(164*i,0))
 ImageDraw.Draw(sheet).text((164*i+20,174),['A  微暖','B  再暖一点'][i],font=font)
sheet.save(p/'room.png')
concept=Image.open(e/'protagonist_front_concepts_1124/C.png').convert('RGBA')
for i,(im,label) in enumerate(zip([base,concept,*variants],['认可两色版','概念 C','A  微暖','B  再暖一点'])):
 sh=im.crop(im.getbbox())
 sh=sh.resize((round(sh.width*351/sh.height),351),Image.Resampling.NEAREST)
 board.paste(sh,(160*i+(160-sh.width)//2,18),sh)
 draw.text((160*i+32,379),label,font=font)
board.save(p/'compare.png')
print('Outside alpha differences: 0. Wardrobe-only differences:',differences)
