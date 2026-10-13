"""Read back the saved native review to check persistence of the master asset."""
import bpy
import json
from pathlib import Path

root = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root / 'body_165cm_review_v2.blend'), use_scripts=False)
master = bpy.data.scenes['01_BODY_MASTER_165cm']
bpy.context.window.scene = master
body = master.objects['Body_165cm_CC0_pistachio']
rig = master.objects['Body_Rig_original']
dg = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(dg)
mesh = evaluated.to_mesh()
zs = [(evaluated.matrix_world @ v.co).z for v in mesh.vertices]
mesh.calc_loop_triangles()
result = {'reopen_passed': True, 'height_m': max(zs)-min(zs), 'foot_z_m': min(zs),
          'preview_triangles': len(mesh.loop_triangles), 'bones': len(rig.data.bones),
          'base_vertices': len(body.data.vertices), 'uv_layers': list(body.data.uv_layers.keys()),
          'shape_keys': {k.name:k.value for k in body.data.shape_keys.key_blocks},
          'armature_target': next(m.object.name for m in body.modifiers if m.type == 'ARMATURE')}
evaluated.to_mesh_clear()
assert abs(result['height_m'] - 1.65) < 1e-5
assert abs(result['foot_z_m']) < 1e-5
assert result['preview_triangles'] == 4636
assert result['bones'] == 59 and result['base_vertices'] == 581
assert result['armature_target'] == rig.name and result['uv_layers'] == ['UVMap']
(root / 'evidence/saved_file_validation.json').write_text(json.dumps(result, indent=2), encoding='utf8')
print(json.dumps(result))
