"""Register the PixelLab poses, measure each visible sole and export the loop."""
import csv
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont

from rig_run import FRAMES, HERE, HIP, PHASES, body
from review_jog import head
from finish import separate_limbs, matte, save_gif

GROUND=125
NEAREST=Image.Resampling.NEAREST
# Foot-only measuring regions. Bounds separate the two actual feet, including
# the folded foot which never enters the usual y>=116 contact band.
DIVIDER=(78,82,69,76)


def passing_arm(im,frame):
    # These two generated fists and sleeves are present, but the central strip
    # of skin is painted as gown. Connect them in the existing skin palette.
    paths=([(69,49),(72,56),(68,60),(60,65)],
           [(65,49),(66,56),(62,59),(54,61)])
    path=paths[frame==6]
    pen=ImageDraw.Draw(im)
    pen.line(path,fill=(175,142,126,255),width=5,joint="curve")
    pen.line([(x,y-1) for x,y in path],fill=(230,189,151,255),width=3,joint="curve")


def tuck_front_hand(im):
    src=im.copy()
    # Taper the forward projection at the wrist without shifting the elbow.
    for y in range(38,58):
        for x in range(34,52):
            im.putpixel((x,y),(0,0,0,0))
        for x in range(34,53):
            c=src.getpixel((x,y))
            if c[3]:
                im.putpixel((x+round(np.clip((53-x)*.33,0,4)),y),c)


def region_bounds(im,phase):
    a=np.array(im)[:,:,3]>127
    regions=[(18,DIVIDER[phase]),(DIVIDER[phase],124)]
    result=[]
    for start,end in regions:
        yy,xx=np.where(a[92:,start:end])
        bottom=int(yy.max()+92)
        result.append((bottom,int(xx[yy>=yy.max()-6].min()+start)))
    return result


def register_feet(im,phase):
    """Adjust each generated calf/foot locally; retain its painted foot roll."""
    src=im.copy()
    baselines=region_bounds(src,phase)
    clearance=((0,4),(0,23),(12,0),(2,12))[phase]
    for limb,(start,end) in enumerate([(18,DIVIDER[phase]),(DIVIDER[phase],124)]):
        old,_=baselines[limb]
        target=GROUND-clearance[limb]
        top=min(old-9,104) if phase!=1 else (103 if limb==0 else 90)
        patch=src.crop((start,top,end,old+1)).resize((end-start,target-top+1),NEAREST)
        im.paste((0,0,0,0),(start,top,end,128))
        im.paste(patch,(start,top))
    if phase==0:
        a=np.array(im)
        # Centre the weight-bearing forefoot 10 px ahead of the hip. Use the
        # ball through the heel for contact, retaining rounded outside toes.
        foot=(a[119:,:73,3]>127).any(axis=0)
        xs=np.flatnonzero(foot)
        src=im.copy()
        for x in xs:
            if not (46<=x<=60):
                continue
            bottom=np.flatnonzero(a[:,x,3])[-1]
            if bottom < 120:
                continue
            desired=GROUND-int(x<48 or x>59)
            for y in range(113,128):
                offset=round((desired-bottom)*min(1,(y-113)/7))
                im.putpixel((int(x),y),src.getpixel((int(x),int(np.clip(y-offset,0,127)))))
        # Register the rear forefoot to the previous delivery's stride scale.
        mask=np.array(im)[116:,78:,3]>127
        rear=78+int(np.nonzero(mask)[1].min())
        front=int(np.nonzero(np.array(im)[116:,:75,3]>127)[1].min())
        delta=(front+60)-rear
        src=im.copy()
        for y in range(96,128):
            dx=round(delta*np.clip((y-96)/17,0,1))
            im.paste((0,0,0,0),(80,y,128,y+1))
            im.paste(src.crop((80,y,124,y+1)),(80+dx,y))
    if phase==2:
        # The toes are the leading end of the plantar surface at push-off.
        a=np.asarray(im)
        hits=np.flatnonzero(a[GROUND,69:,3]>127)+69
        if len(hits)>3:
            pen=ImageDraw.Draw(im)
            for x in hits[3:]:
                pen.point((int(x),GROUND),fill=(0,0,0,0))
    if phase==1:
        # Sustain the load under the hip across the compression pose.
        src=im.copy()
        a=np.array(src)
        for x in range(59,70):
            bottom=np.flatnonzero(a[:,x,3])[-1]
            if bottom>=121:
                for y in range(116,128):
                    sy=y-round((GROUND-bottom)*min(1,(y-116)/5))
                    im.putpixel((x,y),src.getpixel((x,int(np.clip(sy,0,127)))))


