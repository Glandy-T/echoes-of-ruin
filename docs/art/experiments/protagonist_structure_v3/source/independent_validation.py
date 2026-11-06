"""Read-only independent validation for protagonist_structure_v3."""
from pathlib import Path
import hashlib, json, struct
from collections import Counter, defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import bpy

EXP=Path(__file__).resolve().parent.parent
V2=EXP.parent/'protagonist_tripo_cn_cleanup_v2'; RAW=EXP.parent/'protagonist_tripo_cn_p20_v1/model/protagonist_tripo_cn_p20_v1_raw.obj'
BLEND=EXP/'model/protagonist_structure_v3.blend'; GLB=EXP/'model/protagonist_structure_v3.glb'; REPORT=EXP/'source/build_report.json'; OUT=EXP/'source/independent_validation.json'
V2_HASH='9f5fd46d630c318108ebbe16dcc46aef9a837234f51ac4685f1e0f8390b80105'; RAW_HASH='f9717909d1df005269bfa695aa8a6863193ce4c27e583b3e52b9360d3ed58ff6'
CAPS=set(json.loads(REPORT.read_text(encoding='utf-8'))['removed_cap_raw_face_ids']); PARTS=('Hair_Main','Robe_Outer_Inner_Rims','Body_Base_Separate_From_Clothes','Preserved_Unclassified_Source_Details')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def fail(c): return [k for k,v in c.items() if not v]
def v(v): return [float(x) for x in v]
def x90(m):
    t=((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)); return all(abs(m[r][c]-t[r][c])<2e-5 for r in range(4) for c in range(4))
def snapshot(ob):
    me=ob.data; raw=me.attributes.get('raw_obj_face_index'); comp=me.attributes.get('raw_component_id')
    if not raw or not comp:return None
    return {int(raw.data[p.index].value):{'co':[tuple(me.vertices[i].co) for i in p.vertices],'n':[tuple(me.corner_normals[i].vector) for i in p.loop_indices],'comp':int(comp.data[p.index].value),'sides':len(p.vertices)} for p in me.polygons}
def edges(me, polys):
    d=Counter()
    for p in polys:
        q=list(p.vertices)
        for a,b in zip(q,q[1:]+q[:1]):d[tuple(sorted((a,b)))]+=1
    return {'edge_count':len(d),'boundary_edges':sum(n==1 for n in d.values()),'nonmanifold_edges':sum(n!=2 for n in d.values())}
def components(polys):
    d=defaultdict(list)
    for p in polys:
        q=list(p.vertices)
        for a,b in zip(q,q[1:]+q[:1]):d[tuple(sorted((a,b)))].append(p.index)
    g=defaultdict(set)
    for z in d.values():
        if len(z)==2:g[z[0]].add(z[1]);g[z[1]].add(z[0])
    left={p.index for p in polys}; total=0
    while left:
        total+=1; todo=[left.pop()]
        while todo:
            for n in g[todo.pop()]:
                if n in left:left.remove(n);todo.append(n)
    return total
def tris(me,pred):
    me.calc_loop_triangles(); ans=[]
    for t in me.loop_triangles:
        p=me.polygons[t.polygon_index]
        if pred(p):
            co=[me.vertices[i].co.copy() for i in t.vertices];ans.append({'poly':p.index,'verts':tuple(t.vertices),'co':co,'center':sum(co,Vector())/3})
    return ans
def bvh(a,b):
    if not a or not b:return {'pair_count':0,'pairs_sample':[]}
    av=[x for r in a for x in r['co']];bv=[x for r in b for x in r['co']]; ap=[(3*i,3*i+1,3*i+2) for i in range(len(a))];bp=[(3*i,3*i+1,3*i+2) for i in range(len(b))]
    pairs=BVHTree.FromPolygons(av,ap,all_triangles=True).overlap(BVHTree.FromPolygons(bv,bp,all_triangles=True))
    return {'pair_count':len(pairs),'pairs_sample':[{'a_polygon':a[i]['poly'],'b_polygon':b[j]['poly'],'approx_local_position':v((a[i]['center']+b[j]['center'])/2)} for i,j in pairs[:40]]}
