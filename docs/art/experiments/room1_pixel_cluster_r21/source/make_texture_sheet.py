"""Three exact material versions, arranged with nearest display enlargement."""
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
canvas=Image.new('RGB',(1596,1480),'#192527');draw=ImageDraw.Draw(canvas);y=0
for key in ['wall','lid','shell_side','shell_end']:
    name='wall_left' if key=='wall' else 'pod_'+key
    old=Image.open(HERE/f'baseline_{key}.png').convert('RGB')
    middle=Image.open(ROOT/f'assets/art/room1_pixel_cluster_r20/{name}.png').convert('RGB')
    new=Image.open(ROOT/f'assets/art/room1_pixel_cluster_r21/{name}.png').convert('RGB')
    if key=='wall':middle=middle.crop((432,16,688,272));new=new.crop((432,16,688,272))
    for column,(image,label) in enumerate([(old,'r19 original'),(middle,'r20 / 2x material grid'),(new,'r21 / 4x material grid')]):
        assert image.size==old.size
        x=column*532;draw.text((x+10,y+8),key+' / '+label,fill='#dde5df')
        canvas.paste(image.resize((image.width*2,image.height*2),Image.Resampling.NEAREST),(x+10,y+30))
    y+=old.height*2+30
canvas.crop((0,0,1596,y)).save(EXP/'evidence/texture_comparison.png')
print('R21_TEXTURE_SHEET_BUILT')
