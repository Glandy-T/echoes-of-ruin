"""Clone r28 and rebind the existing door color image only; no geometry/light changes."""
from pathlib import Path
import bpy,json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
def state():
 out={}
 for o in bpy.data.objects:
  d={'type':o.type,'matrix':[list(v) for v in o.matrix_world],'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'parent':o.parent.name if o.parent else None}
  if o.type=='MESH':
   d.update(vertices=[list(v.co) for v in o.data.vertices],faces=[list(p.vertices) for p in o.data.polygons],UVs={u.name:[list(x.uv) for x in u.data] for u in o.data.uv_layers},materials=[m.name if m else None for m in o.data.materials])
  if o.type=='LIGHT':d['light']=[o.data.type,o.data.energy,list(o.data.color)]
  if o.type=='CAMERA':d['camera']=[o.data.type,o.data.lens,o.data.ortho_scale]
  out[o.name]=hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
 return out
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'docs/art/experiments/room1_pod_age_full_r28/room1_pod_age_full_r28.blend'));before=state();changes=[]
old='assets/art/room1_integrated_door_pixellab_v7/door_front.png';new='assets/art/room1_door_material_r29/door_front.png'
for im in bpy.data.images:
 if not im.filepath:continue
 try:rel=Path(bpy.path.abspath(im.filepath)).resolve().relative_to(ROOT.resolve()).as_posix()
 except ValueError:continue
 if rel==old:
  im.filepath=str(ROOT/new);im.reload();changes.append({'image':im.name,'old':old,'new':new})
assert changes and state()==before
bpy.context.scene['r29_notice']='Only door face color map replaced, r28 room and all20 accepted pod variants unchanged. No new GI or door-light changes. Godot actual captures are presentation authority.'
bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(EXP/'room1_door_material_r29.blend'),compress=True,check_existing=False)
bpy.ops.wm.open_mainfile(filepath=str(EXP/'room1_door_material_r29.blend'));assert state()==before
external=[im for im in bpy.data.images if im.filepath and not im.packed_file];missing=[im.name for im in external if not Path(bpy.path.abspath(im.filepath)).is_file()];absolute=[im.name for im in external if not im.filepath.startswith('//')]
assert not missing and not absolute
(HERE/'blender_readback.json').write_text(json.dumps({'result':'PASS','frozen_objects':len(before),'geometry_UVs_transforms_material_slots_lights_cameras_exact':True,'image_changes':changes,'external_images':len(external),'missing':missing,'absolute_paths':absolute,'new_bake':False},indent=2),encoding='utf8')
print('R29_BLENDER_PASS',len(before),'frozen objects;',len(changes),'door image replacements')