def area(t):
    # Triangle inputs and clipped convex polygons share the same shoelace area.
    return abs(sum(t[i][0]*t[(i+1)%len(t)][1]-t[i][1]*t[(i+1)%len(t)][0] for i in range(len(t))))*.5 if len(t)>=3 else 0.0
def clipped(subject,clip):
    def ccw(p):return p if sum(p[i][0]*p[(i+1)%len(p)][1]-p[i][1]*p[(i+1)%len(p)][0] for i in range(len(p)))>=0 else list(reversed(p))
    out=ccw(subject);clip=ccw(clip)
    for a,b in zip(clip,clip[1:]+clip[:1]):
        inp=out;out=[]
        if not inp:break
        s=inp[-1];ss=(b[0]-a[0])*(s[1]-a[1])-(b[1]-a[1])*(s[0]-a[0])
        for e in inp:
            es=(b[0]-a[0])*(e[1]-a[1])-(b[1]-a[1])*(e[0]-a[0]);sin=ss>=-1e-12;ein=es>=-1e-12
            if sin!=ein:
                den=ss-es
                if abs(den)>1e-30:
                    z=ss/den;out.append((s[0]+z*(e[0]-s[0]),s[1]+z*(e[1]-s[1])))
            if ein:out.append(e)
            s,ss=e,es
    return out
def islands(me):
    uv=me.uv_layers.active.data; d=defaultdict(list)
    for p in me.polygons:
        ls=list(p.loop_indices)
        for la,lb in zip(ls,ls[1:]+ls[:1]):
            a,b=me.loops[la].vertex_index,me.loops[lb].vertex_index;d[tuple(sorted((a,b)))].append((p.index,{a:tuple(uv[la].uv),b:tuple(uv[lb].uv)}))
    g=defaultdict(set)
    for z in d.values():
        if len(z)==2:
            (a,ua),(b,ub)=z
            if all((Vector(ua[k])-Vector(ub[k])).length<=1e-7 for k in ua):g[a].add(b);g[b].add(a)
    left={p.index for p in me.polygons};n=0
    while left:
        n+=1;q=[left.pop()]
        while q:
            for x in g[q.pop()]:
                if x in left:left.remove(x);q.append(x)
    return n
def uvaudit(me):
    lay=me.uv_layers.active
    if not lay:return {'missing_uv':True}
    dat=lay.data;me.calc_loop_triangles(); rows=[];zero=[];total=0
    for t in me.loop_triangles:
        q=[tuple(dat[i].uv) for i in t.loops];ar=area(q);total+=ar
        if ar<=1e-12:zero.append(t.polygon_index);continue
        xs=[x for x,y in q];ys=[y for x,y in q];rows.append({'face':t.polygon_index,'uv':q,'bbox':(min(xs),max(xs),min(ys),max(ys))})
    buckets=defaultdict(list);cand=set()
    for i,r in enumerate(rows):
        x0,x1,y0,y1=r['bbox'];ax=max(0,min(31,int(x0*32)));bx=max(0,min(31,int(x1*32)));ay=max(0,min(31,int(y0*32)));by=max(0,min(31,int(y1*32)))
        for x in range(ax,bx+1):
            for y in range(ay,by+1):
                for j in buckets[(x,y)]:cand.add((j,i))
                buckets[(x,y)].append(i)
    hits=[]
    for i,j in sorted(cand):
        a,b=rows[i],rows[j];x0,x1,y0,y1=a['bbox'];u0,u1,w0,w1=b['bbox']
        if x1<u0-1e-9 or u1<x0-1e-9 or y1<w0-1e-9 or w1<y0-1e-9:continue
        z=clipped(a['uv'],b['uv']); ar=area(z) if len(z)>=3 else 0
        if ar>1e-10:hits.append({'face_a':a['face'],'face_b':b['face'],'area':ar})
    return {'missing_uv':False,'islands':islands(me),'faces':len(me.polygons),'uv_loop_count':len(dat),'outside_unit_square':sum(any(x<-1e-6 or x>1+1e-6 for x in q.uv) for q in dat),'zero_area_triangle_parent_faces':sorted(set(zero)),'sum_triangle_uv_area':total,'positive_overlap_pair_count':len(hits),'positive_overlap_pairs_sample':hits[:200],'spatial_hash_grid':'32x32'}

