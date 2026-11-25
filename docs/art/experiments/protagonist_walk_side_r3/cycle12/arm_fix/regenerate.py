"""Ask PixelLab to redraw only four selected poses. All other drawings stay on disk."""
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT.parent))
from api_input import build_request
from generate import main

FRAMES = (5,6,11,12)
# On this west-facing sprite the back edge is at about x=71–74.
# Adjust just elbow and wrist; keep shoulders rooted in the original poses.
BACK_ARMS = {
    5: ("RIGHT",(70,48),(76,65)),
    6: ("RIGHT",(72,48),(80,64)),
    9: ("RIGHT",(69,50),(75,67)),
    11: ("LEFT",(74,48),(77,65)),
    12: ("LEFT",(76,48),(81,64)),
}


def body():
    result = build_request()
    targets = []
    for frame in FRAMES:
        joints = result["keypoints"][frame-1]
        side, elbow, wrist = BACK_ARMS[frame]
        for joint in joints:
            for name, point in [("ELBOW",elbow),("ARM",wrist)]:
                if joint["label"] == side+" "+name:
                    joint.update(x=(point[0]+.5)/128,y=(point[1]+.5)/128)
        targets.append(joints)
    result["keypoints"] = targets
    result["description"] += ", two visible bare arms, near arm light and far arm in shade"
    return result


if __name__ == "__main__":
    main(OUT,body,FRAMES)
