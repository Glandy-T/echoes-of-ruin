from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
def sheet(paths,labels,columns,size,target):
    w,h=size
    out=Image.new('RGB',(columns*w,((len(paths)+columns-1)//columns)*(h+28)),'#454e4d')
    draw=ImageDraw.Draw(out)
    for i,(f,label) in enumerate(zip(paths,labels)):
        im=Image.open(f).convert('RGBA');im.thumbnail((w,h),Image.Resampling.LANCZOS)
        x=(i%columns)*w;y=(i//columns)*(h+28)
        out.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2),im)
        draw.text((x+w//2,y+h+3),label,font=font,anchor='mt',fill='white')
    out.save(p/target)
for stem in ('walk','walk2'):
    for side,key in [('正面','f'),('人物右侧','s')]:
        files=sorted(p.glob(stem+'_'+key+'[0-9][0-9].png'))
        if files: sheet(files,[side+f' {i+1}/8' for i in range(len(files))],4,(200,200),stem+'_'+key+'_frames.png')

