from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageChops
p = Path(__file__).resolve().parent
sources = [p.parent/'protagonist_front_c_raw_v2/B_original.png', p.parent/'protagonist_sprite_r5_native_r1/sprite_45.png', p/'redraw.png', p/'direct.png']
keys = ['B','render','redraw','direct']
labels = ['B 正面原图','R5 原生渲染','R5 渲染重画','B 直接转向']
font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
for room in (False,True):
    w,h = (278,272) if room else (384,384)
    sheet = Image.new('RGB',(w*4,h+38),'#363d40')
    draw = ImageDraw.Draw(sheet)
    for i,(src,key,label) in enumerate(zip(sources,keys,labels)):
        if room:
            im = Image.open(p/f'room_{key}.png').convert('RGB')
            assert im.size == (1280,720)
            if i == 0:
                baseline = im.copy()
            else:
                diff = ImageChops.difference(baseline,im).getbbox()
                print(key, 'room difference',diff)
                assert diff and diff[0]>525 and diff[2]<755 and diff[1]>240 and diff[3]<520
            sheet.paste(im.crop((501,245,779,517)),(i*w,38))
        else:
            im = Image.open(src).convert('RGBA')
            print(key,im.size,im.getchannel('A').getbbox())
            assert im.size == (128,128)
            im=im.resize((w,h),Image.Resampling.NEAREST)
            sheet.paste(im,(i*w,38),im.getchannel('A'))
        draw.text((i*w+w//2,9),label,font=font,fill='white',anchor='mt')
    sheet.save(p/('room_compare.png' if room else 'sprites_3x.png'))
