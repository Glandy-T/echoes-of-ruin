"""Call official PixelLab inpaint-v3 on project-owned guide/mask, no secret logs.

POST is never retried. Poll a submitted job separately to avoid duplicate use.
"""
import argparse
import base64
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "docs/art/experiments/pixellab_direct_api_check_v1/source"))
from pixellab_direct import credential, request  # noqa: E402


def encoded(path):
    return {"image": {"base64": "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")},
            "size": {"width": 112, "height": 184}}


def find_image(value):
    if isinstance(value, dict):
        if isinstance(value.get("base64"), str):
            return value["base64"]
        for child in value.values():
            found = find_image(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_image(child)
            if found:
                return found
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("submit", "poll"))
    parser.add_argument("--variant", choices=("base", "revision", "header"), default="base")
    args = parser.parse_args()
    token = credential(True)  # official Aseprite PixelLab account, memory only
    suffix = "" if args.variant == "base" else "_" + args.variant
    submission_path = HERE / ("submission" + suffix + ".json")
    if args.action == "submit":
        if submission_path.exists():
            raise RuntimeError("This variant already has a submitted PixelLab job; POST was not retried")
        payload = {"description": (HERE / ("prompt" + suffix + ".txt")).read_text(encoding="utf-8"),
                   "inpainting_image": encoded(HERE / ("header_guide.png" if args.variant == "header" else "guide.png")),
                   "mask_image": encoded(HERE / ("header_mask.png" if args.variant == "header" else "mask.png")),
                   "no_background": False, "crop_to_mask": False}
        result = request("POST", "/inpaint-v3", token, payload)
        job = result.get("background_job_id")
        if not job:
            raise RuntimeError("PixelLab did not return a job ID; POST was not retried")
        safe = {"endpoint": "/inpaint-v3", "background_job_id": job,
                "status": result.get("status"), "usage": result.get("usage")}
        submission_path.write_text(json.dumps(safe, indent=2), encoding="utf-8")
        print(json.dumps(safe))
        return
    submitted = json.loads(submission_path.read_text(encoding="utf-8"))
    result = request("GET", "/background-jobs/" + submitted["background_job_id"], token)
    status = result.get("status")
    print("PIXELLAB_JOB", status)
    if status != "completed":
        if status == "failed":
            (HERE / ("job_failed" + suffix + ".json")).write_text(json.dumps({"status": status,
                "keys": list((result.get("last_response") or {}).keys())}, indent=2), encoding="utf-8")
        return
    raw = find_image(result.get("last_response"))
    if not raw:
        print("Completed response has no inline image; result keys:", list((result.get("last_response") or {}).keys()))
        return
    output = HERE.parent / "raw" / ("pixellab_inpaint_v3" + suffix + ".png")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(base64.b64decode(raw.split(",")[-1], validate=True))
    safe = {"endpoint": "/inpaint-v3", "background_job_id": submitted["background_job_id"],
            "status": status, "usage": result.get("usage"), "image_file": output.name}
    (HERE.parent / ("result" + suffix + ".json")).write_text(json.dumps(safe, indent=2), encoding="utf-8")
    print("PIXELLAB_SAVED", output.name)


if __name__ == "__main__":
    main()
