"""Build and audit the final broad-island body UV on a Basis-only clone.

Blender 5.0 crashes when this shape-keyed source mesh is edited by UV operators
in background mode.  The source body therefore remains out of Edit Mode: a
same-topology Basis clone preserves the author's three broad charts, repairs
complete foot and shoulder patches, and transfers only loop UV coordinates
back to the rigged source body.  Mesh topology, shape keys, weights, armature,
and modifiers are checked before the result is saved.
"""
from __future__ import annotations
import hashlib, json, math
from collections import defaultdict
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parents[1] / 'player_basemesh_v2_1' / 'body_165cm_validated_v2_1.blend'
OUT = ROOT / 'body_uv_ready_v5.blend'
REPORT = ROOT / 'bounded_validation_report.json'
CHECKER = ROOT / 'body_uv_checker.png'
SVG = ROOT / 'uv_body_pixel.svg'
BODY, RIG, SCENE = 'Body_165cm_CC0_pistachio', 'Body_Rig_original', '01_BODY_MASTER_165cm'
UV = 'UV_Body_Pixel'; PRESERVED = 'UV_Original_Preserved'; EPS = 1e-10

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def area(p):
    """Signed shoelace area for any convex clipping polygon.

    The overlap routine starts from triangles, but Sutherland-Hodgman can
    return four to six vertices.  Limiting the shoelace sum to three vertices
    misclassified ordinary edge contact as positive-area overlap.
    """
    return .5 * sum(
        p[i][0] * p[(i + 1) % len(p)][1]
        - p[(i + 1) % len(p)][0] * p[i][1]
        for i in range(len(p))
    ) if len(p) >= 3 else 0.0
def overlap_area(a,b):
    out=list(a); clip=list(b)
    if area(clip)<0: clip.reverse()
    for i,s in enumerate(clip):
        e=clip[(i+1)%3]; inp,out=out,[]
        if not inp: break
        def side(q): return (e[0]-s[0])*(q[1]-s[1])-(e[1]-s[1])*(q[0]-s[0])
        prev=inp[-1]; pin=side(prev)>=-EPS
        for cur in inp:
            cin=side(cur)>=-EPS
            if cin!=pin:
                ps,cs=side(prev),side(cur); d=ps-cs
                if abs(d)>EPS:
                    t=ps/d; out.append((prev[0]+t*(cur[0]-prev[0]),prev[1]+t*(cur[1]-prev[1])))
            if cin: out.append(cur)
            prev,pin=cur,cin
    return abs(area(out)) if len(out)>=3 else 0.

