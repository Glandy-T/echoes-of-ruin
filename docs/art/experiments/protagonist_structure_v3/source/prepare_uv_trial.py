"""Editable per-part UV calibration, not the final pixel-art atlas/density."""
import bpy,bmesh,math,json
from collections import defaultdict
from pathlib import Path

def signature(mesh,p):return tuple(sorted(tuple(mesh.vertices[v].co) for v in p.vertices))
def mark_structural_seams(ob):
    mesh=ob.data;labels={};edges={}
    for p in mesh.polygons:
        center=sum((mesh.vertices[v].co for v in p.vertices),mesh.vertices[p.vertices[0]].co*0)/len(p.vertices)
        kind=mesh.attributes['surface_kind'].data[p.index].value;comp=mesh.attributes['raw_component_id'].data[p.index].value
        if ob.name.startswith('Robe'):
            family=0 if kind in (0,4) else kind;label=(family,center.x>-.012)
        elif ob.name.startswith('Hair'):
            label=('back',) if center.x<-.03 else ('front',center.z>0)
        else:
            if kind in (3,5,6):
                name={3:'leg',5:'torso',6:'arm'}[kind];side=center.z>0 if kind!=5 else None
                label=(name,side,'cap') if len(p.vertices)>4 else (name,side,center.x>(-.02 if kind==3 else -.012))
            elif comp in (0,19):label=('foot',comp,p.normal.y>0)
            elif comp in (3,20):label=('hand',comp,center.x>-.006)
            else:label=('head',center.x>0)
        labels[p.index]=label
        vs=list(p.vertices)
        for a,b in zip(vs,vs[1:]+vs[:1]):edges.setdefault(tuple(sorted((a,b))),[]).append(p.index)
    count=0
    for edge in mesh.edges:
        linked=edges.get(tuple(sorted(edge.vertices)),[])
        edge.use_seam=len(linked)!=2 or len({labels[f] for f in linked})>1
        count+=int(edge.use_seam)
    return count
def uv_metrics(mesh):
    uv=mesh.uv_layers.active.data;edge_faces={};adj={p.index:set() for p in mesh.polygons}
    for p in mesh.polygons:
        inds=list(p.loop_indices)
        for i,a in enumerate(inds):
            b=inds[(i+1)%len(inds)];va,vb=mesh.loops[a].vertex_index,mesh.loops[b].vertex_index
            key=tuple(sorted((va,vb)));data={va:tuple(uv[a].uv),vb:tuple(uv[b].uv)};edge_faces.setdefault(key,[]).append((p.index,data))
    for linked in edge_faces.values():
        for i,(fa,a) in enumerate(linked):
            for fb,b in linked[i+1:]:
                if all(max(abs(a[v][k]-b[v][k]) for k in (0,1))<1e-6 for v in a):adj[fa].add(fb);adj[fb].add(fa)
    seen=set();islands=[]
    for p in mesh.polygons:
        if p.index in seen:continue
        stack=[p.index];seen.add(p.index);group=[]
        while stack:
            fi=stack.pop();group.append(fi)
            for n in adj[fi]:
                if n not in seen:seen.add(n);stack.append(n)
        islands.append(group)
    mesh.calc_loop_triangles();degenerate=[];area=0
    for tri in mesh.loop_triangles:
        a,b,c=[uv[i].uv for i in tri.loops];value=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))*.5;area+=value
        if value<1e-12:degenerate.append(tri.polygon_index)
    return {'islands':len(islands),'faces':len(mesh.polygons),'uv_loop_count':len(uv),'outside_unit_square':sum(any(c<-1e-6 or c>1+1e-6 for c in p.uv) for p in uv),'zero_area_triangle_parent_faces':sorted(set(degenerate)),'sum_triangle_uv_area':area,'uv_space':'Independent per-part unit tile; tiles are not a shared atlas and have no final texel density.'}

# This is deliberately equivalent to independent_validation.py's exact
# triangle clipping test.  Triangles made while tessellating *one* n-gon are
# excluded: their shared interior is a triangulation detail, not two surfaces
# occupying the same UV region.
def _area(poly):
    return abs(sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[i][1]*poly[(i+1)%len(poly)][0] for i in range(len(poly))))*.5 if len(poly)>=3 else 0.0
