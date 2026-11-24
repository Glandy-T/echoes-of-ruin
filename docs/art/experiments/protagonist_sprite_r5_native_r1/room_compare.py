from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
p=Path(__file__).resolve().parent
sheet=Image.new('RGB',(3*278,304),'#24292a')
draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
base=Image.open(p/'room_B.png').convert('RGB')
for i,(key,label) in enumerate([('B','B 原图'),('0','R5 正面'),('45','R5 斜 45°')]):
    im=Image.open(p/f'room_{key}.png').convert('RGB')
    assert im.size==base.size==(1280,720)
    bounds=ImageChops.difference(base,im).getbbox()
    if key!='B':
        assert bounds and bounds[0]>560 and bounds[2]<710 and bounds[1]>240 and bounds[3]<520,bounds
    sheet.paste(im.crop((501,245,779,517)),(278*i,32))
    draw.text((278*i+139,7),label,anchor='mt',font=font,fill='white')
sheet.save(p/'room_compare.png')
