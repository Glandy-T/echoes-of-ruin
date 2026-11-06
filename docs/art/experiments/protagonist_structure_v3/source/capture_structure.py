"""Gray technical evidence of real interior surfaces, openings and leg attachments."""
from pathlib import Path
import bpy,json,hashlib
from mathutils import Vector
EXP=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(EXP/'model/protagonist_structure_v3.blend'))
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO'
scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.62,.65,.65)
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
before=bpy.data.collections['BEFORE_V2'];after=bpy.data.collections['AFTER_V3'];before.hide_render=True
for o in list(before.all_objects):o.hide_render=True
after.hide_render=False
for o in list(after.all_objects):o.hide_render=False
robe=bpy.data.objects['Robe_Outer_Inner_Rims'];body=bpy.data.objects['Body_Base_Separate_From_Clothes']
for o in list(after.all_objects):
    if o not in (robe,body):o.hide_render=True
camera=bpy.data.cameras.new('_TECH_only');obj=bpy.data.objects.new('_TECH_only',camera);scene.collection.objects.link(obj);camera.type='ORTHO';scene.camera=obj
report=json.loads((EXP/'source/build_report.json').read_text(encoding='utf-8'));shots=[]
def shot(name,pos,target,scale):
    obj.location=Vector(pos);obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler();camera.ortho_scale=scale
    path=EXP/'evidence'/name;scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    shots.append({'file':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'camera_matrix':[list(row) for row in obj.matrix_world],'scope':'Technical camera, not saved in model or game.'})
shot('structure_underhem_after.png',(-.10,-.30,-.12),(-.015,0,.165),.38)
body.hide_render=True
shot('structure_inner_cloth_after.png',(-.08,-.23,-.08),(-.015,0,.20),.36)
body.hide_render=False
for i,loop in enumerate(x for x in report['cloth_opening_rings_before_inner_shell'] if x['vertices']==10):
    target=robe.matrix_world@Vector(loop['center_local']);sign=1 if target.y>0 else -1
    shot(f'structure_cuff_{i}_after.png',target+Vector((.12,sign*.17,-.10)),target,.16)
target=robe.matrix_world@Vector(next(x['center_local'] for x in report['cloth_opening_rings_before_inner_shell'] if x['vertices']==18))
shot('structure_collar_after.png',target+Vector((.15,-.12,.12)),target,.18)
(EXP/'source/structure_capture_record.json').write_text(json.dumps(shots,indent=2),encoding='utf-8')
print('STRUCTURE_TECHNICAL_VIEWS',len(shots),'NO_MODEL_SAVE')
