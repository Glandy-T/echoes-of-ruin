"""4F exterior-only review, independent modules from frozen coordinates; no extra pod interiors."""
from pathlib import Path
import bpy,json,math,hashlib,time,runpy,os
from mathutils import Vector
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4];EXP=HERE.parent;OUT=ROOT/'assets/art/cryo_4f_complete_v3'
for p in [OUT,EXP/'evidence']:p.mkdir(parents=True,exist_ok=True)
D=json.loads((ROOT/'docs/cad/cryo_standard_floor/v3_trim/floor_layout.json').read_text(encoding='utf-8'))
ATLAS=4096;DENSITY=16;SAMPLES=int(os.environ.get('CRYO_4F_SAMPLES','4096'))
bpy.ops.wm.read_factory_settings(use_empty=True)
receivers=[];shells=[];records={};walk=[]
for r in D['corridors']+D['protected_gallery_floors']+[r for r in D['personnel_structural_nodes'] if r['tag']=='personnel_node_corridor']:
 walk.append([r['x1'],r['y1'],r['x2'],r['y2']])

def mat(name,texture=None,color=(.2,.25,.26,1)):
 m=bpy.data.materials.new(name);m.diffuse_color=color;m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=color;p.inputs['Roughness'].default_value=.95
 uv=m.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap'
 if texture:
  t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(texture),check_existing=True);t.interpolation='Closest';t.extension='REPEAT';m.node_tree.links.new(uv.outputs['UV'],t.inputs['Vector']);m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
 if name=='Wall':
  t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ROOT/'assets/art/cryo_corridor_sample_v1/wall_emission.png'));t.interpolation='Closest';t.extension='REPEAT';m.node_tree.links.new(uv.outputs['UV'],t.inputs['Vector']);m.node_tree.links.new(t.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=20*.06/.225
 return m
wall=mat('Wall',ROOT/'assets/art/cryo_corridor_sample_v1/wall.png');floor=mat('Floor',ROOT/'assets/art/cryo_corridor_sample_v1/floor.png');door=mat('Door',ROOT/'assets/art/room1_door_window_r30/door_front.png');dark=mat('Shell',color=(.12,.16,.16,1))

def quad(name,verts,uv,material,kind,zone=''):
 me=bpy.data.meshes.new(name);me.from_pydata([(x,y-4.2,z) for x,y,z in verts],[],[(0,1,2,3)]);me.update();u=me.uv_layers.new(name='UVMap')
 for i,v in enumerate(uv):u.data[i].uv=v
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(material)
 ob['kind']=kind;ob['zone']=zone;records[name]={'kind':kind,'zone':zone};receivers.append(ob);return ob

def box(name,x1,y1,x2,y2,z0,z1,kind='shell'):
 vs=[(x1,y1-4.2,z0),(x2,y1-4.2,z0),(x2,y2-4.2,z0),(x1,y2-4.2,z0),(x1,y1-4.2,z1),(x2,y1-4.2,z1),(x2,y2-4.2,z1),(x1,y2-4.2,z1)]
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(dark);shells.append(ob);ob['kind']=kind;return ob

def intervals(axis,fixed,lo,hi,sign,probe=.02):
 parts=[]
 for x0,y0,x1,y1 in walk:
  a,b,c,d=(x0,y0,x1,y1) if axis=='x' else (y0,x0,y1,x1)
  if b-1e-5<=fixed+sign*probe<=d+1e-5 and min(hi,c)-max(lo,a)>.015:parts.append((max(lo,a),min(hi,c)))
 result=[]
 for a,b in sorted(parts):
  if result and a<=result[-1][1]+1e-5:result[-1]=(result[-1][0],max(b,result[-1][1]))
  else:result.append((a,b))
 return result

def wall_faces(name,r,z0=0,z1=3.4,material=None,kind='wall',probe=.02):
 material=material or wall;x0,y0,x1,y1=[r[k] for k in ['x1','y1','x2','y2']]
 for axis,fixed,lo,hi,sgn in [('x',y0,x0,x1,-1),('x',y1,x0,x1,1),('y',x0,y0,y1,-1),('y',x1,y0,y1,1)]:
  for i,(a,b) in enumerate(intervals(axis,fixed,lo,hi,sgn,probe)):
   f=fixed+sgn*.003
   if axis=='x':v=[(a,f,z0),(b,f,z0),(b,f,z1),(a,f,z1)]
   else:v=[(f,a,z0),(f,b,z0),(f,b,z1),(f,a,z1)]
   if (axis=='x' and sgn>0) or (axis=='y' and sgn<0):v=list(reversed(v))
   uv=[]
   for x,y,z in v:
    u=((x-a) if axis=='x' else (y-a))/(1.4 if kind=='door' else 3.2)
    uv.append((u,(z-z0)/(z1-z0) if kind=='door' else z/3.4))
   quad(f'Face_{name}_{axis}_{sgn}_{i}',v,uv,material,kind)

for r in D['walls']:
 # Room1 already supplies its own exact shell; outside receiver cladding remains.
 if not (r['x1']>=-.001 and r['x2']<=21.001 and r['y1']>=4.199 and r['y2']<=13.701):box('Shell_'+r['id'],r['x1'],r['y1'],r['x2'],r['y2'],0,3.4)
 wall_faces(r['id'],r)

door_records=[]
for d in D['doors']:
 h=d['width']/2
 r=dict(x1=d['x']-h,y1=d['y']-.1,x2=d['x']+h,y2=d['y']+.1) if d['orientation']=='H' else dict(x1=d['x']-.1,y1=d['y']-h,x2=d['x']+.1,y2=d['y']+h)
 box('Header_'+d['id'],r['x1'],r['y1'],r['x2'],r['y2'],2.4,3.4)
 wall_faces('Header_'+d['id'],r,2.4,3.4)
 if d['id'] not in ['D001','D077']:
  leaf=dict(r)
  if d['orientation']=='H':leaf['y1']=d['y']-.035;leaf['y2']=d['y']+.035
  else:leaf['x1']=d['x']-.035;leaf['x2']=d['x']+.035
  box('LockedDoor_'+d['id'],leaf['x1'],leaf['y1'],leaf['x2'],leaf['y2'],0,2.4,'locked_door')
  wall_faces('Door_'+d['id'],leaf,0,2.4,door,'door',.18)
 door_records.append(dict(d,godot=[d['x'],0,4.2-d['y']],locked=d['id'] not in ['D001','D077']))

# Disjoint rectangular cover of walkable floor: overlap is removed, no room floors/pods.
xs=sorted({round(v,6) for r in walk for v in [r[0],r[2]]});ys=sorted({round(v,6) for r in walk for v in [r[1],r[3]]})
for yi,(y0,y1) in enumerate(zip(ys,ys[1:])):
 runs=[]
 for x0,x1 in zip(xs,xs[1:]):
  if any(a<=(x0+x1)/2<=c and b<=(y0+y1)/2<=d for a,b,c,d in walk):
   if runs and abs(runs[-1][1]-x0)<1e-5:runs[-1]=(runs[-1][0],x1)
   else:runs.append((x0,x1))
 for j,(x0,x1) in enumerate(runs):
  v=[(x0,y0,.003),(x1,y0,.003),(x1,y1,.003),(x0,y1,.003)]
  quad(f'Floor_{yi}_{j}',v,[(x/3.2,y/2.4) for x,y,z in v],floor,'floor')

# A separate non-rendered ceiling only participates in the bake.
ceiling=[]
for i,r in enumerate(walk):
 x0,y0,x1,y1=r;ob=box('ContextCeiling_'+str(i),x0,y0,x1,y1,3.41,3.51,'context');ceiling.append(ob)
 for c in ob.users_collection:pass

# Shelf charts preserve each planar face, including its internal diagonal.
cx=cy=8;rowh=0;charts={}
for ob in sorted(receivers,key=lambda o:-max((o.data.vertices[1].co-o.data.vertices[0].co).length,(o.data.vertices[2].co-o.data.vertices[1].co).length)):
 v=[p.co for p in ob.data.vertices];w=(v[1]-v[0]).length;h=(v[2]-v[1]).length
 pw=max(2,math.ceil(w*DENSITY));ph=max(2,math.ceil(h*DENSITY))
 if pw+16>ATLAS:raise RuntimeError('Chart too long')
 if cx+pw+8>ATLAS:cx=8;cy+=rowh+16;rowh=0
 assert cy+ph+8<ATLAS,'Atlas overflow'
 layer=ob.data.uv_layers.new(name='LightmapUV')
 for i,(u,vv) in enumerate([(0,0),(1,0),(1,1),(0,1)]):layer.data[i].uv=((cx+pw*u)/ATLAS,(cy+ph*vv)/ATLAS)
 ob.data.uv_layers.active_index=0;ob.data.uv_layers['UVMap'].active_render=True
 charts[ob.name]=[cx,cy,cx+pw,cy+ph];records[ob.name]['chart']=charts[ob.name]
 cx+=pw+16;rowh=max(rowh,ph)
audit=runpy.run_path(str(ROOT/'scripts/dev/room1_uv2_audit.py'))['audit_uv2_layout'](receivers)
assert audit['positive_area_overlap_count']==audit['uv_degenerate_triangle_count']==audit['out_of_atlas_vertex_count']==0
audit.update({'atlas':ATLAS,'lightmap_density_px_m':DENSITY,'margin_px':4,'chart_gap_px':16,'used_height':cy+rowh+8})
(EXP/'uv2_validation.json').write_text(json.dumps(audit,indent=2))
layout={'rooms':D['rooms'],'room_count':48,'other_room_pods':0,'walk_rects':walk,'doors':door_records,'receivers':records,'stairs':D['stairs'],'source_sha256':hashlib.sha256((ROOT/'docs/cad/cryo_standard_floor/v3_trim/floor_layout.json').read_bytes()).hexdigest(),'atlas':ATLAS}
(OUT/'layout.json').write_text(json.dumps(layout,indent=2))

# Export no ceiling; shells remain as the exterior-only room representation.
for o in bpy.context.scene.objects:o.select_set(False)
for o in receivers+[o for o in shells if o not in ceiling]:o.select_set(True)
bpy.context.view_layer.objects.active=receivers[0]
bpy.ops.export_scene.gltf(filepath=str(OUT/'cryo_4f_complete_v3.glb'),export_format='GLB',use_selection=True,export_extras=True)
print('F4_GEOMETRY_EXPORTED',len(receivers),'receivers',len(shells),'shells; no other-room pods',flush=True)

# Bake all receiver charts together, same room light/color separation.
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=SAMPLES;sc.cycles.use_adaptive_sampling=False;sc.cycles.max_bounces=4;sc.cycles.diffuse_bounces=3;sc.world=bpy.data.worlds.new('UnlitWorld');sc.world.color=(0,0,0)
device='CPU'
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
 for dev in prefs.devices:dev.use=dev.type=='CUDA'
 if any(d.type=='CUDA' for d in prefs.devices):sc.cycles.device='GPU';device='CUDA'
except Exception:sc.cycles.device='CPU'
im=bpy.data.images.new('F4_Irradiance',width=ATLAS,height=ATLAS,alpha=False,float_buffer=True);im.colorspace_settings.name='Non-Color'
for m in {m for o in receivers for m in o.data.materials}:
 t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;m.node_tree.nodes.active=t
bpy.ops.object.select_all(action='DESELECT');copies=[]
for original in receivers:
 ob=original.copy();ob.data=original.data.copy();bpy.context.collection.objects.link(ob);ob.select_set(True);original.hide_render=True;copies.append(ob)
bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();joined=bpy.context.object
sc.render.bake.use_pass_color=False;sc.render.bake.use_pass_direct=True;sc.render.bake.use_pass_indirect=True
start=time.monotonic();print('F4_BAKE_BEGIN',SAMPLES,'samples',device,'atlas',ATLAS,flush=True)
bpy.ops.object.bake(type='DIFFUSE',pass_filter={'DIRECT','INDIRECT'},uv_layer='LightmapUV',margin=4,use_clear=True)
bpy.data.objects.remove(joined,do_unlink=True)
for ob in receivers:ob.hide_render=False;ob.data.uv_layers.active_index=0;ob.data.uv_layers['UVMap'].active_render=True
# Half-float ZIP is linear HDR, reduces storage without blurring color art.
sc.render.image_settings.file_format='OPEN_EXR';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.color_depth='16';sc.render.image_settings.exr_codec='ZIP'
im.save_render(str(OUT/'strip_irradiance.exr'),scene=sc)
bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(EXP/'cryo_4f_complete_v3.blend'),compress=True)
sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=16;sc.render.resolution_y=16;sc.render.resolution_percentage=100
group=bpy.data.node_groups.new('F4_LinearDenoise','CompositorNodeTree');sc.compositing_node_group=group;s=group.nodes.new('CompositorNodeImage');s.image=im;n=group.nodes.new('CompositorNodeDenoise');group.links.new(s.outputs['Image'],n.inputs['Image']);o=group.nodes.new('CompositorNodeOutputFile');o.directory=str(OUT);o.file_name='strip_irradiance_denoised';o.file_output_items.new('RGBA','Irradiance');o.format.media_type='IMAGE';o.format.file_format='OPEN_EXR';o.format.color_mode='RGB';o.format.color_depth='16';o.format.exr_codec='ZIP';o.save_as_render=False;group.links.new(n.outputs['Image'],o.inputs[0]);bpy.ops.render.render();(OUT/'strip_irradiance_denoisedIrradiance.exr').replace(OUT/'strip_irradiance_denoised.exr')
manifest={'samples':SAMPLES,'device':device,'bake_seconds':time.monotonic()-start,'atlas':ATLAS,'receiver_count':len(receivers),'shell_count':len(shells)-len(ceiling),'room_count':48,'other_room_pods':0,'lightmap_density':DENSITY,'lightmap_storage':'linear 16-bit half float ZIP EXR','pass':'DIFFUSE DIRECT+INDIRECT; COLOR off','chart_gap':16,'dilation':4,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.suffix in ['.glb','.exr','.json']}}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));print('F4_BAKE_COMPLETE',manifest['bake_seconds'],flush=True)
