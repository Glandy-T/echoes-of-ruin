"""Read-only normal-orientation and interior-UV audit for pod volume v4."""
from pathlib import Path
import json
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
BLEND=ROOT/'room1_pod_volume_v4.blend'
OUT=ROOT/'source'/'geometry_orientation_uv_audit.json'

def triangulated_signed_volume(mesh):
    total=0.0
    for poly in mesh.polygons:
        vs=[mesh.vertices[i].co for i in poly.vertices]
        for i in range(1,len(vs)-1): total += vs[0].dot(vs[i].cross(vs[i+1]))/6.0
    return total

def face_outward_ratio(mesh):
    centroid=sum((v.co for v in mesh.vertices),Vector())/len(mesh.vertices)
    outward=0
    for p in mesh.polygons:
        if p.normal.dot(p.center-centroid)>0: outward+=1
    return outward,len(mesh.polygons),round(outward/len(mesh.polygons),6)

def tri_uv_area(a,b,c): return abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2

def interior_uv_audit(obj):
    uv=obj.data.uv_layers.get('UV_TRIAL_V3_INTERIOR_XY')
    if not uv: return {'error':'missing UV_TRIAL_V3_INTERIOR_XY'}
    stats={'interior_polygons':0,'triangles':0,'uv_degenerate_triangles':0,'near_degenerate_triangles':0,'vertical_interior_polygons':0,'examples':[]}
    for p in obj.data.polygons:
        mat=obj.data.materials[p.material_index]
        if not mat or mat.name!='POD_V4_interior': continue
        stats['interior_polygons']+=1
        vertical=abs(p.normal.z)<.15
        if vertical: stats['vertical_interior_polygons']+=1
        loops=list(p.loop_indices)
        for i in range(1,len(loops)-1):
            a,b,c=(uv.data[loops[j]].uv for j in (0,i,i+1)); area=tri_uv_area(a,b,c); stats['triangles']+=1
            if area<1e-10:
                stats['uv_degenerate_triangles']+=1
                if len(stats['examples'])<12: stats['examples'].append({'polygon':p.index,'normal':[round(x,4) for x in p.normal],'uv_area':area,'vertical':vertical})
            elif area<1e-6: stats['near_degenerate_triangles']+=1
    return stats

def material_face_bounds(obj):
    rows={}
    for p in obj.data.polygons:
        m=obj.data.materials[p.material_index]; key=m.name if m else '<none>'
        entry=rows.setdefault(key,{'faces':0,'min':[1e9]*3,'max':[-1e9]*3,'center_face_examples':[]})
        entry['faces']+=1
        verts=[obj.data.vertices[i].co for i in p.vertices]
        for axis in range(3):
            entry['min'][axis]=min(entry['min'][axis],*(v[axis] for v in verts)); entry['max'][axis]=max(entry['max'][axis],*(v[axis] for v in verts))
        if abs(p.center.x)<.18 and len(entry['center_face_examples'])<8:
            entry['center_face_examples'].append({'index':p.index,'center':[round(v,4) for v in p.center],'normal':[round(v,4) for v in p.normal],'verts':len(p.vertices)})
    for e in rows.values(): e['min']=[round(v,5) for v in e['min']]; e['max']=[round(v,5) for v in e['max']]
    return rows

def selected_face_vertices(obj, indices):
    return {str(index):{'material':obj.data.materials[obj.data.polygons[index].material_index].name,'normal':[round(v,6) for v in obj.data.polygons[index].normal],'vertices_m':[[round(c,6) for c in obj.data.vertices[vi].co] for vi in obj.data.polygons[index].vertices]} for index in indices}

def basin_lip_contact(shell, lip):
    tree=BVHTree.FromPolygons([v.co for v in shell.data.vertices],[p.vertices[:] for p in shell.data.polygons],all_triangles=False)
    distances=[]
    for v in lip.data.vertices:
        hit=tree.find_nearest(v.co)
        distances.append(hit[3] if hit else None)
    return {'vertex_to_fixed_shell_min_m':round(min(d for d in distances if d is not None),6),'vertex_to_fixed_shell_max_m':round(max(d for d in distances if d is not None),6),'all_vertex_distances_m':[round(d,6) if d is not None else None for d in distances]}

def shell_opening_rim(shell):
    # Candidate source vertices at the interior's upper opening height.
    out=[]
    for index,v in enumerate(shell.data.vertices):
        if abs(v.co.z-.345)<1e-5:
            out.append({'index':index,'co':[round(c,6) for c in v.co]})
    return out

def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND)); bpy.context.scene.frame_set(1)
    new={}
    for name in ('pod_v4_window_frame','pod_v4_window_inner_seal','pod_v4_display_housing','pod_v4_lid_inner_backing','pod_v4_basin_seal_lip'):
        mesh=bpy.data.objects[name].data; signed=triangulated_signed_volume(mesh); out,total,ratio=face_outward_ratio(mesh)
        new[name]={'signed_volume_m3':signed,'signed_volume_sign':'outward_positive' if signed>0 else 'inward_negative_or_invalid','face_normal_vs_centroid':{'outward_faces':out,'total_faces':total,'ratio':ratio}}
    cover=bpy.data.objects['ONE_PIECE_COVER_head_window']; shell=bpy.data.objects['Reference_led_fixed_shell']
    result={'new_mesh_orientation':new,'existing_interior_xy_uv':{name:interior_uv_audit(bpy.data.objects[name]) for name in ('ONE_PIECE_COVER_head_window','Reference_led_fixed_shell')},'material_local_bounds':{name:material_face_bounds(bpy.data.objects[name]) for name in ('ONE_PIECE_COVER_head_window','Reference_led_fixed_shell')},'selected_source_faces':{'cover_inner_center':selected_face_vertices(cover,[117]),'shell_end_samples':selected_face_vertices(shell,[4,8,12,16,20,24,28,32])},'shell_opening_rim_vertices_z345':shell_opening_rim(shell),'basin_lip_contact':basin_lip_contact(shell,bpy.data.objects['pod_v4_basin_seal_lip']),'scope':'Read-only audit; no mesh or UV mutation.'}
    OUT.write_text(json.dumps(result,indent=2),encoding='utf8'); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
