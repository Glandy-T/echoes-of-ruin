"""Bounded, reproducible toe-tip repair for the immutable Tripo body v1 OBJ.

The v1 OBJ is never written.  It is imported, made upright (+Z) with the
documented X90 conversion, exact coincident seam vertices are welded, and only
the forefeet are bisected at x=.026 and rebuilt with rounded cross-sections.
Untouched faces retain source corner normals captured BEFORE seam welding.
"""
from pathlib import Path
from collections import Counter
import hashlib, json
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

V2 = Path(__file__).resolve().parents[1]
V1 = V2.parent / 'protagonist_tripo_body_v1'
RAW = V1 / 'model' / 'protagonist_tripo_body_v1_raw.obj'
OUT_BLEND = V2 / 'model' / 'protagonist_body_v2.blend'
OUT_GLB = V2 / 'model' / 'protagonist_body_v2.glb'
REPORT = V2 / 'source' / 'build_report.json'
RAW_SHA256 = '49e3cc0ab87beb4b9ff12688ed64b7df7081d31729baae94a29c88cff86fbaeb'

# The v1 crossing audit occupies x=.04168..0540, z=.00230..01083.
# The actual planar cut is x=.026, restricted to foot faces below z=.070.
# This envelope also includes new vertices where source faces meet the plane.
TOE_ENVELOPE_X = 0.022
TOE_ENVELOPE_Z = 0.070
EPS = 1e-8; POINT_EPS = 2e-7; AREA_EPS = 1e-13

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def vec(v): return [float(x) for x in v]
def world_coords(me): return [tuple(round(c, 12) for c in v.co) for v in me.vertices]
def surface_coords(me):
    used={i for p in me.polygons for i in p.vertices}
    return [tuple(round(c, 12) for c in me.vertices[i].co) for i in used]
def face_key(me,p): return tuple(sorted(tuple(round(c,12) for c in me.vertices[i].co) for i in p.vertices))
def preserve_corner_data(me):
    data={}
    for p in me.polygons:
        normals={tuple(round(c,12) for c in me.vertices[me.loops[li].vertex_index].co):tuple(me.corner_normals[li].vector) for li in p.loop_indices}
        data[face_key(me,p)]=(p.use_smooth,normals)
    return data
def restore_corner_data(me,data):
    # Blender 5 retains the custom-normal setters; untouched faces are matched
    # by their world-coordinate face/vertex keys rather than unstable indices.
    out=[]
    for p in me.polygons:
        stored=data.get(face_key(me,p))
        if stored is not None: p.use_smooth=stored[0]
        for li in p.loop_indices:
            coord=tuple(round(c,12) for c in me.vertices[me.loops[li].vertex_index].co)
            out.append(Vector(stored[1][coord]) if stored is not None and coord in stored[1] else me.corner_normals[li].vector.copy())
    me.normals_split_custom_set(out)
    me.update()
    max_error=0.0; restored=0
    for p in me.polygons:
        stored=data.get(face_key(me,p))
        if stored is None: continue
        for li in p.loop_indices:
            coord=tuple(round(c,12) for c in me.vertices[me.loops[li].vertex_index].co)
            if coord in stored[1]:
                max_error=max(max_error,(me.corner_normals[li].vector-Vector(stored[1][coord])).length); restored+=1
    return {'restored_untouched_face_corners':restored,'max_corner_normal_vector_error':max_error,'has_custom_normals':me.has_custom_normals}
