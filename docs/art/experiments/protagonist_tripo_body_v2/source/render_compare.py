"""Render original and locally repaired body with identical technical cameras."""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector
EXP=Path(__file__).resolve().parents[1]
BASE=EXP.parent/'protagonist_tripo_body_v1/model/protagonist_tripo_body_v1_raw.obj'
MODEL=EXP/'model/protagonist_body_v2.blend'
bpy.ops.wm.open_mainfile(filepath=str(MODEL))
after=[o for o in bpy.context.scene.objects if o.type=='MESH']
for ob in list(bpy.data.objects):
 if ob.type!='MESH':bpy.data.objects.remove(ob,do_unlink=True)
before_set=set(bpy.data.objects)
bpy.ops.wm.obj_import(filepath=str(BASE))
before=[o for o in bpy.data.objects if o not in before_set and o.type=='MESH']
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.62,.65,.65)
scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('Review background');scene.world.color=(.045,.055,.06)
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=False
out=EXP/'evidence';out.mkdir(exist_ok=True)
shots=[('front',(1,0,0),(0,0,.5),2.18),('side',(0,-1,0),(0,0,.5),2.18),('back',(-1,0,0),(0,0,.5),2.18),('quarter',(.8,-1,.25),(0,0,.5),2.18),('feet',(1,-.1,.65),(.025,0,.025),.25),('foot_side',(.1,-1,.25),(.02,-.05,.025),.18)]
records=[]
for name,direction,target,scale in shots:
 data=bpy.data.cameras.new('Review_'+name);cam=bpy.data.objects.new(data.name,data);scene.collection.objects.link(cam)
 target=Vector(target);cam.location=target+Vector(direction).normalized()*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale;scene.camera=cam
 for label,visible in [('before',before),('after',after)]:
  for ob in before+after:ob.hide_render=ob not in visible
  scene.render.filepath=str(out/f'{name}_{label}.png');bpy.ops.render.render(write_still=True)
 records.append({'view':name,'matrix':[list(row) for row in cam.matrix_world],'orthographic_scale':scale,'resolution':[1280,720]})
(EXP/'source/capture_record.json').write_text(json.dumps({'baseline_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),'model_sha256':hashlib.sha256(MODEL.read_bytes()).hexdigest(),'shots':records,'scope':'Actual Blender workbench renders. No model or camera was saved by this renderer.'},indent=2),encoding='utf-8')
print('STATIC_COMPARISON_SAVED')
