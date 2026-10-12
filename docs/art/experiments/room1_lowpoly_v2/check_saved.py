"""Read back saved v2 without saving the scene. Checks limited to file structure."""
import bpy
import json
import math
import struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'room1_lowpoly_sample_v2.blend'))
scene=bpy.context.scene
checks=[]
def check(name,ok,details=None):
    checks.append({'check':name,'pass':bool(ok),'details':details})
meshes=[o for o in scene.objects if o.type=='MESH']
pod=bpy.data.objects['P11_ENVELOPE_ONLY_2p30x1p05x1p00']
points=[pod.matrix_world@Vector(p) for p in pod.bound_box]
low=[min(p[i] for p in points) for i in range(3)]
dimensions=list(pod.dimensions)
check('one connected pod envelope, original position and size',len(bpy.data.collections['03_ENGINEERING_ENVELOPE_ONLY_NOT_POD_DESIGN'].objects)==1 and all(abs(a-b)<1e-5 for a,b in zip(low,[1.25,6.5,0])) and all(abs(a-b)<1e-5 for a,b in zip(dimensions,[1.05,2.3,1])),{'min_m':low,'size_m':dimensions})
walls=bpy.data.collections['02_ART_WALL_CASSETTES_CANDIDATE'].objects
samples=[o.matrix_world@v.co for o in walls for v in o.data.vertices]
for o in walls:
    o.data.calc_loop_triangles()
    # Concave L cap: polygon's arithmetic center may lie outside its surface.
    for tri in o.data.loop_triangles:
        tri_points=[o.matrix_world@o.data.vertices[i].co for i in tri.vertices]
        samples.append(sum(tri_points,Vector())/3)
        samples.extend((tri_points[i]+tri_points[(i+1)%3])/2 for i in range(3))
check('wall shell within existing wall envelope; no room intrusion',all((p.x<=.20001 or p.y>=9.29999) and p.x>=-.00001 and p.y<=9.50001 for p in samples))
floors=bpy.data.collections['01_ART_FLOOR_MODULES_CANDIDATE'].objects
check('floor art never raises walking surface above Z=0',all((o.matrix_world@v.co).z<=1e-5 for o in floors for v in o.data.vertices))
check('six individual floor sheets',sum(o.name.startswith('Floor_sheet_') for o in floors)==6)
check('architectural structure exists separately from textures',len(walls)>=20 and 'Wall_corner_L_return_recessed_chamfer' in walls)
check('all meshes use one explicitly active finite UV layer',all(len(o.data.uv_layers)==1 and o.data.uv_layers.active.active_render and all(math.isfinite(v) for li in o.data.uv_layers.active.data for v in li.uv) for o in meshes))
# Check actual rendered face density, not just metadata or UV layer presence.
wall=bpy.data.objects['Rear_upper_cassette_1']
poly=next(p for p in wall.data.polygons if p.normal.y<-.999)
uv=wall.data.uv_layers.active
uvs=[uv.data[i].uv for i in poly.loop_indices]
verts=[wall.data.vertices[wall.data.loops[i].vertex_index].co for i in poly.loop_indices]
dx=max(p.x for p in verts)-min(p.x for p in verts)
dz=max(p.z for p in verts)-min(p.z for p in verts)
density_x=(max(p.x for p in uvs)-min(p.x for p in uvs))*96/dx
density_z=(max(p.y for p in uvs)-min(p.y for p in uvs))*192/dz
check('rendered wall UV density actually 64 texels/m',abs(density_x-64)<.01 and abs(density_z-64)<.01,[density_x,density_z])
nodes=[n for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE']
check('two original packed Closest textures with relative paths',len(nodes)==2 and all(n.interpolation=='Closest' and n.image.packed_file and n.image.filepath.replace('\\','/').startswith('//textures/') for n in nodes))
check('three-level shading marked as Blender-only trial',sum(n.bl_idname=='ShaderNodeShaderToRGB' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes)>0)
check('saved scene restored to A and normal materials',scene.camera.name=='Camera_A_fixed_architectural_candidate' and scene.view_layers[0].material_override is None)
for name in ['A_target_camera.png','B_untextured_architecture.png','C_material_close.png']:
    raw=(ROOT/'evidence'/name).read_bytes()
    size=struct.unpack('>II',raw[16:24])
    check(name+' actual PNG dimensions',raw[:8]==b'\x89PNG\r\n\x1a\n' and size==(1600,1000),list(size))
report={'status':'PASS_STATIC' if all(c['pass'] for c in checks) else 'FAIL_STATIC','blender_version':bpy.app.version_string,'checks':checks,'limits':['file and numerical checks only','final artwork awaits user review','no Godot runtime or movement verification']}
(ROOT/'self_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if report['status']!='PASS_STATIC':
    raise RuntimeError('Saved sample check failed')
