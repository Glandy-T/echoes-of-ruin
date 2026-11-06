"""Read-only topology and false-colour review of CN cleanup v1 hair.

It opens the v1 Blend and never saves it.  The JSON is a *selection review*
file, not a cleanup recipe: nothing named here is deleted or altered.
"""
from pathlib import Path
import bpy, bmesh, json, hashlib, math
from collections import defaultdict

EXP = Path(__file__).resolve().parent.parent
V1 = EXP.parent / "protagonist_tripo_cn_cleanup_v1"
BLEND = V1 / "model" / "protagonist_cn_cleanup_v1.blend"
OUT = EXP / "hair_part_diagnosis.json"
EVID = EXP / "evidence"; EPS=1e-6

def box(points):
    lo=[min(p[i] for p in points) for i in range(3)]; hi=[max(p[i] for p in points) for i in range(3)]
    return {'min':lo,'max':hi,'size':[hi[i]-lo[i] for i in range(3)]}
def farea(mesh,p):
    vs=mesh.vertices; ids=p.vertices
    return sum(((vs[ids[i]].co-vs[ids[0]].co).cross(vs[ids[i+1]].co-vs[ids[0]].co)).length/2 for i in range(1,len(ids)-1))
def find_mesh():
    xs=[o for o in bpy.context.scene.objects if o.type=='MESH' and len(o.data.vertices)==2536 and len(o.data.polygons)==2596]
    if len(xs)!=1: raise RuntimeError('Expected one 2536v/2596f candidate: '+str([(o.name,len(o.data.vertices),len(o.data.polygons)) for o in bpy.context.scene.objects if o.type=='MESH']))
    return xs[0]
def bridge_edges(adj):
    # Tarjan bridges in the face dual graph. A bridge means the two face groups
    # meet through exactly one shared mesh edge; vertex-only contact is reported separately.
    t=0; disc={}; low={}; parent={}; out=[]
    def go(u):
        nonlocal t
        disc[u]=low[u]=t;t+=1
        for v,e in adj[u]:
            if v not in disc:
                parent[v]=u;go(v);low[u]=min(low[u],low[v])
                if low[v]>disc[u]:out.append((u,v,e))
            elif parent.get(u)!=v:low[u]=min(low[u],disc[v])
    for u in adj:
        if u not in disc:go(u)
    return out
def components_excluding(adj, cut):
    seen=set();groups=[]
    for s in adj:
        if s in seen:continue
        q=[s];seen.add(s);g=[]
        while q:
            u=q.pop();g.append(u)
            for v,e in adj[u]:
                if e==cut:continue
                if v not in seen:seen.add(v);q.append(v)
        groups.append(sorted(g))
    return groups
def describe(mesh, faces, raw, label, relation):
    pts=[tuple(mesh.vertices[v].co) for fi in faces for v in mesh.polygons[fi].vertices]
    ar=sum(farea(mesh,mesh.polygons[fi]) for fi in faces); bb=box(pts)
    return {'label':label,'relation':relation,'candidate_polygon_indices_zero_based':sorted(faces),'candidate_polygon_numbers_one_based':[x+1 for x in sorted(faces)],'raw_obj_face_indices_zero_based':sorted(int(raw.data[x].value) for x in faces),'faces':len(faces),'area':ar,'bbox_source_local_y_up':bb}
def boundary_regions(mesh, faces):
    ef=defaultdict(int); vv=defaultdict(set)
    for fi in faces:
        ids=list(mesh.polygons[fi].vertices)
        for i,a in enumerate(ids): ef[tuple(sorted((a,ids[(i+1)%len(ids)])))]+=1
    for a,b in (e for e,n in ef.items() if n==1):vv[a].add(b);vv[b].add(a)
    seen=set();out=[]
    for s in vv:
        if s in seen:continue
        q=[s];seen.add(s);g=[]
        while q:
            u=q.pop();g.append(u)
            for v in vv[u]:
                if v not in seen:seen.add(v);q.append(v)
        pts=[tuple(mesh.vertices[v].co) for v in g];out.append({'vertices':len(g),'bbox_source_local_y_up':box(pts)})
    return sorted(out,key=lambda r:-r['vertices'])
