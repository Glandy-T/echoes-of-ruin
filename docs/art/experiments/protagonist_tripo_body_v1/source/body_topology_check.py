"""Independent, read-only topology QA for the newly downloaded Tripo body GLB."""
from pathlib import Path
from collections import Counter
import hashlib, json
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

EXP=Path(__file__).resolve().parents[1]
RAW=EXP/'model/protagonist_tripo_body_v1_raw.glb'; OBJ=EXP/'model/protagonist_tripo_body_v1_raw.obj'
INSPECTION=EXP/'model/protagonist_body_v1_inspection.blend'; RECORD=EXP/'source/generation_record.json'; OUT=EXP/'source/body_topology_check.json'
GLB_HASH='b5fe1a0aff5581c47121f935f905bc991fbf0ae6f32aed8f7135c1f35c742069'; OBJ_HASH='49e3cc0ab87beb4b9ff12688ed64b7df7081d31729baae94a29c88cff86fbaeb'
EPS=1e-8; POINT_EPS=2e-7; AREA_EPS=1e-13
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def vec(x):return [float(v) for v in x]
def area2(q):return abs(sum(q[i][0]*q[(i+1)%len(q)][1]-q[i][1]*q[(i+1)%len(q)][0] for i in range(len(q))))*.5 if len(q)>=3 else 0
def clip2(subject,clip):
    def signed(q):return sum(q[i][0]*q[(i+1)%len(q)][1]-q[i][1]*q[(i+1)%len(q)][0] for i in range(len(q)))
    out=list(subject) if signed(subject)>=0 else list(reversed(subject)); clip=list(clip) if signed(clip)>=0 else list(reversed(clip))
    for a,b in zip(clip,clip[1:]+clip[:1]):
        old=out;out=[]
        if not old:break
        s=old[-1];ss=(b[0]-a[0])*(s[1]-a[1])-(b[1]-a[1])*(s[0]-a[0])
        for e in old:
            es=(b[0]-a[0])*(e[1]-a[1])-(b[1]-a[1])*(e[0]-a[0]);sin=ss>=-EPS;ein=es>=-EPS
            if sin!=ein:
                den=ss-es
                if abs(den)>1e-30:
                    t=ss/den;out.append((s[0]+t*(e[0]-s[0]),s[1]+t*(e[1]-s[1])))
            if ein:out.append(e)
            s,ss=e,es
    return out
def dedupe(ps):
    ans=[]
    for p in ps:
        if not any((p-q).length<=POINT_EPS for q in ans):ans.append(p)
    return ans
def segment_triangle(p0,p1,tri):
    a,b,c=tri;d=p1-p0;e1=b-a;e2=c-a;h=d.cross(e2);det=e1.dot(h)
    if abs(det)<=EPS:return None
    inv=1/det;s=p0-a;u=inv*s.dot(h);q=s.cross(e1);w=inv*d.dot(q);t=inv*e2.dot(q)
    if u<-EPS or w<-EPS or u+w>1+EPS or t<-EPS or t>1+EPS:return None
    strict=(u>EPS and w>EPS and u+w<1-EPS and t>EPS and t<1-EPS)
    return p0+d*t,strict
def triangle_intersection(a,b):
    na=(a[1]-a[0]).cross(a[2]-a[0]);nb=(b[1]-b[0]).cross(b[2]-b[0])
    if na.length<=EPS or nb.length<=EPS:return {'kind':'degenerate','points':[]}
    nua=na.normalized();nub=nb.normalized();parallel=abs(abs(nua.dot(nub))-1)<=2e-6;distance=max(abs(nua.dot(p-a[0])) for p in b)
    if parallel and distance<=POINT_EPS:
        drop=max(range(3),key=lambda i:abs(nua[i]));aa=[tuple(p[i] for i in range(3) if i!=drop) for p in a];bb=[tuple(p[i] for i in range(3) if i!=drop) for p in b];overlap=area2(clip2(aa,bb))
        return {'kind':'coplanar_overlap' if overlap>AREA_EPS else 'coplanar_touch_or_disjoint','points':[],'projected_overlap_area':overlap}
    hits=[];strict=False
    for tri,other in ((a,b),(b,a)):
        for p0,p1 in zip(tri,tri[1:]+tri[:1]):
            hit=segment_triangle(p0,p1,other)
            if hit:hits.append(hit[0]);strict=strict or hit[1]
    hits=dedupe(hits)
    if len(hits)>=2 and max((p-q).length for p in hits for q in hits)>POINT_EPS:kind='proper_crossing' if strict else 'edge_crossing'
    elif hits:kind='point_touch'
    else:kind='disjoint'
    return {'kind':kind,'points':[vec(p) for p in hits]}
def topology(me):
    use=Counter()
    for p in me.polygons:
        vs=list(p.vertices)
        for a,b in zip(vs,vs[1:]+vs[:1]):use[tuple(sorted((a,b)))]+=1
    parent=list(range(len(me.vertices)))
    def find(x):
        while x!=parent[x]:parent[x]=parent[parent[x]];x=parent[x]
        return x
    for a,b in use:
        a,b=find(a),find(b)
        if a!=b:parent[b]=a
    comps=Counter(find(i) for i in range(len(me.vertices)))
    return {'vertices':len(me.vertices),'polygons':len(me.polygons),'triangles':len(me.loop_triangles),'connected_components':len(comps),'component_vertex_counts_descending':sorted(comps.values(),reverse=True),'boundary_edges':sum(n==1 for n in use.values()),'nonmanifold_edges':sum(n>2 for n in use.values()),'degenerate_faces':sum(p.area<=1e-12 for p in me.polygons),'uv_layers':len(me.uv_layers),'vertex_groups':len(bpy.context.object.vertex_groups),'shape_keys':bool(me.shape_keys),'armature_modifiers':sum(m.type=='ARMATURE' for m in bpy.context.object.modifiers)}
