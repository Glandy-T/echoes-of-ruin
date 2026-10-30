"""Structural validation for r23 same-camera wall comparison captures."""
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
RECORD = EVIDENCE / "capture_record.json"
VIEWS = ("game_rear_patch_closed", "rear_patch_full_closed", "rear_patch_whole_closed", "rear_patch_joint_detail_closed", "rear_patch_base_color", "game_rear_patch_open", "rear_patch_full_open", "rear_patch_whole_open")

def main() -> None:
    records = json.loads(RECORD.read_text(encoding="utf-8"))
    by_name = {item["file"]: item for item in records}
    checks: dict[str, bool] = {}
    for view in VIEWS:
        items = [by_name[f"{mode}_{view}.png"] for mode in range(1, 5)]
        checks[f"{view}_four_modes"] = len(items) == 4
        checks[f"{view}_same_camera"] = len({item["camera"] for item in items}) == 1
        checks[f"{view}_same_fov"] = len({item["fov"] for item in items}) == 1
        checks[f"{view}_same_resolution"] = len({tuple(item["resolution"]) for item in items}) == 1
        for item in items:
            image = Image.open(EVIDENCE / item["file"])
            checks[f"{item['file']}_matches_record"] = list(image.size) == item["resolution"]
    # Exact A-reference restoration confirms the final texture reset did not
    # leave a candidate texture assigned. Image pixels are expected to match
    # because the capture freezes label subviewports and hides the actor/UI.
    restored = Image.open(EVIDENCE / "1_restore_rear_patch_closed.png")
    initial = Image.open(EVIDENCE / "1_rear_patch_full_closed.png")
    checks["reference_restore_pixel_exact"] = restored.tobytes() == initial.tobytes()
    result = {"result": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
              "scope": "Capture structure only: same pose/FOV/resolution for modes 1-4 and exact final reference restoration. It does not judge artistic preference."}
    (ROOT / "source" / "capture_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("R23_CAPTURE", result["result"], "checks=", len(checks))
    if result["result"] != "PASS": raise SystemExit(1)

if __name__ == "__main__": main()
