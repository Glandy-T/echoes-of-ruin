from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent
out=Image.new('RGB',(780,680),'#303639')
draw=ImageDraw.Draw(out)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
for col,(label,base,names) in enumerate([('R2   7,784',p.parent/'protagonist_gray_tripo_r2',['front','right']),('R4   993,540',p.parent/'protagonist_turnaround_tripo_r4',['parts_front','parts_side']),('R5   8,563',p,['mesh_front','mesh_side'])]):
    draw.text((col*260+130,14),label,anchor='mt',fill='white',font=font)
    for row,name in enumerate(names):
        im=Image.open(base/(name+'.png')).convert('RGBA')
        im=im.crop(im.getchannel('A').getbbox())
        im.thumbnail((240,305),Image.Resampling.LANCZOS)
        out.paste(im,(col*260+(260-im.width)//2,40+row*320+305-im.height),im)
out.save(p/'comparison.png')
