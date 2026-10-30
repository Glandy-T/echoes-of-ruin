"""Read current closed-v8 support vertices; write masks only, do not save the model."""
from pathlib import Path
import bpy,json,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'docs/art/experiments/room1_wall_detail_full_r24/room1_wall_detail_full_r24.blend'))
def hull(points):
    pts=sorted(set(points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[];hi=[]
    for p in pts:
        while len(lo)>=2 and cross(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi)>=2 and cross(hi[-2],hi[-1],p)<=0:hi.pop()
        hi.append(p)
    return lo[:-1]+hi[:-1]
old={p['pod']:p for p in json.loads((ROOT/'docs/art/experiments/room1_floor_variants_r15/source/pod_footprints.json').read_text())['pods']}
rows=[]
for obj in sorted(bpy.data.objects,key=lambda o:o.name):
    if not re.fullmatch(r'R19_P\d\d_closed_receiver',obj.name):continue
    pid=obj.name[4:7];vertices=[obj.matrix_world@v.co for v in obj.data.vertices]
    support=[(round(v.x,6),round(-v.y,6)) for v in vertices if -.02<=v.z<=.035]
    assert len(support)>=3,(pid,min(v.z for v in vertices))
    world=hull(support);poly=[(round((x-.2)*80),round((z+9.3)*80)) for x,z in world]
    rows.append({'pod':pid,'object':obj.name,'ground_vertex_height_m':[-.02,.035],'hull_godot_xz':world,'pixel_polygon':poly,'old_v3_polygon':old[pid]['pixel_polygon']})
assert len(rows)==20
report={'source':'room1_wall_detail_full_r24.blend / r19 v8 closed receivers','model_saved':False,'method':'convex hull of actual transformed world vertices within floor support threshold; Blender(x,y,z) to Godot(x,z,-y)','pods':rows}
(HERE/'current_pod_footprints.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('R26_V8_SUPPORT_READ',len(rows),'actual closed-pod support hulls; no model save',flush=True)
