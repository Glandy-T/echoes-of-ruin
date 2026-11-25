"""Submit once and resume polling the same PixelLab job on subsequent runs."""
import base64
import json
import os
import time
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import UUID

from api_input import HERE, build_request


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def request(path, body=None):
    req = Request("https://api.pixellab.ai/v2/" + path, headers={
        "Authorization": "Bearer " + os.environ["PIXELLAB_API_TOKEN"],
        "Content-Type": "application/json", "User-Agent": "EchoesOfRuin-art/1.0",
    }, data=None if body is None else json.dumps(body).encode())
    try:
        with build_opener(NoRedirect()).open(req, timeout=75) as response:
            return json.load(response)
    except HTTPError as exc:
        raise SystemExit(f"PixelLab {path}: HTTP {exc.code} {exc.reason}") from None


def main(directory=HERE, make_body=build_request, frame_numbers=tuple(range(1,13))):
    receipt = directory / "generation.json"
    if receipt.exists():
        job = json.loads(receipt.read_text())
    else:
        before = request("balance")
        response = request("animate-with-skeleton-v3", make_body())
        job = dict(id=str(UUID(response["background_job_id"])), before=before,
                   usage=response.get("usage"))
        receipt.write_text(json.dumps(job, indent=2))
    print("Tracking", job["id"], flush=True)
    while True:
        response = request("background-jobs/" + str(UUID(job["id"])))
        if response["status"] in ("completed", "failed", "cancelled", "canceled"):
            break
        print(response["status"], flush=True)
        time.sleep(8)
    job["status"] = response["status"]
    job["after"] = request("balance")
    result = response.get("last_response") or {}
    job["result_usage"] = result.get("usage")
    receipt.write_text(json.dumps(job, indent=2))
    if job["status"] != "completed":
        raise SystemExit("PixelLab job " + job["status"])
    frames = result["images"]
    assert len(frames) == len(frame_numbers)
    raw = directory / "raw"
    raw.mkdir(exist_ok=True)
    for i, frame in zip(frame_numbers, frames):
        encoded = frame["base64"].split(",")[-1]
        png = base64.b64decode(encoded, validate=True)
        assert png.startswith(b"\x89PNG\r\n\x1a\n")
        (raw / f"{i:02}.png").write_bytes(png)
    print("Saved", len(frames), "raw PNGs")


if __name__ == "__main__":
    main()
