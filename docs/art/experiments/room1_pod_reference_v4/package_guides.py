"""Encode rendered animation and rasterize actual UV coordinates into paint guides."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
frames=[]
for path in sorted((ROOT/'.preview_frames').glob('*.png')):
    with Image.open(path) as image:
        frames.append(image.convert('RGB'))
if frames:
    palette=frames[0].quantize(colors=128)
    indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    indexed[0].save(ROOT/'evidence'/'whole_lid_motion.gif',save_all=True,
                    append_images=indexed[1:],duration=[125]*(len(indexed)-1)+[1000],loop=0,disposal=2)
for path in (ROOT/'uv').glob('*.json'):
    layout=json.loads(path.read_text(encoding='utf-8'))
    canvas=Image.new('RGBA',(1024,1024),(0,0,0,0))
    draw=ImageDraw.Draw(canvas)
    for face in layout['faces']:
        draw.polygon([(u*1024,(1-v)*1024) for u,v in face['uv']],outline=(60,60,60,255),width=1)
    canvas.save(path.with_suffix('.png'))
print('Review GIF and transparent UV guides saved')
