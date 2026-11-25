"""Trace the approved three-quarter standing sprite and pose it in native pixels."""
import base64
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REF = HERE.parent / "protagonist_five_idle_eyes_r3/final_45.png"
sys.path.insert(0, str(HERE.parent / "protagonist_walk_side_r3/cycle12"))
from generate import main

# Back-to-front order, with anatomical left closest to the camera.
REFERENCE = {
    "RIGHT HIP": (59, 64), "RIGHT KNEE": (59, 94), "RIGHT LEG": (60, 117),
    "RIGHT SHOULDER": (56, 32), "RIGHT ELBOW": (52, 51), "RIGHT ARM": (49, 66),
    "RIGHT EAR": (55, 18), "RIGHT EYE": (58, 17), "NECK": (62, 27),
    "NOSE": (59, 20), "LEFT EAR": (69, 18), "LEFT EYE": (62, 17),
    "LEFT HIP": (68, 65), "LEFT KNEE": (69, 95), "LEFT LEG": (70, 120),
    "LEFT SHOULDER": (70, 33), "LEFT ELBOW": (74, 52), "LEFT ARM": (73, 67),
}
RELAXED = REFERENCE | {
    "LEFT HIP": (70, 63), "LEFT KNEE": (70, 95), "RIGHT HIP": (60, 65),
    "RIGHT KNEE": (55, 94), "RIGHT LEG": (57, 119),
    "LEFT SHOULDER": (70, 34), "RIGHT SHOULDER": (56, 32),
    "NOSE": (61, 21), "RIGHT EYE": (59, 18), "LEFT EYE": (63, 18),
    "RIGHT EAR": (55, 18), "LEFT EAR": (69, 18),
    "RIGHT ELBOW": (52, 51), "RIGHT ARM": (60, 67),
    "LEFT ELBOW": (74, 52), "LEFT ARM": (60, 62),
}
LOW_ARMS = RELAXED | {
    "RIGHT ELBOW": (50, 51), "RIGHT ARM": (47, 66),
    "LEFT ELBOW": (76, 52), "LEFT ARM": (75, 67),
}
SEEDS = dict(A=6112531, B=6112547, C=6112591, D=6112613)


def points(pose):
    return [dict(label=k, x=(x + .5) / 128, y=(y + .5) / 128, z_index=i)
            for i, (k, (x, y)) in enumerate(pose.items())]


def request_body(key, arms_down=False):
    pose = points(LOW_ARMS if arms_down else RELAXED)
    hands = ("Both arms rest low at her sides with a slight bend at each elbow and fingers loose."
             if arms_down else "One open hand loosely cradles the opposite forearm just above the wrist, low in front of her lower belly. The held hand hangs below it, visible and relaxed.")
    return dict(description="The same short dark-haired barefoot woman from the reference, same sleepy eyes, eyelids, face, ivory hospital shift and pixel palette.",
                action="One still relaxed standing pose, left leg bearing weight, right knee soft and right foot slightly forward and out, both soles resting flat. Shoulders countertilted and relaxed, chin slightly lowered, gaze slightly toward viewer. " + hands,
                direction="south-west", view="side", no_background=True, seed=SEEDS[key],
                first_frame=dict(base64=base64.b64encode(REF.read_bytes()).decode()),
                first_frame_keypoints=points(REFERENCE), keypoints=[pose] * 3)


if __name__ == "__main__":
    for key in sys.argv[1:]:
        out = HERE / key
        out.mkdir(exist_ok=True)
        main(out, lambda: request_body(key, arms_down=(key == "D")), (1, 2, 3))
