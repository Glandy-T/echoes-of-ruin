"""Four alternate contact/flight samples of a symmetric eight-exposure run."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/"protagonist_walk_side_r3"/"cycle12"))
from api_input import build_request
from generate import main

FRAMES = (1,3,5,7)


def pilot_request():
    body = build_request()
    poses = []
    for n in FRAMES:
        flight = n in (3,7)
        near_leads = n < 5
        source = [p.copy() for p in body["first_frame_keypoints"]]
        # Contact reaches forward with a flexed knee. In flight the landing
        # leg has passed below the hips while the other knee drives forward.
        lead_leg = [(64,58),(41,83),(35,119)] if not flight else [(64,53),(77,80),(96,108)]
        other_leg = [(62,57),(87,75),(112,99)] if not flight else [(62,53),(42,70),(65,92)]
        back_arm = [(61,30),(79,45),(74,59)] if not flight else [(59,26),(60,46),(43,46)]
        forward_arm = [(57,29),(48,46),(31,40)] if not flight else [(55,26),(73,41),(72,56)]
        coords = {"NECK":(58,32 if not flight else 29)}
        for side, leads in [("LEFT",near_leads),("RIGHT",not near_leads)]:
            for names, chain in [(("HIP","KNEE","LEG"),lead_leg if leads else other_leg),
                                 (("SHOULDER","ELBOW","ARM"),back_arm if leads else forward_arm)]:
                for name,pt in zip(names,chain):
                    coords[side+" "+name] = (pt[0],pt[1]+(4 if names[0]=="SHOULDER" else 0))
        for joint in source:
            label = joint["label"]
            pt = coords.get(label)
            if pt is None:
                pt=(int(joint["x"]*128)-5,int(joint["y"]*128)+(1 if not flight else -2))
            joint.update(x=(pt[0]+.5)/128,y=(pt[1]+.5)/128)
        poses.append(source)
    body.update(action="run",keypoints=poses,description="Barefoot young woman with short dark hair and loose ivory gown, near limbs light and far limbs in shade")
    return body


if __name__ == "__main__":
    main(HERE,pilot_request,FRAMES)
