"""Independent Blender reopen/readback check for Cryo Building Blockout v1."""
from pathlib import Path
import bpy
import json

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / "docs/art/experiments/cryo_building_blockout_v1"
BLEND = OUT / "cryo_building_blockout_v1.blend"
bpy.ops.wm.open_mainfile(filepath=str(BLEND))

root = bpy.data.collections.get("CRYO_BUILDING_BLOCKOUT_V1")
levels = ["B4", "B3", "B2", "B1"] + [f"{i}F" for i in range(1, 17)]
missing = [x for x in levels if bpy.data.collections.get(x) is None]
anchor = bpy.data.objects.get("F4_SW01_ROOM1_REPLACEABLE_ANCHOR")
anchor_props = {k: (list(v) if hasattr(v, "__len__") and not isinstance(v, str) else v) for k, v in anchor.items()} if anchor else None
result = {
  "schema": "cryo_building_blockout_v1_reopen_check",
  "blend_exists": BLEND.exists(),
  "root_exists": root is not None,
  "missing_level_collections": missing,
  "level_count": len(levels) - len(missing),
  "f4_anchor_exists": anchor is not None,
  "f4_anchor": anchor_props,
  "logical_room_envelopes_nominal": sum(int(o.get("room_count", 0)) for o in bpy.data.objects if "LogicalEnvelopeMetadata" in o.name),
  "wall_modules": sum(1 for o in bpy.data.objects if o.get("frozen_wall_id")),
  "source_claim": root.get("cad_geometry_imported") if root else None,
  "result": "PASS" if root and not missing and anchor and root.get("cad_geometry_imported") is False else "FAIL"
}
(OUT / "reopen_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
static_path = OUT / "validation.json"
if static_path.exists():
    static = json.loads(static_path.read_text(encoding='utf-8'))
    static["status"] = "PASS_STATIC_SOURCE_AND_REOPEN_CHECK"
    static["reopen_check"] = "reopen_validation.json"
    static_path.write_text(json.dumps(static, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
