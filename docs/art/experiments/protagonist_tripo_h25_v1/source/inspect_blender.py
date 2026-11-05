"""Inspect a legitimately downloaded GLB; keep original geometry and materials intact."""
from pathlib import Path
import bpy, math, json, hashlib
from mathutils import Vector

EXP=Path(__file__).resolve().parents[1]
files=list((EXP/'model').glob('*.glb'))
if len(files)!=1:
 raise RuntimeError(f'Expected exactly one downloaded GLB, found {len(files)}; do not generate a substitute')
raw=files[0]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(raw))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
if not meshes:raise RuntimeError('GLB imported without meshes')
points=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
minimum=Vector([min(v[a] for v in points) for a in range(3)])
maximum=Vector([max(v[a] for v in points) for a in range(3)])
center=(minimum+maximum)/2
span=maximum-minimum
def audit(o):
 m=o.data;m.calc_loop_triangles()
 parent=list(range(len(m.vertices)))
 def find(a):
  while a!=parent[a]:parent[a]=parent[parent[a]];a=parent[a]
  return a
 for e in m.edges:
  a,b=map(find,e.vertices)
  if a!=b:parent[b]=a
 groups={}
 for v in m.vertices:groups[find(v.index)]=groups.get(find(v.index),0)+1
 uses=[0]*len(m.edges)
 lookup={tuple(sorted(e.vertices)):e.index for e in m.edges}
 for p in m.polygons:
  for a,b in p.edge_keys:uses[lookup[tuple(sorted((a,b)))]]+=1
 uv=[]
 for layer in m.uv_layers:
  coords=[tuple(x.uv) for x in layer.data]
  uv.append({'name':layer.name,'loops':len(coords),'outside_0_1':sum(any(c< -1e-5 or c>1.00001 for c in p) for p in coords)})
 return {'object':o.name,'vertices':len(m.vertices),'edges':len(m.edges),'polygons':len(m.polygons),'triangles':len(m.loop_triangles),'triangle_faces':sum(len(p.vertices)==3 for p in m.polygons),'quad_faces':sum(len(p.vertices)==4 for p in m.polygons),'connected_components':len(groups),'component_vertex_counts':sorted(groups.values(),reverse=True),'boundary_edges':sum(x==1 for x in uses),'loose_edges':sum(x==0 for x in uses),'edges_with_more_than_2_faces':sum(x>2 for x in uses),'zero_area_faces':sum(p.area<1e-12 for p in m.polygons),'UV_layers':uv,'materials':[s.material.name if s.material else None for s in o.material_slots],'vertex_groups':len(o.vertex_groups),'shape_keys':list(m.shape_keys.key_blocks.keys()) if m.shape_keys else [],'armature_modifiers':[a.name for a in o.modifiers if a.type=='ARMATURE']}
report={'raw_file':raw.name,'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'blender_version':bpy.app.version_string,'mesh_objects':len(meshes),'armatures':sum(o.type=='ARMATURE' for o in bpy.context.scene.objects),'image_datablocks':len(bpy.data.images),'bounds_in_imported_units':{'min':list(minimum),'max':list(maximum),'dimensions':list(span)},'scale_status':'Raw GLB scale retained. Physical character height not approved.','meshes':[audit(o) for o in meshes],'limits':['Connected components do not establish semantic body/gown/hair separation.','UV layer presence is not UV overlap or painting-readiness validation.','No rigging, animation or Godot validation.','No cleanup, decimation, UV unwrap, new textures or silhouette edits performed.']}
(EXP/'source/mesh_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE'
scene.display.shading.single_color=(0.62,0.65,0.65)
scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('Review Background')
scene.world.color=(0.045,0.055,0.06)
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.display.shading.show_specular_highlight=False
qa=bpy.data.collections.new('QA_CAMERAS_ONLY');scene.collection.children.link(qa)
height=max(span.z,0.01);distance=max(span)*4
for name,direction in [('front',(0,-1,0)),('side',(1,0,0)),('back',(0,1,0)),('quarter',(0.8,-1,0.25))]:
 data=bpy.data.cameras.new('QA_'+name);cam=bpy.data.objects.new('QA_'+name,data);qa.objects.link(cam)
 cam.location=center+Vector(direction).normalized()*distance
 cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
 data.type='ORTHO';data.ortho_scale=height*1.22*(scene.render.resolution_x/scene.render.resolution_y);data.clip_end=distance*10
 scene.camera=cam;scene.render.filepath=str(EXP/'evidence'/f'blender_{name}.png')
 bpy.ops.render.render(write_still=True)
scene.camera=bpy.data.objects['QA_quarter']
for o in bpy.context.selected_objects:o.select_set(False)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   space=area.spaces.active;space.region_3d.view_location=center
   space.region_3d.view_rotation=scene.camera.rotation_euler.to_quaternion()
   space.region_3d.view_distance=height*1.6;space.region_3d.view_perspective='ORTHO'
   space.overlay.show_floor=False;space.overlay.show_axis_x=False;space.overlay.show_axis_y=False
   space.shading.type='SOLID';space.shading.color_type='SINGLE';space.shading.single_color=(0.62,0.65,0.65)
bpy.ops.wm.save_as_mainfile(filepath=str(EXP/'model/protagonist_h25_inspection.blend'))
print('H25_IMPORTED_AUDITED_RENDERED;mesh_geometry_and_materials_unchanged')
