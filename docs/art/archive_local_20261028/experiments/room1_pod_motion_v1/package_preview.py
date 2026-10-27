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
