"""Versioned corridor DIFFUSE direct+indirect irradiance; original albedo stays separate."""
from pathlib import Path
import bpy,json,hashlib,time,runpy,os
from mathutils import Vector
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
EXP=ROOT/'docs/art/experiments/cryo_corridor_baked_v2';OUT=ROOT/'assets/art/cryo_corridor_baked_v2'
for p in [EXP,OUT,EXP/'evidence']:p.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(HERE.parent/'cryo_corridor_sample_v1.blend'))
receivers=list(bpy.context.scene.objects)
assert len(receivers)==3
rects={'Wall_3p2m_TwoBays':(16,16,400,424),'Room1_Exterior_Wall_Module':(416,16,800,424),'Floor_3p2m_Unique':(16,448,400,736)}
for ob in receivers:
 layer=ob.data.uv_layers.new(name='LightmapUV');a,b,c,d=rects[ob.name]
 for i,v in enumerate(ob.data.uv_layers['UVMap'].data):layer.data[i].uv=((a+v.uv.x*(c-a))/1024,(b+v.uv.y*(d-b))/1024)
 ob.data.uv_layers.active_index=0
 for uv in ob.data.uv_layers:uv.active_render=uv.name=='UVMap'
 # Same physical ribbon radiance basis as the room: strength20 *.06/.225.
 for mat in ob.data.materials:
  bsdf=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
  uvnode=mat.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='UVMap'
  for tex in [n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE']:mat.node_tree.links.new(uvnode.outputs['UV'],tex.inputs['Vector'])
  if 'Wall' in ob.name:bsdf.inputs['Emission Strength'].default_value=20*.06/.225
audit=runpy.run_path(str(ROOT/'scripts/dev/room1_uv2_audit.py'))['audit_uv2_layout'](receivers)
assert audit['positive_area_overlap_count']==audit['out_of_atlas_vertex_count']==audit['uv_degenerate_triangle_count']==0
audit.update({'atlas_size':1024,'rectangles_px':rects,'minimum_chart_gap_px':16,'bake_margin_px':4,'lightmap_density_px_m':120,'continuous_quad_charts':True})
(EXP/'uv2_validation.json').write_text(json.dumps(audit,indent=2))
# Export only the three receivers. The surrounding frozen route is bake context.
bpy.ops.object.select_all(action='DESELECT')
for o in receivers:o.select_set(True)
bpy.context.view_layer.objects.active=receivers[0]
bpy.ops.export_scene.gltf(filepath=str(OUT/'corridor_baked_v2.glb'),export_format='GLB',use_selection=True,export_texcoords=True,export_extras=True)
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/art/cryo_building_room1_route_v3/room1_west_route_v3.glb'))
context=[]
neutral=bpy.data.materials.new('Context_gray_concrete');neutral.diffuse_color=(.22,.26,.27,1)
for ob in set(bpy.data.objects)-before:
 if ob.type!='MESH':continue
 ob.location+=Vector((93.2,38.9,-11.4))
 bpy.context.view_layer.update()
 pts=[ob.matrix_world@Vector(p) for p in ob.bound_box]
 if max(p.z for p in pts)<-.11 or min(p.z for p in pts)>3.41 or max(p.x for p in pts)<3 or min(p.x for p in pts)>14 or max(p.y for p in pts)<8 or min(p.y for p in pts)>16:
  ob.hide_render=True;continue
 ob.data.materials.clear();ob.data.materials.append(neutral);context.append(ob)
def plane(name,verts):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[(0,1,2,3)]);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(neutral);context.append(ob)
plane('Context_cutaway_ceiling',[(3,9.5,3.4),(3,11.9,3.4),(14,11.9,3.4),(14,9.5,3.4)])
for a,b in [(3,9.8),(11.2,14)]:plane('Context_Room1_opaque_backing',[(a,9.5,0),(b,9.5,0),(b,9.5,3.4),(a,9.5,3.4)])
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=4096;scene.cycles.use_adaptive_sampling=False
scene.cycles.max_bounces=4;scene.cycles.diffuse_bounces=3
scene.world=bpy.data.worlds.new('Corridor_unlit_world');scene.world.color=(0,0,0)
device='CPU'
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
 for dev in prefs.devices:dev.use=dev.type=='CUDA'
 if any(d.type=='CUDA' for d in prefs.devices):scene.cycles.device='GPU';device='CUDA'
