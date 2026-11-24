from pathlib import Path
from collections import Counter
from PIL import Image,ImageDraw,ImageFont,ImageChops
import json
p=Path(__file__).resolve().parent
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
def board(tags,crops,file):
    panels=[]
    for key,label in tags:
        row=[]
        for prefix,title in [('before','区域平涂'),('after','A · 三阶')]:
            image=Image.open(p/f'{prefix}_{key}.png').convert('RGB')
            row.append((image.crop(crops[key]),title+' · '+label))
        panels.append(row)
    w,h=panels[0][0][0].size
    out=Image.new('RGB',(2*w,(h+33)*len(panels)),'#24292a')
    draw=ImageDraw.Draw(out)
    for y,row in enumerate(panels):
        for x,(im,title) in enumerate(row):
            out.paste(im,(x*w,y*(h+33)+33))
            draw.text((x*w+w/2,y*(h+33)+7),title,anchor='mt',font=font,fill='white')
    out.save(p/file)
im=Image.open(p/'after_neutral.png').convert('RGB')
w,h=im.size
box=(w//2-int(h*.44),0,w//2+int(h*.44),h)
board([('neutral','中性光')],{'neutral':box},'neutral_compare.png')
tags=[('room_stand','站立'),('room_walk','行走 · 第 21 帧')]
board(tags,{key:(490,235,810,557) for key,_ in tags},'room_compare.png')
hits=Counter(im.getdata())
palette=[(231,223,207),(190,182,167),(128,144,140)]
qa={'neutral_palette_pixel_counts':{str(c):hits[c] for c in palette},'room_difference_bounds':{}}
for key,_ in tags:
    a,b=[Image.open(p/f'{v}_{key}.png').convert('RGB') for v in ('before','after')]
    qa['room_difference_bounds'][key]=ImageChops.difference(a,b).getbbox()
(p/'qa.json').write_text(json.dumps(qa,indent=2))
print(qa)
