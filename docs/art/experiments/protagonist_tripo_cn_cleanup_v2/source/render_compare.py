"""Render visibility-only comparisons from a preserved before/after cleanup file."""
from pathlib import Path
import bpy,json,hashlib
EXP=Path(__file__).resolve().parent.parent
BLEND=EXP/'model/protagonist_cn_cleanup_v2.blend'
if not BLEND.is_file():raise RuntimeError('Repair file not ready; no substitute generated')
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.display.shading.color_type='SINGLE'
scene.display.shading.single_color=(0.62,0.65,0.65)
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
before=bpy.data.collections.get('BEFORE_V1')
after=bpy.data.collections.get('AFTER_V2')
if not before or not after:raise RuntimeError('Missing declared original/candidate collections')
(EXP/'evidence').mkdir(exist_ok=True)
records=[]
for state in ('before','after'):
    for group,enabled in ((before,state=='before'),(after,state=='after')):
        group.hide_render=not enabled
        group.hide_viewport=not enabled
        for obj in group.all_objects:
            obj.hide_render=not enabled
            obj.hide_set(not enabled)
    for view in ('front','side','back','quarter','head_back'):
        camera=bpy.data.objects.get('QA_'+view)
        if camera is None:raise RuntimeError('Missing fixed QA camera '+view)
        scene.camera=camera
        path=EXP/'evidence'/f'{state}_{view}.png'
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        records.append({'state':state,'view':view,'file':path.name,'camera_world_matrix':[list(row) for row in camera.matrix_world],'resolution':[1280,720],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(EXP/'source/capture_record.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
print('REPAIR_COMPARE_RENDERED_SAME_CAMERAS_NO_MODEL_EDITS')
