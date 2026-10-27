"""Regular Python + Pillow: encode actual Blender frames into a review GIF."""
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent
files=sorted((ROOT/'.preview_frames').glob('*.png'))
assert len(files)==36,'Run render_preview.py in Blender first'
with Image.open(files[0]) as first:
    palette=first.convert('RGB').quantize(colors=128)
frames=[]
for file in files:
    with Image.open(file) as image:
        frames.append(image.convert('RGB').quantize(palette=palette,dither=Image.Dither.NONE))
durations=[125]*len(frames)
durations[-1]=1000
frames[0].save(ROOT/'evidence'/'whole_lid_motion.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=2)
print('PREVIEW_GIF_SAVED')
import json
from PIL import ImageDraw
layouts=json.loads((ROOT/'uv'/'uv_layouts.json').read_text(encoding='utf-8'))
colors=['#d3dedc','#819caa','#bcb897','#6c7b87']
for name,layout in layouts.items():
    canvas=Image.new('RGBA',(1024,1024),(0,0,0,0))
    guide=Image.new('RGB',(1024,1024),'#202932')
    drawing=ImageDraw.Draw(canvas)
    preview=ImageDraw.Draw(guide)
    for face in layout['faces']:
        coords=[(u*1024,(1-v)*1024) for u,v in face['uv']]
        drawing.polygon(coords,outline=(60,60,60,255),width=1)
        preview.polygon(coords,fill=colors[face['material']%4],outline='#273942',width=1)
    canvas.save(ROOT/'uv'/(name+'_lines.png'))
    guide.save(ROOT/'uv'/(name+'_regions.png'))
print('UV_TEMPLATES_SAVED')
