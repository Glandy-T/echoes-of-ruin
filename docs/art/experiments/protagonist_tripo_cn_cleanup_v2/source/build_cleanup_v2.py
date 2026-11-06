"""Evidence-led v2 hair cleanup builder.

Builds from immutable v1: removes the visually confirmed left loop and fairs
only the lowest hair region, with per-move oriented-triangle backoff. Existing
corner normals and nonhair geometry are retained. Use --audit after Blender's
argument separator to reproduce the earlier source-selection diagnostic.
"""
from pathlib import Path
import json,sys,itertools
import bpy, bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

EXP = Path(__file__).resolve().parent.parent
V1 = EXP.parent / "protagonist_tripo_cn_cleanup_v1"
V1_BLEND = V1 / "model" / "protagonist_cn_cleanup_v1.blend"
OUT = EXP / "source" / "v2_seed_audit.json"
EVID = EXP / "evidence"
LEFT_RAW = {2796,2799,2800,2801,2802,2805,2806,2857,2858,2928,2930,2936,2937,3019}
RIGHT_RAW = {1620,1621,1622,1623,1624,1625,1626,1627,1633,1746,1747,1750,1751,1753}
OUT_BLEND=EXP/'model/protagonist_cn_cleanup_v2.blend'; OUT_GLB=EXP/'model/protagonist_cn_cleanup_v2.glb'; REPORT=EXP/'source/build_report.json'


def camera_ray(scene, camera, x, y):
    """Return a world-space ray for a 1280x720 QA camera pixel (top-left origin)."""
    width, height = scene.render.resolution_x, scene.render.resolution_y
    u, v = (x + .5) / width, 1.0 - (y + .5) / height
    bl, tl, tr, br = camera.data.view_frame(scene=scene)
    local = (bl * ((1-u)*(1-v)) + tl * ((1-u)*v) + tr * (u*v) + br * (u*(1-v)))
    origin = camera.matrix_world.translation
    direction = (camera.matrix_world.to_3x3() @ local).normalized()
    return origin, direction


def raycast_seed(scene, camera, x, y):
    origin, direction = camera_ray(scene, camera, x, y)
    hit, loc, normal, face_index, obj, matrix = scene.ray_cast(bpy.context.evaluated_depsgraph_get(), origin, direction)
    if not hit or obj is None or obj.type != 'MESH':
        return {"pixel": [x, y], "hit": False}
    raw = obj.data.attributes.get("raw_obj_face_index")
    comp = obj.data.attributes.get("raw_component_id")
    return {"pixel": [x, y], "hit": True, "object": obj.name, "candidate_polygon_index": face_index,
            "raw_obj_face_index": int(raw.data[face_index].value) if raw else None,
            "raw_component_id": int(comp.data[face_index].value) if comp else None,
            "location": list(loc), "normal": list(normal)}


def make_emission(name, rgb):
    mat=bpy.data.materials.new(name); mat.use_nodes=True
    nodes=mat.node_tree.nodes; nodes.clear(); out=nodes.new('ShaderNodeOutputMaterial'); em=nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value=(*rgb,1.0); em.inputs['Strength'].default_value=1.0; mat.node_tree.links.new(em.outputs[0],out.inputs[0])
    return mat