except Exception:scene.cycles.device='CPU'
image=bpy.data.images.new('Corridor_v2_linear_irradiance',width=1024,height=1024,alpha=False,float_buffer=True);image.colorspace_settings.name='Non-Color'
for mat in {m for o in receivers for m in o.data.materials}:
 node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image;mat.node_tree.nodes.active=node
bpy.ops.object.select_all(action='DESELECT')
for o in receivers:o.select_set(True)
bpy.context.view_layer.objects.active=receivers[0]
copies=[]
bpy.ops.object.select_all(action='DESELECT')
for original in receivers:
 copy=original.copy();copy.data=original.data.copy();bpy.context.collection.objects.link(copy);copy.select_set(True);original.hide_render=True;copies.append(copy)
bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();joined=bpy.context.object
scene.render.bake.use_pass_color=False;scene.render.bake.use_pass_direct=True;scene.render.bake.use_pass_indirect=True
print('CORRIDOR_BAKE_BEGIN',scene.cycles.samples,'samples',device,flush=True);start=time.monotonic()
bpy.ops.object.bake(type='DIFFUSE',pass_filter={'DIRECT','INDIRECT'},uv_layer='LightmapUV',use_clear=True,margin=4)
seconds=time.monotonic()-start
bpy.data.objects.remove(joined,do_unlink=True)
for original in receivers:original.hide_render=False
image.filepath_raw=str(OUT/'strip_irradiance.exr');image.file_format='OPEN_EXR';image.save()
# Restore UV0 render sampling in source after bake.
for ob in receivers:
 ob.data.uv_layers.active_index=0;ob.data.uv_layers['UVMap'].active_render=True
bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(EXP/'cryo_corridor_baked_v2.blend'),compress=True)
# Native compositor denoise, linear HDR only. Original color maps stay untouched.
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=16;scene.render.resolution_y=16;scene.render.resolution_percentage=100
group=bpy.data.node_groups.new('Corridor_linear_denoise','CompositorNodeTree');scene.compositing_node_group=group
source=group.nodes.new('CompositorNodeImage');source.image=image
denoise=group.nodes.new('CompositorNodeDenoise');group.links.new(source.outputs['Image'],denoise.inputs['Image'])
output=group.nodes.new('CompositorNodeOutputFile');output.directory=str(OUT);output.file_name='strip_irradiance_denoised';output.file_output_items.new('RGBA','Irradiance')
output.format.media_type='IMAGE';output.format.file_format='OPEN_EXR';output.format.color_mode='RGB';output.format.color_depth='32';output.format.exr_codec='ZIP';output.save_as_render=False
group.links.new(denoise.outputs['Image'],output.inputs[0]);bpy.ops.render.render()
(OUT/'strip_irradiance_denoisedIrradiance.exr').replace(OUT/'strip_irradiance_denoised.exr')
manifest={'samples':scene.cycles.samples,'device':device,'seconds':seconds,'receivers':3,'context_meshes':len(context),'atlas':1024,'pass':'DIFFUSE DIRECT+INDIRECT, COLOR off','ribbon_strength':20*.06/.225,'bounces':4,'world_illumination':0,'runtime_realtime_lights':0,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.suffix in ['.glb','.exr']}}
(OUT/'bake_manifest.json').write_text(json.dumps(manifest,indent=2));print('CORRIDOR_BAKE_COMPLETE',seconds,flush=True)