# First read v2; no collection/object visibility is changed before or after the snapshot.
bpy.ops.wm.open_mainfile(filepath=str(V2/'model/protagonist_cn_cleanup_v2.blend'))
v2col={c.name:[o.name for o in list(c.all_objects)] for c in bpy.data.collections if c.name in ('BEFORE_V1','AFTER_V2')}
v2src=bpy.data.objects.get('CN_P20_V2_AFTER') or next((o for o in bpy.data.objects if o.type=='MESH' and 'V2_AFTER' in o.name),None)
bpy.context.view_layer.update()
v2map=snapshot(v2src) if v2src else None

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
col_snapshot={c.name:[o.name for o in list(c.all_objects)] for c in bpy.data.collections if c.name in ('BEFORE_V2','AFTER_V3')}
bpy.context.view_layer.update(); depsgraph=bpy.context.evaluated_depsgraph_get()
before=bpy.data.collections.get('BEFORE_V2');after=bpy.data.collections.get('AFTER_V3');before_mesh=[o for o in list(before.all_objects) if o.type=='MESH'] if before else [];after_mesh=[o for o in list(after.all_objects) if o.type=='MESH'] if after else [];parts={o.name:o for o in after_mesh}
checks={'v2_blend_hash_unchanged':sha(V2/'model/protagonist_cn_cleanup_v2.blend')==V2_HASH,'raw_source_obj_hash_unchanged':RAW.exists() and sha(RAW)==RAW_HASH,'before_v2_is_single_unchanged_mesh':len(before_mesh)==1 and before_mesh[0].name=='V2_Baseline_Unchanged','after_v3_has_exact_four_declared_parts':set(parts)==set(PARTS),'all_parts_have_v2_rotation_x90_transform':len(parts)==4 and all(x90(o.matrix_world) for o in parts.values())}
metrics={'collection_snapshot_before_readback':col_snapshot,'v2_collection_objects':v2col}
if v2map and before_mesh:
    bm=snapshot(before_mesh[0]);dc=dn=0
    for rid in set(bm)&set(v2map):
        for a,b in zip(bm[rid]['co'],v2map[rid]['co']):dc=max(dc,(Vector(a)-Vector(b)).length)
        for a,b in zip(bm[rid]['n'],v2map[rid]['n']):dn=max(dn,(Vector(a)-Vector(b)).length)
    checks['before_v2_raw_faces_match_v2_baseline']=set(bm)==set(v2map);checks['before_v2_geometry_and_corner_normals_unchanged']=dc<=1e-7 and dn<=1e-7;metrics.update({'before_v2_raw_face_count':len(bm),'before_v2_max_coordinate_delta':dc,'before_v2_max_corner_normal_delta':dn})
else:checks['before_v2_raw_faces_match_v2_baseline']=False;checks['before_v2_geometry_and_corner_normals_unchanged']=False
retained={};cnt=Counter();kindcnt=Counter()
for ob in after_mesh:
    raw=ob.data.attributes.get('raw_obj_face_index');kind=ob.data.attributes.get('surface_kind')
    if raw and kind:
        for p in ob.data.polygons:
            rid=int(raw.data[p.index].value);k=int(kind.data[p.index].value);kindcnt[k]+=1
            if rid>=0:cnt[rid]+=1;retained[rid]=(ob,p)