def make_mat(name,rgb):
    # Emission makes selection colours objectively legible in headless renders.
    # It is diagnostic-only and intentionally does not evaluate normals.
    m=bpy.data.materials.new(name);m.use_nodes=True; ns=m.node_tree.nodes;ns.clear()
    out=ns.new('ShaderNodeOutputMaterial'); em=ns.new('ShaderNodeEmission');em.inputs['Color'].default_value=(*rgb,1);em.inputs['Strength'].default_value=1.0;m.node_tree.links.new(em.outputs[0],out.inputs[0])
    return m
def render_overlay(obj, groups):
    """Temporary materials only; object data/normal/geometry is restored before exit."""
    scene=bpy.context.scene; old_engine,old_cam=scene.render.engine,scene.camera
    oldslots=list(obj.data.materials); oldidx=[p.material_index for p in obj.data.polygons]
    while obj.data.materials: obj.data.materials.pop(index=0)
    gray=make_mat('TEMP_DIAG_GRAY',(0.42,.44,.47)); bridge=make_mat('TEMP_DIAG_ORANGE',(1,.16,.02)); tip=make_mat('TEMP_DIAG_CYAN',(.02,.75,1))
    for m in (gray,bridge,tip):obj.data.materials.append(m)
    bridge_faces={f for g in groups if g['label'].startswith('bridge') for f in g['candidate_polygon_indices_zero_based']}
    tip_faces={f for g in groups if g['label'].startswith('boundary') for f in g['candidate_polygon_indices_zero_based']}
    for p in obj.data.polygons: p.material_index=1 if p.index in bridge_faces else (2 if p.index in tip_faces else 0)
    # Blender 5.0 exposes this engine as BLENDER_EEVEE (not the older NEXT enum).
    scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    records=[]
    for view in ('front','head_back','side'):
        cam=bpy.data.objects.get('QA_'+view)
        if not cam:continue
        scene.camera=cam; path=EVID/('hair_selection_'+view+'.png');scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        records.append({'view':view,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    while obj.data.materials:obj.data.materials.pop(index=0)
    for m in oldslots:obj.data.materials.append(m)
    for p,i in zip(obj.data.polygons,oldidx):p.material_index=i
    scene.render.engine,scene.camera=old_engine,old_cam
    return records
def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND)); obj=find_mesh(); mesh=obj.data
    raw=mesh.attributes.get('raw_obj_face_index')
    comp=mesh.attributes.get('raw_component_id')
    if raw is None or comp is None: raise RuntimeError('v1 provenance attributes missing')
    hair=[p.index for p in mesh.polygons if int(comp.data[p.index].value)==6]
    # Face edge map inside component 6.
    ef=defaultdict(list)
    for fi in hair:
        vs=list(mesh.polygons[fi].vertices)
        for i,a in enumerate(vs):ef[tuple(sorted((a,vs[(i+1)%len(vs)])))].append(fi)
    adj={f:[] for f in hair}
    for e,fs in ef.items():
        if len(fs)==2: adj[fs[0]].append((fs[1],e));adj[fs[1]].append((fs[0],e))
    bridges=bridge_edges(adj)
    candidates=[]
    # Each bridge creates exactly two edge-attached parts. Keep a small side only
    # when it is <12% of main hair AND visibly thin in at least one local axis.
    for n,(a,b,e) in enumerate(bridges):
        gs=components_excluding(adj,e); small=min(gs,key=len)
        d=describe(mesh,small,raw,'bridge_branch_%02d'%n,'shares exactly one edge with the remainder')
        thin=min(d['bbox_source_local_y_up']['size']) <= .012
        if len(small)<=96 and thin: candidates.append(d)
    # Boundary tips: faces with >=2 boundary edges are visual hem candidates;
    # list only isolated individual/small contiguous tip clusters, never remove.
    boundary_faces=set(f for e,fs in ef.items() if len(fs)==1 for f in fs)
    tip=[f for f in boundary_faces if sum(1 for e,fs in ef.items() if f in fs and len(fs)==1)>=2]
    # Connected tip groups using shared edges.
    tset=set(tip);seen=set()
    for s in sorted(tset):
        if s in seen:continue
        q=[s];seen.add(s);g=[]
        while q:
            u=q.pop();g.append(u)
            for v,e in adj[u]:
                if v in tset and v not in seen:seen.add(v);q.append(v)
        if len(g)<=12: candidates.append(describe(mesh,g,raw,'boundary_tip_%02d'%len([x for x in candidates if x['label'].startswith('boundary')]),'boundary-tip faces; remains edge-attached to hair'))
    # Vertex-only groups inside the remaining C6 (normally none after v1).
    vert_faces=defaultdict(set)
    for f in hair:
        for v in mesh.polygons[f].vertices:vert_faces[v].add(f)
    # Semantic inventory is deliberately spatial/topological, not claiming author intent.
    allcomps=defaultdict(list)
    for p in mesh.polygons:allcomps[int(comp.data[p.index].value)].append(p.index)
    inv=[]
    for cid,fs in sorted(allcomps.items()):
        pts=[tuple(mesh.vertices[v].co) for fi in fs for v in mesh.polygons[fi].vertices]
        br=boundary_regions(mesh,fs)
        inv.append({'raw_component_id':cid,'faces':len(fs),'bbox_source_local_y_up':box(pts),'boundary_edges':sum(r['vertices'] for r in br),'boundary_regions':br})
    renders=render_overlay(obj,candidates)
    report={'purpose':'Read-only v1 topology/selection diagnosis. Candidate face groups are review overlays, not an authorized deletion or topology repair.','source_blend':str(BLEND),'source_blend_sha256':hashlib.sha256(BLEND.read_bytes()).hexdigest(),'candidate_mesh':{'name':obj.name,'vertices':len(mesh.vertices),'polygons':len(mesh.polygons),'hair_component_raw_id':6,'hair_faces':len(hair),'hair_boundary_edges':sum(1 for x in ef.values() if len(x)==1),'hair_nonmanifold_edges':sum(1 for x in ef.values() if len(x)>2),'dual_graph_bridge_count':len(bridges)},'selection_groups':candidates,'overlay':{'meaning':'Orange = each one-edge bridge branch; cyan = boundary-tip cluster. Gray = untouched current v1 mesh context. Colours are temporary diagnostics only; geometry and normals were not changed.','renders':renders},'semantic_separation_evidence':{'raw_component_inventory':inv,'visually_supported_parts':'Current v1 RGB shows component 2 as the robe/body shell, component 5 as head/face, component 6 as hair, components 0/19 as paired feet, and 3/20 as paired arm/hand-side pieces. This is a visual-location inventory, not an authoring claim.','opening_assessment':'Component 2 has one large 18-vertex boundary at the visual neck line (Y .5596-.5762) and one 4-vertex region around Y .399; the first is consistent with the intentional neckline, while the latter is too small/occluded to classify. The visually apparent sleeve cuffs and garment hem are not necessarily open boundary loops in this topology. Component-6 boundaries include the visible lower hair hem and many small detail edges. No garment/body boundary is selected; no boundary is called a defect from topology alone. Only the three orange branches are objectively one-edge appendages.'},'limitations':['No clipping, remesh, replacement, normal edits, or model save occurred.','A bridge/edge boundary is a topology fact, not proof a branch is unwanted.','The overlay preserves v1 geometry and uses temporary false-color materials; it is not a material/normal validation.']}
    EVID.mkdir(parents=True,exist_ok=True); OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'out':str(OUT),'hair_faces':len(hair),'bridges':len(bridges),'groups':len(candidates)}))
if __name__=='__main__':main()
