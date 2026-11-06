"""Read-only v2 garment-opening and cap-face diagnosis.

The script only writes v3 diagnosis JSON and temporary diagnostic PNGs.  It
does not save the v2 Blend or modify the candidate mesh.
"""
from pathlib import Path
import bpy, json, hashlib, math
from mathutils import Vector

EXP=Path(__file__).resolve().parent.parent
V2=EXP.parent/'protagonist_tripo_cn_cleanup_v2'
BLEND=V2/'model/protagonist_cn_cleanup_v2.blend'
OUT=EXP/'garment_diagnosis.json'; EVID=EXP/'evidence'

def bbox(points):
    return {'min':[min(p[i] for p in points) for i in range(3)],
            'max':[max(p[i] for p in points) for i in range(3)]}

def connected_edges(edges):
    adj={}
    for a,b in edges: adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
    groups=[];seen=set()
    for start in adj:
        if start in seen: continue
        todo=[start];seen.add(start);group=set()
        while todo:
            v=todo.pop();group.add(v)
            for n in adj[v]:
                if n not in seen:seen.add(n);todo.append(n)
        groups.append(group)
    return groups,adj

def ordered_loop(vertices,adj):
    """Return a deterministic walk when the boundary component is a simple loop."""
    start=min(vertices);out=[start];prev=None;cur=start
    while True:
        choices=sorted(n for n in adj[cur] if n in vertices and n!=prev)
        if not choices: return None
        nxt=choices[0]
        if nxt==start:
            return out if len(out)==len(vertices) else None
        if nxt in out:return None
        out.append(nxt);prev,cur=cur,nxt

def component_boundary_loops(mesh, component_data, component_id):
    faces=[p for p in mesh.polygons if int(component_data[p.index].value)==component_id]
    edge_faces={}
    for p in faces:
        ids=list(p.vertices)
        for i,a in enumerate(ids):edge_faces.setdefault(tuple(sorted((a,ids[(i+1)%len(ids)]))),[]).append(p.index)
    boundary=[edge for edge,used in edge_faces.items() if len(used)==1]
    groups,adj=connected_edges(boundary)
    result=[]
    for verts in groups:
        ordered=ordered_loop(verts,adj)
        result.append({'vertex_ids_ordered':ordered,'vertex_count':len(verts),'is_simple_ordered_loop':ordered is not None,'bbox_local':bbox([tuple(mesh.vertices[v].co) for v in verts])})
    return result

def one_face_components(indices,edge_faces,mesh):
    target=set(indices);adj={i:set() for i in target}
    for faces in edge_faces.values():
        here=[f for f in faces if f in target]
        for a in here:
            adj[a].update(x for x in here if x!=a)
    seen=set();out=[]
    for start in target:
        if start in seen:continue
        todo=[start];seen.add(start);group=[]
        while todo:
            f=todo.pop();group.append(f)
            for n in adj[f]:
                if n not in seen:seen.add(n);todo.append(n)
        out.append(sorted(group))
    return sorted(out,key=lambda x:(-len(x),x[0]))

