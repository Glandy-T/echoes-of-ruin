from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np
p=Path(__file__).resolve().parent
cols=[('front','正面','protagonist_front_c_raw_v2/B_original.png'),('right','右侧','protagonist_side_eye_v4/side.png'),('back','背面','protagonist_back_v1/back.png')]
sheet=Image.new('RGB',(840,448),'#52605c')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
draw=ImageDraw.Draw(sheet)
for j,(name,label,ref) in enumerate(cols):
    row=[]
    for path in [p.parent/ref,p/(name+'.png')]:
        im=Image.open(path).convert('RGBA')
        bounds=im.getbbox()
        im=im.crop(bounds)
        im=im.resize((round(im.width*368/im.height),368),Image.Resampling.NEAREST if path!=p/(name+'.png') else Image.Resampling.LANCZOS)
        row.append(im)
    # Each column shows the same sprite-to-model comparison; overlay separately below.
    for i,im in enumerate(row):
        x=280*j+70+140*i
        sheet.paste(im,(x-im.width//2,8),im)
        draw.text((x,388),label+[' · 原画',' · 灰模'][i],font=font,anchor='mt')
sheet.save(p/'compare.png')
sheet=Image.new('RGB',(540,426),'#34403d')
draw=ImageDraw.Draw(sheet)
for j,(name,label,ref) in enumerate(cols):
    masks=[]
    for path in [p.parent/ref,p/(name+'.png')]:
        im=Image.open(path).convert('RGBA')
        im=im.crop(im.getbbox())
        im=im.resize((round(im.width*368/im.height),368),Image.Resampling.NEAREST)
        a=np.zeros((368,180),bool)
        x=(180-im.width)//2
        a[:,x:x+im.width]=np.asarray(im)[:,:,3]>127
        masks.append(a)
    pix=np.full((368,180,3),(52,64,61),np.uint8)
    a,b=masks
    pix[a]=(104,200,229);pix[b]=(239,154,97);pix[a&b]=(195,202,190)
    sheet.paste(Image.fromarray(pix),(180*j,8))
    draw.text((180*j+90,384),label,font=font,anchor='mt')
draw.text((270,406),'蓝：仅原画   橙：仅灰模   灰白：重叠',font=font,anchor='mt')
sheet.save(p/'overlay.png')