expected=set(v2map or set())-CAPS;checks['all_retained_v2_faces_present_once_except_40_approved_caps']=set(retained)==expected and all(n==1 for n in cnt.values()) and len(CAPS)==40;checks['only_approved_caps_absent_from_v2']=set(v2map or set())-set(retained)==CAPS
dc=dn=0;loopbad=[]
for rid,(ob,p) in retained.items():
    s=v2map[rid];q=[tuple(ob.data.vertices[i].co) for i in p.vertices];n=[tuple(ob.data.corner_normals[i].vector) for i in p.loop_indices]
    if len(q)!=len(s['co']):loopbad.append(rid);continue
    for a,b in zip(q,s['co']):dc=max(dc,(Vector(a)-Vector(b)).length)
    for a,b in zip(n,s['n']):dn=max(dn,(Vector(a)-Vector(b)).length)
checks['retained_source_coordinates_exact']=not loopbad and dc<=.002;checks['retained_source_custom_corner_normals_within_002']=not loopbad and dn<=.002
details=parts.get('Preserved_Unclassified_Source_Details');dids=[]
if details:
    raw=details.data.attributes.get('raw_obj_face_index');dids=[int(raw.data[p.index].value) for p in details.data.polygons] if raw else []
checks['all_90_unclassified_source_faces_preserved']=len(dids)==90 and all(x>=0 for x in dids) and len(set(dids))==90
checks['new_faces_do_not_spoof_source_ids']=all(int(o.data.attributes['raw_obj_face_index'].data[p.index].value)==-1 for o in after_mesh for p in o.data.polygons if int(o.data.attributes['surface_kind'].data[p.index].value) in (1,2,3,4,5,6))
metrics.update({'retained_raw_face_count':len(retained),'expected_retained_raw_face_count':len(expected),'missing_retained_raw_ids':sorted(expected-set(retained)),'unexpected_retained_raw_ids':sorted(set(retained)-expected),'duplicate_retained_raw_ids':sorted(k for k,z in cnt.items() if z!=1),'retained_max_coordinate_delta':dc,'retained_max_corner_normal_delta':dn,'loop_mismatch_raw_ids':loopbad,'surface_kind_face_counts':dict(kindcnt),'unclassified_detail_raw_ids':dids})
robe=parts.get('Robe_Outer_Inner_Rims')
if robe:
    me=robe.data;k=me.attributes['surface_kind'].data;outer=[p for p in me.polygons if int(k[p.index].value) in (0,4)];inner=[p for p in me.polygons if int(k[p.index].value)==1];rim=[p for p in me.polygons if int(k[p.index].value)==2];top=edges(me,me.polygons);comps=components(me.polygons);deg=[p.index for p in me.polygons if p.area<=1e-12];ot=tris(me,lambda p:int(k[p.index].value) in (0,4));it=tris(me,lambda p:int(k[p.index].value)==1);raw=me.attributes['raw_obj_face_index'].data;parent=me.attributes['parent_raw_face_index'].data;oh=Counter(int(raw[t['poly']].value) for t in ot);ih=Counter(int(parent[t['poly']].value) for t in it);inout=bvh(ot,it)
    checks['robe_tissue_closed_manifold_no_boundary_or_nonmanifold_edges']=top['boundary_edges']==0 and top['nonmanifold_edges']==0;checks['robe_outer_inner_rim_single_connected_tissue']=comps==1 and bool(outer) and bool(inner) and bool(rim);checks['robe_has_no_degenerate_faces']=not deg;checks['inner_matches_outer_exact_triangle_parent_histogram']=len(ot)==len(it) and oh==ih;checks['inner_vs_outer_bvh_has_no_triangle_intersections']=inout['pair_count']==0
    metrics['robe']={'outer_faces':len(outer),'inner_faces':len(inner),'rim_faces':len(rim),'topology':top,'face_components':comps,'degenerate_face_ids':deg,'outer_triangle_count':len(ot),'inner_triangle_count':len(it),'inner_parent_histogram_matches':oh==ih,'inner_vs_outer_bvh':inout}
