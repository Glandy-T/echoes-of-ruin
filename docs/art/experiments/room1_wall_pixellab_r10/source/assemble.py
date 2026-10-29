"""Only align/mask PixelLab material; no authored aging shapes."""
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
OUT=ROOT/"assets/art/room1_wall_pixellab_r10"
OUT.mkdir(parents=True,exist_ok=True)
base=Image.open(HERE/"wall_left_baseline.png").convert("RGBA")
raw=Image.open(HERE.parent/"raw/pixellab_wall.png").convert("RGBA")
mask=Image.open(HERE/"mask.png").convert("L")
assert raw.size==mask.size==(256,256)
for x in range(256):
    # Technical handoff at the test crop edges; fixed whole-room corners stay exact.
    alpha=min(1.0,max(0.0,(min(x,255-x)-8)//4/4))
    for y in range(256):mask.putpixel((x,y),round(mask.getpixel((x,y))*alpha))
mask.save(HERE/"composite_mask.png")
detail=raw.copy();detail.putalpha(mask)
overlay=Image.new("RGBA",base.size,(0,0,0,0));overlay.paste(detail,(128,16))
overlay.save(HERE/"pixellab_wall_layer.png")
Image.alpha_composite(base,overlay).save(OUT/"wall_left.png")
