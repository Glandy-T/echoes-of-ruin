"""Same-camera original/reconstructed robe and transparent silhouette masks."""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector
EXP=Path(__file__).resolve().parents[1]
MODEL=EXP/'model/DIAGNOSTIC_static_robe.blend';RAW=EXP.parent/'protagonist_tripo_robe_v2/model/protagonist_tripo_robe_v2_raw.glb'
bpy.ops.wm.open_mainfile(filepath=str(MODEL));after=[o for o in bpy.context.scene.objects if o.type=='MESH']
present=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(RAW));before=[o for o in bpy.data.objects if o not in present and o.type=='MESH'];scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.62,.65,.65);scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('Robe review background');scene.world.color=(.045,.055,.06);scene.display.shading.show_specular_highlight=False
out=EXP/'evidence';out.mkdir(exist_ok=True)
shots=[('front',(1,0,0),(0,0,.5),2.18),('side',(0,-1,0),(0,0,.5),2.18),('back',(-1,0,0),(0,0,.5),2.18),('quarter',(.8,-1,.25),(0,0,.5),2.18),('neck',(.5,-.2,1),(0,0,.94),.55),('cuff',(.4,-1,-.3),(0,-.27,.63),.55),('hem',(.8,-.8,-.6),(0,0,.1),.9)]
records=[]
for name,direction,target,scale in shots:
 cd=bpy.data.cameras.new('Review_'+name);cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=scale;target=Vector(target);cam.location=target+Vector(direction).normalized()*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 for label,visible in [('before',before),('after',after)]:
  for ob in before+after:ob.hide_render=ob not in visible
  scene.render.film_transparent=False;scene.display.shading.light='STUDIO';scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.show_shadows=True;scene.render.filepath=str(out/f'robe_{name}_{label}.png');bpy.ops.render.render(write_still=True)
  if name in ('front','side','back','quarter'):
   scene.render.film_transparent=True;scene.display.shading.light='FLAT';scene.display.shading.show_cavity=False;scene.display.shading.show_shadows=False;scene.render.filepath=str(out/f'mask_{name}_{label}.png');bpy.ops.render.render(write_still=True)
 records.append({'view':name,'resolution':[1280,720],'ortho_scale':scale,'camera_world_matrix':[list(row) for row in cam.matrix_world]})
(EXP/'source/robe_comparison_capture.json').write_text(json.dumps({'raw_sha256':hashlib.sha256(RAW.read_bytes()).hexdigest(),'repaired_blend_sha256':hashlib.sha256(MODEL.read_bytes()).hexdigest(),'shots':records,'scope':'Actual workbench same-camera comparisons and transparent silhouette masks; renderer did not save either model.'},indent=2),encoding='utf-8')
print('ROBE_SAME_CAMERA_COMPARISON_RENDERED')