def self_intersections(me,world):
    me.calc_loop_triangles();tris=[]
    for i,t in enumerate(me.loop_triangles):
        co=[world@me.vertices[x].co for x in t.vertices];tris.append({'index':i,'polygon':t.polygon_index,'vertices':tuple(t.vertices),'co':co,'center':sum(co,Vector())/3})
    co=[p for t in tris for p in t['co']];faces=[(3*i,3*i+1,3*i+2) for i in range(len(tris))];pairs=BVHTree.FromPolygons(co,faces,all_triangles=True).overlap(BVHTree.FromPolygons(co,faces,all_triangles=True));pairs=sorted({tuple(sorted(x)) for x in pairs if x[0]!=x[1]})
    counts=Counter();true=[]
    for ai,bi in pairs:
        a,b=tris[ai],tris[bi]
        if set(a['vertices'])&set(b['vertices']):counts['excluded_shared_vertex_neighbor']+=1;continue
        r=triangle_intersection(a['co'],b['co']);counts[r['kind']]+=1
        if r['kind'] in ('proper_crossing','edge_crossing','coplanar_overlap'):
            pts=[Vector(x) for x in r.get('points',[])];pos=sum(pts,Vector())/len(pts) if pts else (a['center']+b['center'])/2
            true.append({'triangle_a':a['index'],'triangle_b':b['index'],'polygon_a':a['polygon'],'polygon_b':b['polygon'],'vertices_a':list(a['vertices']),'vertices_b':list(b['vertices']),'kind':r['kind'],'position_world':vec(pos),'intersection_points':r.get('points',[]),'projected_overlap_area':r.get('projected_overlap_area')})
    pos=[Vector(row['position_world']) for row in true]
    bounds=None
    if pos:
        bounds={'min':vec((min(p.x for p in pos),min(p.y for p in pos),min(p.z for p in pos))),
                'max':vec((max(p.x for p in pos),max(p.y for p in pos),max(p.z for p in pos)))}
    locality={'all_true_intersections_world_bounds':bounds,'all_true_intersections_at_or_below_z_002':bool(pos) and all(p.z<=.02 for p in pos),'negative_y_count':sum(p.y<0 for p in pos),'positive_y_count':sum(p.y>=0 for p in pos)}
    return {'bvh_candidate_pair_count':len(pairs),'classification_counts':dict(counts),'true_nonadjacent_intersection_count':len(true),'true_nonadjacent_intersections_sample':true[:100],'locality':locality,'method':'BVH candidates then exact triangle classifier; pairs sharing any mesh vertex excluded; point/edge-only coplanar contacts not counted.'}

before={'glb':sha(RAW),'obj':sha(OBJ),'inspection_blend':sha(INSPECTION)}
rec=json.loads(RECORD.read_text(encoding='utf-8'))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(RAW))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
checks={'glb_hash_unchanged':before['glb']==GLB_HASH,'obj_hash_unchanged':before['obj']==OBJ_HASH,'one_private_prompt_generation_recorded':rec.get('requested_count')==1 and rec.get('submission_count')==1 and rec.get('new_generation_count')==1 and rec.get('requested_privacy')=='Private' and rec.get('requested_input')=='Text prompt only; no third-party imagery or PixelCanals assets','one_glb_mesh':len(meshes)==1}
if meshes:
    ob=meshes[0];bpy.context.view_layer.objects.active=ob;me=ob.data;me.calc_loop_triangles();top=topology(me);inter=self_intersections(me,ob.matrix_world)
    checks['expected_glb_closed_single_component_topology']=top['vertices']==3067 and top['polygons']==6130 and top['triangles']==6130 and top['connected_components']==1 and top['boundary_edges']==0 and top['nonmanifold_edges']==0 and top['degenerate_faces']==0
    checks['no_uv_rig_or_shape_keys']=top['uv_layers']==0 and top['vertex_groups']==0 and not top['shape_keys'] and top['armature_modifiers']==0
    checks['no_true_nonadjacent_triangle_self_intersections']=inter['true_nonadjacent_intersection_count']==0
else:top={};inter={};checks['expected_glb_closed_single_component_topology']=False;checks['no_uv_rig_or_shape_keys']=False;checks['no_true_nonadjacent_triangle_self_intersections']=False
after={'glb':sha(RAW),'obj':sha(OBJ),'inspection_blend':sha(INSPECTION)};checks['raw_and_inspection_artifacts_unchanged_during_readonly_check']=before==after
result={'status':'PASS_STATIC_CANDIDATE' if all(checks.values()) else 'FAIL_STATIC_CANDIDATE','checks':checks,'failed_checks':[k for k,v in checks.items() if not v],'artifact_sha256_before':before,'artifact_sha256_after':after,'topology':top,'self_intersection_audit':inter,'visual_readback_boundary':'Review rendered front/back/side/quarter separately. This file-side check cannot approve anatomy, underarm visual quality, finger clearance, deformation, rigging, UVs, clothing fit, or final art.','verdict':'Static body candidate only; a closed manifold and zero nonadjacent crossings do not establish animation-ready topology.'}
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result['status'],result['failed_checks'])
