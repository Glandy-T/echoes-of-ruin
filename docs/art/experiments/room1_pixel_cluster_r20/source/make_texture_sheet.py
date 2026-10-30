"""Arrange exact native pixels for inspection; no retouching."""
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
canvas=Image.new('RGB',(1064,1480),'#192527');draw=ImageDraw.Draw(canvas)
y=0
for key in ['wall','lid','shell_side','shell_end']:
    a=Image.open(HERE/f'baseline_{key}.png').convert('RGB')
    name='wall_left' if key=='wall' else 'pod_'+key
    b=Image.open(ROOT/f'assets/art/room1_pixel_cluster_r20/{name}.png').convert('RGB')
    if key=='wall':b=b.crop((432,16,688,272))
    assert a.size==b.size
    for column,(image,label) in enumerate([(a,'A current r19'),(b,'B PixelLab 2x material grid')]):
        x=column*532;draw.text((x+10,y+8),key+' / '+label,fill='#dde3df')
        scaled=image.resize((image.width*2,image.height*2),Image.Resampling.NEAREST)
        canvas.paste(scaled,(x+10,y+30))
    y+=a.height*2+30
canvas.crop((0,0,1064,y)).save(EXP/'evidence/texture_comparison.png')
print('R20_TEXTURE_SHEET_BUILT')