def render_overlay(scene,obj,sets,loops):
    old_engine,old_camera=scene.render.engine,scene.camera
    oldslots=list(obj.data.materials);oldidx=[p.material_index for p in obj.data.polygons]
    def mat(name,rgb):
        m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);return m
    obj.data.materials.clear()
    colors=[(.44,.47,.48),(.90,.28,.12),(.16,.74,.88),(.93,.79,.14),(.76,.35,.90)]
    for i,c in enumerate(colors):obj.data.materials.append(mat('TEMP_GARMENT_'+str(i),c))
    labels=['hem_cap','left_cuff_cap','right_cuff_cap','collar_adjacent']
    index={name:i+1 for i,name in enumerate(labels)}
    for p in obj.data.polygons:p.material_index=index.get(next((n for n,s in sets.items() if p.index in s),''),0)
    scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
    scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    records=[]
    for view in ('front','side','quarter','head_back'):
        scene.camera=bpy.data.objects['QA_'+view];path=EVID/f'garment_caps_{view}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        records.append({'view':view,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    # True isolated under-hem view: use a temporary robe-only copy so the feet
    # cannot occlude the diagnostic cap faces.
    import bmesh
    isolate_mesh=obj.data.copy(); bm=bmesh.new();bm.from_mesh(isolate_mesh);bm.faces.ensure_lookup_table()
    isolate_comp=isolate_mesh.attributes['raw_component_id'].data
    bmesh.ops.delete(bm,geom=[bm.faces[p.index] for p in isolate_mesh.polygons if int(isolate_comp[p.index].value)!=2],context='FACES')
    bm.to_mesh(isolate_mesh);bm.free();isolate_mesh.update()
    isolate=bpy.data.objects.new('TEMP_GARMENT_ONLY',isolate_mesh);scene.collection.objects.link(isolate);isolate.matrix_world=obj.matrix_world.copy()
    # The copied material indices already encode the cap selection above.
    for material in obj.data.materials:isolate.data.materials.append(material)
    old_hide=obj.hide_render;obj.hide_render=True
    camdata=bpy.data.cameras.new('TEMP_GARMENT_UNDERSIDE');cam=bpy.data.objects.new('TEMP_GARMENT_UNDERSIDE',camdata);scene.collection.objects.link(cam)
    camdata.type='ORTHO';camdata.ortho_scale=.34
    target=obj.matrix_world @ Vector((-.012,.112,0));cam.location=target+Vector((.0,-.20,-.28))
    direction=target-cam.location;cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
    scene.camera=cam;path=EVID/'garment_caps_underside.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    records.append({'view':'underside','file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    bpy.data.objects.remove(cam,do_unlink=True);bpy.data.cameras.remove(camdata);bpy.data.objects.remove(isolate,do_unlink=True);bpy.data.meshes.remove(isolate_mesh);obj.hide_render=old_hide
    obj.data.materials.clear()
    for m in oldslots:obj.data.materials.append(m)
    for p,i in zip(obj.data.polygons,oldidx):p.material_index=i
    scene.render.engine,scene.camera=old_engine,old_camera
    return records