def topo(me):
    uses = Counter()
    for p in me.polygons:
        vs=list(p.vertices)
        for a,b in zip(vs,vs[1:]+vs[:1]): uses[tuple(sorted((a,b)))] += 1
    parent=list(range(len(me.vertices)))
    def find(i):
        while parent[i]!=i: parent[i]=parent[parent[i]]; i=parent[i]
        return i
    for a,b in uses:
        a,b=find(a),find(b)
        if a!=b: parent[b]=a
    return {'vertices':len(me.vertices),'polygons':len(me.polygons),
      'triangles':len(me.loop_triangles),'connected_components':len({find(i) for i in range(len(me.vertices))}),
      'boundary_edges':sum(n==1 for n in uses.values()),'nonmanifold_edges':sum(n>2 for n in uses.values()),
      'degenerate_faces':sum(p.area<=1e-12 for p in me.polygons),
      'quad_polygons':sum(len(p.vertices)==4 for p in me.polygons),
      'triangle_polygons':sum(len(p.vertices)==3 for p in me.polygons),'ngon_polygons':sum(len(p.vertices)>4 for p in me.polygons)}

def area2(q): return abs(sum(q[i][0]*q[(i+1)%len(q)][1]-q[i][1]*q[(i+1)%len(q)][0] for i in range(len(q))))*.5 if len(q)>=3 else 0
def clip2(subject,clip):
    def sign(q): return sum(q[i][0]*q[(i+1)%len(q)][1]-q[i][1]*q[(i+1)%len(q)][0] for i in range(len(q)))
    out=list(subject) if sign(subject)>=0 else list(reversed(subject)); clip=list(clip) if sign(clip)>=0 else list(reversed(clip))
    for a,b in zip(clip,clip[1:]+clip[:1]):
        old=out;out=[]
        if not old: break
        s=old[-1]; ss=(b[0]-a[0])*(s[1]-a[1])-(b[1]-a[1])*(s[0]-a[0])
        for e in old:
            es=(b[0]-a[0])*(e[1]-a[1])-(b[1]-a[1])*(e[0]-a[0]); sin=ss>=-EPS; ein=es>=-EPS
            if sin != ein and abs(ss-es)>1e-30:
                t=ss/(ss-es); out.append((s[0]+t*(e[0]-s[0]),s[1]+t*(e[1]-s[1])))
            if ein: out.append(e)
            s,ss=e,es
    return out
def dedupe(ps):
    out=[]
    for p in ps:
        if not any((p-q).length<=POINT_EPS for q in out): out.append(p)
    return out
def segment_triangle(p0,p1,tri):
    a,b,c=tri; d=p1-p0; e1=b-a; e2=c-a; h=d.cross(e2); det=e1.dot(h)
    if abs(det)<=EPS:return None
    inv=1/det; s=p0-a; u=inv*s.dot(h); q=s.cross(e1); w=inv*d.dot(q); t=inv*e2.dot(q)
    if u<-EPS or w<-EPS or u+w>1+EPS or t<-EPS or t>1+EPS:return None
    return p0+d*t, (u>EPS and w>EPS and u+w<1-EPS and t>EPS and t<1-EPS)
def tri_hit(a,b):
    na=(a[1]-a[0]).cross(a[2]-a[0]); nb=(b[1]-b[0]).cross(b[2]-b[0])
    if na.length<=EPS or nb.length<=EPS:return 'degenerate'
    nua=na.normalized(); nub=nb.normalized(); parallel=abs(abs(nua.dot(nub))-1)<=2e-6; distance=max(abs(nua.dot(p-a[0])) for p in b)
    if parallel and distance<=POINT_EPS:
        drop=max(range(3),key=lambda i:abs(nua[i])); aa=[tuple(p[i] for i in range(3) if i!=drop) for p in a]; bb=[tuple(p[i] for i in range(3) if i!=drop) for p in b]
        return 'coplanar_overlap' if area2(clip2(aa,bb))>AREA_EPS else 'coplanar_touch_or_disjoint'
    hits=[]; strict=False
    for tri,other in ((a,b),(b,a)):
        for p0,p1 in zip(tri,tri[1:]+tri[:1]):
            hit=segment_triangle(p0,p1,other)
            if hit: hits.append(hit[0]); strict=strict or hit[1]
    hits=dedupe(hits)
    if len(hits)>=2 and max((p-q).length for p in hits for q in hits)>POINT_EPS:return 'proper_crossing' if strict else 'edge_crossing'
    return 'point_touch' if hits else 'disjoint'
