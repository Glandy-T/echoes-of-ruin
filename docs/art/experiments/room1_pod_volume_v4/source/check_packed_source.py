"""Reopen delivered Blender source and verify its eight active packed maps."""
from pathlib import Path
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'room1_pod_volume_v4.blend'))
rows={}
for key in ['lid','shell_side','shell_end','interior','mattress','glass','display','section']:
    mat=bpy.data.materials['POD_V4_'+key]
    images=[n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE']
    assert len(images)==1 and images[0].packed_file
    data=bytes(images[0].packed_file.data)
    assert hashlib.sha256(data).digest()==hashlib.sha256((ROOT/'textures'/f'{key}.png').read_bytes()).digest()
    rows[key]={'packed':True,'exact_png_bytes':True,'size':list(images[0].size)}
result={'active_material_images':rows,'frame60_rotation_y':None}
bpy.context.scene.frame_set(60)
result['frame60_rotation_y']=round(bpy.data.objects['Whole_lid_motion'].rotation_euler.y,6)
assert abs(result['frame60_rotation_y']-.785398)<.00001
(ROOT/'source/packed_source_readback.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print('PACKED_SOURCE_READBACK_PASS')
