from pathlib import Path
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parent
game=Image.open(p.parent/'protagonist_simplification_l123/evidence/game/game_L2_front.png').convert('RGB')
plate=game.crop((688,180,1008,524)).resize((160,172),Image.Resampling.NEAREST)
base=Image.open(p.parent/'protagonist_l2_front_twotone_v1/front_twotone.png').convert('RGBA')
ref=game.getpixel((640,360))
gain=[a/b for a,b in zip(ref,(218,221,216))]
sheet=Image.new('RGB',(800,202),'#293531')
board=Image.new('RGB',(960,466),'#52605b')
for i,name in enumerate(['L2','A','B','C','D']):
    im=base if i==0 else Image.open(p/(name+'.png')).convert('RGBA')
    im=im.crop(im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox())
    shape=im.resize((round(im.width*117/im.height),117),Image.Resampling.NEAREST)
    print(name,shape.size,ref)
    if i:
        big=im.resize((round(im.width*416/im.height),416),Image.Resampling.NEAREST)
        x=(i-1)*240
        board.paste(big,(x+(240-big.width)//2,14),big)
        ImageDraw.Draw(board).text((x+116,440),name)
    channels=shape.split()
    lit=Image.merge('RGBA',tuple(c.point(lambda v,g=g:round(v*g)) for c,g in zip(channels,gain))+(channels[3],))
    panel=plate.copy()
    panel.paste(lit,(24-lit.width//2,158-117),lit)
    panel.save(p/('room_'+name+'.png'))
    sheet.paste(panel,(160*i,0))
    ImageDraw.Draw(sheet).text((160*i+73,181),name)
sheet.save(p/'room.png')
board.save(p/'concepts.png')
