"""Fit the approved idle neck to the existing run, using the chin as the origin."""
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFont, ImageSequence

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "neck_fix"
sys.path.insert(0, str(PREVIOUS))
from fix_neck import NEAREST, compare, matte, save_gif


def measure(im):
    a = np.asarray(im).astype(int)
    r, g, _, alpha = a.transpose(2,0,1)
    top = im.getbbox()[1]
    left = lambda y: int(np.flatnonzero(alpha[y]).min())
    chin = next(y for y in range(top+17,top+25) if left(y+1)-left(y)>=3)
    skin = (r-g >= 16) & (alpha > 0)
    hair = (g>=r-5) & (g<133) & (alpha>0)
    lowest = int(np.flatnonzero(skin.any(axis=1) & (np.arange(im.height)<top+34))[-1])
    collar_x = int(np.flatnonzero(skin[lowest])[0])
    # Measure uninterrupted skin in a vertical column between hair and cloth.
    runs = []
    for x in range(left(chin+1),left(chin+1)+12):
        for y in range(chin-3,chin+5):
            if hair[y,x]:
                end = y+1
                while end<40 and skin[end,x]:
                    end += 1
                if end>y+1 and alpha[end,x] and not hair[end,x]:
                    runs.append(end-y-1)
    return (left(chin),chin), collar_x-left(chin), max(runs)


def fit(old, idle):
    (cx,cy), _, _ = measure(old)
    (ix,iy), _, _ = measure(idle)
    out = old.copy()
    # Six rows contain the original design's jaw shadow, neck and collar.
    for offset in range(1,7):
        y = cy+offset
        out.paste((0,0,0,0),(0,y,128,y+1))
        out.paste(idle.crop((0,iy+offset,128,iy+offset+1)),(cx-ix,y))
    # The running head's nape ends two rows higher than the idle hairline.
    # Raise the back lip of the neckline under that lock, using the idle palette.
    ivory, shade, edge = (228,221,203,255), (188,180,163,255), (143,148,136,255)
    for row, start_x, colors in ((2,10,[edge]),(3,7,[ivory,shade,shade,shade,edge]),
                                 (4,7,[ivory])):
        for j,color in enumerate(colors):
            out.putpixel((cx+start_x+j,cy+row),color)
    # Rejoin the lifted collar to this frame's original shoulder, inside the cloth.
    start=cy+6
    def span(im,y):
        l,_,r,_=im.crop((0,y,128,y+1)).getbbox()
        return l,r
    end_l,end_r = span(old,start+6)
    new_l,new_r = span(out,start)
    for d in range(1,6):
        y=start+d
        l,r = span(old,y)
        t=d/6
        lo=round(new_l+(end_l-new_l)*t)
        hi=round(new_r+(end_r-new_r)*t)
        strip = old.crop((l,y,r,y+1)).resize((hi-lo,1),NEAREST)
        out.paste((0,0,0,0),(0,y,128,y+1))
        out.paste(strip,(lo,y))
    return out


def delays(path):
    with Image.open(path) as gif:
        return [frame.info["duration"] for frame in ImageSequence.Iterator(gif)]


def main():
    idle = Image.open(HERE.parents[2]/"protagonist_five_idle_eyes_r3/final_90.png").convert("RGBA")
    _, target_x, target_skin = measure(idle)
    assert (target_x,target_skin)==(4,4)
    frames, pairs, measurements = [], [], []
    font=ImageFont.truetype("msyh.ttc",14)
    (HERE/"frames").mkdir(exist_ok=True)
    for n in range(1,9):
        name=f"{n:02}.png"
        old=Image.open(PREVIOUS/"frames"/name).convert("RGBA")
        im=fit(old,idle)
        path=HERE/"frames"/name
        im.save(path)
        result=Image.open(path).convert("RGBA")
        (cx,cy),dx,skin=measure(result)
        assert (dx,skin)==(target_x,target_skin), (n,dx,skin)
        assert (cx,cy)==measure(old)[0]
        for band in ((0,0,128,cy+1),(0,cy+12,128,128)):
            assert result.crop(band).tobytes()==old.crop(band).tobytes()
        frames.append(result)
        pairs.append(compare(old,result,n,font))
        measurements.append((n,im.getbbox()[1],cx,cy,dx,skin))
    with (HERE/"neck.csv").open("w",newline="") as f:
        w=csv.writer(f)
        w.writerow(("frame","crown_y","chin_x","chin_y","chin_to_collar_x_px","nape_skin_px"))
        w.writerows(measurements)
    period=2*60*1.65/125/2.5
    for scale in (1,3):
        save_gif([matte(im).resize((128*scale,128*scale),NEAREST) for im in frames],HERE/f"run_{scale}x.gif",period)
    save_gif(pairs,HERE/"comparison.gif",period)
    for name in ("run_1x.gif","run_3x.gif","comparison.gif"):
        assert delays(HERE/name)==delays(PREVIOUS/"run_1x.gif")


if __name__=="__main__":
    main()


