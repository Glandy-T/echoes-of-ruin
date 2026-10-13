"""Encode Blender frames and rasterize actual UV coordinates for pixel painting."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
frames=[]
for p in sorted((ROOT/'.preview_frames').glob('*.png')):
    with Image.open(p) as image:
        frames.append(image.convert('RGB'))
if frames:
    palette=frames[0].quantize(colors=128)
    indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    indexed[0].save(ROOT/'evidence'/'opening_45deg.gif',save_all=True,append_images=indexed[1:],
                    duration=[125]*(len(indexed)-1)+[1600],loop=0,disposal=2)
for path in (ROOT/'uv').glob('*.json'):
    layout=json.loads(path.read_text(encoding='utf-8'))
    width,height=layout['template_pixels']
    canvas=Image.new('RGBA',(width,height),(0,0,0,0));draw=ImageDraw.Draw(canvas)
    for face in layout['faces']:
        draw.polygon([(u*(width-1),(1-v)*(height-1)) for u,v in face['uv']],outline=(60,60,60,255),width=1)
    canvas.save(path.with_suffix('.png'))
print('GIF and UV templates saved')
