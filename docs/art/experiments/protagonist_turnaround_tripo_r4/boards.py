from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
def board(entries, cols, w,h, output):
    canvas=Image.new('RGB',(cols*w,((len(entries)+cols-1)//cols)*(h+35)), '#59645f')
    draw=ImageDraw.Draw(canvas)
    for i,(path,label) in enumerate(entries):
        img=Image.open(path).convert('RGBA')
        bbox=img.getchannel('A').point(lambda a:255 if a>120 else 0).getbbox()
        if not bbox: continue
        img=img.crop(bbox)
        fac=min((w-18)/img.width,(h-12)/img.height)
        img=img.resize((round(img.width*fac),round(img.height*fac)),Image.Resampling.LANCZOS)
        x=i%cols*w; y=i//cols*(h+35)
        canvas.paste(img,(x+(w-img.width)//2,y+h-6-img.height),img)
        draw.text((x+w//2,y+h+4),label,font=font,anchor='mt',fill='white')
    canvas.save(p/output)
entries=[]
for n,src,title in [('front','front','正面'),('side','right','右侧'),('back','back','背面')]:
    entries.append((p.parent/'protagonist_model_turnaround_v3'/(src+'.png'),title+'参考'))
    entries.append((p/('parts_'+n+'.png'),title+'灰模'))
board(entries,6,162,480,'comparison.png')
files=sorted(p.glob('parts_piece_*.png'))
board([(f,'部件 '+str(i)) for i,f in enumerate(files)],5,150,150,'isolated.png')
