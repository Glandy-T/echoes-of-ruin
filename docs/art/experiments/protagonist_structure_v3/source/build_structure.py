"""Keep the v2 exterior; build cloth interior and covered legs in source local Y-up.
Default also calls prepare_uv_trial.py. --geometry-only runs a diagnostic stage.
"""
from pathlib import Path
import bpy,json,hashlib,sys,importlib.util,math
from mathutils import Vector
EXP=Path(__file__).resolve().parent.parent
BASE=EXP.parent/'protagonist_tripo_cn_cleanup_v2/model/protagonist_cn_cleanup_v2.blend'
CAPS={16,17,18,19,20,21,23,297,298,299,300,301,318,319,582,671,1198,1205,1829,1884,2372,2379,62,63,64,66,701,704,705,1259,1262,362,364,369,370,2018,2119,2120,2876,2879}
FEET={0:[988,989,1317,1318,1323,1324,1332,991],19:[1858,1859,2167,2168,2170,2185,2183,1861]}
SHA='9f5fd46d630c318108ebbe16dcc46aef9a837234f51ac4685f1e0f8390b80105'
THICKNESS=.0007
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def boundary_loops(faces):
    edges={}
    for face in faces:
        for a,b in zip(face,face[1:]+face[:1]):edges.setdefault(tuple(sorted((a,b))),[]).append((a,b))
    nxt={}
    for vals in edges.values():
        if len(vals)==1:
            a,b=vals[0]
            if a in nxt:raise RuntimeError('Non-simple boundary')
            nxt[a]=b
    loops=[];left=set(nxt)
    while left:
        start=min(left);v=start;loop=[]
        while True:
            if v not in left:raise RuntimeError('Boundary not a closed simple ring')
            left.remove(v);loop.append(v);v=nxt[v]
            if v==start:break
        loops.append(loop)
    return loops
def create_part(name,verts,records,group,matrix,material):
    mesh=bpy.data.meshes.new(name+'_Mesh');mesh.from_pydata([tuple(v) for v in verts],[],[r['v'] for r in records]);mesh.update()
    obj=bpy.data.objects.new(name,mesh);group.objects.link(obj);obj.matrix_world=matrix.copy();mesh.materials.append(material)
    for attr in ('raw_obj_face_index','raw_component_id','surface_kind','parent_raw_face_index'):mesh.attributes.new(attr,'INT','FACE')
    normals=[]
    for p,r in zip(mesh.polygons,records):
        p.use_smooth=r.get('smooth',True)
        for attr,key,default in (('raw_obj_face_index','raw',-1),('raw_component_id','comp',-1),('surface_kind','kind',3),('parent_raw_face_index','parent',-1)):
            mesh.attributes[attr].data[p.index].value=r.get(key,default)
        normals.extend(r.get('n',[tuple(mesh.corner_normals[i].vector) for i in p.loop_indices]))
    mesh.normals_split_custom_set(normals);mesh.update();return obj
def compact(verts,records,predicate):
    selected=[r for r in records if predicate(r)];used=sorted({v for r in selected for v in r['v']});mapping={v:i for i,v in enumerate(used)}
    return [verts[v].copy() for v in used],[dict(r,v=[mapping[v] for v in r['v']]) for r in selected],mapping
def low_neck_ring(records,positions):
    edges={}
    for r in records:
        if r['comp']!=5:continue
        f=r['v']
        for a,b in zip(f,f[1:]+f[:1]):edges.setdefault(tuple(sorted((a,b))),[]).append((a,b))
    directed=[xs[0] for xs in edges.values() if len(xs)==1 and all(positions[v].y<.60 for v in xs[0])]
    adj={}
    for a,b in directed:adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
    if len(adj)!=16 or any(len(ns)!=2 for ns in adj.values()):raise RuntimeError('Low neck boundary is not the reviewed 16-ring')
    start=min(adj);loop=[start];prev=None;cur=start
    while True:
        nex=next(v for v in adj[cur] if v!=prev)
        if nex==start:break
        loop.append(nex);prev,cur=cur,nex
    if sum((a,b) in directed for a,b in zip(loop,loop[1:]+loop[:1]))<8:loop.reverse()
    return loop