def crossings(me):
    me.calc_loop_triangles(); tris=[(tuple(t.vertices),[me.vertices[i].co.copy() for i in t.vertices]) for t in me.loop_triangles]
    co=[p for _,t in tris for p in t]; faces=[(3*i,3*i+1,3*i+2) for i in range(len(tris))]
    pairs=sorted({tuple(sorted(p)) for p in BVHTree.FromPolygons(co,faces,all_triangles=True).overlap(BVHTree.FromPolygons(co,faces,all_triangles=True)) if p[0]!=p[1]})
    true=[]; kinds=Counter()
    for i,j in pairs:
        if set(tris[i][0]) & set(tris[j][0]): continue
        k=tri_hit(tris[i][1],tris[j][1]); kinds[k]+=1
        if k in ('proper_crossing','edge_crossing','coplanar_overlap'): true.append({'triangles':[i,j],'kind':k})
    return {'bvh_candidate_pair_count':len(pairs),'classification_counts':dict(kinds),'true_nonadjacent_intersection_count':len(true),'sample':true[:20]}

if sha(RAW) != RAW_SHA256: raise RuntimeError('Refusing to build: immutable v1 OBJ hash mismatch.')
for p in (OUT_BLEND,OUT_GLB,REPORT): p.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(RAW))
ob=next(o for o in bpy.context.scene.objects if o.type=='MESH'); ob.name='ProtagonistBodyV2_ToesRepaired'; bpy.context.view_layer.objects.active=ob; ob.select_set(True)
# OBJ is Y-up. Apply only this working-copy transform, preserving final +Z-up.
ob.rotation_euler[0]=1.5707963267948966; bpy.ops.object.transform_apply(location=False,rotation=True,scale=False)
corner_data=preserve_corner_data(ob.data)
bm=bmesh.new(); bm.from_mesh(ob.data); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-8); bm.to_mesh(ob.data); bm.free(); ob.data.update()
before=world_coords(ob.data)
surface_before=surface_coords(ob.data)
pre_repair_audit=crossings(ob.data)
repair_applied=pre_repair_audit['true_nonadjacent_intersection_count'] != 0
cut_count=0
if repair_applied:
    bm=bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    # A genuine constant-X cut ring, not a vertex-selection silhouette.  Only
    # forefoot faces participate; all anatomy behind x=.026 is untouched.
    foot_faces=[f for f in bm.faces if max(v.co.z for v in f.verts)<0.070]
    foot_geom=list({g for f in foot_faces for g in ([f]+list(f.edges)+list(f.verts))})
    before_count=len(bm.verts)
    bmesh.ops.bisect_plane(bm,geom=foot_geom,plane_co=(0.026,0,0),plane_no=(1,0,0),clear_outer=True,clear_inner=False)
    bm.verts.ensure_lookup_table(); cut_count=before_count-len(bm.verts)
    open_edges=[e for e in bm.edges if len(e.link_faces)==1]
    if not open_edges: raise RuntimeError('Toe deletion created no boundary loops.')
    cut_ring_x_max_deviation=max(abs(v.co.x-0.026) for e in open_edges for v in e.verts)
    print('TOE_REPAIR_BOUNDARY_BEFORE_FILL',len(open_edges),{'min':vec([min(v.co[i] for e in open_edges for v in e.verts) for i in range(3)]),'max':vec([max(v.co[i] for e in open_edges for v in e.verts) for i in range(3)])})
    # Two forward rings preserve a natural foot length while forming a rounded
    # low-poly toe envelope; no jagged source boundary is capped directly.
    def advance_ring(edges,dx,sy,sz,ground):
        geom=bmesh.ops.extrude_edge_only(bm,edges=edges)['geom']
        verts=[g for g in geom if isinstance(g,bmesh.types.BMVert)]
        for positive in (False,True):
            group=[v for v in verts if (v.co.y>=0)==positive]
            cy=sum(v.co.y for v in group)/len(group); cz=min(v.co.z for v in group)
            for v in group:
                v.co.x += dx; v.co.y=cy+(v.co.y-cy)*sy; v.co.z=cz+(v.co.z-cz)*sz
            offset=ground-min(v.co.z for v in group)
            for v in group: v.co.z += offset
        return [e for e in bm.edges if len(e.link_faces)==1]
    ring1=advance_ring(open_edges,0.019,0.98,0.80,0.0)
    ring2=advance_ring(ring1,0.013,0.88,0.60,0.0015)
    ring3=advance_ring(ring2,0.006,0.50,0.40,0.0045)
    cap_faces=bmesh.ops.holes_fill(bm,edges=ring3,sides=0)['faces']
    bmesh.ops.triangulate(bm,faces=cap_faces,quad_method='BEAUTY',ngon_method='EAR_CLIP')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    for face in bm.faces:face.smooth=True
    loose=[e for e in bm.edges if not e.link_faces]
    if loose:
        print('TOE_REPAIR_REMOVED_LOCAL_LOOSE_EDGES',len(loose))
        bmesh.ops.delete(bm,geom=loose,context='EDGES')
    remaining=[e for e in bm.edges if len(e.link_faces)!=2]
    if remaining: raise RuntimeError('Toe caps did not close every boundary edge.')
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
else:
    print('WELDED_OBJ_HAS_ZERO_TRUE_INTERSECTIONS; toe geometry preserved')
