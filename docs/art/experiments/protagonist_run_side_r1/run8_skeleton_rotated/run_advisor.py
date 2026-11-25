"""Run the advisor's integer-pixel poses with the existing run8_lean request."""
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parent/"run8_lean"))
from rig_lean import upper_body, FRAMES
from generate import main


def request_body():
    request=upper_body()
    joints=json.loads((OUT.parent/"advisor_lean_mock/joints_rotated.json").read_text(encoding="utf-8-sig"))
    old=json.loads((OUT.parent/"run8/joints.json").read_text())
    for n,pose in zip(FRAMES,request["keypoints"],strict=True):
        points=joints[str(n)]
        assert {point["label"] for point in pose}==set(points)
        for point in pose:
            label=point["label"]
            x,y=points[label]
            if label.endswith((" HIP"," KNEE"," LEG")):
                assert [x,y]==old[str(n)][label]
            point.update(x=(x+.5)/128,y=(y+.5)/128)
    return request


if __name__=="__main__":
    main(OUT,request_body,FRAMES)