def audit(mesh, layer):
    mesh.calc_loop_triangles(); tris=[]; bad=[]; outside=[]
    for i,t in enumerate(mesh.loop_triangles):
        p=[tuple(float(layer.data[x].uv[j]) for j in range(2)) for x in t.loops]
        a=abs(area(p)); xs=[q[0] for q in p]; ys=[q[1] for q in p]
        if a<=EPS: bad.append(i)
        if any(not math.isfinite(v) or v<-EPS or v>1+EPS for q in p for v in q): outside.append(i)
        tris.append((p,(min(xs),min(ys),max(xs),max(ys))))
    grid=defaultdict(set); size=48
    for i,(_,b) in enumerate(tris):
        for x in range(max(0,int(math.floor(b[0]*size))),min(size-1,int(math.floor(b[2]*size)))+1):
            for y in range(max(0,int(math.floor(b[1]*size))),min(size-1,int(math.floor(b[3]*size)))+1): grid[x,y].add(i)
    pairs=set()
    for vals in grid.values():
        v=sorted(vals)
        for i,x in enumerate(v):
            for y in v[i+1:]: pairs.add((x,y))
    hits=[]
    for x,y in pairs:
        a,ab=tris[x];b,bb=tris[y]
        if ab[2]<bb[0]-EPS or bb[2]<ab[0]-EPS or ab[3]<bb[1]-EPS or bb[3]<ab[1]-EPS: continue
        z=overlap_area(a,b)
        if z>EPS:hits.append((x,y,z))
    labels,_=uv_island_labels(mesh,layer)
    same_polygon=sum(
        mesh.loop_triangles[a].polygon_index == mesh.loop_triangles[b].polygon_index
        for a,b,_ in hits
    )
    same_island=sum(
        labels[mesh.loop_triangles[a].polygon_index] == labels[mesh.loop_triangles[b].polygon_index]
        for a,b,_ in hits
    )
    island_hit_counts=defaultdict(int)
    for a,b,_ in hits:
        island_hit_counts[labels[mesh.loop_triangles[a].polygon_index]]+=1
        if labels[mesh.loop_triangles[b].polygon_index]!=labels[mesh.loop_triangles[a].polygon_index]:
            island_hit_counts[labels[mesh.loop_triangles[b].polygon_index]]+=1
    affected_polygons=sorted({mesh.loop_triangles[t].polygon_index for a,b,_ in hits for t in (a,b)})
    affected_geometry={}
    for polygon_index in affected_polygons:
        p=mesh.polygons[polygon_index]
        center=p.center
        affected_geometry[str(polygon_index)]={
            'center':[float(x) for x in center],
            'vertices':list(p.vertices),
            'normal':[float(x) for x in p.normal],
        }
    return {'triangles':len(tris),'zero_area_triangles':len(bad),'outside_unit_square_triangles':len(outside),'positive_area_self_overlap_pairs':len(hits),'same_polygon_overlap_pairs':same_polygon,'cross_polygon_overlap_pairs':len(hits)-same_polygon,'same_island_overlap_pairs':same_island,'different_island_overlap_pairs':len(hits)-same_island,'overlap_pairs_by_island':dict(sorted(island_hit_counts.items(),key=lambda item:(-item[1],item[0]))),'affected_polygons':affected_polygons,'affected_polygon_geometry':affected_geometry,'largest_overlap_area':max((x[2] for x in hits),default=0.),'candidate_pairs_tested':len(pairs),'samples':[{'triangles':[a,b],'polygons':[mesh.loop_triangles[a].polygon_index,mesh.loop_triangles[b].polygon_index],'uv_islands':[labels[mesh.loop_triangles[a].polygon_index],labels[mesh.loop_triangles[b].polygon_index]],'shared_vertices':sorted(set(mesh.loop_triangles[a].vertices)&set(mesh.loop_triangles[b].vertices)),'area':c} for a,b,c in hits[:12]]},tris

def island_geometry_summary(mesh,layer,island_ids):
    labels,_=uv_island_labels(mesh,layer)
    result={}
    for island_id in island_ids:
        polygons=[p for p in mesh.polygons if labels[p.index]==int(island_id)]
        vertices={v for p in polygons for v in p.vertices}
        coords=[mesh.vertices[v].co for v in vertices]
        result[str(island_id)]={
            'polygons':len(polygons),
            'bounds':[[min(c[i] for c in coords),max(c[i] for c in coords)] for i in range(3)],
            'centroid':[sum(c[i] for c in coords)/len(coords) for i in range(3)],
        }
    return result

def uv_island_labels(mesh,layer):
    by_edge=defaultdict(list)
    for p in mesh.polygons:
        for i,li in enumerate(p.loop_indices):
            nxt=p.loop_indices[(i+1)%len(p.loop_indices)]
            edge=tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)])))
            by_edge[edge].append((p.index,li,nxt))
    adj=defaultdict(set)
    for refs in by_edge.values():
        if len(refs)!=2:continue
        (a,al0,al1),(b,bl0,bl1)=refs
        pa=[layer.data[al0].uv,layer.data[al1].uv];pb=[layer.data[bl0].uv,layer.data[bl1].uv]
        same=(pa[0]-pb[0]).length<=1e-6 and (pa[1]-pb[1]).length<=1e-6
        flipped=(pa[0]-pb[1]).length<=1e-6 and (pa[1]-pb[0]).length<=1e-6
        if same or flipped:adj[a].add(b);adj[b].add(a)
    remaining=set(range(len(mesh.polygons)));labels={};sizes=[]
    while remaining:
        start=remaining.pop();stack=[start];members=[]
        while stack:
            p=stack.pop();members.append(p)
            for q in adj[p]&remaining:remaining.remove(q);stack.append(q)
        label=len(sizes);sizes.append(len(members))
        for p in members:labels[p]=label
    return labels,sizes