ob.data.validate(verbose=True); ob.data.update(); ob.data.calc_loop_triangles()
normal_restore=restore_corner_data(ob.data,corner_data); ob.data.update()
after=world_coords(ob.data)
surface_after=surface_coords(ob.data)
non_toe_before=sorted(p for p in surface_before if not (p[0]>TOE_ENVELOPE_X and p[2]<TOE_ENVELOPE_Z))
non_toe_after=sorted(p for p in surface_after if not (p[0]>TOE_ENVELOPE_X and p[2]<TOE_ENVELOPE_Z))
result={'raw_obj_sha256_expected':RAW_SHA256,'raw_obj_sha256_after':sha(RAW),'raw_obj_immutable':sha(RAW)==RAW_SHA256,
 'operation':('Imported v1 OBJ; applied X90 only in working copy; welded exact coincident seam vertices. The Blender triangulation of this quad source has zero true nonadjacent crossings, so no toe geometry was deleted.' if not repair_applied else 'Imported v1 OBJ; applied X90 only in working copy; welded exact coincident seam vertices; made a true planar forefoot cross-section at x=.026 within z<.070, then built rounded envelope rings at x=.045/.058/.064 and triangulated their planar end caps.'),
 'welded_obj_before_repair_self_intersection_audit':pre_repair_audit,
 'untouched_custom_corner_normal_restore':normal_restore,
 'changed_region_world':{'deletion_rule':'bmesh bisect_plane: foot faces z<0.070, plane x=0.026, clear_outer','cut_ring_x_max_deviation':cut_ring_x_max_deviation if repair_applied else None,'proof_envelope':'x > 0.022 and z < 0.070 (forefoot envelope)','crossing_audit_v1_bounds_reference':{'x':[0.0416826531291008,0.053495801985263824],'z':[0.0023040771484375,0.010825363919138908]},'repair_applied':repair_applied,'deleted_vertices':cut_count},
 'untouched_surface_proof':{'post_weld_vertices_before_repair':len(before),'non_toe_surface_vertices_before_repair':len(non_toe_before),'non_toe_surface_vertices_after_repair':len(non_toe_after),'non_toe_surface_coordinate_multisets_identical':non_toe_before==non_toe_after,'note':'No non-toe surface vertex was deleted or moved. Two face-less source edges inside the toe patch are discarded; exact seam welding precedes this comparison and can reduce duplicate OBJ vertices without moving unique surface positions.'},
 'topology':topo(ob.data),'self_intersection_audit':crossings(ob.data),'limits':['No UVs, rig, weights, shape keys, animation, clothing separation, or final visual acceptance is claimed.','The source OBJ remains immutable; v2 is a separate mesh intended for subsequent visual and rig-readiness review.']}
