from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent.parent
v2=p.parent/'protagonist_r5_face_v2'
b=Image.open(p.parent/'protagonist_front_c_raw_v2/B_original.png').convert('RGBA')
# Crown to chin: original rows 3..24; orthographic 3D rows 42..239.
views=[('B 原脸',b.crop((46,3,82,25)),Image.Resampling.NEAREST),('当前 3D',Image.open(v2/'after_front.png').crop((12,42,308,240)),Image.Resampling.LANCZOS),('头部小样',Image.open(p/'after_front.png').crop((12,42,308,240)),Image.Resampling.LANCZOS)]
sheet=Image.new('RGB',(900,250),'#121616');draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
for i,(label,im,method) in enumerate(views):
    im=im.convert('RGBA');im=im.resize((round(im.width*176/im.height),176),method)
    if i:
        # The Blender review uses a black background.
        im.putalpha(im.convert('RGB').convert('L').point(lambda a:255 if a>2 else 0))
    sheet.paste(im,(i*300+(300-im.width)//2,36),im)
    draw.text((i*300+150,222),label,font=font,anchor='mt',fill='white')
sheet.save(p/'comparison.png')
