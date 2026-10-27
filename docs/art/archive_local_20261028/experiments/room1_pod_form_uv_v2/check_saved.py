"""Read back saved model: geometry, active UV bounds/overlap, distortion metrics."""
import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'room1_pod_form_uv_v2.blend'))
scene=bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
objects=[bpy.data.objects[n] for n in ('Original_continuous_shell','ONE_RIGID_LID_with_head_window','Plain_interior_support')]
body,lid,bed=objects
results=[]
def check(name,passed,value=None):
    results.append({'check':name,'pass':bool(passed),'value':value})
points=[o.matrix_world@v.co for o in (body,lid) for v in o.data.vertices]
dimensions=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
check('closed external size 1.05 x 2.30 x 1.00 m',all(abs(a-b)<1e-5 for a,b in zip(dimensions,[1.05,2.30,1])),dimensions)
def cross(a,b):
    return a[0]*b[1]-a[1]*b[0]
def area(poly):
    return abs(sum(cross(poly[i],poly[(i+1)%len(poly)]) for i in range(len(poly)))/2) if len(poly)>2 else 0
def intersect_area(subject,clip):
    sign=1 if cross(clip[1]-clip[0],clip[2]-clip[0])>0 else -1
    for i in range(3):
        a,b=clip[i],clip[(i+1)%3]
        old=subject
        subject=[]
        if not old:
            return 0
        previous=old[-1]
        dp=sign*cross(b-a,previous-a)
        for current in old:
            dc=sign*cross(b-a,current-a)
            if (dc>=0)!=(dp>=0):
                subject.append(previous+(current-previous)*(dp/(dp-dc)))
            if dc>=0:
                subject.append(current)
            previous,dp=current,dc
    return area(subject)
stats={}
for obj in objects:
    mesh=obj.data
    bm=bmesh.new()
    bm.from_mesh(mesh)
    check(obj.name+' closed mesh',all(e.is_manifold for e in bm.edges))
    unseen=set(bm.verts)
    parts=0
    while unseen:
        parts+=1
        todo=[unseen.pop()]
        while todo:
            v=todo.pop()
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in unseen:
                    unseen.remove(other)
                    todo.append(other)
    bm.free()
    check(obj.name+' one connected component',parts==1,parts)
    layer=mesh.uv_layers.active
    check(obj.name+' active unique UV within 0-1',len(mesh.uv_layers)==1 and layer.active_render and all(-1e-5<=v<=1+1e-5 and math.isfinite(v) for p in layer.data for v in p.uv))
    mesh.calc_loop_triangles()
    triangles=[]
    distortions=[]
    bad_area=0
    for tri in mesh.loop_triangles:
        uv=[layer.data[i].uv.copy() for i in tri.loops]
        vs=[mesh.vertices[i].co for i in tri.vertices]
        e1,e2=vs[1]-vs[0],vs[2]-vs[0]
        d1,d2=uv[1]-uv[0],uv[2]-uv[0]
        physical_area=e1.cross(e2).length/2
        uarea=area(uv)
        if physical_area>1e-10 and uarea<1e-12:
            bad_area+=1
        if e1.length>1e-10 and physical_area>1e-10:
            l=e1.length
            p=e1.dot(e2)/l
            h=2*physical_area/l
            a=d1/l
            b=(d2-a*p)/h
            trace=a.length_squared+b.length_squared
            determinant=cross(a,b)**2
            disc=max(0,trace*trace-4*determinant)**.5
            ratio=math.sqrt((trace+disc)/max(trace-disc,1e-20))
            distortions.append((ratio,physical_area))
        bbox=(min(p.x for p in uv),min(p.y for p in uv),max(p.x for p in uv),max(p.y for p in uv))
        triangles.append((uv,bbox))
    overlap=[]
    for i,(u,a) in enumerate(triangles):
        for j in range(i+1,len(triangles)):
            v,b=triangles[j]
            if min(a[2],b[2])-max(a[0],b[0])<=1e-7 or min(a[3],b[3])-max(a[1],b[1])<=1e-7:
                continue
            value=intersect_area(u[:],v)
            if value>1e-8:
                overlap.append([i,j,value])
    check(obj.name+' no positive-area UV triangle overlap',not overlap,overlap[:10])
    check(obj.name+' no collapsed UV triangles',bad_area==0,bad_area)
    total=sum(w for _,w in distortions)
    accumulated=0
    p95=1
    for ratio,weight in sorted(distortions):
        accumulated+=weight
        if accumulated>=total*.95:
            p95=ratio
            break
    stats[obj.name]={'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),'uv_seams':sum(e.use_seam for e in mesh.edges),'uv_overlap_pairs':len(overlap),'area_weighted_p95_anisotropy':p95,'max_anisotropy':max(r for r,_ in distortions)}
controller=lid.parent
scene.frame_set(30)
check('lift first 0.12m without lateral roll',abs(controller.location.z-.65)<1e-5 and abs(controller.location.x)<1e-5 and abs(controller.rotation_euler.y)<1e-5)
scene.frame_set(90)
check('whole lid stowed 90 degrees',abs(controller.rotation_euler.y-math.pi/2)<1e-5)
motion=json.loads((ROOT/'motion_measurements.json').read_text(encoding='utf-8'))
check('sampled opening clearance',not motion['surface_intersection_frames'] and motion['minimum_ground_clearance_m']>0 and motion['maximum_swept_x_m']<1.225)
report={'status':'PASS_FILE_UV_AND_SAMPLED_GEOMETRY' if all(c['pass'] for c in results) else 'FAIL','checks':results,'mesh_statistics':stats,'total_asset_triangles':sum(s['triangles'] for s in stats.values()),'UV_scope':'one separate 0-1 map per shell, lid, sleeping surface; no intentional overlaps','limits':['curved surfaces have local distortion','paint resolution and density not approved','not human/mechanical validation','final silhouette awaits review']}
(ROOT/'saved_check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
if report['status']=='FAIL':
    raise RuntimeError('Readback checks failed')
