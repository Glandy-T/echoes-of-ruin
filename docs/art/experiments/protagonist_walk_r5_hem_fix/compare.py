from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent
canvas=Image.new('RGB',(680,336),'#424a49')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
for i,(folder,label) in enumerate(((p.parent/'protagonist_smart_mesh_walk_r5','R5 原版'),(p,'裙摆权重修正'))):
    img=Image.open(folder/'walk_s03.png').convert('RGBA')
    canvas.paste(img,(10+i*340,0),img)
    ImageDraw.Draw(canvas).text((170+i*340,310),label+' · 第 21 帧',anchor='mt',font=font)
canvas.save(p/'before_after.png')
