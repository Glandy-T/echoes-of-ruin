"""Independent read-only topology, opening, and exact self-intersection QA."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib,json
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

EXP=Path(__file__).resolve().parents[1];RAW=EXP/'model/protagonist_tripo_robe_v2_raw.glb';OBJ=EXP/'model/protagonist_tripo_robe_v2_raw.obj';INSPECTION=EXP/'model/protagonist_robe_v2_inspection.blend';OUT=EXP/'source/robe_topology_check.json';SVG=EXP/'evidence/independent_boundary_loops.svg'
GLB_HASH='f37e04f2760ef710de31635c035ff4dbe9c3c54381d43a19c1b739ef325c63b7';OBJ_HASH='daf2747947c55780b4155fa4995d802eef0473d75ff6574763e8d616e7f34a09';EPS=1e-8;POINT=2e-7;AREA=1e-13
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def vec(x):return [float(v) for v in x]
def area2(q):return abs(sum(q[i][0]*q[(i+1)%len(q)][1]-q[i][1]*q[(i+1)%len(q)][0] for i in range(len(q))))*.5 if len(q)>=3 else 0
def clip2(s,c):
    def sign(q):return sum(q[i][0]*q[(i+1)%len(q)][1]-q[i][1]*q[(i+1)%len(q)][0] for i in range(len(q)))
    out=list(s) if sign(s)>=0 else list(reversed(s));c=list(c) if sign(c)>=0 else list(reversed(c))
    for a,b in zip(c,c[1:]+c[:1]):
        old=out;out=[]
        if not old:break
        p=old[-1];ps=(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        for q in old:
            qs=(b[0]-a[0])*(q[1]-a[1])-(b[1]-a[1])*(q[0]-a[0]);pin=ps>=-EPS;qin=qs>=-EPS
            if pin!=qin:
                d=ps-qs
                if abs(d)>1e-30:
                    t=ps/d;out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
            if qin:out.append(q)
            p,ps=q,qs
    return out
def segtri(p0,p1,t):
    a,b,c=t;d=p1-p0;e1=b-a;e2=c-a;h=d.cross(e2);det=e1.dot(h)
    if abs(det)<=EPS:return None
    inv=1/det;s=p0-a;u=inv*s.dot(h);q=s.cross(e1);w=inv*d.dot(q);z=inv*e2.dot(q)
    if u<-EPS or w<-EPS or u+w>1+EPS or z<-EPS or z>1+EPS:return None
    return p0+d*z,(u>EPS and w>EPS and u+w<1-EPS and z>EPS and z<1-EPS)
def exact(a,b):
    na=(a[1]-a[0]).cross(a[2]-a[0]);nb=(b[1]-b[0]).cross(b[2]-b[0])
    if na.length<=EPS or nb.length<=EPS:return ('degenerate',[])
    n=na.normalized();m=nb.normalized()
    if abs(abs(n.dot(m))-1)<=2e-6 and max(abs(n.dot(p-a[0])) for p in b)<=POINT:
        drop=max(range(3),key=lambda i:abs(n[i]));aa=[tuple(p[i] for i in range(3) if i!=drop) for p in a];bb=[tuple(p[i] for i in range(3) if i!=drop) for p in b];return ('coplanar_overlap' if area2(clip2(aa,bb))>AREA else 'coplanar_touch_or_disjoint',[])
    hits=[];strict=False
    for t,o in ((a,b),(b,a)):
        for p,q in zip(t,t[1:]+t[:1]):
            r=segtri(p,q,o)
            if r and not any((r[0]-x).length<=POINT for x in hits):hits.append(r[0]);strict=strict or r[1]
    if len(hits)>=2 and max((p-q).length for p in hits for q in hits)>POINT:return ('proper_crossing' if strict else 'edge_crossing',hits)
    return ('point_touch' if hits else 'disjoint',hits)
def edge_data(me):
    uses=Counter();faces=defaultdict(list)
    for p in me.polygons:
        vs=list(p.vertices)
        for a,b in zip(vs,vs[1:]+vs[:1]):k=tuple(sorted((a,b)));uses[k]+=1;faces[k].append(p.index)
    return uses,faces
def component_count(me,uses):
    parent=list(range(len(me.vertices)))
    def find(x):
        while x!=parent[x]:parent[x]=parent[parent[x]];x=parent[x]
        return x
    for a,b in uses:
        a,b=find(a),find(b)
        if a!=b:parent[b]=a
    groups=Counter(find(i) for i in range(len(me.vertices)))
    return len(groups),sorted(groups.values(),reverse=True)
def boundary_components(me,uses):
    adj=defaultdict(set)
    for a,b in (k for k,n in uses.items() if n==1):adj[a].add(b);adj[b].add(a)
    left=set(adj);out=[]
    while left:
        start=next(iter(left));stack=[start];vs=set()
        while stack:
            x=stack.pop()
            if x in vs:continue
            vs.add(x);left.discard(x);stack.extend(adj[x]-vs)
        es=[(a,b) for a,b in uses if a in vs and b in vs and uses[(a,b)]==1];pts=[me.vertices[i].co for i in vs];center=sum(pts,Vector())/len(pts)
        out.append({'vertices':len(vs),'edges':len(es),'closed_simple_ring':all(len(adj[x])==2 for x in vs),'center':vec(center),'bounds':{'min':vec((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts))),'max':vec((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))},'vertex_ids':sorted(vs)})
    return out,adj
def selfcheck(me,world):
    me.calc_loop_triangles();rows=[]
    for i,t in enumerate(me.loop_triangles):
        co=[world@me.vertices[x].co for x in t.vertices];rows.append((i,t.polygon_index,tuple(t.vertices),co))
    co=[p for _,_,_,q in rows for p in q];fac=[(3*i,3*i+1,3*i+2) for i in range(len(rows))];pairs=BVHTree.FromPolygons(co,fac,all_triangles=True).overlap(BVHTree.FromPolygons(co,fac,all_triangles=True));pairs=sorted({tuple(sorted(p)) for p in pairs if p[0]!=p[1]});counts=Counter();true=[]
    for ai,bi in pairs:
        a,b=rows[ai],rows[bi]
        if set(a[2])&set(b[2]):counts['excluded_shared_vertex_neighbor']+=1;continue
        kind,points=exact(a[3],b[3]);counts[kind]+=1
        if kind in ('proper_crossing','edge_crossing','coplanar_overlap'):
            pos=sum(points,Vector())/len(points) if points else (sum(a[3],Vector())+sum(b[3],Vector()))/6;true.append({'triangle_a':a[0],'triangle_b':b[0],'polygon_a':a[1],'polygon_b':b[1],'vertices_a':list(a[2]),'vertices_b':list(b[2]),'kind':kind,'position_world':vec(pos),'intersection_points':[vec(x) for x in points]})
    return {'bvh_candidate_pair_count':len(pairs),'classification_counts':dict(counts),'true_nonadjacent_intersection_count':len(true),'true_nonadjacent_intersections_sample':true[:100],'method':'BVH broad-phase then exact segment/coplanar classifier; shared-vertex neighbors excluded; point-touch and coplanar edge contact are not crossings.'}
def probe(bvh,origin,direction,span=.08):
    hit=bvh.ray_cast(Vector(origin),Vector(direction),span);return {'origin':vec(origin),'direction':vec(direction),'first_hit_distance':float(hit[3]) if hit[0] is not None else None,'first_hit_polygon':int(hit[2]) if hit[0] is not None else None}
def opening_probes(me,world):
    me.calc_loop_triangles();co=[world@me.vertices[x].co for t in me.loop_triangles for x in t.vertices];fa=[(3*i,3*i+1,3*i+2) for i in range(len(me.loop_triangles))];bvh=BVHTree.FromPolygons(co,fa,all_triangles=True)
    # A true mouth admits at least one central short ray without an immediate cap hit.
    sets={'neck':[probe(bvh,(x,y,1.04),(0,0,-1)) for x in (-.018,0,.018) for y in (-.018,0,.018)],'hem':[probe(bvh,(x,y,-.04),(0,0,1)) for x in (-.05,0,.05) for y in (-.05,0,.05)],'cuff_negative_y':[probe(bvh,(x,-.36,z),(0,1,0)) for x in (-.018,0,.018) for z in (.46,.50,.54)],'cuff_positive_y':[probe(bvh,(x,.36,z),(0,-1,0)) for x in (-.018,0,.018) for z in (.46,.50,.54)]}
    out={}
    for name,rows in sets.items():
        # A no-hit within 0.08 means this exterior-to-interior centerline was not capped immediately.
        out[name]={'rays':rows,'uncapped_centerline_rays':sum(r['first_hit_distance'] is None for r in rows),'immediate_cap_hits_under_002':sum(r['first_hit_distance'] is not None and r['first_hit_distance']<.02 for r in rows)}
    return out
def write_svg(me,components):
    # Front (+X) projection of actual boundary edges only. Empty sleeves/hem here are meaningful: solid-shell mouths may have zero boundary edges.
    w,h=720,720; scale=1500;cx,cy=360,650
    paths=[]
    for c in components:
        ids=c['vertex_ids'];pts=[me.vertices[i].co for i in ids];d=' '.join(f'{cx-p.y*scale:.1f},{cy-p.z*scale:.1f}' for p in pts);paths.append(f'<polyline points="{d}" fill="none" stroke="#e35d4f" stroke-width="2"/>')
    SVG.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="100%" height="100%" fill="#202a2f"/><text x="20" y="30" fill="white" font-size="18">Raw GLB boundary edges only, front projection (+X)</text><text x="20" y="55" fill="#d0d0d0" font-size="14">Solid-shell mouths can be zero-boundary; use JSON ray probes for opening status.</text>{"".join(paths)}</svg>',encoding='utf-8')
def render_underhem():
    scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.62,.65,.65);scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('Independent QA background');scene.world.color=(.04,.05,.06);scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
    data=bpy.data.cameras.new('Independent_underhem_QA');cam=bpy.data.objects.new('Independent_underhem_QA',data);scene.collection.objects.link(cam);target=Vector((0,0,.13));cam.location=(.34,-.34,-.16);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=.43;scene.camera=cam;scene.render.filepath=str(EXP/'evidence/independent_underhem_opening.png');bpy.ops.render.render(write_still=True);return {'file':'evidence/independent_underhem_opening.png','camera_location':vec(cam.location),'camera_target':vec(target),'scope':'Technical underhem opening view only; camera is not saved into inspection blend.'}

before={'glb':sha(RAW),'obj':sha(OBJ),'inspection_blend':sha(INSPECTION)}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(RAW));obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];checks={'raw_glb_hash_unchanged':before['glb']==GLB_HASH,'raw_obj_hash_unchanged':before['obj']==OBJ_HASH,'one_glb_mesh':len(obs)==1}
if obs:
    ob=obs[0];bpy.context.view_layer.objects.active=ob;me=ob.data;me.calc_loop_triangles();uses,faces=edge_data(me);components,adj=boundary_components(me,uses);non=[{'edge':list(e),'face_count':n,'faces':faces[e],'midpoint':vec((me.vertices[e[0]].co+me.vertices[e[1]].co)/2)} for e,n in uses.items() if n>2];probes=opening_probes(me,ob.matrix_world);inter=selfcheck(me,ob.matrix_world);write_svg(me,components);underhem=render_underhem();component_total,component_sizes=component_count(me,uses)
    stats={'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'connected_components':component_total,'component_vertex_counts_descending':component_sizes,'boundary_edges':sum(n==1 for n in uses.values()),'nonmanifold_edges':len(non),'degenerate_faces':sum(p.area<=1e-12 for p in me.polygons),'uv_layers':len(me.uv_layers),'vertex_groups':len(ob.vertex_groups),'shape_keys':bool(me.shape_keys),'armature_modifiers':sum(m.type=='ARMATURE' for m in ob.modifiers)}
    checks['glb_single_connected_mesh']=stats['vertices']==2020 and stats['triangles']==4049 and stats['connected_components']==1;checks['no_degenerate_faces']=stats['degenerate_faces']==0;checks['no_nonmanifold_edges']=stats['nonmanifold_edges']==0;checks['openings_have_uncapped_centerline_evidence']=all(v['uncapped_centerline_rays']>0 for v in probes.values());checks['no_true_nonadjacent_self_intersections']=inter['true_nonadjacent_intersection_count']==0
else:stats={};components=[];non=[];probes={};inter={};underhem=None;checks.update({'glb_single_connected_mesh':False,'no_degenerate_faces':False,'no_nonmanifold_edges':False,'openings_have_uncapped_centerline_evidence':False,'no_true_nonadjacent_self_intersections':False})
after={'glb':sha(RAW),'obj':sha(OBJ),'inspection_blend':sha(INSPECTION)};checks['raw_and_inspection_files_unchanged_during_readback']=before==after
result={'status':'PASS_STATIC_ROBE_CANDIDATE' if all(checks.values()) else 'FAIL_STATIC_ROBE_CANDIDATE','checks':checks,'failed_checks':[k for k,v in checks.items() if not v],'artifact_sha256_before':before,'artifact_sha256_after':after,'topology':stats,'boundary_components':components,'nonmanifold_edges':non,'opening_ray_probes':probes,'self_intersection_audit':inter,'evidence':{'actual_boundary_edge_projection':'evidence/independent_boundary_loops.svg','underhem_technical_render':underhem},'scope':{'static_checked':'raw hashes, mesh counts/connectivity, boundary components, opening centerline ray probes, nonmanifold locations, exact non-neighbor self-intersections.','not_tested':'Rigging, skin weights, deformation/animation, UV/texture readiness, body fit, Godot import, and final art approval.'},'verdict':'Static garment candidate only. Passing opening probes or zero crossings would not establish animation-ready clothing.'}
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(result['status'],result['failed_checks'])
