"""Translate the run8 head and shoulders intact and shear the cloth below the armpit."""
import csv
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageSequence

OUT = Path(__file__).resolve().parent
RUN = OUT.parent / "run8"
LEAN = OUT.parent / "run8_lean"
sys.path.insert(0, str(RUN))
from review_run import HIP, NEAREST, matte, save_gif

SHIFT = (5,5,6,6)
PIT = (40,43,40,37)
# First cloth column under the raised hand of run8. Interpolate only where
# the raised wrist hides the front edge of the gown.
EDGE = ((40,53),(45,53),(51,54),(56,55),(60,55))
SKIN_DARK = {(111,99,93),(84,80,74),(125,110,101)}
PHASE = ("触地","下沉","蹬地","腾空")


def sprite(folder,n):
    return Image.open(folder/"frames"/f"{n:02}.png").convert("RGBA")


def shift_at(y,phase):
    pit,hip=PIT[phase],HIP[phase]
    return round(SHIFT[phase]*max(0,min(1,(hip-y)/(hip-pit))))


def shear(im,phase):
    result=im.copy()
    for y in range(HIP[phase]):
        d=shift_at(y,phase)
        result.paste((0,0,0,0),(0,y,128,y+1))
        result.paste(im.crop((0,y,128,y+1)),(-d,y))
    return result


def is_skin(pixel):
    r,g,b,a=pixel
    return a and (int(r)-int(g)>=16 or (r,g,b) in SKIN_DARK)


def arms(source, donor, other, n):
    phase=(n-1)%4
    if phase==1:
        # Both hands cross the waist. The passing pose already exists on run8.
        return shear(source,phase)
    clean=source.copy()
    near=n in (3,4,5)
    pit=PIT[phase]
    for y in range(pit+1,57):
        edge=round(np.interp(y,*zip(*EDGE)))
        clean.paste((0,0,0,0),(34,y,edge,y+1))
        if near:
            # Reveal the gown under the old raised forearm, using the garment
            # from the matching phase of the opposite step.
            for x in range(edge,64):
                px=source.getpixel((x,y))
                if is_skin(px) or (y>=46 and x<62 and (not px[3] or px[0]<145)):
                    fabric=other.getpixel((x,y))
                    if not fabric[3] or is_skin(fabric) or fabric[0]<145:
                        fabric=(228,221,203,255) if x<59 else (188,180,163,255)
                    clean.putpixel((x,y),fabric)
    result=shear(clean,phase)
    if near:
        # Meet the run8 sleeve opening, then bring the donor forearm to the
        # lowered hand. At hand height the source pixels translate rigidly.
        start=43
        for y in range(start,62):
            t=max(0,min(1,(y-start)/(50-start)))
            sy=y+round(4*(1-t))+1
            dx=round(-7+5*t)
            for x in range(54 if sy<52 else 38,64):
                color=donor.getpixel((x,sy))
                if is_skin(color):
                    result.putpixel((x+dx,y),color)
    else:
        # The far forearm emerges from behind the torso. Preserve its darker
        # silhouette and overlap the root with the garment edge.
        arm=Image.new("RGBA",source.size)
        # The run8 chest sits farther back at elbow height. Complete the short
        # stretch of forearm previously occluded by the lean version's gown.
        palm_y={1:56,7:56,8:54}[n]
        pen=ImageDraw.Draw(arm)
        pen.line([(47,palm_y),(51,palm_y-1),(57,palm_y-3)],fill="#897069",width=3)
        pen.line([(49,palm_y-1),(53,palm_y-2),(57,palm_y-4)],fill="#a2857a",width=1)
        for y in range(50,62):
            for x in range(37,59):
                color=donor.getpixel((x,y))
                if is_skin(color):
                    arm.putpixel((x-2,y-1),color)
        result=Image.alpha_composite(arm,result)
    return result


