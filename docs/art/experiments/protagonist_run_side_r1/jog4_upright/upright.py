"""Four upright jogging poses, using the same stride and side convention as jog4."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"jog4"))
from skeleton import FRAMES, jog
from generate import main


def request_body():
    body = jog()
    for n,pose in zip(FRAMES,body["keypoints"]):
        high = n in (3,7)
        y = 62 - 3*high
        points = {"NECK":(62,y-29)}
        for side in ("LEFT","RIGHT"):
            near = side == "LEFT"
            supporting = near == (n<5)
            forward_leg = supporting != high
            shoulder = (61+2*near,y-27)
            sx,sy = shoulder
            # Upper arm rotates back at the shoulder. The hand remains below
            # the elbow on both sides, and clears the back in silhouette.
            if forward_leg:
                elbow,wrist=(sx+18,sy+11),(sx+14,sy+28)
            else:
                elbow,wrist=(sx-2,sy+18),(sx-18,sy+24)
            if high:
                knee,ankle = ((76,89),(90,117)) if supporting else ((50,87),(49,112))
            else:
                knee,ankle = ((49,90),(40,119)) if supporting else ((79,88),(95,114))
            for label,point in zip(("SHOULDER","ELBOW","ARM","KNEE","LEG"),
                                   (shoulder,elbow,wrist,knee,ankle)):
                points[side+" "+label]=point
        for p in pose:
            label=p["label"]
            x,y0=points.get(label,(int(p["x"]*128),int(p["y"]*128)))
            if label in ("NOSE","LEFT EYE","RIGHT EYE","LEFT EAR","RIGHT EAR"):
                x+=3
            p.update(x=(x+.5)/128,y=(y0+.5)/128)
    body.update(action="jog",description="Short-haired woman in ivory gown, relaxed loosely curled hands, level gaze, bare feet, dark far limbs")
    return body


if __name__=="__main__":
    main(HERE,request_body,FRAMES)
