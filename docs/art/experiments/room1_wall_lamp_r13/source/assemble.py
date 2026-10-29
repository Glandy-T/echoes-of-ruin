from pathlib import Path
from PIL import Image,ImageDraw
import json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
OUT=ROOT/"assets/art/room1_wall_lamp_r13";OUT.mkdir(parents=True,exist_ok=True)
lamp_mask=Image.open(HERE/"mask_lamp.png").convert("L")
lamps={}
for key in ("lamp_a","lamp_b"):
    tile=Image.open(EXP/f"raw/{key}.png").convert("RGBA");assert tile.size==(256,64)
    # PixelLab invented rounded fixture ends at canvas edges. Use only its
    # central continuous surface, then technically blend into clean construction.
    tile=tile.crop((64,0,192,64));alpha=lamp_mask.crop((64,0,192,64))
    for x in range(128):
        factor=min(1.0,min(x,127-x)/8.0)
        for y in range(64):alpha.putpixel((x,y),round(alpha.getpixel((x,y))*factor))
    tile.putalpha(alpha);lamps[key]=tile
portal=Image.open(HERE/"guide_portal.png").convert("RGBA")
raw=Image.open(EXP/"raw/portal.png").convert("RGBA")
raw.putalpha(Image.open(HERE/"mask_portal.png").convert("L"))
portal=Image.alpha_composite(portal,raw)
phases={"left":-64,"right":-128,"front":-192,"rear":0}
manifest={}
for wall,phase in phases.items():
    base=Image.open(ROOT/f"assets/art/room1_wall_pixellab_r12/wall_{wall}.png").convert("RGBA")
    base.save(HERE/f"baseline_{wall}.png")
    replacement=Image.new("RGBA",base.size,(0,0,0,0))
    if wall=="rear":replacement.paste(portal,(688,16))
    replacement.save(HERE/f"{wall}_portal_layer.png")
    lamp=Image.new("RGBA",base.size,(0,0,0,0));placements=[]
    for i,x in enumerate(range(phase,base.width,128)):
        key="lamp_a" if (i+(1 if wall in ("right","rear") else 0))%2==0 else "lamp_b"
        lamp.paste(lamps[key],(x,0));placements.append([x,key])
    alpha=lamp.getchannel("A");d=ImageDraw.Draw(alpha)
    d.rectangle((0,0,1,63),fill=0);d.rectangle((base.width-2,0,base.width-1,63),fill=0)
    lamp.putalpha(alpha);lamp.save(HERE/f"{wall}_lamp_layer.png")
    result=Image.alpha_composite(Image.alpha_composite(base,replacement),lamp)
    result.save(OUT/f"wall_{wall}.png")
    manifest[wall]={"size":list(base.size),"lamp_placements":placements,"rear_bay_replaced":[688,16,944,272] if wall=="rear" else None}
(HERE/"assembly.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
