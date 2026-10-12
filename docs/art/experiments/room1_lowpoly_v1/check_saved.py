"""Read back the saved sample. Static checks only; no scene save or mutation."""
import bpy
import json
import math
import struct
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'room1_lowpoly_sample_v1.blend'))
scene=bpy.context.scene
results=[]
def check(name, condition, details=None):
    results.append({'check':name,'pass':bool(condition),'details':details})
pods=[o for o in scene.objects if o.get('engineering_pod_id')=='P11']
points=[o.matrix_world @ Vector(c) for o in pods for c in o.bound_box]
low=[min(p[i] for p in points) for i in range(3)]
high=[max(p[i] for p in points) for i in range(3)]
dims=[high[i]-low[i] for i in range(3)]
check('P11 world origin and union size', all(abs(a-b)<1e-5 for a,b in zip(low,[1.25,6.5,0])) and all(abs(a-b)<1e-5 for a,b in zip(dims,[1.05,2.3,1])), {'min_m':low,'dimensions_m':dims})
meshes=[o for o in scene.objects if o.type=='MESH']
check('local scope: 3 shell, 4 pod layers, 1 scale marker', len(meshes)==8 and len(pods)==4)
check('all meshes have finite UV coordinates', all(o.data.uv_layers.active and all(math.isfinite(v) for loop in o.data.uv_layers.active.data for v in loop.uv) for o in meshes))
body=bpy.data.objects['P11_Body_inherited']
check('body label occupies one long side material slot',len(body.data.materials)==2 and sum(p.material_index==1 for p in body.data.polygons)==1)
nodes=[n for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE']
check('all 4 image textures use Closest, are packed and have portable paths', len(nodes)==4 and all(n.interpolation=='Closest' and n.image.packed_file and n.image.filepath.replace('\\','/').startswith('//textures/') for n in nodes), [{'image':n.image.name,'path':n.image.filepath,'packed':bool(n.image.packed_file),'sampling':n.interpolation} for n in nodes])
check('review camera restored, clay override cleared, marker restored', scene.camera.name=='Camera_A_local_near_side_candidate' and scene.view_layers[0].material_override is None and not bpy.data.objects['Scale_column_1p68m_NOT_CHARACTER'].hide_render)
for filename in ['A_target_camera.png','B_geometry_without_textures.png','C_pixel_texture_close.png']:
    data=(ROOT/'evidence'/filename).read_bytes()
    size=struct.unpack('>II',data[16:24])
    check(filename+' actual PNG size',data[:8]==b'\x89PNG\r\n\x1a\n' and size==(1600,1000),list(size))
report={'status':'PASS_STATIC' if all(r['pass'] for r in results) else 'FAIL_STATIC', 'blender_version':bpy.app.version_string,'checks':results,'not_validated':['final art acceptance','interactive boarding or turning','Godot runtime','global pixel grid or temporal stability']}
(ROOT/'self_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if report['status']!='PASS_STATIC':
    raise RuntimeError('Saved-file static validation failed')
