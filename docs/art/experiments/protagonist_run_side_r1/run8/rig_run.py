"""Pose one contact, compression, push and flight, and repeat with exchanged limbs."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"jog4"))
from skeleton import build_request
from generate import main

FRAMES=tuple(range(1,9))
PHASES=("Contact","Down","Push","Flight")
HIP=(62,65,62,61)
# Each entry is knee and ankle. In Down the recovery shank is almost horizontal.
STANCE=(((50,92),(56,119)),((49,90),(68,119)),((77,88),(93,113)),((69,90),(95,104)))
SWING=(((76,92),(109,111)),((66,93),(96,94)),((48,85),(56,104)),((49,89),(57,118)))
# Offsets to elbow, then from elbow to wrist. Moving forwards flexes the
# wrist towards the chest. At compression both upper arms pass the ribcage.
BACK=((16,11),(-8,14))
FRONT=((-9,16),(-8,-5))
PASS_BACK=((7,17),(-10,8))
PASS_FRONT=((1,18),(-12,2))


def body():
    req=build_request()
    targets=[]
    for n in FRAMES:
        phase=(n-1)%4
        h=HIP[phase]
        coords={"NECK":(62,h-29)}
        for side in ("LEFT","RIGHT"):
            near=side=="LEFT"
            planted=near==(n<=4)
            knee,ankle=(STANCE if planted else SWING)[phase]
            sh=(62+2*near,h-27)
            upper,lower=((BACK,PASS_BACK,FRONT,FRONT) if planted else
                         (FRONT,PASS_FRONT,BACK,BACK))[phase]
            el=(sh[0]+upper[0],sh[1]+upper[1])
            wrist=(el[0]+lower[0],el[1]+lower[1])
            for key,pt in zip(("HIP","KNEE","LEG","SHOULDER","ELBOW","ARM"),
                             ((64,h),knee,ankle,sh,el,wrist)):
                coords[side+" "+key]=pt
        joints=[p.copy() for p in req["first_frame_keypoints"]]
        for p in joints:
            xy=coords.get(p["label"],(int(128*p["x"])-1,int(128*p["y"])+h-62))
            p.update(x=(xy[0]+.5)/128,y=(xy[1]+.5)/128)
        targets.append(joints)
    req.update(keypoints=targets,action="running, contact, compression with heel folding behind, toe off and low flight",
               description="Barefoot woman with short charcoal hair and loose ivory gown, upright head, loosely curled hands swinging near chest and hip, far limbs darker")
    return req


if __name__=="__main__":
    main(HERE,body,FRAMES)
