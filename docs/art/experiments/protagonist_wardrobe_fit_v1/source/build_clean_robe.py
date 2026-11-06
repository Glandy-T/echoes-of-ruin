"""Build a bounded clean outer robe shell from the diagnosed v2 raw garment.

This is intentionally a repair, not a redesign: it retains the diagnostic
strict-outer triangles at their original coordinates, removes only the 42
faces implicated by exact crossings, welds only *exactly coincident* vertices,
and fills only non-semantic boundary loops.  Neck, hem and two cuffs remain
open before the inward solid-shell operation.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from pathlib import Path
import hashlib, json, math

import bpy
import bmesh
from mathutils import Vector

EXP = Path(__file__).resolve().parents[1]
RAW = EXP.parent / "protagonist_tripo_robe_v2/model/protagonist_tripo_robe_v2_raw.glb"
DIAG = EXP / "source/robe_repair_diagnosis.json"
OUT_BLEND = EXP / "scratch/outer_extraction_diagnostic.blend"
OUT_GLB = EXP / "scratch/outer_extraction_diagnostic.glb"
REPORT = EXP / "source/clean_robe_report.json"
QA = EXP.parent / "protagonist_tripo_body_v1/source/body_topology_check.py"
THICKNESS = 0.00693


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def import_mesh(path):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [o for o in set(bpy.context.scene.objects)-before if o.type == 'MESH']
    if len(meshes) != 1: raise RuntimeError(f"expected one raw mesh, got {len(meshes)}")
    ob = meshes[0]; ob.name = 'Robe_Raw_Reference'
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); ob.select_set(False)
    return ob


def exact_qa():
    # Reuse the known-correct body classifier, never a copied/mutated variant.
    src = QA.read_text(encoding='utf-8').split("before={'glb':")[0]
    scope = {'__file__': str(QA), '__name__': 'clean_robe_qa'}
    exec(compile(src, str(QA), 'exec'), scope)
    return scope


def topology_edges(mesh):
    uses = defaultdict(list)
    for p in mesh.polygons:
        for e in p.edge_keys: uses[tuple(sorted(e))].append(p.index)
    return uses


def face_components(mesh):
    uses = topology_edges(mesh); nbr = defaultdict(set)
    for fs in uses.values():
        if len(fs) == 2: nbr[fs[0]].add(fs[1]); nbr[fs[1]].add(fs[0])
    todo=set(range(len(mesh.polygons))); out=[]
    while todo:
        seed=next(iter(todo)); q=[seed]; comp=set()
        while q:
            f=q.pop()
            if f not in todo: continue
            todo.remove(f); comp.add(f); q.extend(nbr[f] & todo)
        out.append(comp)
    return sorted(out,key=len,reverse=True)


def boundary_loops(mesh):
    uses=topology_edges(mesh); edges=[e for e,fs in uses.items() if len(fs)==1]
    adj=defaultdict(list)
    for a,b in edges: adj[a].append(b); adj[b].append(a)
    remaining=set(edges); loops=[]; branches=[]
    while remaining:
        edge=next(iter(remaining)); start,a=edge; prev=start; cur=a; path=[start,cur]; remaining.remove(edge)
        ok=True
        while cur!=start:
            candidates=[n for n in adj[cur] if n!=prev and tuple(sorted((cur,n))) in remaining]
            if len(candidates)!=1: ok=False; break
            nxt=candidates[0]; remaining.remove(tuple(sorted((cur,nxt))))
            prev,cur=cur,nxt; path.append(cur)
            if len(path)>len(edges)+1: ok=False; break
        if ok and len(path)>3: loops.append(path[:-1])
        else: branches.append(path)
    return loops,branches


def make_mesh_from_source(src, source_faces, name):
    # Preserve raw vertex identity (and therefore all visible coordinates).
    # Exact-coordinate welding is deliberately deferred: it can turn two
    # non-connected strips that merely touch at a quantized position into a
    # branched boundary.
    coord_to_new={}; verts=[]; faces=[]
    for fi in sorted(source_faces):
        face=[]
        for vi in src.data.polygons[fi].vertices:
            co=src.data.vertices[vi].co; key=vi
            if key not in coord_to_new: coord_to_new[key]=len(verts); verts.append(tuple(co))
            face.append(coord_to_new[key])
        if len(set(face))==3: faces.append(face)
    me=bpy.data.meshes.new(name+'Mesh'); me.from_pydata(verts,[],faces); me.update()
    ob=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(ob); return ob


def loop_kind(mesh, loop):
    pts=[mesh.vertices[v].co for v in loop]; z=sum(p.z for p in pts)/len(pts); ay=sum(abs(p.y) for p in pts)/len(pts)
    if z < .12: return 'hem'
    if z > .86: return 'neck'
    if .45 < z < .83 and ay > .16: return 'cuff_pos' if sum(p.y for p in pts)>=0 else 'cuff_neg'
    return 'patch'


def fill_loop(mesh, loop):
    bm=bmesh.new(); bm.from_mesh(mesh); bm.verts.ensure_lookup_table()
    edges=[]
    for a,b in zip(loop,loop[1:]+loop[:1]):
        e=bm.edges.get((bm.verts[a],bm.verts[b]))
        if not e: bm.free(); raise RuntimeError('boundary edge disappeared before fill')
        edges.append(e)
    bmesh.ops.triangle_fill(bm, edges=edges, use_beauty=True); bm.to_mesh(mesh); bm.free(); mesh.update()


def delete_non_main_components(ob):
    comps=face_components(ob.data); keep=comps[0]
    if len(comps)==1: return [len(c) for c in comps]
    bm=bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in range(len(bm.faces)) if i not in keep], context='FACES')
    bm.to_mesh(ob.data); bm.free(); ob.data.update(); return [len(c) for c in comps]


def add_inward_solid_shell(ob):
    # Negative offset places added thickness toward the classified inner side.
    mod=ob.modifiers.new('Inward thickness 0.00693','SOLIDIFY')
    mod.thickness=THICKNESS; mod.offset=-1; mod.use_even_offset=True; mod.use_quality_normals=True
    bpy.context.view_layer.objects.active=ob; ob.select_set(True); bpy.ops.object.modifier_apply(modifier=mod.name); ob.select_set(False)


def camera_and_material(raw, repaired):
    for ob,col in ((raw,(.35,.08,.08,1)),(repaired,(.14,.42,.68,1))):
        ma=bpy.data.materials.new(ob.name+'_mat'); ma.diffuse_color=col; ob.data.materials.append(ma)
    # Same saved orthographic front camera is a visual-review entrypoint; raw is
    # initially hidden so the repaired silhouette can be inspected without overlap.
    cam=bpy.data.cameras.new('SameCamera_OuterRepair'); cam.type='ORTHO'; cam.ortho_scale=1.2
    co=bpy.data.objects.new('SameCamera_OuterRepair',cam); bpy.context.scene.collection.objects.link(co)
    co.location=(0,-2.4,.52); co.rotation_euler=(math.radians(90),0,0); bpy.context.scene.camera=co
    raw.hide_render=True; raw.hide_viewport=True


def main():
    before=sha(RAW); diag=json.loads(DIAG.read_text(encoding='utf-8')); qa=exact_qa()
    strict={r['face'] for r in diag['face_rows'] if r['classification']=='outer'}
    bad=set(diag['candidate_audits']['strict_outer_only']['crossing_implicated_source_faces'])
    if len(bad)!=42: raise RuntimeError(f'expected 42 exact crossing faces, got {len(bad)}')
    bpy.ops.wm.read_factory_settings(use_empty=True); raw=import_mesh(RAW)
    thin=make_mesh_from_source(raw, strict-bad, 'Robe_Outer_Thin_Repaired')
    pre_components=delete_non_main_components(thin)
    loops,branches=boundary_loops(thin.data)
    if branches:
        # The classified outer sheet is already intersection-free, but these
        # are T/branch networks, not simple holes.  Filling them would choose
        # an arbitrary surface across sleeve-root/strip ambiguities and risks
        # capping an intended opening.  Preserve the safe thin result instead.
        thin_qa={'topology':qa['topology'](thin.data),'crossings':qa['self_intersections'](thin.data,thin.matrix_world)}
        camera_and_material(raw,thin); raw.hide_render=True; raw.hide_viewport=True
        OUT_BLEND.parent.mkdir(parents=True,exist_ok=True); bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
        bpy.context.view_layer.objects.active=thin; thin.select_set(True); bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', use_selection=True); thin.select_set(False)
        after=sha(RAW)
        result={'status':'BLOCKED_OPEN_BOUNDARY_SCOPE','raw_sha256':before,'source_unchanged':before==after,'method':{'preserved_strict_outer_faces':len(strict-bad),'removed_exact_crossing_faces':sorted(bad),'discarded_disconnected_component_face_counts':pre_components[1:],'no_coordinate_edits':True},'thin_outer':thin_qa,'boundary_blocker':{'simple_loops_found':len(loops),'branched_boundary_networks':len(branches),'reason':'The extracted outer surface has branched boundary networks. They cannot be classified as patch holes versus the neck/hem/cuff openings without adding new surface interpretation beyond the evidence.'},'outputs':{'blend':str(OUT_BLEND),'glb':str(OUT_GLB),'same_camera':'SameCamera_OuterRepair'}}
        REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(result,ensure_ascii=False)); return
    by_kind=defaultdict(list)
    for loop in loops: by_kind[loop_kind(thin.data,loop)].append(loop)
    semantic={}
    for k in ('hem','neck','cuff_pos','cuff_neg'):
        if not by_kind[k]: raise RuntimeError(f'missing intended {k} opening')
        semantic[k]=max(by_kind[k],key=len)
    patches=[loop for loop in loops if loop not in semantic.values()]
    for loop in patches: fill_loop(thin.data,loop)
    remaining,branches_after=boundary_loops(thin.data)
    if branches_after or len(remaining)!=4: raise RuntimeError(f'patch result has {len(remaining)} loops / {len(branches_after)} branches, not 4 simple openings')
    thin_qa={'topology':qa['topology'](thin.data),'crossings':qa['self_intersections'](thin.data,thin.matrix_world)}
    if thin_qa['topology']['nonmanifold_edges'] or thin_qa['topology']['degenerate_faces'] or thin_qa['crossings']['true_nonadjacent_intersection_count']:
        raise RuntimeError('thin outer QA failed')
    solid=thin.copy(); solid.data=thin.data.copy(); solid.name='Robe_Clean_Solid'; bpy.context.scene.collection.objects.link(solid)
    add_inward_solid_shell(solid)
    solid_qa={'topology':qa['topology'](solid.data),'crossings':qa['self_intersections'](solid.data,solid.matrix_world)}
    if solid_qa['topology']['boundary_edges'] or solid_qa['topology']['nonmanifold_edges'] or solid_qa['topology']['degenerate_faces'] or solid_qa['crossings']['true_nonadjacent_intersection_count']:
        raise RuntimeError('solid shell QA failed; local curvature repair required')
    camera_and_material(raw,solid); thin.hide_render=True; thin.hide_viewport=True
    OUT_BLEND.parent.mkdir(parents=True,exist_ok=True); bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    bpy.context.view_layer.objects.active=solid; solid.select_set(True); bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', use_selection=True); solid.select_set(False)
    after=sha(RAW)
    result={'status':'PASS' if before==after else 'FAIL_SOURCE_MUTATED','raw_sha256':before,'source_unchanged':before==after,'method':{'preserved_strict_outer_faces':len(strict-bad),'removed_exact_crossing_faces':sorted(bad),'exact_coordinate_vertex_weld_only':True,'discarded_disconnected_component_face_counts':pre_components[1:],'patched_nonsemantic_loops':len(patches),'semantic_openings':['neck','hem','cuff_pos','cuff_neg'],'thickness':THICKNESS},'thin_outer':thin_qa,'solid_shell':solid_qa,'outputs':{'blend':str(OUT_BLEND),'glb':str(OUT_GLB),'same_camera':'SameCamera_OuterRepair'}}
    REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
