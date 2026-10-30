from pathlib import Path
import bpy,json,subprocess,sys
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
bpy.ops.wm.open_mainfile(filepath=str(EXP/'room1_wall_detail_full_r24.blend'))
external=[im for im in bpy.data.images if im.filepath and not im.packed_file]
missing=[im.name for im in external if not Path(bpy.path.abspath(im.filepath)).is_file()]
absolute=[im.name for im in external if not im.filepath.startswith('//')]
new=[im.name for im in external if '/room1_wall_detail_full_r24/' in im.filepath.replace('\\','/')]
assert len(bpy.data.objects)==131 and len(new)==7 and not missing and not absolute
tracked_check=None
if '--require-tracked' in sys.argv:
    tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode('utf-8').split(chr(0)))
    paths=[Path(bpy.path.abspath(im.filepath)).resolve().relative_to(ROOT.resolve()).as_posix() for im in external]
    absent=[p for p in paths if p not in tracked];assert not absent,absent
    tracked_check=len(paths)
report={'result':'PASS','objects':len(bpy.data.objects),'external_unpacked':len(external),'r24_wall_image_datablocks':len(new),'missing_images':missing,'absolute_paths':absolute,'tracked_images_checked':tracked_check,'blend_modified':False}
(HERE/'upload_blender_paths.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('R24_UPLOAD_BLENDER_PASS',json.dumps(report),flush=True)
