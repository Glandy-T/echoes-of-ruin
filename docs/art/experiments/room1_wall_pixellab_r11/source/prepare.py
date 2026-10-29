"""Prepare clean structure only. No legacy aging or broad mineral polygons."""
from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
SRC=ROOT/"docs/art/experiments/room1_seam_contact_r6/source/wall_layers"
for wall in ("left","right","front","rear"):
    base=Image.open(SRC/f"{wall}_base.png").convert("RGBA")
    for name in ("structure","joints"):
        base=Image.alpha_composite(base,Image.open(SRC/f"{wall}_{name}.png").convert("RGBA"))
    base.save(HERE/f"clean_{wall}.png")
guide=Image.open(HERE/"clean_left.png").crop((48,16,304,272))
mask=Image.new("L",(256,256),0);d=ImageDraw.Draw(mask)
d.rectangle((1,28,254,232),fill=255)
d.rectangle((127,28,128,232),fill=0)
d.rectangle((1,240,254,252),fill=255)
guide.save(HERE/"guide.png");mask.save(HERE/"mask.png")
# The door's original 3.2m rear-wall bay has no center joint above its header.
portal=guide.copy();px=portal.load()
for x in range(124,132):
    for y in range(28,233):px[x,y]=(211,214,201,255)
portal.save(HERE/"guide_portal.png")
pmask=mask.copy();ImageDraw.Draw(pmask).rectangle((1,28,254,232),fill=255)
pmask.save(HERE/"mask_portal.png")
print("Clean guides exclude quiet_mineral_plane, top_deposit, lower_accumulation, joint_seal_film, base_contact")