def islands(mesh, layer):
    # UV continuity across a shared mesh edge identifies broad paint islands.
    _,sizes=uv_island_labels(mesh,layer)
    return {'uv_island_count':len(sizes),'largest_island_polygons':sorted(sizes,reverse=True)[:12],'single_polygon_islands':sum(x==1 for x in sizes)}

def protected(body,rig):
    return {'vertices':len(body.data.vertices),'edges':len(body.data.edges),'polygons':len(body.data.polygons),'shape_keys':[(k.name,k.value,len(k.data)) for k in body.data.shape_keys.key_blocks],'modifiers':[(m.name,m.type) for m in body.modifiers],'parent':body.parent.name if body.parent else None,'armature':body.find_armature().name if body.find_armature() else None,'body_visibility':[body.hide_viewport,body.hide_render,body.hide_get()],'rig_visibility':[rig.hide_viewport,rig.hide_render,rig.hide_get()],'bones':[(b.name,b.parent.name if b.parent else None) for b in rig.data.bones],'weights':[sorted((g.group,round(g.weight,8)) for g in v.groups) for v in body.data.vertices]}

def clone_basis(body):
    source=body.data; basis=source.shape_keys.key_blocks['Basis']
    mesh=bpy.data.meshes.new('__BODY_UV_BASIS_CLONE_MESH__')
    mesh.from_pydata([p.co[:] for p in basis.data],[],[tuple(p.vertices) for p in source.polygons]);mesh.update()
    obj=bpy.data.objects.new('__BODY_UV_BASIS_CLONE__',mesh);bpy.context.scene.collection.objects.link(obj)
    return obj

def build_directional_charts(clone):
    """Create broad six-direction charts instead of per-face projections.

    Faces with the same dominant normal direction share one global projection,
    so connected head, torso and limb surfaces remain connected UV charts.
    Direction changes become predictable front/back/side/top/bottom seams.
    """
    mesh=clone.data
    layer=mesh.uv_layers.new(name='__DIRECTIONAL_ANATOMY_CHARTS__',do_init=False)
    mesh.uv_layers.active=layer
    counts=defaultdict(int)
    for poly in mesh.polygons:
        normal=poly.normal
        axis=max(range(3),key=lambda i:abs(normal[i]))
        sign=1 if normal[axis]>=0 else -1
        counts[f'{"XYZ"[axis]}{"+" if sign>0 else "-"}']+=1
        for loop_index,vertex_index in zip(poly.loop_indices,poly.vertices):
            x,y,z=mesh.vertices[vertex_index].co
            if axis==0:   # left/right side charts
                u=(-y if sign>0 else y);v=z
            elif axis==1: # front/back charts; model front is -Y
                u=(x if sign<0 else -x);v=z
            else:         # scalp, shoulders, soles and horizontal caps
                u=x;v=(y if sign>0 else -y)
            layer.data[loop_index].uv=(u,v)
    return layer,dict(counts)

