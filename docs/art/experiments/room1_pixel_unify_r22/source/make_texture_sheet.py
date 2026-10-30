"""Nearest-neighbour arrangement of real exports; creates no material pixels."""
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];EXP=HERE.parent
before=ROOT/'assets/art';after=before/'room1_pixel_unify_r22'
items=[
 ('wall / same existing 2-bay crop',before/'room1_wall_lamp_r13/wall_left.png',after/'wall_left.png',(432,16,688,272)),
 ('P12 opaque lid / geometry fixed',before/'room1_complete_r19/numbered/P12_lid.png',after/'numbered/P12_lid.png',None),
 ('P12 long side',before/'room1_pod_pixellab_r16/variant_a/shell_side.png',after/'variant_a/shell_side.png',None),
 ('P12 short end / ID retained',before/'room1_complete_r19/numbered/P12_shell_end.png',after/'numbered/P12_shell_end.png',None),
 ('floor / same world-space crop',before/'room1_floor_variants_r15/floor_with_leaks.png',after/'floor_with_leaks.png',(720,300,976,556)),
]
heights=[]
for _,p,_,box in items:
    im=Image.open(p);h=(box[3]-box[1]) if box else im.height;heights.append(h*2+55)
sheet=Image.new('RGB',(1120,sum(heights)+40),'#182629');d=ImageDraw.Draw(sheet)
d.text((16,10),'A / current r19',fill='#e1e8df');d.text((576,10),'B / whole-room candidate r22',fill='#e1e8df');y=40
for (label,p,q,box),height in zip(items,heights):
    d.text((16,y),label,fill='#d5e0dc');d.text((576,y),label,fill='#d5e0dc')
    for x,file in [(16,p),(576,q)]:
        im=Image.open(file).convert('RGB');im=im.crop(box) if box else im
        im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);sheet.paste(im,(x,y+24))
    y+=height
sheet.save(EXP/'evidence/texture_comparison.png');print('R22_TEXTURE_SHEET_BUILT')
