"""Assemble only clean construction + new PixelLab pixels, never legacy aging."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
OUT=ROOT/"assets/art/room1_wall_pixellab_r11";OUT.mkdir(parents=True,exist_ok=True)
orders={"left":["a","b","c","d"],"right":["d","a","c","b"],"front":["b","d","a","c","a","d"],"rear":["c","a","d","b","d","c"]}
mask=Image.open(HERE/"mask.png").convert("L")
tiles={}
for key in ("a","b","c","d","portal2"):
    tile=Image.open(EXP/f"raw/wall_{key}.png").convert("RGBA");assert tile.size==(256,256)
    tile.putalpha(Image.open(HERE/"mask_portal2.png").convert("L") if key=="portal2" else mask)
    tiles[key]=tile
manifest={}
for wall,order in orders.items():
    base=Image.open(HERE/f"clean_{wall}.png").convert("RGBA")
    if wall=="rear":
        ImageDraw.Draw(base).rectangle((812,44,819,248),fill=(211,214,201,255))
        base.save(HERE/"clean_rear.png")
    overlay=Image.new("RGBA",base.size,(0,0,0,0));placements=[]
    for index,start in enumerate(range(-208,base.width,256)):
        key=order[index%len(order)];overlay.paste(tiles[key],(start,16));placements.append([start,key])
    if wall=="rear":
        # Replace the whole door bay, including previous transparent regions.
        overlay.paste(tiles["portal2"],(688,16));placements.append([688,"portal2"])
    # All physical corners share the same clean construction profile.
    alpha=overlay.getchannel("A");d=ImageDraw.Draw(alpha)
    d.rectangle((0,0,1,271),fill=0);d.rectangle((base.width-2,0,base.width-1,271),fill=0)
    overlay.putalpha(alpha);overlay.save(HERE/f"{wall}_pixellab_layer.png")
    Image.alpha_composite(base,overlay).save(OUT/f"wall_{wall}.png")
    manifest[wall]={"size":list(base.size),"placements":placements,"legacy_aging_layers":[]}
(HERE/"assembly.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
