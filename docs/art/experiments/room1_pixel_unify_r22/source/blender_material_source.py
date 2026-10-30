"""Versioned r19 geometry source with r22 material paths only; never rebakes light."""
from pathlib import Path
import bpy,json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];EXP=HERE.parent
OLD=ROOT/'docs/art/experiments/room1_complete_r19/room1_complete_r19.blend'
NEW=EXP/'room1_pixel_unify_r22.blend'
def digest(value):return hashlib.sha256(json.dumps(value,separators=(',',':'),sort_keys=True).encode()).hexdigest()
def frozen_state():
    result={}
    for obj in bpy.data.objects:
        data={'type':obj.type,'matrix':[list(row) for row in obj.matrix_world],'parent':obj.parent.name if obj.parent else None,'hide_render':obj.hide_render,'hide_viewport':obj.hide_viewport}
        if obj.type=='MESH':
            mesh=obj.data
            data['vertices']=[list(v.co) for v in mesh.vertices]
            data['polygons']=[list(p.vertices) for p in mesh.polygons]
            data['uvs']={uv.name:[list(loop.uv) for loop in uv.data] for uv in mesh.uv_layers}
            data['material_names']=[m.name if m else None for m in mesh.materials]
        if obj.type=='LIGHT':data['light']=[obj.data.type,obj.data.energy,list(obj.data.color)]
        if obj.type=='CAMERA':data['camera']=[obj.data.type,obj.data.lens,obj.data.ortho_scale,obj.data.clip_start,obj.data.clip_end]
        result[obj.name]=digest(data)
    return result
bpy.ops.wm.open_mainfile(filepath=str(OLD));before=frozen_state()
mapping={}
for side in ['left','right','front','rear']:mapping[f'assets/art/room1_wall_lamp_r13/wall_{side}.png']=f'assets/art/room1_pixel_unify_r22/wall_{side}.png'
mapping['assets/art/room1_floor_variants_r15/floor_with_leaks.png']='assets/art/room1_pixel_unify_r22/floor_with_leaks.png'
for variant in 'abcd':
    for role in ['lid','shell_side','shell_end']:mapping[f'assets/art/room1_pod_pixellab_r16/variant_{variant}/{role}.png']=f'assets/art/room1_pixel_unify_r22/variant_{variant}/{role}.png'
for number in range(1,21):
    for role in ['lid','shell_end']:mapping[f'assets/art/room1_complete_r19/numbered/P{number:02d}_{role}.png']=f'assets/art/room1_pixel_unify_r22/numbered/P{number:02d}_{role}.png'
changed=[]
for image in bpy.data.images:
    if not image.filepath:continue
    absolute=Path(bpy.path.abspath(image.filepath)).resolve()
    try:relative=absolute.relative_to(ROOT.resolve()).as_posix()
    except ValueError:continue
    if relative not in mapping:continue
    target=ROOT/mapping[relative];assert target.is_file(),target
    assert not image.packed_file,'Expected the r19 portable external source, not packed texture'
    image.filepath=str(target);image.reload()
    changed.append({'image':image.name,'old':relative,'new':mapping[relative]})
assert len(changed)>=60, len(changed)
assert frozen_state()==before,'Unexpected geometry, UV, camera or light change'
bpy.context.scene['r22_review_notice']='Material candidate only; geometry, UVs, lights unchanged from r19. Godot still uses r19 GI; no new bake.'
bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(NEW),compress=True,check_existing=False)
bpy.ops.wm.open_mainfile(filepath=str(NEW));after=frozen_state();assert after==before
external=[im for im in bpy.data.images if im.filepath and not im.packed_file]
missing=[im.name for im in external if not Path(bpy.path.abspath(im.filepath)).is_file()]
absolute=[im.name for im in external if not im.filepath.startswith('//')]
assert not missing and not absolute,(missing,absolute)
report={'result':'PASS','objects':len(before),'geometry_UVs_transforms_lights_cameras_exact_after_reopen':True,'state_sha256':digest(before),'updated_image_datablocks':len(changed),'image_rebindings':changed,'external_unpacked':len(external),'missing_images':missing,'absolute_paths':absolute,'new_bake':False}
(HERE/'blender_readback.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('R22_BLENDER_SOURCE_PASS',len(before),'frozen objects',len(changed),'material image rebindings',flush=True)
