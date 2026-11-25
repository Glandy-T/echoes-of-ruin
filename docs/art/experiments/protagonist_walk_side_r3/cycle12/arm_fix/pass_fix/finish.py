"""Restore the visible limbs in four exposures of the reviewed arm pass."""
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
sys.path.insert(0, str(BASE.parent))
from finish import matte, save_gif

NEAREST = Image.Resampling.NEAREST
DARK = [(111,99,93),(137,112,105),(153,128,123),(162,133,122)]


def arm_sample(donor, frame):
    """Retain the frame-2 sleeve opening, tapered wrist and knuckle texture."""
    sample = np.asarray(donor)
    arm = Image.new("RGBA", donor.size)
    if frame == 7:
        top, bottom, centres = 42, 69, (69,74,80,81)
    elif frame == 3:
        top, bottom, centres = 45, 76, (69,70,71,71)
    else:
        top, bottom, centres = 43, 75, (67,67,64,62)
    for y in range(top, bottom+1):
        t = (y-top)/(bottom-top)
        row = sample[46+round(30*t)]
        skin = (row[:,0].astype(int)-row[:,1].astype(int)>14) & (row[:,3]>0)
        xs = np.flatnonzero(skin & (np.arange(128)>=65))
        cx = round(np.interp(t,[0,.30,.75,1],centres))
        for x in range(xs[0],xs[-1]+1):
            color = tuple(map(int,row[x]))
            if frame == 7:
                color = (*DARK[np.searchsorted([151,179,211],color[0])],255)
            arm.putpixel((cx+x-round(xs.mean()),y),color)
    return arm


def restore(im, donor, frame):
    arm = arm_sample(donor,frame)
    base = np.array(im)
    if frame == 7:
        # Remove the intermittent old hand at the trailing garment edge.
        for y in range(45,70):
            edge = round(np.interp(y,[45,53,61,69],[70,71,72,73]))
            base[y,edge+1:80] = 0
            base[y,edge] = (124,139,133,255)
        return Image.alpha_composite(arm,Image.fromarray(base))
    # Restore the cloth at residual hand pixels before painting the near arm
    # in front. Preserve the dark far arm on the opposite side of frame 3.
    for y in range(45 if frame==3 else 43,77):
        for x in range(66 if frame==3 else 58,76 if frame==3 else 70):
            old = base[y,x]
            if old[3] and int(old[0])-int(old[1])>14 and not arm.getpixel((x,y))[3]:
                base[y,x] = (188,180,163,255) if x>=65 else (228,221,203,255)
    return Image.alpha_composite(Image.fromarray(base),arm)


def main():
    inputs = [Image.open(BASE/"frames"/f"{n:02}.png").convert("RGBA") for n in range(1,13)]
    output = []
    frames = OUT/"frames"
    frames.mkdir(exist_ok=True)
    chosen = (3,4,7,10)
    sheet = Image.new("RGB",(768,564),"#414548")
    comparisons = []
    for n,old in enumerate(inputs,1):
        new = restore(old,inputs[1],n) if n in chosen else old
        new.save(frames/f"{n:02}.png")
        a,b = (matte(p) for p in (old,new))
        output.append(b)
        pair = Image.new("RGB",(512,274),"#414548")
        for k,(img,label) in enumerate([(a,"Before"),(b,"After")]):
            pair.paste(img.resize((256,256),NEAREST),(k*256,18))
            ImageDraw.Draw(pair).text((k*256+10,3),f"{n:02}  {label}",fill="white")
            if n in chosen:
                idx = chosen.index(n)
                x,y = (idx%2)*384+k*192,(idx//2)*282
                sheet.paste(img.crop((16,0,112,128)).resize((192,256),NEAREST),(x,y+23))
                ImageDraw.Draw(sheet).text((x+6,y+5),f"{n:02}  {label}",fill="white")
        comparisons.append(pair)
        changed = np.any(np.asarray(new)!=np.asarray(old),axis=2)
        assert not changed[:40].any() and not changed[77:].any()
        assert bool(changed.any()) == (n in chosen)
    sheet.save(OUT/"four_poses.png")
    save_gif(output,OUT/"walk_1x.gif",1.08)
    save_gif([im.resize((384,384),NEAREST) for im in output],OUT/"walk_3x.gif",1.08)
    save_gif(comparisons,OUT/"before_after.gif",1.08)


if __name__ == "__main__":
    main()
