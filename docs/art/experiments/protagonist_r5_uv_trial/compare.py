from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent
out=Image.new('RGB',(980,374),'#24292a')
draw=ImageDraw.Draw(out);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
for i,(size,pose) in enumerate([(128,'stand'),(256,'stand'),(128,'walk'),(256,'walk')]):
    image=Image.open(p/f'room_{size}_{pose}.png')
    crop=image.crop((545,250,790,580))
    out.paste(crop,(245*i,40))
    draw.text((245*i+122,10),f'{size} × {size} · '+('站立' if pose=='stand' else '迈步'),anchor='mt',font=font,fill='white')
out.save(p/'comparison.png')