def _clipped(subject,clip):
    def ccw(points):
        return points if sum(points[i][0]*points[(i+1)%len(points)][1]-points[i][1]*points[(i+1)%len(points)][0] for i in range(len(points)))>=0 else list(reversed(points))
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
def positive_uv_overlaps(mesh):
    dat=mesh.uv_layers.active.data;mesh.calc_loop_triangles();rows=[]
    for tri in mesh.loop_triangles:
        uv=[tuple(dat[i].uv) for i in tri.loops]
        if _area(uv)<=1e-12:continue
        xs=[p[0] for p in uv];ys=[p[1] for p in uv]
        rows.append({'face':tri.polygon_index,'uv':uv,'bbox':(min(xs),max(xs),min(ys),max(ys))})
    buckets=defaultdict(list);candidates=set()
    for i,row in enumerate(rows):
        x0,x1,y0,y1=row['bbox'];ax=max(0,min(31,int(x0*32)));bx=max(0,min(31,int(x1*32)));ay=max(0,min(31,int(y0*32)));by=max(0,min(31,int(y1*32)))
        for x in range(ax,bx+1):
            for y in range(ay,by+1):
                for j in buckets[(x,y)]:candidates.add((j,i))
                buckets[(x,y)].append(i)
    hits=[]
    for i,j in sorted(candidates):
        a,b=rows[i],rows[j]
        if a['face']==b['face']:continue
        x0,x1,y0,y1=a['bbox'];u0,u1,w0,w1=b['bbox']
        if x1<u0-1e-9 or u1<x0-1e-9 or y1<w0-1e-9 or w1<y0-1e-9:continue
        value=_area(_clipped(a['uv'],b['uv']))
        if value>1e-10:hits.append({'face_a':a['face'],'face_b':b['face'],'area':value})
    return hits
