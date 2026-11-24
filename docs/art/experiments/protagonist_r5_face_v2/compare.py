from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
p=Path(__file__).resolve().parent
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
def strip(entries,out):
    imgs=[im.convert('RGB') for label,im in entries]
    w,h=imgs[0].size
    sheet=Image.new('RGB',(len(imgs)*w,h+36),'#242a2b')
    d=ImageDraw.Draw(sheet)
    for i,((label,_),im) in enumerate(zip(entries,imgs)):
        sheet.paste(im,(i*w,36));d.text((i*w+w/2,8),label,font=font,anchor='mt',fill='white')
    sheet.save(p/out)
strip([(label,Image.open(p/name).crop((34,54,282,266))) for label,name in [('原正面','before_front.png'),('修正正面','after_front.png'),('修正斜侧','after_three_quarter.png')]],'face_compare.png')
strip([(label,Image.open(path).crop((500,245,780,525))) for label,path in [('原脸 · 原光',p.parent/'protagonist_r5_pixel_skin_v1/room_128_stand.png'),('修正 · 原光',p/'room_128_stand.png'),('修正 · 角色补光试验',p/'room_fill_128_stand.png')]],'room_compare.png')