def render_overlay(scene, obj):
    """Diagnostic-only material assignment; mesh, normals and transform restore unchanged."""
    raw=obj.data.attributes['raw_obj_face_index']; comp=obj.data.attributes['raw_component_id']
    left=[p.index for p in obj.data.polygons if int(raw.data[p.index].value) in LEFT_RAW]
    right=[p.index for p in obj.data.polygons if int(raw.data[p.index].value) in RIGHT_RAW]
    if len(left)!=len(LEFT_RAW) or len(right)!=len(RIGHT_RAW): raise RuntimeError('Proposed raw-face selection is missing from v1 baseline')
    if any(int(comp.data[i].value)!=6 for i in left+right): raise RuntimeError('Selection escaped hair component 6')
    old_engine,old_camera=scene.render.engine,scene.camera; oldslots=list(obj.data.materials); oldidx=[p.material_index for p in obj.data.polygons]
    obj.data.materials.clear()
    for m in (make_emission('TEMP_V2_GRAY',(.42,.44,.47)),make_emission('TEMP_V2_LEFT',(1,.22,.02)),make_emission('TEMP_V2_RIGHT',(.85,.03,.8))):obj.data.materials.append(m)
    ls,rs=set(left),set(right)
    for p in obj.data.polygons:p.material_index=1 if p.index in ls else (2 if p.index in rs else 0)
    scene.render.engine='BLENDER_EEVEE'; scene.render.resolution_x=1280; scene.render.resolution_y=720; scene.render.resolution_percentage=100; scene.render.image_settings.file_format='PNG'
    EVID.mkdir(exist_ok=True); rec=[]
    for view in ('front','head_back','side'):
        scene.camera=bpy.data.objects['QA_'+view]; path=EVID/f'proposed_hair_cleanup_{view}.png'; scene.render.filepath=str(path); bpy.ops.render.render(write_still=True)
        import hashlib; rec.append({'view':view,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    obj.data.materials.clear()
    for m in oldslots:obj.data.materials.append(m)
    for p,i in zip(obj.data.polygons,oldidx):p.material_index=i
    scene.render.engine,scene.camera=old_engine,old_camera
    legend={'purpose':'Proposed v2 visual selection only: orange=left small loop face set; magenta=right rear raised-strip face set. Gray=v1 context. No deletion, normal edit, hole patch, or silhouette edit has occurred.','source_blend':str(V1_BLEND),'left_raw_face_indices_zero_based':sorted(LEFT_RAW),'right_raw_face_indices_zero_based':sorted(RIGHT_RAW),'selection_method':'QA_head_back camera projection of actual C6 boundary edges; direct rays were occluded at visible outline pixels.','anticipated_patch_if_approved':'Delete selected ribbon faces only, preserve all other C6 faces, restore retained source custom corner normals, then evaluate whether each deletion leaves a hole requiring a minimal local patch.','renders':rec}
    (EVID/'proposed_hair_cleanup_legend.json').write_text(json.dumps(legend,indent=2),encoding='utf-8')
    return legend


def build_v2():
    bpy.ops.wm.open_mainfile(filepath=str(V1_BLEND)); scene=bpy.context.scene
    source=bpy.data.objects['CN_P20_STAGE3_AFTER']; before=bpy.data.collections.new('BEFORE_V1'); after=bpy.data.collections.new('AFTER_V2'); scene.collection.children.link(before);scene.collection.children.link(after)
    for c in list(source.users_collection):c.objects.unlink(source)
    before.objects.link(source); source.name='CN_P20_V1_BEFORE'
    cand=source.copy(); cand.data=source.data.copy(); cand.name='CN_P20_V2_AFTER'; after.objects.link(cand)
    raw=cand.data.attributes['raw_obj_face_index']; comp=cand.data.attributes['raw_component_id']
    # exact source-normal map before BMesh deletes topology
    normals={(int(raw.data[p.index].value),tuple(round(x,8) for x in cand.data.vertices[cand.data.loops[li].vertex_index].co)):tuple(cand.data.corner_normals[li].vector) for p in cand.data.polygons for li in p.loop_indices}
    normals_by_face_corner={(int(raw.data[p.index].value),n):tuple(cand.data.corner_normals[li].vector) for p in cand.data.polygons for n,li in enumerate(p.loop_indices)}
    delete=[p.index for p in cand.data.polygons if int(raw.data[p.index].value) in LEFT_RAW]
    if len(delete)!=14 or any(int(comp.data[i].value)!=6 for i in delete):raise RuntimeError('approved v2 selection mismatch')
    bm=bmesh.new();bm.from_mesh(cand.data);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in delete],context='FACES');bm.to_mesh(cand.data);bm.free();cand.data.update()
    # restore every retained source split normal by raw face and local corner coordinate
    raw=cand.data.attributes['raw_obj_face_index']; targets=[]; missing=[]
    for p in cand.data.polygons:
      rid=int(raw.data[p.index].value)
      for li in p.loop_indices:
        key=(rid,tuple(round(x,8) for x in cand.data.vertices[cand.data.loops[li].vertex_index].co)); n=normals.get(key)
        if n is None:missing.append((rid,li));targets.append((0,0,1))
        else:targets.append(n)
    if missing:raise RuntimeError('normal mapping missing '+str(missing[:3]))
    cand.data.normals_split_custom_set(targets);cand.data.update()
    # Explicit bounded lower-hair fairing (raw Y = local Y;
    # object rotation maps this naturally to world Z for the QA cameras).
    comp=cand.data.attributes['raw_component_id']
    hairpolys=[p for p in cand.data.polygons if int(comp.data[p.index].value)==6]; hairverts={v for p in hairpolys for v in p.vertices}; miny=min(cand.data.vertices[v].co.y for v in hairverts); maxy=max(cand.data.vertices[v].co.y for v in hairverts)
    ef={}
    for p in hairpolys:
      ids=list(p.vertices)
      for j,a in enumerate(ids):ef.setdefault(tuple(sorted((a,ids[(j+1)%len(ids)]))),[]).append(p.index)
    adj={v:set() for v in hairverts}
    for p in hairpolys:
      ids=list(p.vertices)
      for j,a in enumerate(ids):adj[a].add(ids[(j+1)%len(ids)]);adj[a].add(ids[(j-1)%len(ids)])
    snapshot_y={v:float(cand.data.vertices[v].co.y) for v in hairverts}; fair=[]; affected=set(); rejected=[]
    original_positions=[v.co.copy() for v in cand.data.vertices]
    face_triangles={}
    vertex_faces={v:[] for v in hairverts}
    for p in hairpolys:
      # Check both diagonals of a quad, so a later exporter cannot reveal a fold
      # by choosing a different diagonal. Degeneracies already in v1 are recorded
      # separately and are not presented as repaired by this local operation.
      tris=[]
      for ids in itertools.combinations(tuple(p.vertices),3):
        a,b,c=(original_positions[i] for i in ids);cross=(b-a).cross(c-a)
        if cross.length_squared>1e-20:tris.append((ids,cross))
      face_triangles[p.index]=tris
      for v in p.vertices:vertex_faces[v].append(p.index)
    def valid_faces(indices):
      for fi in indices:
        for ids,oldcross in face_triangles[fi]:
          a,b,c=(cand.data.vertices[i].co for i in ids);newcross=(b-a).cross(c-a)
          if newcross.dot(oldcross)<=0 or newcross.length_squared<oldcross.length_squared*.0025:return False
      return True
    for v,ns in sorted(adj.items()):
      y=snapshot_y[v]
      if y<=miny+1e-9 or y>=maxy-1e-9 or y>miny+.02:continue
      vals=sorted(snapshot_y[n] for n in ns); target=vals[len(vals)//2] if len(vals)%2 else (vals[len(vals)//2-1]+vals[len(vals)//2])*.5; delta=max(-.003,min(.003,target-y))
      if abs(delta)<1e-9:continue
      accepted=None
      for exponent in range(9):
        trial=delta*(.5**exponent);cand.data.vertices[v].co.y=y+trial
        if valid_faces(vertex_faces[v]):accepted=trial;break
      if accepted is None:
        cand.data.vertices[v].co.y=y;rejected.append(v);continue
      fair.append({'vertex_id':v,'before_y':y,'after_y':y+accepted,'delta_y':accepted,'proposed_delta_y':delta,'safety_scale':accepted/delta,'one_ring_neighbors':sorted(ns)})
      affected.update(vertex_faces[v])
    if not valid_faces(face_triangles):raise RuntimeError('Final hair triangle orientation/area gate failed')
    cand.data.update()
    # Preserve original split normals for every retained face, including loops
    # next to coordinate-only fairing; do not introduce dark flat patches.
    finalnorm=[]
    for p in cand.data.polygons:
      rid=int(raw.data[p.index].value)
      for n,li in enumerate(p.loop_indices):finalnorm.append(normals_by_face_corner[(rid,n)])
    cand.data.normals_split_custom_set(finalnorm);cand.data.update()
    # Keep precisely the current v1 comparison and the new candidate. The raw
    # Tripo source remains in its own immutable experiment, not nested again.
    for name in ('BEFORE_ORIGINAL','AFTER_REPAIR'):
      coll=bpy.data.collections.get(name)
      if coll:
        for obj in list(coll.objects):bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.collections.remove(coll)
    # Semantic selections are editable groups, not a claim of animation-ready
    # mesh separation. Unclassified small fragments retain their raw-ID tags.
    for name,ids in {'Hair_Main':{6},'Robe':{2},'Head_Neck':{5},'Hands':{3,20},'Feet':{0,19}}.items():
      group=cand.vertex_groups.new(name=name)
      verts={v for p in cand.data.polygons if int(comp.data[p.index].value) in ids for v in p.vertices}
      group.add(sorted(verts),1.0,'REPLACE')
    source.hide_render=True;source.hide_set(True);before.hide_render=True;before.hide_viewport=True;after.hide_render=False;after.hide_viewport=False;cand.hide_render=False;cand.hide_set(False)
    for o in bpy.context.selected_objects:o.select_set(False)
    cand.select_set(True);bpy.context.view_layer.objects.active=cand;scene.camera=bpy.data.objects['QA_quarter']
    OUT_BLEND.parent.mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND));bpy.ops.export_scene.gltf(filepath=str(OUT_GLB),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
    report = {
      'stage':'v2_left_loop_delete_right_lock_preserved',
      'baseline_blend':str(V1_BLEND),
      'baseline_sha256':__import__('hashlib').sha256(V1_BLEND.read_bytes()).hexdigest(),
      'approved_raw_face_deletions':{'left_loop':sorted(LEFT_RAW),'right_rear_ribbon_preserved':sorted(RIGHT_RAW),'count':14},
      'mesh_counts':{'before_vertices':2536,'before_faces':2596,'after_vertices':len(cand.data.vertices),'after_faces':len(cand.data.polygons)},
      'normals':{'source_custom':True,'retained_loops_restored':len(finalnorm),'missing':len(missing),'moved_vertex_adjacent_hair_faces':sorted(affected),'method':'Original split normals retained on every surviving face, including coordinate-only hem fairing; no flat geometric normal replacement.'},
      'lower_hair_border_fairing':{'changed_vertices':fair,'rejected_vertices':rejected,'max_displacement':max([abs(x['delta_y']) for x in fair],default=0.0),'rule':'All hair vertices local y within min+0.02 excluding extent anchors; immutable one-ring neighbor median, y only, clamp .003, per-vertex step backoff.','oriented_triangle_gate':{'all_final_pass':valid_faces(face_triangles),'minimum_retained_triangle_area_ratio':0.05,'minimum_positive_orientation_dot':0,'backoff_steps':9,'checked_triangles':sum(len(x) for x in face_triangles.values()),'note':'Both diagonal choices checked for retained quads. Pre-existing zero-area triangles are outside this no-new-fold gate.'}},
      'parts_inventory':{'Hair_Main':'raw component6','Robe':'raw component2','Head_Neck':'raw component5','Hands':'raw components3 and20','Feet':'raw components0 and19','status':'Five editable semantic vertex groups; tiny residual components keep raw-ID attributes. No claim of completed mesh separation, inner garment surfaces or deformation topology.'},
      'residual_topology':{'hair_faces':len(hairpolys),'hair_min_local_y_before':miny,'hair_max_local_y_before':maxy,'hair_min_local_y_after':min(cand.data.vertices[v].co.y for v in hairverts),'hair_max_local_y_after':max(cand.data.vertices[v].co.y for v in hairverts)},
      'new_patches':0,
      'boundary':'Only exposed left loop removed; source backing hair volume remains. Broad right lock retained after visual comparison rejected cutting its middle.'
    }
    REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'v2_faces':len(cand.data.polygons),'v2_vertices':len(cand.data.vertices),'deleted':len(delete)}))


