"""Read actual near-floor pod geometry; do not modify the Blender source."""
import bpy,json
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parents[3]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'docs/art/experiments/room1_surface_lighting_r7/room1_surface_lighting_r7_packed.blend'))
mapping=json.loads((ROOT/'assets/art/room1_surface_lighting_r7/mesh_mapping.json').read_text())
def hull(points):
    pts=sorted(set(points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    low=[];high=[]
    for p in pts:
        while len(low)>1 and cross(low[-2],low[-1],p)<=0:low.pop()
        low.append(p)
    for p in reversed(pts):
        while len(high)>1 and cross(high[-2],high[-1],p)<=0:high.pop()
        high.append(p)
    return low[:-1]+high[:-1]
records=[]
for i in range(1,21):
    name=f'P{i:02}';points=[];parts=[]
    for obj_name,record in mapping.items():
        if record['group']!=name:continue
        obj=bpy.data.objects.get(obj_name)
        if obj is None:continue
        verts=[obj.matrix_world@v.co for v in obj.data.vertices]
        near=[v for v in verts if -.002<=v.z<=.035]
        if near:parts.append(obj_name)
        points += [(round(v.x,6),round(-v.y,6)) for v in near]
    assert len(points)>=4,name
    poly=hull(points);assert len(poly)>=4
    records.append({'pod':name,'ground_vertex_height_m':[-.002,.035],'parts':parts,'hull_godot_xz':poly,'pixel_polygon':[[round((x-.2)*80),round((z+9.3)*80)] for x,z in poly]})
(HERE/'source/pod_footprints.json').write_text(json.dumps({'source':'room1_surface_lighting_r7_packed.blend','mapping':'assets/art/room1_surface_lighting_r7/mesh_mapping.json','method':'Convex outline of actual pod vertices within 3.5cm above floor; no model edits.','pods':records},indent=2),encoding='utf-8')
print('FLOOR_R8_FOOTPRINTS',len(records),records[0]['hull_godot_xz'])
