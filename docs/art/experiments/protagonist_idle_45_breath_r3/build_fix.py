"""Keep the approved trunk motion, register the neckline, and hinge the thin limbs."""
from pathlib import Path
from shutil import copyfile
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import label

HERE = Path(__file__).resolve().parent
R2 = HERE.parent / "protagonist_idle_45_breath_r2"
sys.path.insert(0, str(R2))
from animate import DURATION, POSES, SOURCE, X, Y, draw, loop, tile

OUT = HERE / "45"
# Rightmost painted pixel of the far arm by source row, from the sleeve to fingertips.
EDGE = {**dict.fromkeys(range(41,52),54), **dict.fromkeys(range(52,56),52),
        56:51,57:50,58:50,59:50,60:50,61:49,62:49,63:49,64:49,65:49,
        66:49,67:49,68:48,69:48,70:49,71:49,72:49,73:49,74:47}


def exposure(src, i):
    pose = POSES[i]
    # Use the same R2 motion field for the gown and screen-right arm.
    cloth = src.copy()
    arm = np.zeros_like(src)
    for y, end in EDGE.items():
        arm[y,:end+1] = src[y,:end+1]
        cloth[y,:end+1] = 0
    out = draw(cloth,pose)
    # Move face, jaw, visible neck and central neckline as one vertically aligned unit.
    head_y = pose[4][1]
    hair_y = pose[5][1]
    neck = (Y <= 30) | ((Y <= 32) & (X >= 59) & (X <= 68))
    fringe = (((X>=50)&(X<=54)&(Y>=13)&(Y<=17)) |
              ((X>=53)&(X<=55)&(Y>=21)&(Y<=25)) |
              ((X>=70)&(X<=75)&(Y>=21)&(Y<=25)))
    sy = (Y - np.where(fringe,hair_y,head_y)).clip(0,127)
    out[neck] = src[sy[neck],X[neck]]
    # The lifted sleeve carries the arm. The wrist swings at most one pixel;
    # every painted scanline retains all its original colours and its width.
    arm_y = (0,-1,-1,-1,0,0)[i]
    for y in EDGE:
        row = arm[y,:,3] > 0
        xs = np.flatnonzero(row)
        dx = -int(i in (2,3) and y < 57)
        out[y+arm_y,xs+dx] = arm[y,xs]
        assert np.array_equal(out[y+arm_y,xs+dx],src[y,xs])
    # Keep both leg drawings in native pixel rows. Offset the free knee by one
    # pixel between existing contour steps; preserve the support foot at rest.
    out[87:] = src[87:]
    if i in (2,3,4):
        for y in range(94,111):
            out[y, :63] = 0
            xs = np.flatnonzero(src[y,:63,3])
            out[y,xs+1] = src[y,xs]
    if i in (3,4):
        # Pitch just the rear of the foot. The toe/ball columns are anchored.
        out[114:124,56:62] = src[115:125,56:62]
    for y in range(87,114):
        for limb in (slice(42,63),slice(63,80)):
            old = src[y,limb]
            new = out[y,limb]
            assert np.array_equal(old[old[:,3]!=0],new[new[:,3]!=0])
    face = (Y>=12)&(Y<=30)&~fringe
    assert np.array_equal(out[face],src[(Y[face]-head_y),X[face]])
    assert np.array_equal(out[119:,63:],src[119:,63:])
    assert np.array_equal(out[119:,:56],src[119:,:56])
    assert np.array_equal(out[77:87],draw(src,pose)[77:87])
    assert label(out[:,:,3]>0, np.ones((3,3)))[1] == 1
    return out


def main():
    OUT.mkdir(exist_ok=True)
    src = np.array(Image.open(SOURCE).convert("RGBA"))
    tiles, pairs = [], []
    font = ImageFont.truetype("msyh.ttc",14)
    sheet = Image.new("RGB",(132*6,282),"#424849")
    for i in range(6):
        result = exposure(src,i)
        path = OUT / f"{i+1:02}.png"
        if i==0:
            assert np.array_equal(result,src)
            copyfile(SOURCE,path)
        else:
            Image.fromarray(result).save(path)
        new = tile(Image.open(path).convert("RGBA"))
        old = tile(Image.open(R2/"45"/path.name).convert("RGBA"))
        tiles.append(new)
        pair = Image.new("RGB",(264,282),"#424849")
        for j,(picture,name) in enumerate(((old,"修前"),(new,"修后"))):
            crop = picture.crop((31,0,96,128)).resize((130,256),Image.Resampling.NEAREST)
            pair.paste(crop,(132*j,24))
            ImageDraw.Draw(pair).text((132*j+5,3),name,font=font,fill="white")
            if j:
                sheet.paste(crop,(132*i,24))
                ImageDraw.Draw(sheet).text((132*i+5,4),f"{i+1:02}   {DURATION[i]} ms",fill="white")
        pairs.append(pair)
    sheet.save(OUT/"six_frames.png")
    loop(pairs,OUT/"compare.gif")
    for scale in (1,3):
        loop([im.resize((128*scale,128*scale),Image.Resampling.NEAREST) for im in tiles],OUT/f"breath_{scale}x.gif")


if __name__=="__main__":
    main()
