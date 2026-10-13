"""Write a read-only mesh/material inventory for the v4.1 pod source."""
from pathlib import Path
import json
import bpy

ROOT = Path(__file__).resolve().parent
source = ROOT.parent / "room1_pod_reference_v4_1" / "room1_pod_reference_v4_1.blend"
bpy.ops.wm.open_mainfile(filepath=str(source))

items = []
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    items.append({
        "object": obj.name,
        "mesh": obj.data.name,
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "material_slots": [material.name if material else None for material in obj.data.materials],
        "uv_layers": [layer.name for layer in obj.data.uv_layers],
    })

inventory = {
    "meshes": items,
    "cameras": [obj.name for obj in bpy.data.objects if obj.type == "CAMERA"],
    "lights": [obj.name for obj in bpy.data.objects if obj.type == "LIGHT"],
}
(ROOT / "source_mesh_inventory.json").write_text(
    json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8"
)