def main():
    if sha(BASE)!=SHA:raise RuntimeError('v2 baseline hash changed')
    bpy.ops.wm.open_mainfile(filepath=str(BASE));scene=bpy.context.scene;src=bpy.data.objects['CN_P20_V2_AFTER']
    for coll in bpy.data.collections:
        if src in list(coll.all_objects):coll.hide_viewport=False
    src.hide_set(False);src.hide_viewport=False;bpy.context.view_layer.update()
    matrix=src.matrix_world.copy();original=src.data;positions=[v.co.copy() for v in original.vertices];records=[]
    for p in original.polygons:
        records.append({'v':list(p.vertices),'raw':original.attributes['raw_obj_face_index'].data[p.index].value,'comp':original.attributes['raw_component_id'].data[p.index].value,'kind':0,'smooth':p.use_smooth,'n':[tuple(original.corner_normals[i].vector) for i in p.loop_indices]})
    before=bpy.data.collections.new('BEFORE_V2');after=bpy.data.collections.new('AFTER_V3');scene.collection.children.link(before);scene.collection.children.link(after)
    baseline=src.copy();baseline.data=src.data.copy();baseline.name='V2_Baseline_Unchanged';before.objects.link(baseline);material=src.data.materials[0]
    hv,hr,_=compact(positions,records,lambda r:r['comp']==6);hair=create_part('Hair_Main',hv,hr,after,matrix,material)
    rv,rr,_=compact(positions,records,lambda r:r['comp']==2 and r['raw'] not in CAPS);loops=boundary_loops([r['v'] for r in rr]);repairs=[]
    for loop in loops:
        center=sum((rv[v] for v in loop),Vector())/len(loop)
        if len(loop)==4 and .39<center.y<.41 and center.z<-.05:
            rr.append({'v':list(reversed(loop)),'raw':-1,'comp':2,'kind':4,'smooth':True});repairs.append([tuple(rv[v]) for v in loop])
    loops=boundary_loops([r['v'] for r in rr])
    if sorted(map(len,loops))!=[10,10,18,32] or len(repairs)!=1:raise RuntimeError('Unexpected garment opening rings')
    temp=bpy.data.meshes.new('_ClothOuterNormals');temp.from_pydata(rv,[],[r['v'] for r in rr]);temp.update()
    for p,r in zip(temp.polygons,rr):
        if 'n' not in r:r['n']=[tuple(temp.corner_normals[i].vector) for i in p.loop_indices]
    avg=[Vector() for _ in rv]
    for r in rr:
        for v,n in zip(r['v'],r['n']):avg[v]+=Vector(n)
    for i,n in enumerate(avg):
        if n.length<1e-9:n[:]=temp.vertices[i].normal
        n.normalize()
    # Reversing a nonplanar source quad can change its implicit diagonal and
    # make a thin inner surface cross the exterior. Match its exact triangles.
    temp.calc_loop_triangles();inner_tris=[(t.polygon_index,list(t.vertices)) for t in temp.loop_triangles]
    bpy.data.meshes.remove(temp);nouter=len(rv);clothverts=rv+[p-n*THICKNESS for p,n in zip(rv,avg)];clothrecs=list(rr)
    for pi,tri in inner_tris:
        r=rr[pi];normals=dict(zip(r['v'],r['n']));order=list(reversed(tri))
        clothrecs.append({'v':[v+nouter for v in order],'n':[tuple(-Vector(normals[v])) for v in order],'raw':-1,'parent':r['raw'],'comp':2,'kind':1,'smooth':True})
    for loop in loops:
        for a,b in zip(loop,loop[1:]+loop[:1]):clothrecs.append({'v':[b,a,a+nouter,b+nouter],'raw':-1,'comp':2,'kind':2,'smooth':False})
    robe=create_part('Robe_Outer_Inner_Rims',clothverts,clothrecs,after,matrix,material)
    bodyids={0,3,5,19,20};bv,br,bmap=compact(positions,records,lambda r:r['comp'] in bodyids);limbs=[]
    for cid,expected in FEET.items():
        candidates=[loop for loop in boundary_loops([r['v'] for r in records if r['comp']==cid]) if set(loop)==set(expected)]
        if len(candidates)!=1:raise RuntimeError('Ankle ring differs from source boundary')
        old=candidates[0];previous=[bmap[v] for v in old];center=sum((positions[v] for v in old),Vector())/len(old);sign=1 if center.z>0 else -1
        for height,sx,sz,lateral in ((.235,1.08,1.05,.052),(.35,1.22,1.20,.045)):
            ring=[]
            for vi in old:
                d=positions[vi]-center;ring.append(len(bv));bv.append(Vector((center.x+d.x*sx,height,sign*lateral+d.z*sz)))
            for a,b,c,d in zip(previous,previous[1:]+previous[:1],ring,ring[1:]+ring[:1]):br.append({'v':[b,a,c,d],'raw':-1,'comp':-1,'kind':3,'smooth':True})
            previous=ring
        br.append({'v':list(reversed(previous)),'raw':-1,'comp':-1,'kind':3,'smooth':False});limbs.append({'source_component':cid,'source_ankle_ring':old,'levels_local_y':[.235,.35]})
    # Wardrobe-ready separation requires a body base, not only visible skin.
    # These neutral covered volumes remain provisional, with shoulder/hip joins
    # awaiting deformation retopology. No detailed hidden anatomy is introduced.
    neck=low_neck_ring(records,positions)
    if len(neck)!=16:raise RuntimeError('Head-neck attachment ring changed')
    nc=sum((positions[v] for v in neck),Vector())/len(neck)
    rx=max(abs(positions[v].x-nc.x) for v in neck);rz=max(abs(positions[v].z-nc.z) for v in neck)
    angles=[math.atan2((positions[v].z-nc.z)/rz,(positions[v].x-nc.x)/rx) for v in neck]
    previous=[bmap[v] for v in neck]
    for y,radiusx,radiusz in ((.52,.030,.072),(.46,.036,.058),(.38,.029,.047),(.32,.035,.054)):
        ring=[]
        for angle in angles:
            ring.append(len(bv));bv.append(Vector((-.012+radiusx*math.cos(angle),y,radiusz*math.sin(angle))))
        for a,b,c,d in zip(previous,previous[1:]+previous[:1],ring,ring[1:]+ring[:1]):br.append({'v':[b,a,c,d],'raw':-1,'comp':-1,'kind':5,'smooth':True})
        previous=ring
    br.append({'v':list(reversed(previous)),'raw':-1,'comp':-1,'kind':5,'smooth':False})
    for cid in (3,20):
        rings=boundary_loops([r['v'] for r in records if r['comp']==cid]);old=max(rings,key=len)
        center=sum((positions[v] for v in old),Vector())/len(old);sign=1 if center.z>0 else -1
        axis=(Vector((-.012,.51,sign*.072))-center).normalized()
        u=positions[old[0]]-center;u=(u-axis*u.dot(axis)).normalized();vaxis=axis.cross(u).normalized()
        angles=[math.atan2((positions[v]-center).dot(vaxis),(positions[v]-center).dot(u)) for v in old]
        previous=[bmap[v] for v in old]
        for point,radius in ((Vector((-.012,.445,sign*.102)),.015),(Vector((-.012,.51,sign*.072)),.018)):
            ring=[]
            for angle in angles:ring.append(len(bv));bv.append(point+radius*(u*math.cos(angle)+vaxis*math.sin(angle)))
            for a,b,c,d in zip(previous,previous[1:]+previous[:1],ring,ring[1:]+ring[:1]):br.append({'v':[b,a,c,d],'raw':-1,'comp':-1,'kind':6,'smooth':True})
            previous=ring
        br.append({'v':list(reversed(previous)),'raw':-1,'comp':-1,'kind':6,'smooth':False})
    body=create_part('Body_Base_Separate_From_Clothes',bv,br,after,matrix,material)
    dv,dr,_=compact(positions,records,lambda r:r['comp'] not in bodyids|{2,6});details=create_part('Preserved_Unclassified_Source_Details',dv,dr,after,matrix,material);parts=[hair,robe,body,details]
    keep=set(parts+[baseline])
    for obj in list(bpy.data.objects):
        if obj.type=='MESH' and obj not in keep:bpy.data.objects.remove(obj,do_unlink=True)
    for coll in list(bpy.data.collections):
        if coll not in (before,after) and not coll.objects and not coll.children:bpy.data.collections.remove(coll)
    before.hide_render=True;before.hide_viewport=True;baseline.hide_render=True;baseline.hide_set(True);after.hide_render=False;after.hide_viewport=False
    for obj in parts:obj.hide_render=False;obj.hide_set(False)
    bpy.context.view_layer.update()
    report={'baseline':str(BASE),'baseline_sha256':sha(BASE),'removed_cap_raw_face_ids':sorted(CAPS),'restored_noncap_raw_faces':[68,372],'rear_hole_repair_coordinates':repairs,'cloth_opening_rings_before_inner_shell':[{'vertices':len(loop),'center_local':list(sum((rv[v] for v in loop),Vector())/len(loop))} for loop in loops],'cloth_thickness_raw_units':THICKNESS,'cloth_outer_faces':len(rr),'cloth_inner_faces':len(inner_tris),'cloth_rim_faces':sum(map(len,loops)),'covered_leg_extensions':limbs,'wardrobe_body_base':{'head_neck_ring':neck,'new_neutral_torso':True,'forearms_connected_to_existing_wrist_rings':True,'future_retopology':'Shoulder and hip proxy joins still overlap; not animation-ready or a finalized unclothed body design.'},'parts':[{'name':p.name,'vertices':len(p.data.vertices),'faces':len(p.data.polygons)} for p in parts],'source_unclassified_details_preserved':len(dr),'source_transform':[list(row) for row in matrix],'scope':'Static clothing structure and UV trial; no rigging, final pixel art, final texel-density or game integration approval.'}
    if '--geometry-only' not in sys.argv:
        spec=importlib.util.spec_from_file_location('uv_trial',EXP/'source/prepare_uv_trial.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);report['uv_trial']=module.prepare(parts,EXP)
    else:report['uv_trial']={'status':'NOT_RUN_GEOMETRY_DIAGNOSTIC_ONLY'}
    scene.camera=bpy.data.objects['QA_quarter'];scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.62,.65,.65);scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
    for obj in bpy.context.selected_objects:obj.select_set(False)
    for obj in parts:obj.select_set(True)
    bpy.context.view_layer.objects.active=robe;out=EXP/'model/protagonist_structure_v3.blend';out.parent.mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(out))
    bpy.ops.export_scene.gltf(filepath=str(EXP/'model/protagonist_structure_v3.glb'),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
    (EXP/'source/build_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('STRUCTURE_V3_BUILT',report['parts'])
if __name__=='__main__':main()
