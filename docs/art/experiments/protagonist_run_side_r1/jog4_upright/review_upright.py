import json
from math import atan2, degrees

import numpy as np
from PIL import Image, ImageDraw

from upright import FRAMES, HERE, request_body
from review_jog import GROUND, NEAREST, head
from finish import separate_limbs, matte, save_gif
from review import contact_toes


def land(image,frame):
    out=image.copy()
    mask=np.asarray(image)[:,:,3]>127
    xs=np.flatnonzero(mask[116:,:55].any(axis=0))
    # Roll the original bare sole onto its ball and heel. The two outer toe
    # pixels retain a rounded profile. Register each column to its own floor.
    for x in range(xs[0],xs[-1]+1):
        bottom=np.flatnonzero(mask[:,x])[-1]
        level=GROUND-int(x in (xs[0],xs[-1]))-int(x==xs[0])
        dz=level-bottom
        for y in range(107,128):
            shift=round(dz*min(1,(y-107)/10))
            out.putpixel((x,y),image.getpixel((x,y-shift)))
    if frame==5:
        for y in range(103,128):
            if y>=111:
                out.paste(image.crop((71,y,112,y+1)),(70,y))
    return out


def straighten_phase_three(image,donor):
    # Both flight poses have the same side-view geometry. Use the actual
    # extended leg drawing from 07, then relight it for the opposite side.
    out=image.copy()
    out.paste(donor.crop((0,70,128,128)),(0,70))
    for y in range(38,66):
        edge=round(np.interp(y,[38,44,53,65],[74,71,72,75]))
        out.paste((0,0,0,0),(edge+1,y,91,y+1))
        for x in range(edge+1,90):
            c=donor.getpixel((x,y))
            if c[3] and c[0]-c[1]>14:
                out.putpixel((x,y),c)
    return out


def finish_pose(raw,donor,pose,frame,idle):
    high=frame in (3,7)
    im=straighten_phase_three(raw,donor) if frame==3 else raw.copy()
    im=separate_limbs(im,pose)
    # Let the lead hand hang from the wrist. Keep the model's palm, folded
    # fingers and thumb colours; only the distal pixels roll downward.
    pivot,top,bottom={1:(48,55,61),3:(53,55,62),5:(49,56,63),7:(48,52,60)}[frame]
    hand=im.copy()
    for x in range(pivot-8,pivot):
        shift=round(3*(pivot-x)/8)
        im.paste((0,0,0,0),(x,top,x+1,bottom+1))
        im.paste(hand.crop((x,top,x+1,bottom+1)),(x,top+shift))
    src=im.copy()
    for y in range(70,99):
        weight=np.interp(y,[70,80,88,99],[0,1,1,0])
        row=y-round((1 if high else -2)*weight)
        im.paste(src.crop((0,row,128,row+1)),(0,y))
    if high:
        low=im.getbbox()[3]-1
        strip=im.crop((0,99,128,low+1)).resize((128,GROUND-2-98),NEAREST)
        im.paste((0,0,0,0),(0,99,128,128))
        im.paste(strip,(0,99))
    else:
        im=land(im,frame)
    head(im,idle,high,dx=-1)
    return im


def angle(a,b,c):
    u,v=np.subtract(a,b),np.subtract(c,b)
    return round(float(np.degrees(np.arccos(np.clip(np.dot(u,v)/(np.linalg.norm(u)*np.linalg.norm(v)),-1,1)))),1)


def export():
    original={n:Image.open(HERE/"raw"/f"{n:02}.png").convert("RGBA") for n in FRAMES}
    idle=Image.open(HERE.parents[1]/"protagonist_five_idle_eyes_r3/final_90.png").convert("RGBA")
    frames=[]
    stats=[]
    all_points={}
    for n,kp in zip(FRAMES,request_body()["keypoints"]):
        p={j["label"]:(int(128*j["x"]),int(128*j["y"])) for j in kp}
        all_points[n]=p
        im=finish_pose(original[n],original[7],p,n,idle)
        (HERE/"frames").mkdir(exist_ok=True)
        im.save(HERE/"frames"/f"{n:02}.png")
        frames.append(im)
        clearance=GROUND-(im.getbbox()[3]-1)
        assert clearance==(2 if n in (3,7) else 0)
        mid=np.mean([p["LEFT HIP"],p["RIGHT HIP"]],axis=0)
        row=dict(frame=n,clearance_px=clearance,crown_y=im.getbbox()[1],
                 rig_lean_deg=round(degrees(atan2(mid[0]-p["NECK"][0],mid[1]-p["NECK"][1])),1))
        for side in ("LEFT","RIGHT"):
            row[side+"_elbow_deg"]=angle(*[p[side+" "+k] for k in ("SHOULDER","ELBOW","ARM")])
            row[side+"_knee_deg"]=angle(*[p[side+" "+k] for k in ("HIP","KNEE","LEG")])
        if n in (1,5):
            planted=np.where(np.asarray(im)[GROUND,:55,3]>127)[0]
            assert len(planted)>=10 and np.all(np.diff(planted)==1)
            row["sole_on_ground_px"]=len(planted)
        stats.append(row)
    a,b=contact_toes(frames[0]),contact_toes(frames[2])
    steps=[b[1]-a[0],a[1]-b[0]]
    meters=[s*1.65/125 for s in steps]
    assert steps==[58,59]
    period=sum(meters)/2.5
    metrics=dict(contacts_x=[a,b],steps_px=steps,steps_m=meters,period_s=period,
                 four_fps=4/period,eight_fps=8/period,poses=stats)
    print(metrics)
    (HERE/"measurements.json").write_text(json.dumps(metrics,indent=2))
    (HERE/"joints.json").write_text(json.dumps(all_points,indent=2))
    sheet=Image.new("RGB",(1024,560),"#414548")
    pairs=[]
    for i,(n,im) in enumerate(zip(FRAMES,frames)):
        old=Image.open(HERE.parent/"jog4"/"frames"/f"{n:02}.png").convert("RGBA")
        pair=Image.new("RGB",(512,280),"#414548")
        for j,(pic,label) in enumerate([(old,"jog4"),(im,"Upright jog")]):
            zoom=matte(pic).resize((256,256),NEAREST)
            sheet.paste(zoom,(256*i,280*j+21))
            ImageDraw.Draw(sheet).text((256*i+10,280*j+4),f"{label}   {n:02}",fill="white")
            pair.paste(zoom,(256*j,21))
            ImageDraw.Draw(pair).text((256*j+10,4),label,fill="white")
        pairs.append(pair)
    sheet.save(HERE/"comparison.png")
    save_gif(pairs,HERE/"comparison.gif",period)
    for scale in (1,3):
        save_gif([matte(im).resize((128*scale,128*scale),NEAREST) for im in frames],HERE/f"jog_{scale}x.gif",period)


if __name__=="__main__":
    export()
