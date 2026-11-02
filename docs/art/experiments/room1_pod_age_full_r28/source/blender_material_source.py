"""Clone approved single-pod source and replace only the 60 exterior color bindings."""
from pathlib import Path
import bpy,json,hashlib,re
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
layout={p['id']:p for p in json.loads((ROOT/'assets/art/room1_pod_age_full_r28/layout_variants.json').read_text())['pods']}
def state():
 out={}
 for o in bpy.data.objects:
  d={'type':o.type,'matrix':[list(v) for v in o.matrix_world],'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'parent':o.parent.name if o.parent else None}
  if o.type=='MESH':d.update(vertices=[list(v.co) for v in o.data.vertices],faces=[list(p.vertices) for p in o.data.polygons],UVs={u.name:[list(x.uv) for x in u.data] for u in o.data.uv_layers})
  if o.type=='LIGHT':d['light']=[o.data.type,o.data.energy,list(o.data.color)]
  if o.type=='CAMERA':d['camera']=[o.data.type,o.data.lens,o.data.ortho_scale]
  out[o.name]=hashlib.sha256(json.dumps(d,sort_keys=True).encode()).hexdigest()
 return out
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'docs/art/experiments/room1_pod_age_r27/room1_pod_age_r27.blend'));before=state();changes=[]
for o in bpy.data.objects:
 match=re.match(r'R19_(P\d{2})_closed_receiver',o.name)
 if o.type!='MESH' or not match:continue
 pid=match.group(1);entry=layout[pid]
 for slot in o.material_slots:
  mat=slot.material
  if not mat or not mat.use_nodes:continue
  nodes=[]
  for n in mat.node_tree.nodes:
   if n.type!='TEX_IMAGE' or not n.image:continue
   p=Path(bpy.path.abspath(n.image.filepath)).resolve()
   try:rel=p.relative_to(ROOT.resolve()).as_posix()
   except ValueError:continue
   role=None
   if 'room1_pixel_unify_r22' in rel:
    if p.name==pid+'_lid.png':role='lid'
    elif p.name==pid+'_shell_end.png':role='shell_end'
    elif p.name=='shell_side.png':role='shell_side'
   elif pid=='P12' and 'room1_pod_age_r27' in rel and p.stem in ['lid','shell_side','shell_end']:role=p.stem
   if role:nodes.append((n.name,role,rel))
  if not nodes:continue
  clone=mat.copy();clone.name=mat.name+'_r28_'+pid;slot.material=clone
  for node,role,old in nodes:
   rel=entry['maps'][role].removeprefix('res://');p=ROOT/rel;assert p.is_file()
   im=bpy.data.images.load(str(p),check_existing=True);im.colorspace_settings.name='sRGB';clone.node_tree.nodes[node].image=im;clone.node_tree.nodes[node].interpolation='Closest'
   changes.append({'pod':pid,'role':role,'old':old,'new':rel})
assert len(changes)==60 and {c['pod'] for c in changes}==set(layout),changes
assert state()==before
bpy.context.scene['r28_review_notice']='All20 exterior native PixelLab aging; four independent distributions per role,20 unique combinations. Existing geometry,UVs,lighting and GI unchanged. No new bake.'
bpy.ops.file.make_paths_relative();dst=EXP/'room1_pod_age_full_r28.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dst),compress=True,check_existing=False)
bpy.ops.wm.open_mainfile(filepath=str(dst));assert state()==before
external=[im for im in bpy.data.images if im.filepath and not im.packed_file];missing=[im.name for im in external if not Path(bpy.path.abspath(im.filepath)).is_file()];absolute=[im.name for im in external if not im.filepath.startswith('//')]
assert not missing and not absolute
(HERE/'blender_readback.json').write_text(json.dumps({'result':'PASS','frozen_objects':len(before),'geometry_UVs_transforms_lights_cameras_exact':True,'changes':changes,'external_images':len(external),'missing':missing,'absolute_paths':absolute,'new_bake':False},indent=2),encoding='utf8')
print('R28_BLENDER_PASS',len(before),'frozen objects;',len(changes),'exterior bindings')
