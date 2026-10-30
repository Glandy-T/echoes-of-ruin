"""Only arrange actual Godot frames for inspection; originals remain untouched."""
from pathlib import Path
from PIL import Image,ImageDraw
BASE=Path(__file__).resolve().parents[1]
canvas=Image.new('RGB',(1920,768),'#192527');draw=ImageDraw.Draw(canvas)
for row,view in enumerate(['left_bay_closed','p12_closed']):
    for column,mode in enumerate([1,2,3]):
        original=Image.open(BASE/f'evidence/{mode}_{view}.png').convert('RGB')
        canvas.paste(original.resize((640,360),Image.Resampling.NEAREST),(column*640,row*384+24))
        draw.text((column*640+8,row*384+5),['A original','B r20 material','C r21 stronger material'][column]+' / '+view,fill='#dde5df')
canvas.save(BASE/'evidence/review_sheet.png')
print('R21_REVIEW_SHEET_BUILT')
