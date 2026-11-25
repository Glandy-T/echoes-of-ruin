"""Register the new upper-body drawings on the approved run and check the export."""
import csv
import json
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageSequence

from rig_lean import FRAMES, HERE, HIP, LEAD, PHASES, RUN8, upper_body
from finish import matte, save_gif, separate_limbs

NEAREST = Image.Resampling.NEAREST
PHASE_CN = ("触地", "下沉", "蹬地", "腾空")
SKIRT_START = 70
CROWN_Y = (3, 4, 7, 4)


def settle_head(im, phase):
    # Register the crown on the same sloping axis as the neck. The raw face
    # already looks down; carry it with the crown, tapering to zero at collar.
    arr = np.asarray(im)
    top = im.getbbox()[1]
    xs = np.flatnonzero(arr[top, :, 3])
    target = 64 - round((HIP[phase] - CROWN_Y[phase]) * LEAD[phase] / 29)
    dx = target - round(float(np.mean(xs)))
    dy = CROWN_Y[phase] - top
    src = im.copy()
    for y in range(32):
        blend = float(np.clip((32-y)/7, 0, 1))
        sy = y - round(dy * blend)
        im.paste((0, 0, 0, 0), (0, y, 128, y+1))
        if sy >= 0:
            im.paste(src.crop((0, sy, 128, sy+1)), (round(dx*blend), y))


def finish_hands(im, n):
    # Rejoin the passing upper arm behind the existing cuff on the down poses.
    pen = ImageDraw.Draw(im)
    if n in (2, 6):
        path = ([(65,49),(67,55),(68,59),(64,62),(57,64)] if n == 2
                else [(62,49),(62,54),(62,58),(60,60),(54,62)])
        pen.line(path, fill="#ac8c79", width=5, joint="curve")
        pen.line([(x-1,y) for x,y in path], fill="#e6bd97", width=3, joint="curve")
        return
    # Replace the distal fist only. Keep the generated forearm connected at x=49.
    near = n in (3, 4, 5)
    light, shade = ("#e6bd97", "#be9981") if near else ("#a2857a", "#897069")
    y = (57, 0, 56, 55, 56, 0, 57, 55)[n-1]
    im.paste((0,0,0,0), (34,50,49,63))
    pen.polygon([(49,y-1),(49,y+1),(47,y+2),(45,y+2),(44,y+1),
                 (43,y+1),(43,y),(45,y),(46,y-1),(47,y-2)], fill=shade)
    pen.line([(49,y-1),(47,y-1),(46,y),(44,y)], fill=light)
    pen.line([(47,y+1),(45,y+2),(44,y+3)], fill=light)
    pen.line([(45,y-2),(46,y-1),(47,y-1)],fill=light)


def register_waist(im, old):
    # Transition inside the gown. Copy the approved drawing from y=70 onward.
    for y in range(66, SKIRT_START):
        a = im.crop((0,y,128,y+1))
        b = old.crop((0,y,128,y+1))
        left, _, right, _ = a.getbbox()
        old_l, _, old_r, _ = b.getbbox()
        t = (y-65)/(SKIRT_START-65)
        lo, hi = round(left+(old_l-left)*t), round(right+(old_r-right)*t)
        row = a.crop((left,0,right,1)).resize((hi-lo,1), NEAREST)
        im.paste((0,0,0,0),(0,y,128,y+1))
        im.paste(row,(lo,y))
    bbox = (0,SKIRT_START,128,128)
    im.paste(old.crop(bbox), (0,SKIRT_START))
    assert im.crop(bbox).tobytes() == old.crop(bbox).tobytes()


def comparison(old, new, row, font):
    out = Image.new("RGB", (512, 300), "#414548")
    pen = ImageDraw.Draw(out)
    pen.fontmode = "1"
    for x, sprite, label in ((0,old,"run8"),(256,new,"上身修订")):
        out.paste(matte(sprite).resize((256,256),NEAREST),(x,30))
        pen.text((x+12,5),label,font=font,fill="#ffffff")
    pen.line((256,4,256,290),fill="#636a6a")
    pen.text((344,5), f"{row['frame']:02} {PHASE_CN[(row['frame']-1)%4]}   颈前移 {row['lead_px']} px",font=font,fill="#eadbb8")
    return out


def main():
    old_measure = json.loads((RUN8/"measurements.json").read_text())
    old_joints = json.loads((RUN8/"joints.json").read_text())
    period = old_measure["period_s"]
    joint_log, rows, images, pairs = {}, [], [], []
    font = ImageFont.truetype("msyh.ttc",15)
    (HERE/"frames").mkdir(exist_ok=True)
    for n, pose in zip(FRAMES, upper_body()["keypoints"]):
        phase=(n-1)%4
        p={j["label"]:[int(j["x"]*128),int(j["y"]*128)] for j in pose}
        for joint, xy in p.items():
            if joint.endswith((" HIP"," KNEE"," LEG")):
                assert xy == old_joints[str(n)][joint]
        joint_log[n]=p
        old=Image.open(RUN8/"frames"/f"{n:02}.png").convert("RGBA")
        raw=Image.open(HERE/"raw"/f"{n:02}.png").convert("RGBA")
        im=separate_limbs(raw,p)
        settle_head(im,phase)
        finish_hands(im,n)
        register_waist(im,old)
        path=HERE/"frames"/f"{n:02}.png"
        im.save(path)
        im=Image.open(path).convert("RGBA")
        hx,hy=p["LEFT HIP"]
        nx,ny=p["NECK"]
        cy=im.getbbox()[1]
        cx=np.flatnonzero(np.asarray(im)[cy,:,3]).mean()
        assert cy == CROWN_Y[phase]
        angle=round(math.degrees(math.atan2(hx-nx,hy-ny)),1)
        row=dict(frame=n,phase=PHASES[phase],neck_x=nx,hip_x=hx,lead_px=hx-nx,
                 rig_lean_deg=angle,crown_x=float(cx),crown_y=cy,hip_y=hy,
                 crown_lean_deg=round(math.degrees(math.atan2(hx-cx,hy-cy)),1))
        rows.append(row)
        images.append(im)
        pairs.append(comparison(old,im,row,font))
    (HERE/"joints.json").write_text(json.dumps(joint_log,indent=2))
    with (HERE/"neck_hip.csv").open("w",newline="") as csvfile:
        writer=csv.DictWriter(csvfile,fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    sheet=Image.new("RGB",(1024,300*4),"#414548")
    for i, pair in enumerate(pairs):
        sheet.paste(pair,(512*(i%2),300*(i//2)))
    sheet.save(HERE/"poses.png")
    for scale in (1,3):
        save_gif([matte(im).resize((128*scale,128*scale),NEAREST) for im in images],
                 HERE/f"run_{scale}x.gif",period)
    save_gif(pairs,HERE/"run8_comparison.gif",period)
    def durations(path):
        with Image.open(path) as gif:
            return [im.info["duration"] for im in ImageSequence.Iterator(gif)]
    for path in ("run_1x.gif","run_3x.gif","run8_comparison.gif"):
        assert durations(HERE/path)==durations(RUN8/"run_1x.gif")
    print(rows)


if __name__ == "__main__":
    main()

