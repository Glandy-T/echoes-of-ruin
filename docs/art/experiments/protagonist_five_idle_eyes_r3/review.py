from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import numpy as np
p=Path(__file__).resolve().parent
old=p.parent/'protagonist_five_idle_r1'
b=p.parent/'protagonist_front_c_raw_v2/B_original.png'
cols=[('B',b,old/'room_B.png'),('0°',old/'final_0.png',old/'room_0.png')]
for a in ['45','90']:
    for d,title in [(p.parent/'protagonist_five_idle_eyes_r2','上版'),(p,'本次')]:
        cols.append((a+'° '+title,d/f'final_{a}.png',d/f'room_{a}.png'))
    before,after=[np.array(Image.open(d/f'final_{a}.png').convert('RGBA')) for d in [old,p]]
    y,x=np.where(np.any(before!=after,axis=2))
    print(a,len(y),x.min(),y.min(),x.max(),y.max())
    assert np.array_equal(before[:,:,3],after[:,:,3]) and x.min()>=56 and x.max()<=64 and y.min()>=15 and y.max()<=18
    delta=ImageChops.difference(*[Image.open(d/f'room_{a}.png').convert('RGB') for d in [old,p]]).getbbox()
    print('room difference',delta)
    assert delta and delta[2]-delta[0]<30 and delta[3]-delta[1]<15
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
for room in [False,True]:
    w,h=(244,272) if room else (208,200)
    sheet=Image.new('RGB',(6*w,32+h),'#363d40')
    draw=ImageDraw.Draw(sheet)
    for i,(title,src,screen) in enumerate(cols):
        im=Image.open(screen if room else src).convert('RGBA')
        im=im.crop((518,244,762,516)) if room else im.crop((51,2,77,27)).resize((208,200),Image.Resampling.NEAREST)
        sheet.paste(im,(i*w,32),im)
        draw.text((i*w+w/2,6),title,font=font,fill='white',anchor='mt')
    sheet.save(p/('room_compare.png' if room else 'heads.png'))