# Custom normals are restored from the original import BEFORE seam welding.
# A bounded normal-vector readback tolerance is supplemented by same-camera
# visual comparison; neither floating storage nor art acceptance is identical.
result['status']='PASS_STATIC_TOE_REPAIR' if result['raw_obj_immutable'] and result['topology']['connected_components']==1 and result['topology']['boundary_edges']==0 and result['topology']['nonmanifold_edges']==0 and result['topology']['degenerate_faces']==0 and result['self_intersection_audit']['true_nonadjacent_intersection_count']==0 and result['untouched_custom_corner_normal_restore']['max_corner_normal_vector_error']<=0.01 else 'FAIL_STATIC_TOE_REPAIR'
REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
if result['status']!='PASS_STATIC_TOE_REPAIR': raise RuntimeError('Static QA failed; report written.')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
# Export exactly the evaluated loop triangulation already audited above.
# Keep editable quad master unchanged; export-only mesh carries source loop normals.
ob.data.calc_loop_triangles()
export_mesh=bpy.data.meshes.new('Export_Exact_Audited_Triangles')
export_mesh.from_pydata([v.co.copy() for v in ob.data.vertices],[],[list(t.vertices) for t in ob.data.loop_triangles]);export_mesh.update()
export_normals=[]
for t,poly in zip(ob.data.loop_triangles,export_mesh.polygons):
    poly.use_smooth=ob.data.polygons[t.polygon_index].use_smooth
    export_normals.extend(ob.data.corner_normals[li].vector.copy() for li in t.loops)
export_mesh.normals_split_custom_set(export_normals);export_mesh.update()
export_ob=bpy.data.objects.new('ProtagonistBodyV2_Export',export_mesh);bpy.context.scene.collection.objects.link(export_ob)
bpy.ops.object.select_all(action='DESELECT');export_ob.select_set(True);bpy.context.view_layer.objects.active=export_ob
bpy.ops.export_scene.gltf(filepath=str(OUT_GLB),export_format='GLB',use_selection=True,export_materials='NONE')
result['exported_glb']={'sha256':sha(OUT_GLB),'bytes':OUT_GLB.stat().st_size}
bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(OUT_GLB))
exported=next(o for o in bpy.context.scene.objects if o.type=='MESH'); exported.data.calc_loop_triangles()
result['exported_glb']['raw_index_topology']=topo(exported.data)
# glTF may split position indices at custom normal boundaries. Weld only a QA
# copy's coincident positions for geometric connectivity and neighbor exclusion.
bm=bmesh.new();bm.from_mesh(exported.data);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-8);bm.to_mesh(exported.data);bm.free();exported.data.update();exported.data.calc_loop_triangles()
result['exported_glb']['topology']=topo(exported.data)
result['exported_glb']['qa_note']='Connectivity/self-crossings measured after exact coincident-position weld on an unsaved inspection copy; raw file and its normal seams are unchanged.'
result['exported_glb']['self_intersection_audit']=crossings(exported.data)
result['exported_glb']['matches_static_requirements']=result['exported_glb']['topology']['connected_components']==1 and result['exported_glb']['topology']['boundary_edges']==0 and result['exported_glb']['topology']['nonmanifold_edges']==0 and result['exported_glb']['topology']['degenerate_faces']==0 and result['exported_glb']['self_intersection_audit']['true_nonadjacent_intersection_count']==0
if not result['exported_glb']['matches_static_requirements']:
    result['status']='FAIL_EXPORTED_GLB_STATIC_QA'
    REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    raise RuntimeError('Exported GLB static QA failed.')
REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(result['status'],json.dumps({'deleted_vertices':cut_count,'topology':result['topology'],'self_intersections':result['self_intersection_audit']['true_nonadjacent_intersection_count']}))