def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    scene=bpy.context.scene
    before=bpy.data.collections['BEFORE_V1'];after=bpy.data.collections['AFTER_V2']
    before.hide_viewport=True;before.hide_render=True
    after.hide_viewport=False;after.hide_render=False
    for obj in before.all_objects:obj.hide_set(True);obj.hide_render=True
    for obj in after.all_objects:obj.hide_set(False);obj.hide_render=False
    bpy.context.view_layer.update()
    obj=next(o for o in after.all_objects if o.type=='MESH');mesh=obj.data
    comp=mesh.attributes['raw_component_id'].data;raw=mesh.attributes['raw_obj_face_index'].data
    robe=[p for p in mesh.polygons if int(comp[p.index].value)==2]
    handfaces={cid:[p for p in mesh.polygons if int(comp[p.index].value)==cid] for cid in (3,20)}
    points={cid:[tuple(mesh.vertices[v].co) for p in mesh.polygons if int(comp[p.index].value)==cid for v in p.vertices] for cid in (0,2,3,5,6,19,20)}
    robe_points=[tuple(mesh.vertices[v].co) for p in robe for v in p.vertices]
    rmin=min(p[1] for p in robe_points);rmax=max(p[1] for p in robe_points)
    edge_faces={}
    for p in robe:
        ids=list(p.vertices)
        for i,a in enumerate(ids):edge_faces.setdefault(tuple(sorted((a,ids[(i+1)%len(ids)]))),[]).append(p.index)
    boundary=[e for e,faces in edge_faces.items() if len(faces)==1]
    loopsets,adj=connected_edges(boundary)
    loops=[]
    for verts in loopsets:
        adjacent=sorted({face for e,faces in edge_faces.items() if len(faces)==1 and any(v in verts for v in e) for face in faces})
        ps=[tuple(mesh.vertices[v].co) for v in verts]
        loops.append({'vertex_ids':sorted(verts),'vertex_count':len(verts),'bbox_local':bbox(ps),'centroid_local':[sum(p[i] for p in ps)/len(ps) for i in range(3)],'adjacent_candidate_polygon_ids':adjacent,'adjacent_raw_face_ids':[int(raw[i].value) for i in adjacent]})
    foot_topology={str(cid):component_boundary_loops(mesh,comp,cid) for cid in (0,19)}
    # Cap candidates are not inferred from loops: classify actual robe faces
    # whose local-Y normal and all face vertices lie at exterior extrema.
    hem=set(); collar=set()
    for p in robe:
        vs=[mesh.vertices[v].co for v in p.vertices];cy=sum(v.y for v in vs)/len(vs)
        if max(v.y for v in vs)<=rmin+.010 and p.normal.y<-.25:hem.add(p.index)
        if min(v.y for v in vs)>=rmax-.018 and p.normal.y>.20:collar.add(p.index)
    # Hand-proximity identifies sleeve-end caps: actual robe faces closest to
    # each hand component's vertices, then require a compact local-y band.
    cuffs={}
    for cid,faces in handfaces.items():
        hp=[mesh.vertices[v].co for p in faces for v in p.vertices]
        ranked=[]
        for p in robe:
            center=sum((mesh.vertices[v].co for v in p.vertices),Vector())/len(p.vertices)
            d=min((center-h).length for h in hp)
            ranked.append((d,p.index))
        cutoff=sorted(d for d,_ in ranked)[max(4,min(11,len(ranked)-1))]
        selected={i for d,i in ranked if d<=cutoff}
        # retain the most cap-like of the local sleeve-end faces: avoid tagging
        # the whole sleeve merely because the hand intersects it.
        selected={i for i in selected if abs(mesh.polygons[i].normal.z)>.20 or abs(mesh.polygons[i].normal.x)>.20}
        cuffs[cid]=selected
    sets={'hem_cap':hem,'left_cuff_cap':cuffs[3],'right_cuff_cap':cuffs[20],'collar_adjacent':collar}
    records=render_overlay(scene,obj,sets,loops)
    data={'purpose':'Read-only diagnosis of actual v2 robe caps/openings for v3 structure work. Colors are technical selection only, not material design.',
          'baseline_blend':str(BLEND),'baseline_sha256':hashlib.sha256(BLEND.read_bytes()).hexdigest(),'mesh':obj.name,
          'coordinate_note':'Mesh local Y is vertical/raw Y; the object is rotated +90 degrees on X for Blender world Z-up.',
          'component_bboxes_local':{str(k):bbox(v) for k,v in points.items()},
          'robe_local_y_range':[rmin,rmax],'robe_boundary_loops':loops,
          'foot_component_boundary_loops':foot_topology,
          'cap_face_selection':{name:{'candidate_polygon_ids':sorted(vals),'raw_face_ids':[int(raw[i].value) for i in sorted(vals)],'count':len(vals)} for name,vals in sets.items()},
          'selection_method':{'hem':'all robe-face vertices in bottom .010 local-Y band plus down-facing local normal','collar':'top .018 local-Y band plus up-facing local normal; collar remains an opening because it borders the 18-vertex loop','cuffs':'proximity to actual hand components 3/20, then compact face-normal filter; visual overlay required before treating every selected face as a removable cap'},
          'proposed_minimum_structure':'Use only reviewed cap-face selections as removable exterior closures. Build thin inward shell/rim from their surrounding boundary loops, preserving exterior side faces; add short covered leg proxy cylinders from existing foot/ankle component top rings upward inside the robe. Do not create hidden full anatomy or infer sleeve/hem openings solely from component boundaries.',
          'renders':records,
          'limits':['Current robe boundary loops prove one large neck opening and one small secondary opening only; cuffs and hem need cap-face visual confirmation.','No mesh change, UV, rig, texture or game integration occurred.']}
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    (EVID/'garment_caps_legend.json').write_text(json.dumps({'colors':{'gray':'current v2 context','orange':'hem cap candidate','cyan':'component3 cuff candidate','yellow':'component20 cuff candidate','purple':'collar-adjacent faces'},'renders':records,'boundary':'Selection overlay only; it does not claim cap faces have been deleted or openings made.'},ensure_ascii=False,indent=2),encoding='utf-8')
    print('GARMENT_DIAGNOSIS',len(hem),len(cuffs[3]),len(cuffs[20]),len(collar),len(loops))
if __name__=='__main__':main()
