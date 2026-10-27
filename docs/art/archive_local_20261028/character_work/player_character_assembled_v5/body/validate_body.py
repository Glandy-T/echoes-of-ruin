"""Independent read-back validation for body_uv_ready_v5.blend."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from prepare_body_anatomy import BODY, OUT, PRESERVED, RIG, SOURCE, UV, audit, islands, protected


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), use_scripts=False)
    source_snapshot = protected(bpy.data.objects[BODY], bpy.data.objects[RIG])

    bpy.ops.wm.open_mainfile(filepath=str(OUT), use_scripts=False)
    body = bpy.data.objects[BODY]
    rig = bpy.data.objects[RIG]
    output_snapshot = protected(body, rig)
    layer = body.data.uv_layers.get(UV)
    if layer is None:
        raise RuntimeError(f"Missing {UV}")
    uv_audit, _ = audit(body.data, layer)
    uv_islands = islands(body.data, layer)
    checks = {
        "source_body_rig_weights_unchanged": source_snapshot == output_snapshot,
        "preserved_original_uv_present": body.data.uv_layers.get(PRESERVED) is not None,
        "active_uv": body.data.uv_layers.active == layer,
        "active_render_uv": layer.active_render,
        "zero_area_triangles": uv_audit["zero_area_triangles"] == 0,
        "outside_unit_square_triangles": uv_audit["outside_unit_square_triangles"] == 0,
        "positive_area_self_overlap_pairs": uv_audit["positive_area_self_overlap_pairs"] == 0,
        "broad_islands_no_face_shards": uv_islands["single_polygon_islands"] == 0,
    }
    report = {
        "status": "pass" if all(checks.values()) else "fail",
        "output": str(OUT),
        "checks": checks,
        "uv_audit": uv_audit,
        "uv_islands": uv_islands,
        "shape_key_Key_1_value": body.data.shape_keys.key_blocks["Key 1"].value,
        "rig_bone_count": len(rig.data.bones),
    }
    (ROOT / "independent_validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    if report["status"] != "pass":
        raise RuntimeError("Independent body UV validation failed.")


if __name__ == "__main__":
    main()