def landmarks(im):
    a=np.asarray(im)[:,:,3]
    top=im.getbbox()[1]
    ys,xs=np.nonzero(a[top+5:top+16])
    hx=int(xs.max())
    hy=int(ys[xs==hx][0])+top+5
    sy=top+30
    sx=int(np.flatnonzero(a[sy])[-1])
    return (hx,hy),(sx,sy)


def panel(images,n,font):
    out=Image.new("RGB",(3*232,306),"#414548")
    pen=ImageDraw.Draw(out)
    pen.fontmode="1"
    for k,(im,label) in enumerate(zip(images,("90° 定稿站姿","run8_lean","本次修订"))):
        x=232*k
        tile=matte(im).crop((15,0,125,128)).resize((220,256),NEAREST)
        out.paste(tile,(x+5,24))
        pen.text((x+9,3),label,font=font,fill="white")
        if k==2:
            pen.text((x+124,3),f"{n:02}  {PHASE[(n-1)%4]}",font=font,fill="#eadbb8")
        h,s=landmarks(im)
        for (px,py),color in ((h,"#ffcb6f"),(s,"#80dcd5")):
            # Callouts sit just outside the silhouette.
            sx=x+5+2*(px-15)+2
            sy=24+2*py+1
            pen.line((sx,sy,sx+7,sy),fill=color)
        pen.text((x+10,284),f"后脑 x={h[0]}   后肩 x={s[0]}   差 {h[0]-s[0]:+d} px",
                 fill="#e3e1db",font=font)
    return out


def delays(path):
    with Image.open(path) as f:
        return [im.info["duration"] for im in ImageSequence.Iterator(f)]


def main():
    idle=Image.open(OUT.parents[1]/"protagonist_five_idle_eyes_r3/final_90.png").convert("RGBA")
    period=2*60*1.65/125/2.5
    font=ImageFont.truetype("msyh.ttc",13)
    (OUT/"frames").mkdir(exist_ok=True)
    imgs,panels,rows=[],[],[]
    for n in range(1,9):
        phase=(n-1)%4
        original,donor=sprite(RUN,n),sprite(LEAN,n)
        im=arms(original,donor,sprite(RUN,(n+3)%8+1),n)
        path=OUT/"frames"/f"{n:02}.png"
        im.save(path)
        im=Image.open(path).convert("RGBA")
        pit,hip,d=PIT[phase],HIP[phase],SHIFT[phase]
        registered=Image.new("RGBA",(128,pit+1))
        registered.paste(im.crop((0,0,128,pit+1)),(d,0))
        assert registered.tobytes()==original.crop((0,0,128,pit+1)).tobytes()
        assert im.crop((0,hip,128,128)).tobytes()==original.crop((0,hip,128,128)).tobytes()
        assert all(shift_at(y,phase)-shift_at(y+1,phase) in (0,1) for y in range(pit,hip))
        h,s=landmarks(im)
        oh,os=landmarks(original)
        assert h==(oh[0]-d,oh[1]) and s==(os[0]-d,os[1])
        rows.append((n,d,pit,hip,round(math.degrees(math.atan2(d,hip-pit)),1),*h,*s,h[0]-s[0]))
        imgs.append(im)
        panels.append(panel((idle,donor,im),n,font))
    with (OUT/"measurements.csv").open("w",newline="") as f:
        writer=csv.writer(f)
        writer.writerow(("frame","shift_left","armpit_y","hip_y","shear_deg","head_x","head_y","shoulder_x","shoulder_y","head_minus_shoulder_px"))
        writer.writerows(rows)
    for scale in (1,3):
        save_gif([matte(im).resize((128*scale,128*scale),NEAREST) for im in imgs],OUT/f"run_{scale}x.gif",period)
    save_gif(panels,OUT/"comparison.gif",period)
    for name in ("comparison.gif","run_1x.gif","run_3x.gif"):
        assert delays(OUT/name)==delays(RUN/"run_1x.gif")


if __name__=="__main__":
    main()


