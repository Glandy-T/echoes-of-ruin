"""One bounded, fidelity-measured surface reconstruction of the raw garment.

Used after local outer extraction demonstrably lost the approved shoulder
silhouette. This is geometry repair, not a new garment design or texture pass.
"""
from pathlib import Path
import bpy,bmesh,json,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
EXP=Path(__file__).resolve().parents[1];RAW=EXP.parent/'protagonist_tripo_robe_v2/model/protagonist_tripo_robe_v2_raw.glb';LIB=EXP.parent/'protagonist_tripo_body_v1/source/body_topology_check.py'
ns={'__file__':str(LIB),'__name__':'geometry_library'};exec(compile(LIB.read_text(encoding='utf-8').split("\nbefore={'glb':")[0],str(LIB),'exec'),ns)
original=hashlib.sha256(RAW.read_bytes()).hexdigest();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(RAW));ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
src_vertices=[v.co.copy() for v in ob.data.vertices];ob.data.calc_loop_triangles();src_tri=[tuple(t.vertices) for t in ob.data.loop_triangles];src_bvh=BVHTree.FromPolygons(src_vertices,src_tri,all_triangles=True)
remesh=ob.modifiers.new('Bounded_Surface_Rebuild','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.0025;remesh.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=remesh.name);ob.data.calc_loop_triangles();rebuild_top=ns['topology'](ob.data)
dec=ob.modifiers.new('Controlled_Reduction','DECIMATE');dec.ratio=min(1.,10000/len(ob.data.loop_triangles));dec.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=dec.name)
ob.data.update();ob.data.calc_loop_triangles();top=ns['topology'](ob.data);inter=ns['self_intersections'](ob.data,ob.matrix_world)
dist=[src_bvh.find_nearest(v.co)[3] for v in ob.data.vertices];dist.sort();dst_bvh=BVHTree.FromPolygons([v.co for v in ob.data.vertices],[tuple(t.vertices) for t in ob.data.loop_triangles],all_triangles=True);reverse=sorted(dst_bvh.find_nearest(p)[3] for p in src_vertices)
def summarize(rows):return {'max':rows[-1],'p95':rows[int(.95*(len(rows)-1))],'mean':sum(rows)/len(rows)}
out=EXP/'scratch';out.mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out/'surface_rebuild_trial.blend'))
assert hashlib.sha256(RAW.read_bytes()).hexdigest()==original
result={'status':'TRIAL_ONLY','source_sha256':original,'voxel_size':.0025,'triangle_target':10000,'voxel_before_reduction_topology':rebuild_top,'topology':top,'self_intersections':inter,'distance_to_raw_surface':summarize(dist),'raw_vertex_distance_to_rebuild':summarize(reverse),'limits':'A geometric distance bound is not silhouette or opening/art approval. Do not adopt until visual comparison and opening probes.'}
(EXP/'source/surface_rebuild_trial.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('SURFACE_REBUILD',top,'crossings',inter['true_nonadjacent_intersection_count'],'distance',summarize(dist),summarize(reverse))
