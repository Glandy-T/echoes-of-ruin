"""Make the independent r19 Blender source portable without repacking images."""
from pathlib import Path
import bpy, json, os

HERE = Path(__file__).resolve().parent
BLEND = HERE.parent / "room1_complete_r19.blend"
REPORT = HERE / "relative_paths_check.json"

def scan():
    external = [image for image in bpy.data.images if image.filepath and not image.packed_file]
    missing = [image.name for image in external if not Path(bpy.path.abspath(image.filepath)).is_file()]
    absolute = [image.name for image in external if not image.filepath.startswith("//")]
    return {"external_unpacked":len(external), "absolute_unpacked":len(absolute),
            "missing_unpacked":missing, "absolute_names":absolute}

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
bpy.ops.file.make_paths_relative()
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True, check_existing=False)
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
report = scan()
assert report["absolute_unpacked"] == 0, report["absolute_names"][:8]
assert not report["missing_unpacked"], report["missing_unpacked"][:8]
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("R19_RELATIVE_PATHS_COMPLETE", json.dumps(report, ensure_ascii=False), flush=True)
