"""Original-project gray orthographic guides of the accepted robe silhouette.

This renders the immutable accepted Tripo v2 shape. It never uses the rejected
script cage or any Pixel Canals content, and does not save the source blend.
"""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector
EXP=Path(__file__).resolve().parents[1]
BASE=EXP.parent/'protagonist_tripo_robe_v2/model/protagonist_robe_v2_inspection.blend'
before=hashlib.sha256(BASE.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(BASE));scene=bpy.context.scene
meshes=[o for o in scene.objects if o.type=='MESH'];assert len(meshes)==1
robe=meshes[0]
for o in list(bpy.data.objects):
 if o.type=='MESH':o.hide_render=o!=robe;o.hide_set(o!=robe)
points=[robe.matrix_world@v.co for v in robe.data.vertices];lo=Vector(tuple(min(p[k] for p in points) for k in range(3)));hi=Vector(tuple(max(p[k] for p in points) for k in range(3)));target=(lo+hi)/2
data=bpy.data.cameras.new('Original_Robe_Guide');camera=bpy.data.objects.new(data.name,data);scene.collection.objects.link(camera);data.type='ORTHO';data.ortho_scale=max(hi-lo)*1.15;scene.camera=camera
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.65,.67,.66);scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=False;scene.display.shading.show_specular_highlight=False;scene.render.film_transparent=True
scene.render.resolution_x=1024;scene.render.resolution_y=1024;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
rows=[]
for view,direction in [('front',(1,0,0)),('left',(0,1,0)),('right',(0,-1,0)),('back',(-1,0,0))]:
 camera.location=target+Vector(direction)*3;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();p=EXP/'source'/('guide_'+view+'.png');scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 rows.append({'view':view,'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'camera_world_matrix':[list(row) for row in camera.matrix_world]})
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==before
(EXP/'source/input_provenance.json').write_text(json.dumps({'original_model':str(BASE),'unchanged_sha256':before,'included_mesh':robe.name,'views':rows,'content':'Project-owned accepted robe silhouette only; no body, no Pixel Canals/NoAI material, no rejected cage.','limits':'Views constrain design/pose visually. They do not condition on body skeleton or guarantee single-layer/animation-ready topology.'},ensure_ascii=False,indent=2),encoding='utf-8')
print('ORIGINAL_ROBE_FOUR_GUIDES_SAVED')