def harmonic_disk_chart(mesh,layer,polygon_ids,offset_x):
    """Embed one disk-like anatomical patch with a convex boundary.

    Uniform positive Laplacian weights are a Tutte embedding: with a simple
    convex boundary, interior vertices cannot fold across one another.  This
    is used only for the compact upper-foot and shoulder patches that Blender
    ABF folds on this particular low-poly topology.
    """
    polygon_ids=set(polygon_ids)
    edge_counts=defaultdict(int);neighbors=defaultdict(set);vertices=set()
    for polygon_id in polygon_ids:
        poly=mesh.polygons[polygon_id]
        vertices.update(poly.vertices)
        for edge in poly.edge_keys:
            a,b=tuple(sorted(edge));edge_counts[a,b]+=1
            neighbors[a].add(b);neighbors[b].add(a)
    boundary_edges=[edge for edge,count in edge_counts.items() if count==1]
    boundary_neighbors=defaultdict(list)
    for a,b in boundary_edges:
        boundary_neighbors[a].append(b);boundary_neighbors[b].append(a)
    if not boundary_neighbors or any(len(items)!=2 for items in boundary_neighbors.values()):
        raise RuntimeError('Anatomical patch is not a single disk boundary: '+repr({'polygons':len(polygon_ids),'degrees':sorted(len(x) for x in boundary_neighbors.values())}))
    start=min(boundary_neighbors);boundary=[start];previous=None;current=start
    while True:
        candidates=[v for v in boundary_neighbors[current] if v!=previous]
        nxt=candidates[0]
        if nxt==start:break
        if nxt in boundary:raise RuntimeError('Boundary traversal self-intersected.')
        boundary.append(nxt);previous,current=current,nxt
    if len(boundary)!=len(boundary_neighbors):raise RuntimeError('Patch has more than one boundary loop.')
    lengths=[]
    for i,v in enumerate(boundary):
        lengths.append((mesh.vertices[boundary[(i+1)%len(boundary)]].co-mesh.vertices[v].co).length)
    perimeter=sum(lengths);positions={};travel=0.0
    for i,v in enumerate(boundary):
        angle=2*math.pi*travel/perimeter
        positions[v]=np.array([math.cos(angle)+offset_x,math.sin(angle)],dtype=float)
        travel+=lengths[i]
    interior=sorted(vertices-set(boundary));index={v:i for i,v in enumerate(interior)}
    if interior:
        matrix=np.eye(len(interior),dtype=float);rhs=np.zeros((len(interior),2),dtype=float)
        for v,row in index.items():
            linked=sorted(neighbors[v]);weight=1.0/len(linked)
            for neighbor in linked:
                if neighbor in index:matrix[row,index[neighbor]]-=weight
                else:rhs[row]+=weight*positions[neighbor]
        solution=np.linalg.solve(matrix,rhs)
        for v,row in index.items():positions[v]=solution[row]
    for polygon_id in polygon_ids:
        poly=mesh.polygons[polygon_id]
        for loop_index,vertex_index in zip(poly.loop_indices,poly.vertices):
            layer.data[loop_index].uv=positions[vertex_index]
    return {'polygons':len(polygon_ids),'vertices':len(vertices),'boundary_vertices':len(boundary),'interior_vertices':len(interior)}

