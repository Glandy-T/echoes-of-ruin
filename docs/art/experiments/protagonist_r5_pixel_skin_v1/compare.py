from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent
out=Image.new('RGB',(760,386),'#303635')
draw=ImageDraw.Draw(out);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
for i,state in enumerate(['stand','walk']):
    im=Image.open(p/f'room_128_{state}.png').crop((505,245,765,590))
    out.paste(im,(i*260,36))
    draw.text((130+i*260,10),'站立' if i==0 else '迈步 · 第 21 帧',anchor='mt',font=font,fill='white')
out.paste(Image.open(p/'skin.png').resize((224,224),Image.Resampling.NEAREST),(528,74))
draw.text((642,10),'128 × 128 图集',anchor='mt',font=font,fill='white')
out.save(p/'comparison.png')
