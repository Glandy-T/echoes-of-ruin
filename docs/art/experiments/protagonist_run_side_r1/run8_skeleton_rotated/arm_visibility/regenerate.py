"""Regenerate only the two passing poses whose far arms disappear."""
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from run_advisor import request_body,main


def targets():
    request=request_body()
    frames=request["keypoints"]
    # Make the far silhouette visible at the passing poses without moving
    # the near arm, shoulders, or anything below the waist.
    for n,elbow,wrist in ((2,(57,54),(44,58)),(6,(74,52),(70,61))):
        for p in frames[n-1]:
            if p["label"] in ("RIGHT ELBOW","RIGHT ARM"):
                x,y=elbow if p["label"]=="RIGHT ELBOW" else wrist
                p.update(x=(x+.5)/128,y=(y+.5)/128)
    request["keypoints"]=[frames[n-1] for n in (2,6,2,6)]
    request["seed"]+=2
    request["description"]+=" Both bare arms visible in profile, nearer arm light, far arm in shade, relaxed hands."
    return request


if __name__=="__main__":
    main(HERE,targets,(1,2,3,4))
