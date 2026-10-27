"""Read-only structural checks for room1_pod_volume_v4.blend."""
from pathlib import Path
import json
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
BLEND=ROOT/'room1_pod_volume_v4.blend'
OUT=ROOT/'source'/'geometry_validation.json'

def bounds(obj):
    pts=[obj.matrix_world@Vector(c) for c in obj.bound_box]
    return {'min_m':[round(min(p[i] for p in pts),6) for i in range(3)],'max_m':[round(max(p[i] for p in pts),6) for i in range(3)]}

def boundary_count(mesh):
    counts={}
    for p in mesh.polygons:
        for e in p.edge_keys: counts[tuple(sorted(e))]=counts.get(tuple(sorted(e)),0)+1
    return sum(v==1 for v in counts.values())

def fitted_backing_inside_cover():
    cover=bpy.data.objects['ONE_PIECE_COVER_head_window']; face=cover.data.polygons[117]; source=[cover.data.vertices[i].co for i in face.vertices]
    panel=bpy.data.objects['pod_v4_lid_inner_backing']; top=[v.co for v in panel.data.vertices[:4]]
    minx,maxx=min(v.x for v in source),max(v.x for v in source); miny,maxy=min(v.y for v in source),max(v.y for v in source)
    normal_offsets=[(top[i]-source[i]).dot(face.normal.normalized()) for i in range(4)]
    return {'source_face':117,'source_xy_bounds_m':[[round(minx,6),round(miny,6)],[round(maxx,6),round(maxy,6)]],'panel_top_xy_bounds_m':[[round(min(v.x for v in top),6),round(min(v.y for v in top),6)],[round(max(v.x for v in top),6),round(max(v.y for v in top),6)]],'all_top_vertices_inside_source_xy':all(minx<=v.x<=maxx and miny<=v.y<=maxy for v in top),'mean_top_vertex_distance_to_source_m':round(sum((source[i]-top[i]).length for i in range(4))/4,6),'normal_offsets_m':[round(v,6) for v in normal_offsets],'top_embedded_opposite_inward_normal_1mm':all(abs(v+.001)<1e-6 for v in normal_offsets)}

def basin_outer_embed():
    shell=bpy.data.objects['Reference_led_fixed_shell']; lip=bpy.data.objects['pod_v4_basin_seal_lip']; tree=BVHTree.FromPolygons([v.co for v in shell.data.vertices],[p.vertices[:] for p in shell.data.polygons],all_triangles=False)
    ds=[tree.find_nearest(v.co)[3] for v in lip.data.vertices[:8]]
    return {'source_rim_vertex_count':8,'outer_edge_to_source_min_m':round(min(ds),6),'outer_edge_to_source_max_m':round(max(ds),6)}

def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    scene=bpy.context.scene; lid=bpy.data.objects['Whole_lid_motion']
    rows={}
    for f in (1,60):
        scene.frame_set(f)
        rows[str(f)]={name:bounds(bpy.data.objects[name]) for name in ('ONE_PIECE_COVER_head_window','pod_v4_window_frame','pod_v4_window_inner_seal','pod_v4_display_housing','pod_v4_lid_inner_backing','pod_v4_basin_seal_lip')}
    additions={}
    for name in ('pod_v4_window_frame','pod_v4_window_inner_seal','pod_v4_display_housing','pod_v4_lid_inner_backing','pod_v4_basin_seal_lip'):
        obj=bpy.data.objects[name]; uv=obj.data.uv_layers['UV_POD_V4_SECTION']; vals=[tuple(round(v,6) for v in d.uv) for d in uv.data]
        additions[name]={'parent':obj.parent.name if obj.parent else None,'boundary_edges':boundary_count(obj.data),'uv_bounds':[list(map(min,zip(*vals))),list(map(max,zip(*vals)))]}
    backing_fit=fitted_backing_inside_cover(); basin_embed=basin_outer_embed()
    result={'source_blend':str(BLEND),'motion_parent_frame60':{'location_m':[round(v,6) for v in lid.location],'rotation_y_deg':round(lid.rotation_euler.y*57.2957795,4)},'frame_world_bounds':rows,'new_geometry':additions,'source_fit_checks':{'lid_backing':backing_fit,'basin_lip':basin_embed},'assertions':{'lid_children_follow_existing_motion':all(bpy.data.objects[n].parent==lid for n in ('pod_v4_window_frame','pod_v4_window_inner_seal','pod_v4_lid_inner_backing')),'new_meshes_closed_manifold':all(boundary_count(bpy.data.objects[n].data)==0 for n in additions),'section_uv_non_degenerate_atlas_band':all(a['uv_bounds'][1][0]>a['uv_bounds'][0][0] and a['uv_bounds'][1][1]>a['uv_bounds'][0][1] for a in additions.values()),'backing_top_inside_actual_inner_face':backing_fit['all_top_vertices_inside_source_xy'],'backing_embedded_1mm_into_cover':backing_fit['top_embedded_opposite_inward_normal_1mm'],'basin_outer_edge_embedded_within_3mm':basin_embed['outer_edge_to_source_max_m']<=.003}}
    OUT.write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
