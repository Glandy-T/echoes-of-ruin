"""Retain r24 geometry/walls; rebind only the complete r26 floor material."""
from pathlib import Path
import bpy,json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];EXP=HERE.parent
OLD=ROOT/'docs/art/experiments/room1_wall_detail_full_r24/room1_wall_detail_full_r24.blend'
NEW=EXP/'room1_floor_detail_full_r26.blend'
def digest(data):return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def state():
    result={}
    for obj in bpy.data.objects:
        row={'type':obj.type,'matrix':[list(v) for v in obj.matrix_world],'parent':obj.parent.name if obj.parent else None,'hide_render':obj.hide_render,'hide_viewport':obj.hide_viewport}
        if obj.type=='MESH':
            row['vertices']=[list(v.co) for v in obj.data.vertices];row['polygons']=[list(p.vertices) for p in obj.data.polygons]
            row['UVs']={uv.name:[list(p.uv) for p in uv.data] for uv in obj.data.uv_layers};row['materials']=[m.name if m else None for m in obj.data.materials]
        if obj.type=='LIGHT':row['light']=[obj.data.type,obj.data.energy,list(obj.data.color)]
        if obj.type=='CAMERA':row['camera']=[obj.data.type,obj.data.lens,obj.data.ortho_scale,obj.data.clip_start,obj.data.clip_end]
        result[obj.name]=digest(row)
    return result
bpy.ops.wm.open_mainfile(filepath=str(OLD));before=state();changes=[]
mapping={'assets/art/room1_pixel_unify_r22/floor_with_leaks.png':'assets/art/room1_floor_detail_full_r26/floor_with_leaks.png'}
for image in bpy.data.images:
    if not image.filepath:continue
    try:relative=Path(bpy.path.abspath(image.filepath)).resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:continue
    if relative not in mapping:continue
    target=ROOT/mapping[relative];assert target.is_file() and not image.packed_file
    image.filepath=str(target);image.reload();changes.append({'image':image.name,'old':relative,'new':mapping[relative]})
assert len(changes)>=1 and {r['new'] for r in changes}==set(mapping.values()),changes
assert state()==before
bpy.context.scene['r26_review_notice']='Full-floor native PixelLab material expansion from approved r25 C; r24 walls, geometry/UV/lights/camera/pods/door unchanged. No new GI bake.'
bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(NEW),compress=True,check_existing=False)
bpy.ops.wm.open_mainfile(filepath=str(NEW));assert state()==before
external=[im for im in bpy.data.images if im.filepath and not im.packed_file]
missing=[im.name for im in external if not Path(bpy.path.abspath(im.filepath)).is_file()]
absolute=[im.name for im in external if not im.filepath.startswith('//')]
assert not missing and not absolute
report={'result':'PASS','frozen_objects':len(before),'geometry_UVs_transforms_lights_cameras_exact_after_reopen':True,'state_sha256':digest(before),'image_changes':changes,'new_floor_image_datablocks':len(changes),'external_unpacked':len(external),'missing_images':missing,'absolute_paths':absolute,'new_bake':False}
(HERE/'blender_readback.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('R26_BLENDER_PASS',len(before),'unchanged objects,',len(changes),'floor-image rebindings; no missing paths',flush=True)
