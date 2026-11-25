"""Retarget only the upper joints of the accepted eight-frame run."""
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
RUN8=HERE.parent/"run8"
sys.path.insert(0,str(RUN8))
from rig_run import FRAMES,HIP,PHASES,body
from generate import main

LEAD=(6,5,7,6)
HEAD_DROP=(-1,0,3,0)
NEAR_ROT=(2,0,-1,-2,-2,0,1,2)


def upper_body():
    req=body()
    for i,pose in enumerate(req["keypoints"]):
        phase=i%4
        h=HIP[phase]
        nx=64-LEAD[phase]
        points={"NECK":(nx,h-29)}
        for side in ("LEFT","RIGHT"):
            near=side=="LEFT"
            stance=near==(i<4)
            front=stance==(phase>=2)
            sx=nx+1+int(near)+(NEAR_ROT[i] if near else -NEAR_ROT[i])
            sy=h-25
            if phase==1:
                ex,ey=sx+(7 if stance else 3),sy+16
                wx,wy=ex-(10 if stance else 12),ey+(8 if stance else 5)
            elif front:
                ex,ey=sx,sy+17
                wx,wy=ex-14,ey+3
            else:
                ex,ey=sx+17,sy+10
                wx,wy=(72 if near else 70),h-1
            for name,xy in zip(("SHOULDER","ELBOW","ARM"),((sx,sy),(ex,ey),(wx,wy))):
                points[side+" "+name]=xy
        for j in pose:
            name=j["label"]
            xy=points.get(name)
            if name in ("NOSE","LEFT EYE","RIGHT EYE","LEFT EAR","RIGHT EAR"):
                x=int(j["x"]*128)
                y=int(j["y"]*128)
                xy=(x-round((h-y)*LEAD[phase]/29)+2,y+HEAD_DROP[phase]-(h-62))
            if xy:
                j.update(x=(xy[0]+.5)/128,y=(xy[1]+.5)/128)
    req["description"]="Sleepy barefoot woman in an ivory gown. Relaxed dropped shoulders, softly rounded upper back, chin slightly tucked, eyes forward and slightly down, loose half-open hands at lower rib height."
    return req


if __name__=="__main__":
    main(HERE,upper_body,FRAMES)