def repair_source_uv_patches(clone):
    """Re-unwrap only the two feet and a small folded shoulder patch.

    The source atlas already has three broad, paintable charts.  Its positive
    overlaps are confined to the feet and three shoulder/upper-torso faces.
    Selecting complete anatomical patches keeps the atlas coherent while
    avoiding the earlier one-face-per-island fallback.
    """
    mesh=clone.data
    edge_polygons=defaultdict(list)
    for poly in mesh.polygons:
        for edge_key in poly.edge_keys:edge_polygons[tuple(sorted(edge_key))].append(poly.index)
    adjacency=defaultdict(set)
    for refs in edge_polygons.values():
        if len(refs)==2:
            a,b=refs;adjacency[a].add(b);adjacency[b].add(a)
    feet={p.index for p in mesh.polygons if p.center.z<0.14 and abs(p.center.x)>0.22}
    shoulder={2,515,519}
    frontier=set(shoulder)
    for _ in range(2):
        frontier={q for p in frontier for q in adjacency[p]}-shoulder
        shoulder.update(frontier)
    selected=feet|shoulder
    bpy.context.view_layer.objects.active=clone
    clone.select_set(True)
    bpy.context.scene.tool_settings.use_uv_select_sync=True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for polygon in mesh.polygons:polygon.select=polygon.index in selected
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED',fill_holes=True,correct_aspect=True,margin=.025)
    bpy.ops.object.mode_set(mode='OBJECT')
    # Blender ABF folds the compact 25-quad upper-foot patches around the toes.
    # Parameterize each complete disk with a convex boundary instead.
    layer=mesh.uv_layers.active
    labels,sizes=uv_island_labels(mesh,layer)
    upper_foot_charts=[]
    for label,size in enumerate(sizes):
        members=[p for p in mesh.polygons if labels[p.index]==label]
        if size==25 and members and all(abs(p.center.x)>0.22 and p.center.z<0.14 for p in members):
            upper_foot_charts.append(harmonic_disk_chart(mesh,layer,[p.index for p in members],3.0+3.0*len(upper_foot_charts)))
    shoulder_chart=harmonic_disk_chart(mesh,layer,shoulder,9.0)
    return {
        'foot_polygons':len(feet),
        'shoulder_patch_polygons':len(shoulder),
        'total_reprojected_polygons':len(selected),
        'harmonic_upper_foot_charts':upper_foot_charts,
        'harmonic_shoulder_chart':shoulder_chart,
    }

def transfer_source_seams(source_mesh, source_uv, clone_mesh):
    """Reuse only the original UV cuts, never its overlapping coordinates."""
    refs=defaultdict(list)
    for poly in source_mesh.polygons:
        for i,loop in enumerate(poly.loop_indices):
            next_loop=poly.loop_indices[(i+1)%len(poly.loop_indices)]
            v0,v1=poly.vertices[i],poly.vertices[(i+1)%len(poly.vertices)]
            refs[tuple(sorted((v0,v1)))].append((v0,loop,v1,next_loop))
    clone_edges={tuple(sorted(edge.vertices)):edge for edge in clone_mesh.edges}
    seams=0
    for key,items in refs.items():
        edge=clone_edges[key]
        if len(items)!=2:
            edge.use_seam=True;seams+=1;continue
        a,b=items
        auv={a[0]:source_uv.data[a[1]].uv,a[2]:source_uv.data[a[3]].uv}
        buv={b[0]:source_uv.data[b[1]].uv,b[2]:source_uv.data[b[3]].uv}
        discontinuous=any((auv[vertex]-buv[vertex]).length>1e-6 for vertex in key)
        edge.use_seam=discontinuous
        if discontinuous:seams+=1
    return seams

def make_checker(clone):
    mat=bpy.data.materials.new('__BODY_UV_CHECKER__');mat.use_nodes=True
    nodes=mat.node_tree.nodes;links=mat.node_tree.links; nodes.clear()
    output=nodes.new('ShaderNodeOutputMaterial'); bsdf=nodes.new('ShaderNodeBsdfPrincipled'); tex=nodes.new('ShaderNodeTexChecker'); coord=nodes.new('ShaderNodeTexCoord')
    tex.inputs['Scale'].default_value=40;tex.inputs['Color1'].default_value=(.08,.08,.08,1);tex.inputs['Color2'].default_value=(.85,.85,.85,1);bsdf.inputs['Roughness'].default_value=.8
    links.new(coord.outputs['UV'],tex.inputs['Vector']);links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);links.new(bsdf.outputs['BSDF'],output.inputs['Surface'])
    clone.data.materials.append(mat)

