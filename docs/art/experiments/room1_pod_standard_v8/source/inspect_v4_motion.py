from pathlib import Path
import bpy, json

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "room1_pod_volume_v4" / "room1_pod_volume_v4.blend"
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
rows = []
for obj in bpy.data.objects:
    if obj.animation_data or obj.name in {"Whole_lid_motion", "ONE_PIECE_COVER_head_window"}:
        row = {"name": obj.name, "type": obj.type, "parent": obj.parent.name if obj.parent else None,
               "location": list(obj.location), "rotation": list(obj.rotation_euler)}
        if obj.animation_data and obj.animation_data.action:
            action = obj.animation_data.action
            row["action"] = action.name
            curves = []
            if hasattr(action, "fcurves"):
                curves = action.fcurves
            else:
                for layer in action.layers:
                    for strip in layer.strips:
                        for channelbag in strip.channelbags:
                            curves.extend(channelbag.fcurves)
            row["fcurves"] = [{"path": c.data_path, "index": c.array_index,
                               "keys": [[p.co.x, p.co.y] for p in c.keyframe_points]}
                              for c in curves]
        rows.append(row)
print(json.dumps({"objects": rows,
                  "objects_all": [{"name": o.name, "type": o.type, "parent": o.parent.name if o.parent else None}
                                  for o in bpy.data.objects]}, indent=2))
