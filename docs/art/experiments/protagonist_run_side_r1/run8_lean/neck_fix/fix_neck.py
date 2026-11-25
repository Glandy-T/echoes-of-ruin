"""Fix the neck on the eight existing PixelLab drawings; retain the generated shoulders."""
import csv
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageSequence

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))
from review_lean import HIP, NEAREST, PHASE_CN, matte, save_gif

# Registration relative to frame 04. Body and arm contours below row 38 stay intact.
DX = (0, 1, -1, 0)
DY = (-1, 0, 2, 0)
COLLAR_END = 32
SHOULDER_END = 38


def landmarks(im):
    a = np.array(im).astype(int)
    r, g, b, alpha = a.transpose(2, 0, 1)
    y, x = np.indices(alpha.shape)
    top = im.getbbox()[1]
    crown_x = round(np.flatnonzero(alpha[top]).mean())
    skin = (r >= 130) & (r-g >= 18) & (alpha > 0)
    chin = int(y[skin & (x <= crown_x-3) & (y < 35)].max())
    gown = (r == 228) & (g == 221) & (b == 203) & (alpha > 0)
    collar = int(y[gown & (y < 40)].min())
    return top, chin, collar


def bounds(im, y):
    left, _, right, _ = im.crop((0,y,128,y+1)).getbbox()
    return left, right


def repair(old, reference, phase):
    dx, dy = DX[phase], DY[phase]
    out = old.copy()
    out.paste((0,0,0,0), (0,0,128,SHOULDER_END))
    out.paste(reference.crop((0,0,128,COLLAR_END+1)), (dx,dy))
    # Recover each original back hair tip on its moving root.
    top = landmarks(old)[0]
    tip = old.crop((61+dx,top+10,72+dx,top+21))
    out.paste(tip,(61+dx,4+dy+10))

    # Keep the varying sleeve pitch. Match both neckline edges, and feather
    # their coordinate offsets to zero across the fabric above the sleeve.
    start = COLLAR_END + dy
    original_start = landmarks(old)[2] + COLLAR_END - landmarks(reference)[2]
    original_start = min(original_start, SHOULDER_END-2)
    left, right = bounds(reference, COLLAR_END)
    old_left, old_right = bounds(old, original_start)
    for y in range(start+1, SHOULDER_END):
        t = (y-start)/(SHOULDER_END-start)
        sy = round(original_start+t*(SHOULDER_END-original_start))
        lo, hi = bounds(old,sy)
        x0 = lo + round((left+dx-old_left)*(1-t))
        x1 = hi + round((right+dx-old_right)*(1-t))
        strip = old.crop((lo,sy,hi,sy+1)).resize((x1-x0,1),NEAREST)
        out.paste(strip,(x0,y))
    return out


def compare(old, new, n, font):
    pair = Image.new("RGB",(512,286),"#414548")
    pen = ImageDraw.Draw(pair)
    pen.fontmode = "1"
    for x, frame, title in ((0,old,"修前"),(256,new,"修后")):
        pair.paste(matte(frame).resize((256,256),NEAREST),(x,25))
        pen.text((x+10,5),title,font=font,fill="white")
    pen.text((340,5),f"{n:02}  {PHASE_CN[(n-1)%4]}",font=font,fill="#eadbb8")
    return pair


def main():
    originals = [Image.open(BASE/"frames"/f"{n:02}.png").convert("RGBA") for n in range(1,9)]
    ref = originals[3]
    frames, pairs, rows = [], [], []
    font = ImageFont.truetype("msyh.ttc",14)
    (HERE/"frames").mkdir(exist_ok=True)
    for i, old in enumerate(originals):
        phase = i%4
        im = repair(old,ref,phase)
        path = HERE/"frames"/f"{i+1:02}.png"
        im.save(path)
        im = Image.open(path).convert("RGBA")
        assert im.crop((0,38,128,128)).tobytes() == old.crop((0,38,128,128)).tobytes()
        _, old_chin, old_collar = landmarks(old)
        crown, chin, collar = landmarks(im)
        assert (chin,collar) == (24+DY[phase],28+DY[phase])
        # Chin, nape and the visible base of the neck must be a rigid translation.
        box = (42,24,61,32)
        shifted = tuple(v+(DX[phase] if j%2==0 else DY[phase]) for j,v in enumerate(box))
        assert im.crop(shifted).tobytes() == ref.crop(box).tobytes()
        rows.append(dict(frame=i+1,hip_y=HIP[phase],crown_y=crown,chin_y=chin,collar_y=collar,
                         before_gap_px=old_collar-old_chin,after_gap_px=collar-chin))
        frames.append(im)
        pairs.append(compare(old,im,i+1,font))
    with (HERE/"neck.csv").open("w",newline="") as f:
        writer = csv.DictWriter(f,fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    period = 2*60*1.65/125/2.5
    for scale in (1,3):
        save_gif([matte(im).resize((128*scale,128*scale),NEAREST) for im in frames],
                 HERE/f"run_{scale}x.gif",period)
    save_gif(pairs,HERE/"comparison.gif",period)
    def delays(path):
        with Image.open(path) as gif:
            return [frame.info["duration"] for frame in ImageSequence.Iterator(gif)]
    for name in ("comparison.gif","run_1x.gif","run_3x.gif"):
        assert delays(HERE/name) == delays(BASE/"run_1x.gif")


if __name__ == "__main__":
    main()
