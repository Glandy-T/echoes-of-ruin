"""Four side-view jog drawings, a half cycle apart for each anatomical side."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/"protagonist_walk_side_r3"/"cycle12"))
from api_input import build_request
from generate import main

FRAMES = (1,3,5,7)


def jog():
    body = build_request()
    poses = []
    for frame in FRAMES:
        high = frame in (3,7)
        hip_y = 62-3*high
        coordinates = {"NECK":(60,hip_y-29)}
        for side in ("LEFT","RIGHT"):
            near = side=="LEFT"
            landing_leg = near == (frame<5)
            if high:
                knee,ankle = ((65,90),(76,118)) if landing_leg else ((50,87),(60,110))
            else:
                knee,ankle = ((47,91),(40,119)) if landing_leg else ((74,90),(95,114))
            # The shoulder remains attached to its own side on both steps.
            shoulder = (62+3*near,hip_y-26)
            backward = landing_leg != high
            ex = shoulder[0]+(12 if backward else 3)
            ey = shoulder[1]+(18 if backward else 20)
            elbow = (ex,ey)
            wrist = (ex-(16 if backward else 17),ey+(9 if backward else 3))
            for name,xy in zip(("HIP","KNEE","LEG","SHOULDER","ELBOW","ARM"),
                          ((63+2*near,hip_y),knee,ankle,shoulder,elbow,wrist)):
                coordinates[side+" "+name] = xy
        joints=[p.copy() for p in body["first_frame_keypoints"]]
        for joint in joints:
            x,y=coordinates.get(joint["label"],(int(128*joint["x"])-4,
                                                int(128*joint["y"])+2-3*high))
            joint.update(x=(x+.5)/128,y=(y+.5)/128)
        poses.append(joints)
    body.update(keypoints=poses,action="tired slow jog",description="Sleepy barefoot woman with short charcoal hair and a soft ivory gown hanging close to her legs, near arm and leg lighter, far limbs shaded")
    return body


if __name__=="__main__":
    main(HERE,jog,FRAMES)
