"""Structural validation for r24 all-wall same-camera comparison captures."""
from __future__ import annotations
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
RECORD = EVIDENCE / "capture_record.json"
PAIRED = (
    "game_front_left_closed", "game_front_middle_closed", "game_front_right_closed",
    "game_back_left_closed", "game_back_middle_closed", "game_back_right_closed",
    "corner_rear_left", "corner_rear_right", "corner_front_left", "corner_front_right",
    "front_wall_full", "left_wall_full", "right_wall_full", "rear_wall_full",
    "door_header_and_sides", "game_front_left_open", "p12_oblique_open",
    "scan_front_01", "scan_front_02", "scan_front_03", "scan_front_04",
    "scan_rear_01", "scan_rear_02", "scan_rear_03", "scan_rear_04",
    "scan_left_01", "scan_left_02", "scan_right_01", "scan_right_02",
)

def main() -> None:
    records = json.loads(RECORD.read_text(encoding="utf-8"))
    by_name = {item["file"]: item for item in records}
    checks: dict[str, bool] = {}
    for view in PAIRED:
        items = [by_name[f"{mode}_{view}.png"] for mode in (1, 2)]
        checks[f"{view}_two_modes"] = len(items) == 2
        checks[f"{view}_same_camera"] = len({item["camera"] for item in items}) == 1
        checks[f"{view}_same_fov"] = len({item["fov"] for item in items}) == 1
        resolutions = {tuple(item["resolution"]) for item in items}
        checks[f"{view}_same_resolution"] = len(resolutions) == 1 and resolutions == {(1280, 720)}
        for item in items:
            image = Image.open(EVIDENCE / item["file"])
            checks[f"{item['file']}_matches_record"] = list(image.size) == item["resolution"]
            checks[f"{item['file']}_screen_overlays_frozen"] = item["screen_overlays_frozen"] is True
    # Frozen labels/actor/UI make A-reference restoration an exact, scoped map
    # reset assertion. No broad image threshold is used.
    initial = Image.open(EVIDENCE / "1_rear_wall_full.png")
    restored = Image.open(EVIDENCE / "1_restore_rear_wall_closed.png")
    checks["r22_restore_pixel_exact"] = initial.tobytes() == restored.tobytes()
    # r24 material must also be visible in the inherited raw/denoised r19 GI
    # endpoints. These are not A/B material comparisons and must not imply a rebake.
    for name in ("2_raw_door_header.png", "2_denoised_door_header.png", "2_raw_rear_corner.png", "2_denoised_rear_corner.png"):
        item = by_name[name]
        image = Image.open(EVIDENCE / name)
        checks[f"{name}_r24_gi_diagnostic"] = item["mode"] == 2 and tuple(image.size) == (1280, 720)
    result = {"result": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
              "scope": "Capture structure only: actual rendered all-wall coverage, paired A/B camera/FOV/resolution, frozen screen overlays, and exact r22 A/B/A restoration. Artistic acceptance remains review work."}
    (ROOT / "source" / "capture_validation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("R24_CAPTURE", result["result"], "checks=", len(checks))
    if result["result"] != "PASS": raise SystemExit(1)

if __name__ == "__main__": main()
