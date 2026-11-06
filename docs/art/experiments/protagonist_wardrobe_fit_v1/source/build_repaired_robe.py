"""Controlled surface reconstruction after local shell extraction failed.

Preserves the approved visual envelope rather than claiming identical source
vertex topology. Native voxel surface resolution is .25% of normalized height,
then reduced to 10k triangles. Requires geometry, openings and visual QA.
"""
from pathlib import Path
import bpy,json,hashlib
from mathutils.bvhtree import BVHTree
EXP=Path(__file__).resolve().parents[1]
RAW=EXP.parent/'protagonist_tripo_robe_v2/model/protagonist_tripo_robe_v2_raw.glb'
LIB=EXP.parent/'protagonist_tripo_body_v1/source/body_topology_check.py'
OPEN_LIB=EXP.parent/'protagonist_tripo_robe_v2/source/robe_topology_check.py'
ns={'__file__':str(LIB),'__name__':'geometry_library'}
exec(compile(LIB.read_text(encoding='utf-8').split("\nbefore={'glb':")[0],str(LIB),'exec'),ns)
opening_ns={'__file__':str(OPEN_LIB),'__name__':'opening_library'}
exec(compile(OPEN_LIB.read_text(encoding='utf-8').split('\nbefore=')[0],str(OPEN_LIB),'exec'),opening_ns)
original=hashlib.sha256(RAW.read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(RAW))
ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
ob.data.calc_loop_triangles();points=[v.co.copy() for v in ob.data.vertices];tris=[tuple(t.vertices) for t in ob.data.loop_triangles];source_corner_normals=[[ob.data.corner_normals[i].vector.copy() for i in t.loops] for t in ob.data.loop_triangles];original_bvh=BVHTree.FromPolygons(points,tris,all_triangles=True)
remesh=ob.modifiers.new('Controlled_Surface_Reconstruction','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.0025;remesh.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=remesh.name);ob.data.calc_loop_triangles();voxel_topology=ns['topology'](ob.data)
dec=ob.modifiers.new('Controlled_Reduction','DECIMATE');dec.ratio=min(1.,10000/len(ob.data.loop_triangles));dec.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=dec.name)
ob.data.update();ob.data.calc_loop_triangles()
# Retessellation changes automatic vertex normals even where the actual surface
# moved less than one source pixel. Transfer the source smooth-normal field;
# this is normal data, not painted detail or texture generation.
normal_field=[]
for p in ob.data.polygons:p.use_smooth=True
ob.data.update()
for vertex in ob.data.vertices:
 hit,normal,index,distance=original_bvh.find_nearest(vertex.co);a,b,c=[points[i] for i in tris[index]]
 u=b-a;v=c-a;w=hit-a;uu=u.dot(u);uv=u.dot(v);vv=v.dot(v);wu=w.dot(u);wv=w.dot(v);den=uu*vv-uv*uv
 y=(vv*wu-uv*wv)/den if abs(den)>1e-20 else 0;z=(uu*wv-uv*wu)/den if abs(den)>1e-20 else 0
 n=(source_corner_normals[index][0]*(1-y-z)+source_corner_normals[index][1]*y+source_corner_normals[index][2]*z).normalized()
 if n.dot(vertex.normal)<0:n=-n
 normal_field.append(n)
ob.data.normals_split_custom_set_from_vertices(normal_field);ob.data.update()
top=ns['topology'](ob.data);inter=ns['self_intersections'](ob.data,ob.matrix_world)
openings=opening_ns['opening_probes'](ob.data,ob.matrix_world)
assert top['connected_components']==1 and top['boundary_edges']==0 and top['nonmanifold_edges']==0 and top['degenerate_faces']==0 and inter['true_nonadjacent_intersection_count']==0,'Geometry gate failed'
assert all(row['uncapped_centerline_rays']>0 for row in openings.values()),'Opening gate failed'
dist=sorted(original_bvh.find_nearest(v.co)[3] for v in ob.data.vertices)
rebuilt_bvh=BVHTree.FromPolygons([v.co for v in ob.data.vertices],[tuple(t.vertices) for t in ob.data.loop_triangles],all_triangles=True);reverse=sorted(rebuilt_bvh.find_nearest(p)[3] for p in points)
def summary(values):return {'max':values[-1],'p95':values[int(.95*(len(values)-1))],'mean':sum(values)/len(values)}
ob.name='Robe_Repaired_Raw_Coordinates';out=EXP/'model';out.mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'DIAGNOSTIC_static_robe.blend'))
bpy.ops.export_scene.gltf(filepath=str(out/'DIAGNOSTIC_static_robe.glb'),export_format='GLB',use_selection=True)
assert hashlib.sha256(RAW.read_bytes()).hexdigest()==original
report={'status':'PASS_GEOMETRY_AND_OPENINGS_PENDING_VISUAL','raw_unchanged_sha256':original,'method':'Controlled native .0025 voxel surface reconstruction then native decimate to10k triangles; no garment redesign. Original source faces are NOT preserved bit-identically.','normal_field':'Barycentric original corner-normal transfer to reconstructed vertices, orientation checked. No texture edits.','voxel_before_reduction_topology':voxel_topology,'topology':top,'self_intersections':inter,'openings':openings,'rebuilt_vertex_distance_to_raw':summary(dist),'raw_vertex_distance_to_rebuilt':summary(reverse),'limits':'Surface distances are not silhouettes or final art approval; same-camera images required. Triangulated prototype still requires shared rig/weight/deformation and production UV review.'}
(EXP/'source/repaired_robe_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('REPAIRED_ROBE_GEOMETRY_AND_OPENINGS_PASS',top,summary(dist))
