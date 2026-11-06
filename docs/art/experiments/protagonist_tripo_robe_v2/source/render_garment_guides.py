"""Project-owned gray 3D garment guides, without any human or reference-author imagery."""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector
EXP=Path(__file__).resolve().parent.parent
BASE=EXP.parent/'protagonist_structure_v3/model/protagonist_structure_v3.blend'
bpy.ops.wm.open_mainfile(filepath=str(BASE));scene=bpy.context.scene
robe=bpy.data.objects['Robe_Outer_Inner_Rims']
for coll in bpy.data.collections:coll.hide_render=False;coll.hide_viewport=False
for obj in list(bpy.data.objects):
    if obj.type=='MESH':obj.hide_render=obj!=robe;obj.hide_set(obj!=robe)
bpy.context.view_layer.update()
points=[robe.matrix_world@v.co for v in robe.data.vertices]
lo=Vector(tuple(min(p[k] for p in points) for k in range(3)));hi=Vector(tuple(max(p[k] for p in points) for k in range(3)));target=(lo+hi)/2;span=hi-lo
camdata=bpy.data.cameras.new('_GUIDE_');cam=bpy.data.objects.new('_GUIDE_',camdata);scene.collection.objects.link(cam);camdata.type='ORTHO';camdata.ortho_scale=max(span)*1.15;scene.camera=cam
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.65,.67,.66);scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=False
scene.render.film_transparent=True;scene.render.resolution_x=1024;scene.render.resolution_y=1024;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
files=[]
for view,direction in (('front',Vector((1,0,0))),('back',Vector((-1,0,0)))):
    cam.location=target+direction*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();path=EXP/'source'/('guide_'+view+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    files.append({'view':view,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'camera_world_matrix':[list(row) for row in cam.matrix_world]})
(EXP/'source/guide_provenance.json').write_text(json.dumps({'source_model':str(BASE),'source_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),'included_object':robe.name,'excluded':'All body, hands, feet, hair and other details; no PixelCanals imagery.','meaning':'Own gray model rendering for 3D silhouette guidance only; source v3 is not a final topology/UV asset.','guides':files},ensure_ascii=False,indent=2),encoding='utf-8')
print('OWN_GARMENT_GUIDES_SAVED')
