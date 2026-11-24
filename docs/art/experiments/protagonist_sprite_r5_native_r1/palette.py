from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
p=Path(__file__).resolve().parent
ref=Image.open(p.parent/'protagonist_front_c_raw_v2/B_original.png').convert('RGBA')
b=np.array(ref)
pal=np.unique(b[b[:,:,3]==255,:3],axis=0)
stats={'palette_size':len(pal),'B_bbox':ref.getbbox(),'frames':{}}
panels=[('B 原图',ref)]
for angle in (0,45):
    im=Image.open(p/f'raw_{angle}.png').convert('RGBA')
    a=np.array(im)
    assert im.size==ref.size==(128,128) and set(np.unique(a[:,:,3]))=={0,255}
    mask=a[:,:,3]==255
    rgb=a[mask,:3].astype('int32')
    dist=((rgb[:,None]-pal.astype('int32'))**2).sum(axis=2)
    a[mask,:3]=pal[dist.argmin(1)]
    a[~mask,:3]=0
    out=Image.fromarray(a)
    out.save(p/f'sprite_{angle}.png')
    box=out.getbbox()
    assert abs(box[3]-box[1]-117)<=1
    stats['frames'][angle]=dict(bbox=box,height=box[3]-box[1],colors=len(np.unique(a[mask,:3],axis=0)),opaque=int(mask.sum()))
    panels.append((f'R5 · {angle}°',out))
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
for scale in (1,3):
    n=128*scale
    sheet=Image.new('RGB',(n*3,n+32),'#454e4d')
    draw=ImageDraw.Draw(sheet)
    for i,(label,img) in enumerate(panels):
        im=img.resize((n,n),Image.Resampling.NEAREST)
        sheet.paste(im,(i*n,32),im)
        draw.text((i*n+n//2,7),label,anchor='mt',fill='white',font=font)
    sheet.save(p/f'compare_{scale}x.png')
(p/'metrics.json').write_text(json.dumps(stats,indent=2))
print(stats)
