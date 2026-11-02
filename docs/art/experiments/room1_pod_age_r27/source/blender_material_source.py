"""Clone r26, rebind only P12 exterior materials. Geometry, UVs and illumination stay exact."""
from pathlib import Path
import bpy,json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
def state():
 result={}
 for o in bpy.data.objects:
  d={'type':o.type,'matrix':[list(v) for v in o.matrix_world],'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'parent':o.parent.name if o.parent else None}
  if o.type=='MESH':d.update(vertices=[list(v.co) for v in o.data.vertices],faces=[list(p.vertices) for p in o.data.polygons],UVs={u.name:[list(x.uv) for x in u.data] for u in o.data.uv_layers})
  if o.type=='LIGHT':d['light']=[o.data.type,o.data.energy,list(o.data.color)]
  if o.type=='CAMERA':d['camera']=[o.data.type,o.data.lens,o.data.ortho_scale]
  result[o.name]=hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
 return result
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'docs/art/experiments/room1_floor_detail_full_r26/room1_floor_detail_full_r26.blend'))
before=state();changes=[];candidates=[]
for o in bpy.data.objects:
 if o.type!='MESH' or 'P12' not in o.name:continue
 for slot in o.material_slots:
  mat=slot.material
  if not mat or not mat.use_nodes:continue
  matching=[]
  for n in mat.node_tree.nodes:
   if n.type!='TEX_IMAGE' or not n.image:continue
   p=Path(bpy.path.abspath(n.image.filepath)).resolve()
   try:rel=p.relative_to(ROOT.resolve()).as_posix()
   except ValueError:continue
   candidates.append({'object':o.name,'material':mat.name,'image':rel})
   role=None
   if 'room1_pixel_unify_r22' in rel:
    if p.name=='P12_lid.png':role='lid'
    elif p.name=='P12_shell_end.png':role='shell_end'
    elif p.name=='shell_side.png':role='shell_side'
   if role:matching.append((n.name,role,rel))
  if not matching:continue
  new_mat=mat.copy();new_mat.name=mat.name+'_r27_P12_only';slot.material=new_mat
  for node_name,role,old in matching:
   p=ROOT/'assets/art/room1_pod_age_r27'/f'{role}.png';assert p.is_file()
   image=bpy.data.images.load(str(p),check_existing=True);image.colorspace_settings.name='sRGB'
   node=new_mat.node_tree.nodes[node_name];node.image=image;node.interpolation='Closest'
   changes.append({'object':o.name,'role':role,'old':old,'new':p.relative_to(ROOT).as_posix()})
assert {x['role'] for x in changes}=={'lid','shell_side','shell_end'},candidates
assert state()==before
bpy.context.scene['r27_review_notice']='P12 native pixel exterior aging only. r26 room, UVs, geometry and existing GI unchanged. Godot is presentation authority.'
bpy.ops.file.make_paths_relative();dst=EXP/'room1_pod_age_r27.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dst),compress=True,check_existing=False)
bpy.ops.wm.open_mainfile(filepath=str(dst));assert state()==before
external=[im for im in bpy.data.images if im.filepath and not im.packed_file]
missing=[im.name for im in external if not Path(bpy.path.abspath(im.filepath)).is_file()]
absolute=[im.name for im in external if not im.filepath.startswith('//')]
assert not missing and not absolute
(HERE/'blender_readback.json').write_text(json.dumps({'result':'PASS','frozen_objects':len(before),'geometry_UVs_transforms_lights_cameras_exact':True,'changes':changes,'external_images':len(external),'missing':missing,'absolute_paths':absolute,'new_bake':False},indent=2),encoding='utf8')
print('R27_BLENDER_PASS',len(before),'frozen objects;',len(changes),'P12 bindings')
