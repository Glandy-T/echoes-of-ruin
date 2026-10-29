from pathlib import Path
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
PREV=ROOT/"docs/art/experiments/room1_wall_pixellab_r11/source"
Image.open(PREV/"guide_portal.png").save(HERE/"guide_portal.png")
m=Image.new("L",(256,256),0);d=ImageDraw.Draw(m)
for r in [(1,28,254,70),(1,71,32,196),(223,71,254,196),(1,197,254,232),(1,240,254,252)]:d.rectangle(r,fill=255)
m.save(HERE/"mask_portal.png")
guide=Image.open(PREV/"clean_left.png").crop((48,0,304,64)).convert("RGBA")
guide.save(HERE/"guide_lamp.png")
m=Image.new("L",(256,64),0);d=ImageDraw.Draw(m)
for r in [(3,2,252,10),(3,14,252,17),(3,18,252,35),(3,36,252,43)]:d.rectangle(r,fill=255)
m.save(HERE/"mask_lamp.png")
