"""Arrange original PixelLab panels; no texture painting, mirroring or legacy age."""
from pathlib import Path
from PIL import Image,ImageDraw
import random,json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
PREV=ROOT/"docs/art/experiments/room1_wall_pixellab_r11"
OUT=ROOT/"assets/art/room1_wall_pixellab_r12";OUT.mkdir(parents=True,exist_ok=True)
mask=Image.open(HERE/"mask.png").convert("L")
tiles={};panels={}
for key in "abcdefgh":
    source_key="e2" if key=="e" else key
    path=(PREV if key in "abcd" else EXP)/f"raw/wall_{source_key}.png"
    tile=Image.open(path).convert("RGBA");assert tile.size==(256,256)
    tile.putalpha(mask);tiles[key]=tile
    for half in (0,1):panels[f"{key}{half}"]=tile.crop((half*128,0,(half+1)*128,256))
pool=list(panels);walls=("left","right","front","rear")
clean={w:Image.open(HERE/f"clean_{w}.png").convert("RGBA") for w in walls}
starts={w:list(range(-80,clean[w].width,128)) for w in walls}
rng=random.Random(2026102947)
for attempt in range(10000):
    orders={w:rng.sample(pool,len(starts[w])) for w in walls}
    if any(any(a[0]==b[0] for a,b in zip(seq,seq[1:])) for seq in orders.values()):continue
    if any(a==b for a,b in zip(orders["left"],orders["right"])):continue
    if any(a==b for a,b in zip(orders["front"],orders["rear"])):continue
    corner_pairs=[(orders["left"][-1],orders["rear"][0]),(orders["rear"][-1],orders["right"][-1]),(orders["right"][0],orders["front"][-1]),(orders["front"][0],orders["left"][0])]
    if any(a[0]==b[0] for a,b in corner_pairs):continue
    break
else:raise RuntimeError("Could not arrange distinct panel sequences")
portal=Image.open(PREV/"raw/wall_portal2.png").convert("RGBA")
portal.putalpha(Image.open(HERE/"mask_portal2.png").convert("L"))
manifest={"pool_size":16,"new_variants":["e2","f","g","h"],"panel_e_source":"e2 (original e rejected)","mirror_or_scale_used":False,"walls":{}}
for wall in walls:
    base=clean[wall];overlay=Image.new("RGBA",base.size,(0,0,0,0))
    placements=[]
    for start,key in zip(starts[wall],orders[wall]):
        overlay.paste(panels[key],(start,16));placements.append([start,key])
    if wall=="rear":overlay.paste(portal,(688,16))
    alpha=overlay.getchannel("A");d=ImageDraw.Draw(alpha)
    d.rectangle((0,0,1,271),fill=0);d.rectangle((base.width-2,0,base.width-1,271),fill=0)
    overlay.putalpha(alpha);overlay.save(HERE/f"{wall}_pixellab_layer.png")
    Image.alpha_composite(base,overlay).save(OUT/f"wall_{wall}.png")
    manifest["walls"][wall]={"size":list(base.size),"placements":placements,"unique_panel_ids":len(set(orders[wall]))==len(orders[wall]),"portal_override":[688,"r11 portal2"] if wall=="rear" else None}
(HERE/"assembly.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(json.dumps({w:orders[w] for w in walls}))