def main():
    raw=[Image.open(HERE/"raw"/f"{i:02}.png").convert("RGBA") for i in FRAMES]
    idle=Image.open(HERE.parents[1]/"protagonist_five_idle_eyes_r3/final_90.png").convert("RGBA")
    frames,rows,joints=[],[],{}
    for n,pose in zip(FRAMES,body()["keypoints"]):
        phase=(n-1)%4
        p={j["label"]:(int(j["x"]*128),int(j["y"]*128)) for j in pose}
        joints[n]=p
        im=raw[n-1].copy()
        if n==7:
            # Use the matching extended push-off drawing from this same batch.
            im.paste(raw[2].crop((0,69,128,128)),(0,69))
        im=separate_limbs(im,p)
        if phase==1:
            passing_arm(im,n)
        else:
            tuck_front_hand(im)
        # Head and garment follow-through use the previous exposure's height.
        dy=HIP[phase]-62
        lag=int(np.clip(HIP[(phase-1)%4]-HIP[phase],-2,2))
        head(im,idle,phase in (2,3),dx=-1,dy=dy,lag=lag)
        src=im.copy()
        for y in range(72,96):
            row=y-round(lag*np.interp(y,[72,80,86,96],[0,.75,.75,0]))
            im.paste(src.crop((0,row,128,row+1)),(0,y))
        register_feet(im,phase)
        (HERE/"frames").mkdir(exist_ok=True)
        path=HERE/"frames"/f"{n:02}.png"
        im.save(path)
        im=Image.open(path).convert("RGBA")
        frames.append(im)
        feet=region_bounds(im,phase)
        near_at_left=(n<=4)==(phase<=1)
        near,far=feet if near_at_left else feet[::-1]
        info=dict(frame=n,phase=PHASES[phase],rig_hip_y=p["LEFT HIP"][1],
                  hip_above_ground=GROUND-p["LEFT HIP"][1],hip_vs_contact=62-p["LEFT HIP"][1],
                  near_clearance=GROUND-near[0],far_clearance=GROUND-far[0])
        expected=[(0,4),(0,23),(0,12),(12,2)][phase]
        assert (info["near_clearance"],info["far_clearance"])==(expected if n<=4 else expected[::-1])
        assert im.getbbox()[1]==3+dy
        rows.append(info)
    # Same-foot travel between alternate contacts, measured on the delivered PNGs.
    toes=[]
    for im in frames[::4]:
        a=np.array(im)[116:,:,3]>127
        toes.append([int(np.where(a[:,:75])[1].min()),78+int(np.where(a[:,78:])[1].min())])
    steps=[toes[1][1]-toes[0][0],toes[0][1]-toes[1][0]]
    assert steps==[60,60]
    period=sum(steps)*1.65/125/2.5
    with (HERE/"heights.csv").open("w",newline="") as file:
        writer=csv.DictWriter(file,fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    metrics=dict(contacts_x=toes,step_px=steps,period_s=period,fps=8/period,frames=rows)
    print(metrics)
    (HERE/"measurements.json").write_text(json.dumps(metrics,indent=2))
    (HERE/"joints.json").write_text(json.dumps(joints,indent=2))
    sheet=Image.new("RGB",(1024,566),"#414548")
    pen=ImageDraw.Draw(sheet)
    for i,im in enumerate(frames):
        x,y=(i%4)*256,(i//4)*283
        sheet.paste(matte(im).resize((256,256),NEAREST),(x,y+20))
        pen.text((x+9,y+4),f"{i+1:02}   {PHASES[i%4]}",fill="white")
        pen.line((x+56,y+272,x+226,y+272),fill="#788182")
    sheet.save(HERE/"poses.png")
    line=Image.new("RGB",(8*184,326),"#414548")
    text=ImageDraw.Draw(line)
    font=ImageFont.truetype("msyh.ttc",14)
    for i,(im,r) in enumerate(zip(frames,rows)):
        x=184*i
        line.paste(matte(im).crop((25,0,117,128)).resize((184,256),NEAREST),(x,0))
        text.line((x+3,252,x+180,252),fill="#788182")
        label=("触地","下沉","蹬地","腾空")[i%4]
        text.text((x+5,259),f"{i+1:02}  {label}   髋高 {r['hip_above_ground']} px",font=font,fill="white")
        text.text((x+5,284),f"近脚 {r['near_clearance']}   远脚 {r['far_clearance']} px",font=font,fill="white")
    line.save(HERE/"eight_poses.png")
    for scale in (1,3):
        save_gif([matte(im).resize((128*scale,128*scale),NEAREST) for im in frames],
                 HERE/f"run_{scale}x.gif",period)


if __name__=="__main__":
    main()
