from PIL import Image,ImageFont,ImageDraw
from pathlib import Path
p=Path(__file__).resolve().parent.parent
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
def board(rows,out,w,h):
    im=Image.new('RGB',(len(rows[0])*w,len(rows)*(h+33)),'#24292a')
    dr=ImageDraw.Draw(im)
    for y,row in enumerate(rows):
        for x,(label,view) in enumerate(row):
            dr.text((x*w+w/2,y*(h+33)+8),label,anchor='mt',font=font,fill='white')
            im.paste(view.resize((w,h),Image.Resampling.LANCZOS),(x*w,y*(h+33)+33))
    im.save(p/out)
rows=[]
for tag,name in [('before','R5 原贴图'),('after','区域平涂')]:
    rows.append([(name+' · '+label,Image.open(p/(tag+'_'+key+'.png'))) for key,label in [('front','正面'),('three_quarter','斜侧'),('side','侧面')]])
board(rows,'neutral_compare.png',204,360)
rows=[]
for pose,label in [('stand','站立'),('walk','行走 · 第 21 帧')]:
    rows.append([(name+' · '+label,Image.open(p/(tag+'_room_'+pose+'.png')).crop((500,243,805,560))) for tag,name in [('before','R5 原贴图'),('after','区域平涂')]])
board(rows,'room_compare.png',305,317)
