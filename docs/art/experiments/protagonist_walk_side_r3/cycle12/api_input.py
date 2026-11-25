"""Export the verified PXO to a PixelLab v3 request without submitting a job."""
import base64
import json
from zipfile import ZipFile

from PIL import Image

from prepare import FAR_ARM, FAR_LEG, HERE, NEAR_ARM, NEAR_LEG, NECK, joints, read_layer


def keypoints(image):
    xy, _ = joints(image)
    # The character faces west. The left limbs are on the visible side.
    order = [
        *zip(("RIGHT HIP", "RIGHT KNEE", "RIGHT LEG"), FAR_LEG),
        *zip(("RIGHT SHOULDER", "RIGHT ELBOW", "RIGHT ARM"), FAR_ARM),
        ("RIGHT EAR", (255, 0, 189)), ("RIGHT EYE", (0, 120, 255)),
        ("NECK", NECK), ("NOSE", (255, 255, 0)),
        ("LEFT EAR", (255, 0, 180)), ("LEFT EYE", (0, 130, 255)),
        *zip(("LEFT HIP", "LEFT KNEE", "LEFT LEG"), NEAR_LEG),
        *zip(("LEFT SHOULDER", "LEFT ELBOW", "LEFT ARM"), NEAR_ARM),
    ]
    assert len(order) == len(xy) == 18 and set(dict(order).values()) == set(xy)
    return [
        dict(label=label, x=(xy[key][0] + 0.5) / image.width,
             y=(xy[key][1] + 0.5) / image.height, z_index=depth)
        for depth, (label, key) in enumerate(order)
    ]


def build_request():
    reference = HERE.parents[1] / "protagonist_five_idle_eyes_r3" / "final_90.png"
    with ZipFile(HERE / "walk_44_input.pxo") as archive:
        project = json.loads(archive.read("data.json"))
        with Image.open(reference) as original:
            embedded = read_layer(archive, project, 1, 1)
            assert original.convert("RGBA").tobytes() == embedded.tobytes()
        poses = [keypoints(read_layer(archive, project, i + 1, 2))
                 for i in range(len(project["frames"]))]
    assert len(poses) == 13
    return dict(description="Barefoot young woman with short dark hair and a loose ivory gown",
                action="walk", direction="west", view="side", no_background=True,
                seed=480456224, first_frame=dict(base64=base64.b64encode(reference.read_bytes()).decode()),
                first_frame_keypoints=poses[0], keypoints=poses[1:])


if __name__ == "__main__":
    print(json.dumps(build_request(), separators=(",", ":")))