def render_checker(clone):
    sc=bpy.context.scene
    hidden_state={obj:obj.hide_render for obj in sc.objects}
    previous_camera=sc.camera
    for obj in sc.objects: obj.hide_render=(obj!=clone)
    cam_data=bpy.data.cameras.new('__UV_AUDIT_CAMERA__');cam=bpy.data.objects.new('__UV_AUDIT_CAMERA__',cam_data);sc.collection.objects.link(cam);cam.location=(3,-6,1.15);target=Vector((0,0,.9));cam.rotation_euler=(target-Vector(cam.location)).to_track_quat('-Z','Y').to_euler();cam_data.type='ORTHO';cam_data.ortho_scale=2.15;sc.camera=cam
    light_data=bpy.data.lights.new('__UV_AUDIT_LIGHT__','AREA');light_data.energy=900;light_data.shape='DISK';light_data.size=4;light=bpy.data.objects.new('__UV_AUDIT_LIGHT__',light_data);sc.collection.objects.link(light);light.location=(2,-3,4)
    sc.render.engine='BLENDER_EEVEE';sc.render.resolution_x=700;sc.render.resolution_y=900;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.filepath=str(CHECKER);bpy.ops.render.render(write_still=True)
    sc.camera=previous_camera
    for obj,value in hidden_state.items():
        if obj.name in bpy.data.objects:obj.hide_render=value
    bpy.data.objects.remove(cam,do_unlink=True);bpy.data.objects.remove(light,do_unlink=True)

def svg(tris):
    lines=[]
    for p,_ in tris: lines.append('<polygon points="'+' '.join(f'{42+x*780:.3f},{42+(1-y)*780:.3f}' for x,y in p)+'" fill="#8eb5a1" fill-opacity=".32" stroke="#274b3b" stroke-width=".45"/>')
    SVG.write_text('<?xml version="1.0" encoding="UTF-8"?><svg xmlns="http://www.w3.org/2000/svg" width="864" height="870"><rect width="100%" height="100%" fill="white"/><text x="42" y="25" font-family="sans-serif" font-size="17" font-weight="bold">UV_Body_Pixel — actual loop triangles</text><rect x="42" y="42" width="780" height="780" fill="#fbfbfb" stroke="#222"/>'+''.join(lines)+'<text x="42" y="850" font-family="sans-serif" font-size="14">Texture size and global pixel density remain TBD.</text></svg>',encoding='utf8')

