"""Actual UV-linked checker and independent body/garment technical views."""
from pathlib import Path
import bpy,json,hashlib
EXP=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(EXP/'model/protagonist_structure_v3.blend'))
scene=bpy.context.scene;before=bpy.data.collections['BEFORE_V2'];after=bpy.data.collections['AFTER_V3'];parts=list(after.all_objects)
before.hide_render=True
for o in list(before.all_objects):o.hide_render=True
after.hide_render=False
for o in parts:o.hide_render=False
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
records=[]
def shot(name,camera):
    scene.camera=bpy.data.objects[camera];path=EXP/'evidence'/name;scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    records.append({'file':name,'camera':camera,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'resolution':[1280,720]})
mat=bpy.data.materials.new('_TECH_UV_CHECKER_ONLY');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();links=mat.node_tree.links
uv=n.new('ShaderNodeUVMap');uv.uv_map='UV_Trial';check=n.new('ShaderNodeTexChecker');check.inputs['Scale'].default_value=16
check.inputs['Color1'].default_value=(.65,.65,.65,1);check.inputs['Color2'].default_value=(.12,.12,.12,1)
em=n.new('ShaderNodeEmission');out=n.new('ShaderNodeOutputMaterial');links.new(uv.outputs['UV'],check.inputs['Vector']);links.new(check.outputs['Color'],em.inputs['Color']);links.new(em.outputs[0],out.inputs['Surface'])
slots={o:list(o.data.materials) for o in parts}
for o in parts:o.data.materials.clear();o.data.materials.append(mat)
scene.render.engine='BLENDER_EEVEE'
for view in ('front','back','quarter'):shot('structure_uv_checker_'+view+'.png','QA_'+view)
for o,mats in slots.items():
    o.data.materials.clear()
    for m in mats:o.data.materials.append(m)
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.62,.65,.65)
for o in parts:o.hide_render=o.name not in ('Body_Base_Separate_From_Clothes','Hair_Main')
shot('body_base_separate_front.png','QA_front');shot('body_base_separate_side.png','QA_side')
for o in parts:o.hide_render=o.name!='Robe_Outer_Inner_Rims'
shot('robe_separate_front.png','QA_front');shot('robe_separate_back.png','QA_back')
(EXP/'source/uv_capture_record.json').write_text(json.dumps({'captures':records,'checker_vector_source':'ShaderNodeUVMap(UV_Trial) -> ShaderNodeTexChecker.Vector; NOT generated coordinates.','meaning':'Calibration of each separate part tile only; no final pixel-art or density approval.','model_modified_or_saved':False},indent=2),encoding='utf-8')
print('UV_AND_SEPARATE_PART_VIEWS',len(records),'NO_MODEL_SAVE')
