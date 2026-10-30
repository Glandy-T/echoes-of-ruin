"""Read-only reopened Blender source checks in an independent checkout."""
from pathlib import Path
import bpy,json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
bpy.ops.wm.open_mainfile(filepath=str(EXP/'room1_pixel_unify_r22.blend'))
external=[im for im in bpy.data.images if im.filepath and not im.packed_file]
missing=[im.name for im in external if not Path(bpy.path.abspath(im.filepath)).is_file()]
absolute=[im.name for im in external if not im.filepath.startswith('//')]
new=[im.name for im in external if '/room1_pixel_unify_r22/' in im.filepath.replace('\\','/')]
assert not missing and not absolute,(missing,absolute)
assert len(bpy.data.objects)==131 and len(new)==69,(len(bpy.data.objects),len(new))
report={'result':'PASS','objects':len(bpy.data.objects),'external_unpacked':len(external),'r22_image_paths':len(new),'missing_images':missing,'absolute_paths':absolute,'blend_modified':False}
(HERE/'upload_blender_paths.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('R22_UPLOAD_BLENDER_PATHS_PASS',json.dumps(report),flush=True)