else:
    for n in ('robe_tissue_closed_manifold_no_boundary_or_nonmanifold_edges','robe_outer_inner_rim_single_connected_tissue','robe_has_no_degenerate_faces','inner_matches_outer_exact_triangle_parent_histogram','inner_vs_outer_bvh_has_no_triangle_intersections'):checks[n]=False
body=parts.get('Body_Base_Separate_From_Clothes')
if body and robe:
    bk=body.data.attributes['surface_kind'].data;bp=tris(body.data,lambda p:int(bk[p.index].value) in (3,5,6));ot=tris(robe.data,lambda p:int(robe.data.attributes['surface_kind'].data[p.index].value) in (0,4));prox=bvh(bp,ot);checks['body_proxy_vs_robe_outer_bvh_has_no_triangle_intersections']=prox['pair_count']==0;by={z:tris(body.data,lambda p,z=z:int(bk[p.index].value)==z) for z in (3,5,6)};metrics['body_proxy']={'kind_triangle_counts':{str(z):len(q) for z,q in by.items()},'vs_robe_outer_bvh':prox,'inter_proxy_bvh_documentation':{f'{a}_vs_{b}':bvh(by[a],by[b]) for a,b in ((3,5),(3,6),(5,6))},'limit':'Shoulder/hip proxy overlap remains provisional; not animation-ready or final retopology.'}
else:checks['body_proxy_vs_robe_outer_bvh_has_no_triangle_intersections']=False
expecteduv={'Hair_Main':30,'Robe_Outer_Inner_Rims':16,'Body_Base_Separate_From_Clothes':47,'Preserved_Unclassified_Source_Details':46};uva={n:uvaudit(parts[n].data) for n in PARTS if n in parts};checks['all_parts_have_actual_uv_layer']=len(uva)==4 and all(not q['missing_uv'] for q in uva.values());checks['uv_island_counts_match_structural_trial']=all(uva.get(n,{}).get('islands')==z for n,z in expecteduv.items());checks['uv_all_parts_within_independent_unit_tiles']=all(q.get('outside_unit_square')==0 for q in uva.values());checks['uv_no_zero_area_triangles']=all(not q.get('zero_area_triangle_parent_faces') for q in uva.values());checks['uv_no_positive_triangle_overlap_per_part']=all(q.get('positive_overlap_pair_count')==0 for q in uva.values());metrics['uv_trial_independent']=uva
data=GLB.read_bytes();magic,version,total=struct.unpack_from('<4sII',data);length,kind=struct.unpack_from('<II',data,12);gltf=json.loads(data[20:20+length]);checks['glb_is_valid_v2_and_has_four_meshes']=magic==b'glTF' and version==2 and total==len(data) and kind==0x4E4F534A and len(gltf.get('meshes',[]))==4;checks['glb_excludes_cameras_lights_skins_animations']=not gltf.get('cameras') and not gltf.get('skins') and not gltf.get('animations') and not gltf.get('lights')
result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'failed_checks':fail(checks),'metrics':metrics,'artifact_sha256':{'v2_blend':sha(V2/'model/protagonist_cn_cleanup_v2.blend'),'raw_source_obj':sha(RAW) if RAW.exists() else None,'v3_blend':sha(BLEND),'v3_glb':sha(GLB)},'test_scope':{'file_side':'hashes, saved blend/GLB readback, source retention, topology, BVH collision, exact UV triangle overlap.','runtime_not_tested':'No rigging, animation, Godot import/runtime, final texture painting, or game camera acceptance.','visual_not_yet_scored':'Five matched QA captures and technical cuff/underhem/checker images require separate image review after capture freeze.'}}
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result['status'],len(checks)-len(result['failed_checks']),'/',len(checks),result['failed_checks']);assert all(checks.values()),result['failed_checks']
