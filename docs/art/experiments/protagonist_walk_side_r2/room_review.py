"""Package actual Godot review frames and inspect support-toe positions in screen pixels."""
import json,os
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np

root=Path(__file__).resolve().parent
gait=json.loads((root/"gait.json").read_text())
src=Path(os.environ["TEMP"])/"echoes_room_walk_r2"
imgs=[Image.open(src/f"room_{i:02}.png").convert("RGB") for i in range(32)]
assert all(im.size==(1280,720) for im in imgs)
imgs[0].save(root/"room_start.png")
# Keep native pixels around the entire walk, use one palette across all frames.
box=(365,174,925,535)
seq=[im.crop(box) for im in imgs]
sample=Image.new("RGB",(560,361*4))
for k,n in enumerate([0,8,16,31]):
    sample.paste(seq[n],(0,k*361))
pal=sample.quantize(256)
indexed=[im.quantize(palette=pal,dither=Image.Dither.NONE) for im in seq]
timing=[10*(round((i+1)*gait["period_s"]*100/16)-round(i*gait["period_s"]*100/16)) for i in range(32)]
indexed[0].save(root/"room_walk.gif",save_all=True,append_images=indexed[1:],duration=timing,loop=0,disposal=1,optimize=False)
for i in [0,6,16,22]:
    a=np.array(imgs[i])[478:499,360:925,:]
    feet=(a[:,:,0]>54)&(a[:,:,0].astype(int)>a[:,:,2].astype(int)+4)
    xx=np.flatnonzero(feet.any(axis=0))+360
    runs=[u for u in np.split(xx,np.where(np.diff(xx)>1)[0]+1) if u.size>=5]
    print(i,[(int(u[0]),int(u[-1])) for u in runs])
