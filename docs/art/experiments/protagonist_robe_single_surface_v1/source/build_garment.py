"""Build the approved clean, one-surface robe study; no AI shell geometry is reused."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib, json, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

EXP = Path(__file__).resolve().parents[1]
RAW = EXP.parent / 'protagonist_tripo_robe_v2' / 'model' / 'protagonist_tripo_robe_v2_raw.glb'
OUT_BLEND = EXP / 'model' / 'robe_single_surface.blend'
OUT_GLB = EXP / 'model' / 'robe_single_surface.glb'
OUT_REPORT = EXP / 'source' / 'garment_build_report.json'
RAW_SHA256 = 'f37e04f2760ef710de31635c035ff4dbe9c3c54381d43a19c1b739ef325c63b7'
EPS = 1e-8

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def edge_uses(faces):
    uses = Counter()
    for f in faces:
        for a, b in zip(f, f[1:] + f[:1]): uses[tuple(sorted((a, b)))] += 1
    return uses

def loops_from_boundary(faces):
    uses = edge_uses(faces); adj = defaultdict(set)
    for (a, b), n in uses.items():
        if n == 1: adj[a].add(b); adj[b].add(a)
    left = set(adj); loops = []
    while left:
        start = next(iter(left)); order = [start]; prev = None; cur = start
        while True:
            nxts = [x for x in adj[cur] if x != prev]
            nxt = nxts[0] if nxts else None
            if nxt == start: break
            if nxt is None or nxt in order: raise RuntimeError('boundary is not a simple loop')
            order.append(nxt); prev, cur = cur, nxt
        for x in order: left.discard(x)
        loops.append(order)
    return loops

def component_count(vertex_count, uses):
    parent=list(range(vertex_count))
    def find(x):
        while x != parent[x]: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    for a,b in uses:
        a,b=find(a),find(b)
        if a != b: parent[b]=a
    return len({find(i) for i in range(vertex_count)})

def ray_fitted_radius(bvh, z, theta, fallback):
    # Raw is immutable and is used only as a silhouette measurement.  We cast outward
    # from its central cavity after undoing the approved .74 / +.11 placement.
    raw_z = (z - .11) / .74
    direction = Vector((math.cos(theta), math.sin(theta), 0))
    hit = bvh.ray_cast(Vector((0, 0, raw_z)), direction, 1.0)
    if hit[0] is None: return fallback, False
    radius = hit[3] * .74
    # Sleeve hits and accidental far walls are intentionally not allowed to widen torso.
    if radius < .055 or radius > .145: return fallback, False
    return radius, True

def raw_envelope():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(RAW))
    raw = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    me = raw.data; me.calc_loop_triangles()
    verts = [raw.matrix_world @ v.co for v in me.vertices]
    polys = [tuple(t.vertices) for t in me.loop_triangles]
    bvh = BVHTree.FromPolygons(verts, polys, all_triangles=True)
    return raw, bvh

def add_ring(verts, part, ring_u, points, part_id, u):
    ids = []
    for p in points:
        ids.append(len(verts)); verts.append(tuple(p)); part.append(part_id); ring_u.append(u)
    return ids

def connect(faces, a, b):
    assert len(a) == len(b)
    for i in range(len(a)): faces.append([a[i], a[(i + 1) % len(a)], b[(i + 1) % len(b)], b[i]])

def main():
    before = sha(RAW)
    if before != RAW_SHA256: raise RuntimeError('immutable raw robe hash mismatch')
    raw, bvh = raw_envelope()
    N = 32
    zs = [.12, .14, .20, .30, .42, .54, .64, .70, .74, .78, .81, .84]
    fallback = [.126, .128, .124, .118, .112, .108, .104, .101, .098, .094, .087, .052]
    verts=[]; faces=[]; part=[]; ring_u=[]; torso=[]; sample_hits=[]
    # Elliptical body rings retain the reference's gently flared lower silhouette.
    for j, z in enumerate(zs):
        ring=[]
        for i in range(N):
            th=2*math.pi*i/N; r, hit=ray_fitted_radius(bvh,z,th,fallback[j]) if z <= .70 else (fallback[j],False)
            # Upper torso tapers in X while retaining Y volume for the cloth shell.
            xscale = .75 if z > .70 else 1.0
            ring.append(len(verts)); verts.append((r*xscale*math.cos(th), r*math.sin(th), z)); part.append(0); ring_u.append(-1.0)
            sample_hits.append(hit)
        torso.append(ring)
    # Four columns x three vertical intervals gives exactly 14 edges per armhole.
    holes = {tuple(range(6,10)), tuple(range(22,26))}
    for j in range(len(zs)-1):
        for i in range(N):
            if j in (7,8,9) and any(i in h for h in holes): continue
            faces.append([torso[j][i],torso[j][(i+1)%N],torso[j+1][(i+1)%N],torso[j+1][i]])
    loops = loops_from_boundary(faces)
    hole_loops = [q for q in loops if len(q) == 14]
    if len(hole_loops) != 2: raise RuntimeError(f'expected two 14-edge armholes, got {[len(q) for q in loops]}')
    for boundary in hole_loops:
        mean_y = sum(verts[v][1] for v in boundary)/len(boundary); side = 1 if mean_y > 0 else -1
        center = Vector((0, side*.083, .755))
        # First ring is deliberately separated: no coincident faces at the torso port.
        bridge_ring = add_ring(verts,part,ring_u,[Vector(verts[v])+Vector((0,side*.018,0)) for v in boundary], 1 if side>0 else 2, 0.0)
        connect(faces, boundary, bridge_ring)
        # Boundary traversal, not independently measured polar angles, defines the
        # correspondence to the circular sleeve.  This avoids a corner's angle jump
        # twisting the quad strip through itself.
        angles=[math.atan2((Vector(verts[v]).z-center.z)/.064, (Vector(verts[v]).x-center.x)/.072) for v in boundary]
        previous = bridge_ring
        # Rings use a plane perpendicular to the shoulder-to-wrist centerline.
        guides=[((side*.118,.765),(.046,.055),.12), ((side*.136,.725),(.041,.050),.24),
                ((side*.148,.663),(.035,.040),.48), ((side*.174,.615),(.033,.036),.68),
                ((side*.198,.576),(.034,.035),.84), ((side*.216,.543),(.035,.035),1.0)]
        for gi, ((cy,cz),(rx,rv),u) in enumerate(guides):
            here=Vector((0,cy,cz))
            if gi < len(guides)-1: nxt=Vector((0,guides[gi+1][0][0],guides[gi+1][0][1]))
            else: nxt=here+(here-Vector((0,guides[gi-1][0][0],guides[gi-1][0][1])))
            axis=(nxt-here).normalized(); U=Vector((1,0,0)); V=Vector((0,side*abs(axis.z),abs(axis.y))).normalized()
            # Preserve port clearance while the rectangular opening resolves into
            # the perpendicular sleeve section: vertical at cap, blended at next.
            if gi == 0: V=Vector((0,0,1))
            elif gi == 1: V=(V*.45 + Vector((0,0,1))*.55).normalized()
            points=[here + U*(rx*math.cos(a)) + V*(rv*math.sin(a)) for a in angles]
            ring=add_ring(verts,part,ring_u,points,1 if side>0 else 2,u); connect(faces,previous,ring); previous=ring
    # Remove the measured raw object before saving: the output scene contains one garment mesh only.
    bpy.data.objects.remove(raw, do_unlink=True)
    # Remove all unused patch interior vertices before attributes/export.
    used=sorted({v for f in faces for v in f}); remap={old:new for new,old in enumerate(used)}
    verts=[verts[v] for v in used]; part=[part[v] for v in used]; ring_u=[ring_u[v] for v in used]
    faces=[[remap[v] for v in f] for f in faces]
    me=bpy.data.meshes.new('robe_single_surface_mesh'); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new('robe_single_surface',me); bpy.context.collection.objects.link(ob)
    attr=me.attributes.new('garment_part','INT','POINT'); [setattr(attr.data[i],'value',part[i]) for i in range(len(part))]
    attr=me.attributes.new('ring_u','FLOAT','POINT'); [setattr(attr.data[i],'value',ring_u[i]) for i in range(len(ring_u))]
    me.validate(clean_customdata=False); me.update(); me.calc_loop_triangles()
    uses=edge_uses(faces); boundaries=loops_from_boundary(faces)
    # The body_v1 exact classifier's shared-vertex policy is reproduced here via BVH.
    tri=[tuple(t.vertices) for t in me.loop_triangles]; co=[me.vertices[i].co.copy() for t in tri for i in t]
    bvh2=BVHTree.FromPolygons(co,[(3*i,3*i+1,3*i+2) for i in range(len(tri))],all_triangles=True)
    candidates={tuple(sorted(p)) for p in bvh2.overlap(bvh2) if p[0]!=p[1]}; nonadj=[p for p in candidates if not (set(tri[p[0]]) & set(tri[p[1]]))]
    # This construction is separated in 3D; candidate non-neighbors are exact-checked
    # by the copied classifier below before PASS is assigned.
    def segtri(p0,p1,t):
        a,b,c=t; d=p1-p0; e1=b-a; e2=c-a; h=d.cross(e2); det=e1.dot(h)
        if abs(det)<=EPS:return None
        inv=1/det;s=p0-a;u=inv*s.dot(h);q=s.cross(e1);w=inv*d.dot(q);z=inv*e2.dot(q)
        if u<-EPS or w<-EPS or u+w>1+EPS or z<-EPS or z>1+EPS:return None
        return p0+d*z
    crossings=[]
    for ai,bi in nonadj:
        aa=[me.vertices[i].co for i in tri[ai]]; bb=[me.vertices[i].co for i in tri[bi]]; hits=[]
        for t,o in ((aa,bb),(bb,aa)):
            for p,q in zip(t,t[1:]+t[:1]):
                h=segtri(p,q,o)
                if h is not None and not any((h-x).length<2e-7 for x in hits):hits.append(h)
        if len(hits)>=2 and max((a-b).length for a in hits for b in hits)>2e-7:
            crossings.append((ai,bi,tuple(float(v) for v in ((sum(hits,Vector())/len(hits))))))
    report={'status':'PASS_STATIC_CANDIDATE' if len(boundaries)==4 and not crossings else 'FAIL_STATIC_CANDIDATE',
      'source':{'raw_glb':str(RAW.relative_to(EXP.parents[3])),'raw_sha256_expected':RAW_SHA256,'raw_sha256_before':before,'raw_sha256_after':sha(RAW),'usage':'radial lower-torso silhouette measurements only; no raw vertices/faces copied'},
      'topology':{'vertices':len(me.vertices),'faces':len(me.polygons),'triangles':len(me.loop_triangles),'all_faces_quads':all(len(p.vertices)==4 for p in me.polygons),'connected_components':component_count(len(me.vertices),uses),'boundary_edges':sum(n==1 for n in uses.values()),'boundary_loops':[len(x) for x in boundaries],'nonmanifold_edges':sum(n>2 for n in uses.values()),'degenerate_faces':sum(p.area<=1e-12 for p in me.polygons),'bvh_nonadjacent_candidates':len(nonadj),'exact_nonadjacent_crossings':len(crossings),'crossing_samples':crossings[:25]},
      'attributes':{'garment_part':{'0':'torso','1':'positive_y_sleeve','2':'negative_y_sleeve'},'ring_u':'0 root to 1 cuff on sleeve vertices; torso is -1'},
      'construction':{'torso_rings':len(zs),'torso_ring_vertices':N,'armholes':'two 4-column by 3-interval ports, each 14 boundary edges before bridging','sleeve_rings_after_port':6,'openings_expected':['neck','hem','positive_y_cuff','negative_y_cuff'],'raw_radial_hits':sum(sample_hits),'raw_radial_samples':len(sample_hits)},
      'scope':'Static candidate only: no UVs, thickness, materials, skinning, body collision, animation, Godot import, or visual approval.'}
    OUT_REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    bpy.context.view_layer.objects.active=ob; ob.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    bpy.ops.export_scene.gltf(filepath=str(OUT_GLB),export_format='GLB',use_selection=True,export_materials='NONE')
    print(report['status'], report['topology'])

if __name__ == '__main__': main()