def main():
    if "--audit" not in sys.argv:
        build_v2()
        return
    bpy.ops.wm.open_mainfile(filepath=str(V1_BLEND))
    scene = bpy.context.scene
    # The v1 source collection is hidden by default; unhide and refresh before
    # deriving camera-space evidence so evaluated coordinates are not stale.
    before = bpy.data.collections.get("BEFORE_ORIGINAL")
    after = bpy.data.collections.get("AFTER_REPAIR")
    if before: before.hide_viewport = True; before.hide_render = True
    if after:
        after.hide_viewport = False; after.hide_render = False
        for candidate in after.all_objects: candidate.hide_set(False); candidate.hide_render = False
    bpy.context.view_layer.update()
    scene.render.resolution_x = 1280; scene.render.resolution_y = 720; scene.render.resolution_percentage = 100
    camera = bpy.data.objects["QA_head_back"]
    obj = bpy.data.objects["CN_P20_STAGE3_AFTER"]
    comp = obj.data.attributes["raw_component_id"]
    hair_vertices = {v for p in obj.data.polygons if int(comp.data[p.index].value) == 6 for v in p.vertices}
    projected = [world_to_camera_view(scene, camera, obj.matrix_world @ obj.data.vertices[v].co) for v in hair_vertices]
    # Coarse manual search rectangles covering only the visibly exposed loop
    # and raised rear strip in the parent-reviewed head-back image.
    regions = {"left_loop": (462, 320, 492, 360, 1), "right_strip": (700, 130, 790, 525, 2)}
    result = {"purpose": "No-save coarse camera-ray audit; hits are selection leads only.", "camera": camera.name, "hair_projected_pixel_bbox": {"min": [min(p.x for p in projected)*1280, (1-max(p.y for p in projected))*720], "max": [max(p.x for p in projected)*1280, (1-min(p.y for p in projected))*720]}, "regions": {}}
    result["sanity_center"] = raycast_seed(scene, camera, 640, 360)
    # Project actual C6 boundary edges and rank them against user-visible hints.
    edge_faces = {}
    hair_faces = [p for p in obj.data.polygons if int(comp.data[p.index].value) == 6]
    for poly in hair_faces:
        ids = list(poly.vertices)
        for i, a in enumerate(ids): edge_faces.setdefault(tuple(sorted((a, ids[(i+1) % len(ids)]))), []).append(poly.index)
    boundary = []
    for edge, faces in edge_faces.items():
        if len(faces) != 1: continue
        a,b = (obj.matrix_world @ obj.data.vertices[v].co for v in edge)
        pa,pb = world_to_camera_view(scene,camera,a),world_to_camera_view(scene,camera,b)
        mid=((pa.x+pb.x)*.5*1280,(1-(pa.y+pb.y)*.5)*720)
        boundary.append({"candidate_polygon_index":faces[0],"raw_obj_face_index":int(obj.data.attributes['raw_obj_face_index'].data[faces[0]].value),"edge_vertices":list(edge),"screen_a":[pa.x*1280,(1-pa.y)*720],"screen_b":[pb.x*1280,(1-pb.y)*720],"screen_mid":list(mid)})
    def nearest(target):
        return sorted(boundary,key=lambda r:(r['screen_mid'][0]-target[0])**2+(r['screen_mid'][1]-target[1])**2)[:16]
    result["boundary_edge_leads"]={"left_loop_hint":[477,340],"left_loop_nearest":nearest((477,340)),"right_strip_hint":[742,330],"right_strip_nearest":nearest((742,330))}
    result['proposed_overlay']=render_overlay(scene,obj)
    for label, (x0,y0,x1,y1,step) in regions.items():
        hits = []
        for y in range(y0, y1 + 1, step):
            for x in range(x0, x1 + 1, step):
                record = raycast_seed(scene, camera, x, y)
                if record.get("hit"):
                    hits.append(record)
        result["regions"][label] = hits
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: len(v) for k,v in result["regions"].items()}))

if __name__ == '__main__':
    main()