def locally_reproject_overlap_faces(ob,hits):
    # Cut only the boundaries of faces that participate in a real cross-face
    # overlap.  The rest of the broad structural charts remain untouched.
    mesh=ob.data;selected={h['face_a'] for h in hits}|{h['face_b'] for h in hits}
    if not selected:return []
    for edge in mesh.edges:
        linked=[p.index for p in mesh.polygons if edge.vertices[0] in p.vertices and edge.vertices[1] in p.vertices]
        if any(i in selected for i in linked) and any(i not in selected for i in linked):edge.use_seam=True
    bpy.context.tool_settings.mesh_select_mode=(False,False,True)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT')
    edit=bmesh.from_edit_mesh(mesh);edit.faces.ensure_lookup_table()
    for i in selected:edit.faces[i].select_set(True)
    edit.select_flush_mode();bmesh.update_edit_mesh(mesh,loop_triangles=False,destructive=False)
    if sum(f.select for f in edit.faces)!=len(selected):raise RuntimeError('Overlap correction escaped selected faces')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.02,correct_aspect=False,scale_to_bounds=True)
    bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.average_islands_scale();bpy.ops.uv.pack_islands(rotate=True,margin=.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    return sorted(selected)
def locally_reproject_collapsed_faces(ob,faces):
    """Project only confirmed zero-area parents, with explicit selection proof."""
    mesh=ob.data;faces=sorted(set(faces))
    if not faces:return []
    for edge in mesh.edges:
        if any(edge.vertices[0] in mesh.polygons[i].vertices and edge.vertices[1] in mesh.polygons[i].vertices for i in faces):edge.use_seam=True
    bpy.context.tool_settings.mesh_select_mode=(False,False,True)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT')
    edit=bmesh.from_edit_mesh(mesh);edit.faces.ensure_lookup_table()
    for i in faces:edit.faces[i].select_set(True)
    edit.select_flush_mode();bmesh.update_edit_mesh(mesh,loop_triangles=False,destructive=False)
    if sum(f.select for f in edit.faces)!=len(faces):raise RuntimeError('Local UV correction escaped selected faces')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.02,correct_aspect=False,scale_to_bounds=True)
    bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.average_islands_scale();bpy.ops.uv.pack_islands(rotate=True,margin=.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    return faces

def prepare(parts,exp):
    layouts=exp/'uv_trial';layouts.mkdir(exist_ok=True);stats={}
    for ob in parts:
        for selected in bpy.context.selected_objects:selected.select_set(False)
        bpy.context.view_layer.objects.active=ob;ob.select_set(True)
        mesh=ob.data;normal_map={signature(mesh,p):{tuple(mesh.vertices[mesh.loops[li].vertex_index].co):tuple(mesh.corner_normals[li].vector) for li in p.loop_indices} for p in mesh.polygons}
        layer=mesh.uv_layers.new(name='UV_Trial') if not mesh.uv_layers else mesh.uv_layers[0];mesh.uv_layers.active=layer
        seam_count=mark_structural_seams(ob) if not ob.name.startswith('Preserved') else 0
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        if ob.name.startswith('Preserved'):
            bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.02,area_weight=0.0,correct_aspect=False,scale_to_bounds=True)
        else:
            bpy.ops.uv.unwrap(method='ANGLE_BASED',fill_holes=True,correct_aspect=False,margin=.02)
            bpy.ops.uv.pack_islands(rotate=True,margin=.02)
        bpy.ops.object.mode_set(mode='OBJECT');mesh=ob.data
        bad=uv_metrics(mesh)['zero_area_triangle_parent_faces']
        if bad:
            # Keep the broad seam charts; project only collapsed narrow source
            # patches rather than replacing the entire part by many tiny charts.
            locally_reproject_collapsed_faces(ob,bad);mesh=ob.data
        overlap_before=positive_uv_overlaps(mesh);overlap_reprojected=[]
        # Two passes are enough for this fixed source: a pass can expose an
        # adjacent fold after its first local chart was separated.  Failing
        # closed is preferable to silently shipping a remaining overlap.
        for _ in range(2):
            hits=positive_uv_overlaps(mesh)
            if not hits:break
            overlap_reprojected.extend(locally_reproject_overlap_faces(ob,hits));mesh=ob.data
        overlap_after=positive_uv_overlaps(mesh)
        if overlap_after:raise RuntimeError('Positive UV overlap remains after local correction: '+ob.name)
        trailing_bad=uv_metrics(mesh)['zero_area_triangle_parent_faces']
        if trailing_bad:
            locally_reproject_collapsed_faces(ob,trailing_bad);mesh=ob.data
        if positive_uv_overlaps(mesh) or uv_metrics(mesh)['zero_area_triangle_parent_faces']:
            raise RuntimeError('UV local correction did not converge: '+ob.name)
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.export_layout(filepath=str(layouts/(ob.name+'.svg')),export_all=True,modified=False,mode='SVG',size=(1024,1024),opacity=.3)
        bpy.ops.object.mode_set(mode='OBJECT');mesh=ob.data
        restored=[]
        for p in mesh.polygons:
            lookup=normal_map[signature(mesh,p)]
            restored.extend(lookup[tuple(mesh.vertices[mesh.loops[li].vertex_index].co)] for li in p.loop_indices)
        mesh.normals_split_custom_set(restored);mesh.update();stats[ob.name]=uv_metrics(mesh)
        stats[ob.name]['layout']='uv_trial/'+ob.name+'.svg';stats[ob.name]['marked_seam_edges']=seam_count;stats[ob.name]['locally_reprojected_collapsed_faces']=sorted(set(bad+trailing_bad));stats[ob.name]['positive_overlap_pairs_before']=len(overlap_before);stats[ob.name]['locally_reprojected_overlap_faces']=sorted(set(overlap_reprojected));stats[ob.name]['positive_overlap_pairs_after']=0;ob.select_set(False)
    (exp/'source/uv_trial_metrics.json').write_text(json.dumps(stats,indent=2),encoding='utf-8')
    return {'status':'Editable seam-based calibration; not final painting UV or a shared atlas. Shoulder/hip body joins and source hair topology still need deformation cleanup.','method':'Structural front/back and surface-role seams with angle-based unwrap; only preserved unclassified fragments use automatic projection. Original corner normals restored after edit-mode operation.','parts':stats}
