"""Blender readback: rigid-lid assembly and envelope checks, no scene save."""
import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'room1_pod_whole_lid_motion_v1.blend'))
scene=bpy.context.scene
lid=bpy.data.objects['ONE_RIGID_LID_with_head_window']
body=bpy.data.objects['Original_continuous_shell']
controller=bpy.data.objects['LID_MOTION_RIG_whole_cover']
results=[]
def check(name,condition,value=None):
    results.append({'check':name,'pass':bool(condition),'value':value})
scene.frame_set(1)
bpy.context.view_layer.update()
pts=[o.matrix_world@v.co for o in (lid,body) for v in o.data.vertices]
dims=[max(p[i] for p in pts)-min(p[i] for p in pts) for i in range(3)]
check('closed external size matches 1.05 x 2.30 x 1.00 m',all(abs(a-b)<1e-5 for a,b in zip(dims,[1.05,2.30,1.0])),dims)
bm=bmesh.new()
bm.from_mesh(lid.data)
unseen=set(bm.verts)
components=0
while unseen:
    components+=1
    stack=[unseen.pop()]
    while stack:
        v=stack.pop()
        for edge in v.link_edges:
            other=edge.other_vert(v)
            if other in unseen:
                unseen.remove(other)
                stack.append(other)
check('lid is one connected closed mesh',components==1 and all(e.is_manifold for e in bm.edges),{'connected_components':components,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)})
bm.free()
check('head-window material belongs to same rigid lid',lid.parent==controller and len(lid.data.materials)==2 and any(p.material_index==1 for p in lid.data.polygons))
scene.frame_set(30)
check('lift-first stage is 0.12m with no lateral movement or roll',abs(controller.location.z-.65)<1e-5 and abs(controller.location.x)<1e-5 and abs(controller.rotation_euler.y)<1e-5)
scene.frame_set(90)
check('stowed stage is whole rigid cover rotated down one side',abs(controller.rotation_euler.y-math.pi/2)<1e-5 and abs(controller.location.x-.32)<1e-5)
metrics=json.loads((ROOT/'motion_measurements.json').read_text(encoding='utf-8'))
check('180 sampled states have no body/bed surface intersections',metrics['sample_count']==180 and not metrics['surface_intersection_frames'])
check('sweep remains clear of floor and next closed pod boundary',metrics['minimum_ground_clearance_m']>0 and metrics['maximum_swept_x_m']<1.225)
report={'status':'PASS_FILE_AND_SAMPLED_GEOMETRY' if all(r['pass'] for r in results) else 'FAIL',
        'blender_version':bpy.app.version_string,'checks':results,
        'not_proven':['production mechanism','person boarding/turning','adjacent simultaneous opening','final silhouette approval']}
(ROOT/'saved_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if report['status']=='FAIL':
    raise RuntimeError('Readback validation failed')