def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False)
    body=bpy.data.objects[BODY];rig=bpy.data.objects[RIG]
    if SCENE not in bpy.data.scenes or body.find_armature()!=rig:raise RuntimeError('Required source scene/body/rig binding is absent.')
    before=protected(body,rig);source_uv=body.data.uv_layers.active;clone=clone_basis(body)
    seam_count=transfer_source_seams(body.data,source_uv,clone.data)
    cloned_uv=clone.data.uv_layers.new(name='__SOURCE_UV_REPACK__',do_init=False)
    for destination,source in zip(cloned_uv.data,source_uv.data):
        destination.uv=source.uv
    patch_counts=repair_source_uv_patches(clone)
    directional_face_counts={}
    bpy.context.view_layer.objects.active=clone;clone.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    # Repack the broad directional components as distinct non-overlapping
    # islands.  No mesh topology is changed.
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(rotate=True,rotate_method='ANY',margin_method='SCALED',margin=.018,merge_overlap=False,shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    cloned_uv=clone.data.uv_layers.active
    clone_audit,_=audit(clone.data,cloned_uv)
    clone_islands=islands(clone.data,cloned_uv)
    overlap_island_geometry=island_geometry_summary(clone.data,cloned_uv,clone_audit.get('overlap_pairs_by_island',{}))
    if any(clone_audit[k] for k in ('zero_area_triangles','outside_unit_square_triangles','positive_area_self_overlap_pairs')):
        clone_mesh=clone.data;bpy.data.objects.remove(clone,do_unlink=True)
        if clone_mesh.users==0:bpy.data.meshes.remove(clone_mesh)
        report={'status':'blocked','method':'Basis-only clone; preserve author charts and seam cuts; complete foot/shoulder patch ABF plus harmonic disk repair; average scale and pack','source':str(SOURCE),'blender_version':bpy.app.version_string,'source_seams_transferred_to_clone':seam_count,'reprojected_anatomical_patches':patch_counts,'clone_uv_audit':clone_audit,'clone_uv_islands':clone_islands,'overlap_island_geometry':overlap_island_geometry,'blocker':'The repaired source atlas still has positive-area self-overlaps. It is rejected before any UV values are transferred to the preserved source body.','scope_limit':'No output blend, checker render, texture readiness, or replacement of body_uv_ready_v5.blend is produced by this failed attempt.'}
        REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({'status':report['status'],'audit':clone_audit,'islands':clone_islands},ensure_ascii=False));return
    if cloned_uv is None or len(cloned_uv.data)!=len(body.data.loops):raise RuntimeError('Clone UV loop count cannot be transferred safely.')
    original=body.data.uv_layers.active; original.name=PRESERVED
    if body.data.uv_layers.get(UV):body.data.uv_layers.remove(body.data.uv_layers[UV])
    dest=body.data.uv_layers.new(name=UV,do_init=False)
    for d,s in zip(dest.data,cloned_uv.data):d.uv=s.uv
    body.data.uv_layers.active=dest
    for x in body.data.uv_layers:x.active_render=(x==dest)
    after=protected(body,rig)
    if before!=after:raise RuntimeError('Transfer changed protected body or rig data.')
    final_audit,tris=audit(body.data,dest)
    if any(final_audit[k] for k in ('zero_area_triangles','outside_unit_square_triangles','positive_area_self_overlap_pairs')):raise RuntimeError('Transferred anatomy UV failed bounded audit: '+repr(final_audit))
    island_report=islands(body.data,dest)
    # A numerically non-overlapping chart made of one island per polygon is
    # explicitly not an anatomy-oriented painting layout.  Record the bounded
    # failure and stop before saving an anatomy candidate blend.
    if island_report['single_polygon_islands']:
        clone_mesh=clone.data;bpy.data.objects.remove(clone,do_unlink=True)
        if clone_mesh.users==0:bpy.data.meshes.remove(clone_mesh)
        report={'status':'blocked','method':'Basis-only clone; preserve author charts and seam cuts; complete foot/shoulder patch ABF plus harmonic disk repair; average scale and pack','source':str(SOURCE),'blender_version':bpy.app.version_string,'source_seams_transferred_to_clone':seam_count,'reprojected_anatomical_patches':patch_counts,'uv_audit':final_audit,'uv_islands':island_report,'protected_body_rig_weights':'unchanged','blocker':'The repaired atlas still produced single-polygon islands. This is not a meaningful head/torso/limb paint layout, so no body UV result is accepted.','scope_limit':'Do not treat this failed experiment as texture-ready or as an approved replacement for body_uv_ready_v5.blend.'}
        REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        print(json.dumps(report,ensure_ascii=False,indent=2));return
    make_checker(clone);render_checker(clone);svg(tris)
    clone_mesh=clone.data;bpy.data.objects.remove(clone,do_unlink=True)
    if clone_mesh.users==0:bpy.data.meshes.remove(clone_mesh)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
    report={'status':'pass','method':'Basis-only clone; preserve author charts and seam cuts; complete foot/shoulder patch ABF plus harmonic disk repair; average scale and pack; transfer loop UV only','source':str(SOURCE),'source_sha256':digest(SOURCE),'output':str(OUT),'output_sha256':digest(OUT),'blender_version':bpy.app.version_string,'scene':SCENE,'source_seams_transferred_to_clone':seam_count,'reprojected_anatomical_patches':patch_counts,'uv_layers':[x.name for x in body.data.uv_layers],'active_uv':body.data.uv_layers.active.name,'active_render_uv':next(x.name for x in body.data.uv_layers if x.active_render),'uv_audit':final_audit,'uv_islands':island_report,'checker_render':CHECKER.name,'uv_layout':SVG.name,'protected_body_rig_weights':'unchanged','key_1_value':body.data.shape_keys.key_blocks['Key 1'].value,'rig_bones':len(rig.data.bones),'scope_limit':'Body UV preparation and checker render only; texture resolution, global pixel density, final pixel painting, animation, clothing/hair fitting, and runtime acceptance remain TBD.'}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
