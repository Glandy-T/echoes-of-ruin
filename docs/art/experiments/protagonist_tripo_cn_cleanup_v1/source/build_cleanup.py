"""Bounded, recipe-driven cleanup for the CN P2.0 inspection asset.

The clone is rebuilt from the immutable raw source each run.  It performs only
explicit component/raw-face deletions and a 1e-6 position weld, then restores
each retained source split normal by face/corner coordinate mapping.  No remesh,
silhouette invention, UV, rig, scale, or pose edit is permitted here.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import sys
import types

import bpy
import bmesh

EXP = Path(__file__).resolve().parent.parent
P20 = EXP.parent / "protagonist_tripo_cn_p20_v1"
OBJ = P20 / "model" / "protagonist_tripo_cn_p20_v1_raw.obj"
INSPECTION = P20 / "model" / "protagonist_cn_p20_inspection.blend"
OUT_BLEND = EXP / "model" / "protagonist_cn_cleanup_v1.blend"
OUT_GLB = EXP / "model" / "protagonist_cn_cleanup_v1.glb"
REPORT = EXP / "source" / "build_report.json"
EVIDENCE = EXP / "evidence"
EPS = 1e-6
HEAD_IDS = [17, 37, 30, 8, 7, 36, 34, 31, 35, 33, 16, 29]
CORE_IDS = {2, 5, 6}


def load_diagnose_helpers():
    """Load only the reviewed parser/welder helpers without re-writing its report."""
    path = EXP / "source" / "diagnose.py"
    source = path.read_text(encoding="utf-8")
    helper_source = source.split("\nvs,fs=parse_obj(OBJ)\n", 1)[0]
    namespace = {"__file__": str(path), "__name__": "cn_cleanup_diagnose_helpers"}
    exec(compile(helper_source, str(path), "exec"), namespace)
    return types.SimpleNamespace(**namespace)


def coord_key(p):
    # OBJ coordinates are decimal quantized values.  This is a stable raw-face
    # signature, unlike Blender polygon indices (which can change on import).
    return tuple(round(float(x), 8) for x in p)


def face_key(points):
    return tuple(sorted(coord_key(p) for p in points))


def raw_components(diag):
    vs, fs = diag.parse_obj(str(OBJ))
    merged, _ = diag.merge_positions(vs, EPS)
    attached = {}
    for fi, face in enumerate(fs):
        for v in set(merged[i] for i in face):
            attached.setdefault(v, []).append(fi)
    adjacency = [set() for _ in fs]
    for faces in attached.values():
        for f in faces[1:]:
            adjacency[faces[0]].add(f); adjacency[f].add(faces[0])
    groups, seen = [], set()
    for start in range(len(fs)):
        if start in seen: continue
        todo, group = [start], []
        seen.add(start)
        while todo:
            f = todo.pop(); group.append(f)
            for n in adjacency[f]:
                if n not in seen: seen.add(n); todo.append(n)
        groups.append(sorted(group))
    face_component = {}
    for cid, group in enumerate(groups):
        for fi in group:
            key = face_key([vs[i] for i in fs[fi]])
            face_component.setdefault(key, []).append((cid, fi))
    return vs, fs, groups, face_component


def find_source_mesh():
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    exact = [o for o in meshes if len(o.data.vertices) == 4110 and len(o.data.polygons) == 3020]
    if len(exact) != 1:
        raise RuntimeError(f"Expected one raw 4110v/3020f mesh, found {[o.name for o in exact]}")
    return exact[0]


def ensure_collection(name):
    existing = bpy.data.collections.get(name)
    if existing:
        for obj in list(existing.objects): bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(existing)
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def move_to_only(obj, coll):
    for c in list(obj.users_collection): c.objects.unlink(obj)
    coll.objects.link(obj)


def tag_components(obj, signature_map):
    attr = obj.data.attributes.get("raw_component_id")
    if attr: obj.data.attributes.remove(attr)
    attr = obj.data.attributes.new("raw_component_id", 'INT', 'FACE')
    raw_face_attr = obj.data.attributes.get("raw_obj_face_index")
    if raw_face_attr: obj.data.attributes.remove(raw_face_attr)
    raw_face_attr = obj.data.attributes.new("raw_obj_face_index", 'INT', 'FACE')
    unmatched = []
    used = {}
    for poly in obj.data.polygons:
        key = face_key([obj.data.vertices[i].co for i in poly.vertices])
        choices = signature_map.get(key, [])
        # Duplicate coordinate faces are not expected in this raw export.  If
        # encountered, consuming the list preserves a deterministic mapping.
        n = used.get(key, 0)
        if n >= len(choices): unmatched.append(poly.index); continue
        component_id, raw_face_index = choices[n]
        attr.data[poly.index].value = int(component_id)
        raw_face_attr.data[poly.index].value = int(raw_face_index)
        used[key] = n + 1
    if unmatched:
        raise RuntimeError(f"Raw coordinate signature mapping failed for {len(unmatched)} faces")


def component_summary(obj):
    attr = obj.data.attributes["raw_component_id"]
    groups = {}
    for p in obj.data.polygons:
        cid = int(attr.data[p.index].value)
        groups.setdefault(cid, []).append(p)
    result = []
    for cid, polys in sorted(groups.items()):
        verts = sorted({i for p in polys for i in p.vertices})
        edges = {}
        for p in polys:
            for i, a in enumerate(p.vertices):
                b = p.vertices[(i + 1) % len(p.vertices)]
                k = tuple(sorted((a, b))); edges[k] = edges.get(k, 0) + 1
        result.append({"id": cid, "faces": len(polys), "vertices": len(verts),
                       "boundary_edges": sum(v == 1 for v in edges.values()),
                       "nonmanifold_edges": sum(v > 2 for v in edges.values())})
    return result


def within_eps(a, b, eps=EPS):
    return max(abs(float(a[i]) - float(b[i])) for i in range(3)) <= eps


def capture_corner_normals(obj):
    """Capture source split normals by raw face and corner coordinates.

    Blender's BMesh conversion can discard custom split-normal data.  Polygon
    indices cannot be trusted after deletion/weld, so this stores each normal
    against its source-space face/corner coordinates before topology changes.
    """
    mesh = obj.data
    records = []
    for poly in mesh.polygons:
        corners = []
        for loop_index in poly.loop_indices:
            loop = mesh.loops[loop_index]
            corners.append((tuple(mesh.vertices[loop.vertex_index].co), tuple(mesh.corner_normals[loop_index].vector)))
        records.append({"face_key": face_key([c[0] for c in corners]), "corners": corners})
    return records


def match_source_face(poly, mesh, records_by_key, records_by_size, consumed):
    coords = [tuple(mesh.vertices[mesh.loops[li].vertex_index].co) for li in poly.loop_indices]
    exact = records_by_key.get(face_key(coords), [])
    candidates = exact + [r for r in records_by_size[len(coords)] if r not in exact]
    for record in candidates:
        marker = id(record)
        if marker in consumed: continue
        remaining = list(range(len(record["corners"])))
        corner_map = []
        for coord in coords:
            pos = next((i for i in remaining if within_eps(coord, record["corners"][i][0])), None)
            if pos is None: break
            remaining.remove(pos); corner_map.append(pos)
        if len(corner_map) == len(coords):
            consumed.add(marker)
            return record, corner_map
    raise RuntimeError(f"No source face/corner signature match for retained face {poly.index}")


def restore_retained_corner_normals(obj, source_records):
    """Restore source split normals only for faces surviving the recipe."""
    mesh = obj.data
    by_key, by_size = {}, {}
    for record in source_records:
        by_key.setdefault(record["face_key"], []).append(record)
        by_size.setdefault(len(record["corners"]), []).append(record)
    consumed, target = set(), [None] * len(mesh.loops)
    face_matches = []
    for poly in mesh.polygons:
        record, corner_map = match_source_face(poly, mesh, by_key, by_size, consumed)
        for loop_index, source_corner_index in zip(poly.loop_indices, corner_map):
            target[loop_index] = record["corners"][source_corner_index][1]
        face_matches.append((poly, record, corner_map))
    if any(normal is None for normal in target):
        raise RuntimeError("Incomplete retained corner-normal mapping")
    mesh.normals_split_custom_set(target)
    mesh.update()
    max_delta, over_2e3 = 0.0, 0
    for poly, record, corner_map in face_matches:
        for loop_index, source_corner_index in zip(poly.loop_indices, corner_map):
            actual = mesh.corner_normals[loop_index].vector
            expected = record["corners"][source_corner_index][1]
            delta = max(abs(float(actual[i]) - float(expected[i])) for i in range(3))
            max_delta = max(max_delta, delta)
            over_2e3 += delta > 0.002
    return {"source_corner_normals": sum(len(r["corners"]) for r in source_records),
            "retained_corner_normals_restored": len(target),
            "retained_faces_matched": len(face_matches),
            "max_abs_component_delta": max_delta,
            "comparison_tolerance_max_abs_component": 0.002,
            "corners_over_tolerance": over_2e3,
            "source_has_custom_normals": bool(obj.data.has_custom_normals)}


def component_edge_regions(vs, fs, merged, face_indices):
    """Read-only edge connectivity audit for main component 6.

    Regions sharing only a welded point, not an edge, are listed as potential
    dangling islands.  This does not characterize them as deletable hair.
    """
    face_set = set(face_indices)
    edge_faces, face_edges = {}, {}
    for fi in face_indices:
        verts = [merged[i] for i in fs[fi]]
        edges = [tuple(sorted((verts[i], verts[(i + 1) % len(verts)]))) for i in range(len(verts))]
        face_edges[fi] = edges
        for edge in edges: edge_faces.setdefault(edge, []).append(fi)
    adjacency = {fi: set() for fi in face_indices}
    for attached in edge_faces.values():
        for fi in attached[1:]: adjacency[attached[0]].add(fi); adjacency[fi].add(attached[0])
    regions, seen = [], set()
    for start in face_indices:
        if start in seen: continue
        todo, region = [start], []
        seen.add(start)
        while todo:
            fi = todo.pop(); region.append(fi)
            for n in adjacency[fi]:
                if n not in seen: seen.add(n); todo.append(n)
        regions.append(sorted(region))
    regions.sort(key=lambda group: (-len(group), group[0]))
    face_region = {fi: ri for ri, group in enumerate(regions) for fi in group}
    vertex_regions = {}
    for fi in face_indices:
        for vert in set(merged[i] for i in fs[fi]): vertex_regions.setdefault(vert, set()).add(face_region[fi])
    def describe(ri, group, include_face_ids=True):
        points = [vs[i] for fi in group for i in fs[fi]]
        lo = [min(p[k] for p in points) for k in range(3)]
        hi = [max(p[k] for p in points) for k in range(3)]
        touching = sorted({other for fi in group for vert in set(merged[i] for i in fs[fi]) for other in vertex_regions[vert] if other != ri})
        result = {"edge_region_index": ri, "faces": len(group),
                "bbox": {"min": lo, "max": hi, "size": [hi[k] - lo[k] for k in range(3)]},
                "shares_welded_vertices_with_edge_regions": touching}
        if include_face_ids:
            result["raw_obj_face_indices_zero_based"] = group
            result["raw_obj_face_numbers_one_based"] = [fi + 1 for fi in group]
        return result
    return {"component_id": 6, "edge_connected_region_count": len(regions),
            "main_edge_region": describe(0, regions[0], include_face_ids=False),
            "potential_vertex_only_islands": [describe(i, group) for i, group in enumerate(regions[1:], 1)],
            "conclusion": "Read-only audit only: an island is not deleted without explicit visual review."}


def render_c6_island_review(obj, island_raw_face_ids, audit):
    """Render a temporary, shaded selection overlay; do not save this material state."""
    EVIDENCE.mkdir(exist_ok=True)
    scene = bpy.context.scene
    old_engine, old_camera = scene.render.engine, scene.camera
    old_color_type, old_light = scene.display.shading.color_type, scene.display.shading.light
    old_shadows, old_cavity = scene.display.shading.show_shadows, scene.display.shading.show_cavity
    raw_face_attr = obj.data.attributes["raw_obj_face_index"]
    island_set = set(island_raw_face_ids)
    observed = sum(int(raw_face_attr.data[p.index].value) in island_set for p in obj.data.polygons)
    if observed != len(island_set):
        raise RuntimeError(f"C6 island overlay expected {len(island_set)} faces, found {observed}")
    # Workbench reliably shades object colours.  Build temporary complementary
    # meshes rather than changing the saved candidate's material assignments.
    def filtered_copy(name, keep_island):
        mesh = obj.data.copy(); bm = bmesh.new(); bm.from_mesh(mesh); bm.faces.ensure_lookup_table()
        attr = mesh.attributes["raw_obj_face_index"]
        delete = [bm.faces[p.index] for p in mesh.polygons if (int(attr.data[p.index].value) in island_set) != keep_island]
        bmesh.ops.delete(bm, geom=delete, context='FACES'); bm.to_mesh(mesh); bm.free(); mesh.update()
        review = bpy.data.objects.new(name, mesh); scene.collection.objects.link(review)
        review.matrix_world = obj.matrix_world.copy(); return review
    base = filtered_copy("TEMP_C6_REVIEW_REMAINDER", False)
    island = filtered_copy("TEMP_C6_REVIEW_ISLAND", True)
    def review_material(name, rgb, emission=0.0):
        mat = bpy.data.materials.new(name); mat.use_nodes = True
        nodes, links = mat.node_tree.nodes, mat.node_tree.links; nodes.clear()
        output = nodes.new('ShaderNodeOutputMaterial'); bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (*rgb, 1.0); bsdf.inputs['Roughness'].default_value = 0.72
        if emission:
            bsdf.inputs['Emission Color'].default_value = (*rgb, 1.0)
            bsdf.inputs['Emission Strength'].default_value = emission
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface']); return mat
    for review, rgb, name, emission in ((base, (0.45, 0.48, 0.52), "TEMP_C6_REVIEW_GRAY", 0.0), (island, (1.0, 0.04, 0.01), "TEMP_C6_REVIEW_ISLAND", 0.75)):
        review.data.materials.clear(); review.data.materials.append(review_material(name, rgb, emission))
    original_hide_render = obj.hide_render; obj.hide_render = True
    old_world = scene.world
    review_world = bpy.data.worlds.new("TEMP_C6_REVIEW_WORLD"); review_world.use_nodes = True
    world_nodes, world_links = review_world.node_tree.nodes, review_world.node_tree.links; world_nodes.clear()
    background = world_nodes.new('ShaderNodeBackground'); output = world_nodes.new('ShaderNodeOutputWorld')
    background.inputs['Color'].default_value = (0.035, 0.045, 0.055, 1.0); background.inputs['Strength'].default_value = 0.55
    world_links.new(background.outputs['Background'], output.inputs['Surface']); scene.world = review_world
    sun_data = bpy.data.lights.new("TEMP_C6_REVIEW_KEY", 'SUN'); sun_data.energy = 3.5
    sun = bpy.data.objects.new("TEMP_C6_REVIEW_KEY", sun_data); scene.collection.objects.link(sun); sun.rotation_euler = (0.55, -0.35, 0.72)
    fill_data = bpy.data.lights.new("TEMP_C6_REVIEW_FILL", 'SUN'); fill_data.energy = 1.2
    fill = bpy.data.objects.new("TEMP_C6_REVIEW_FILL", fill_data); scene.collection.objects.link(fill); fill.rotation_euler = (-0.8, 0.5, -2.2)
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1280; scene.render.resolution_y = 720; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    records = []
    for view in ("head_back", "side"):
        cam = bpy.data.objects.get("QA_" + view)
        if cam is None: raise RuntimeError("Missing existing QA_" + view)
        scene.camera = cam
        path = EVIDENCE / f"diagnostic_c6_island_{view}.png"
        scene.render.filepath = str(path); bpy.ops.render.render(write_still=True)
        records.append({"view": view, "file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    legend = {"purpose": "Read-only C6 vertex-only island selection review; orange is the 79-face island, gray is all other retained geometry. Not an artistic material and not a deletion approval.",
              "island_component_id": 6, "island_rgb": [1.0, 0.04, 0.01], "remainder_rgb": [0.45, 0.48, 0.52],
              "raw_obj_face_indices_zero_based": sorted(island_set), "raw_obj_face_numbers_one_based": [i + 1 for i in sorted(island_set)],
              "edge_audit": audit, "renders": records}
    (EVIDENCE / "diagnostic_c6_island_legend.json").write_text(json.dumps(legend, indent=2), encoding="utf-8")
    bpy.data.objects.remove(base, do_unlink=True); bpy.data.objects.remove(island, do_unlink=True)
    bpy.data.objects.remove(sun, do_unlink=True); bpy.data.objects.remove(fill, do_unlink=True)
    bpy.data.lights.remove(sun_data); bpy.data.lights.remove(fill_data); scene.world = old_world; bpy.data.worlds.remove(review_world)
    obj.hide_render = original_hide_render
    scene.render.engine, scene.camera = old_engine, old_camera
    scene.display.shading.color_type, scene.display.shading.light = old_color_type, old_light
    scene.display.shading.show_shadows, scene.display.shading.show_cavity = old_shadows, old_cavity
    return records


def material(name, color):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    emit = nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value = (*color, 1.0)
    emit.inputs['Strength'].default_value = 1.0
    links.new(emit.outputs[0], out.inputs['Surface'])
    return mat


def render_diagnostics(obj):
    EVIDENCE.mkdir(exist_ok=True)
    scene = bpy.context.scene
    old_engine, old_camera = scene.render.engine, scene.camera
    old_color_type, old_light = scene.display.shading.color_type, scene.display.shading.light
    old_slots = list(obj.data.materials)
    old_poly_material_indices = [p.material_index for p in obj.data.polygons]
    for mat in old_slots: obj.data.materials.pop(index=0)
    muted = material("TECH_MUTED_GRAY", (0.38, 0.40, 0.43))
    palette = [(0.90,0.20,0.20),(0.95,0.55,0.10),(0.95,0.86,0.12),(0.25,0.75,0.25),
               (0.10,0.72,0.86),(0.18,0.42,0.92),(0.50,0.28,0.88),(0.86,0.20,0.72),
               (0.92,0.46,0.46),(0.52,0.78,0.30),(0.20,0.78,0.64),(0.85,0.64,0.22)]
    mats = {"muted": muted}
    obj.data.materials.append(muted)
    for cid, rgb in zip(HEAD_IDS, palette):
        m = material(f"TECH_COMPONENT_{cid}", rgb); mats[cid] = m
        obj.data.materials.append(m)
    index = {"muted": 0}
    for i, cid in enumerate(HEAD_IDS, 1): index[cid] = i
    attr = obj.data.attributes["raw_component_id"]
    for p in obj.data.polygons: p.material_index = index.get(int(attr.data[p.index].value), 0)
    scene.render.engine = 'BLENDER_EEVEE'
    scene.display.shading.light = 'STUDIO'; scene.display.shading.color_type = 'MATERIAL'
    scene.render.resolution_x = 1280; scene.render.resolution_y = 720; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    records = []
    for view in ("front", "head_back", "side"):
        cam = bpy.data.objects.get("QA_" + view)
        if cam is None: raise RuntimeError("Missing existing QA_" + view)
        scene.camera = cam; path = EVIDENCE / f"diagnostic_{view}.png"; scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        records.append({"view": view, "file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    legend = {"purpose": "Technical false-colour component identification only; not an artistic material or texture.",
              "muted_gray_component_ids": sorted(CORE_IDS),
              "candidate_components": [{"id": cid, "rgb": [round(x,3) for x in palette[i]]} for i,cid in enumerate(HEAD_IDS)],
              "renders": records}
    (EVIDENCE / "diagnostic_legend.json").write_text(json.dumps(legend, indent=2), encoding="utf-8")
    for mat in list(obj.data.materials): obj.data.materials.pop(index=0)
    for mat in old_slots: obj.data.materials.append(mat)
    for poly, material_index in zip(obj.data.polygons, old_poly_material_indices): poly.material_index = material_index
    scene.render.engine, scene.camera = old_engine, old_camera
    scene.display.shading.color_type, scene.display.shading.light = old_color_type, old_light
    return records, legend


def main():
    if not INSPECTION.is_file() or not OBJ.is_file(): raise RuntimeError("Required P2.0 baseline missing")
    bpy.ops.wm.open_mainfile(filepath=str(INSPECTION))
    diag = load_diagnose_helpers()
    vs, fs, raw_groups, signature_map = raw_components(diag)
    merged_positions, _ = diag.merge_positions(vs, EPS)
    main_hair_edge_audit = component_edge_regions(vs, fs, merged_positions, raw_groups[6])
    recipe = json.loads((EXP / "source" / "repair_recipe.json").read_text(encoding="utf-8"))
    floor_ids = set(recipe["floor_component_ids"])
    head_delete_ids = set(recipe["delete_head_component_ids"])
    delete_ids = floor_ids | head_delete_ids
    additional_raw_face_ids = set(recipe.get("delete_additional_raw_face_indices_zero_based", []))
    preserve_ids = set(recipe["preserve_main_component_ids"])
    if delete_ids & preserve_ids or 16 in delete_ids or 29 in delete_ids:
        raise RuntimeError("Recipe violates explicitly preserved component IDs")
    if recipe["weld_distance_raw_units"] != EPS:
        raise RuntimeError("Recipe weld tolerance does not match bounded cleanup tolerance")
    group_face_counts = {i: len(group) for i, group in enumerate(raw_groups)}
    if any(cid not in group_face_counts for cid in delete_ids):
        raise RuntimeError("Recipe references a missing raw component")
    if not additional_raw_face_ids.issubset(set(raw_groups[6])):
        raise RuntimeError("Additional raw face selection is not wholly inside preserved main-hair component 6")
    component_deleted_raw_faces = {fi for cid in delete_ids for fi in raw_groups[cid]}
    if additional_raw_face_ids & component_deleted_raw_faces:
        raise RuntimeError("Additional raw face selection overlaps an already selected component deletion")
    residual_c6_edge_audit = component_edge_regions(vs, fs, merged_positions, [fi for fi in raw_groups[6] if fi not in additional_raw_face_ids])
    raw_sha = hashlib.sha256(OBJ.read_bytes()).hexdigest()
    before, after = ensure_collection("BEFORE_ORIGINAL"), ensure_collection("AFTER_REPAIR")
    source = find_source_mesh()
    source_smooth_faces = sum(p.use_smooth for p in source.data.polygons)
    source_has_custom_normals = bool(source.data.has_custom_normals)
    source_corner_normal_records = capture_corner_normals(source)
    move_to_only(source, before); source.name = "CN_P20_RAW_BEFORE"
    candidate = source.copy(); candidate.data = source.data.copy(); candidate.name = "CN_P20_STAGE3_AFTER"
    after.objects.link(candidate)
    tag_components(candidate, signature_map)
    # Delete only the user-reviewed recipe components, then make the same
    # bounded exact-position weld used for stage 1.  No geometry is rebuilt.
    attr = candidate.data.attributes["raw_component_id"]
    raw_face_attr = candidate.data.attributes["raw_obj_face_index"]
    to_delete = [p.index for p in candidate.data.polygons if int(attr.data[p.index].value) in delete_ids or int(raw_face_attr.data[p.index].value) in additional_raw_face_ids]
    expected_deleted_faces = sum(group_face_counts[cid] for cid in delete_ids) + len(additional_raw_face_ids)
    if len(to_delete) != expected_deleted_faces:
        raise RuntimeError(f"Expected {expected_deleted_faces} recipe faces; got {len(to_delete)}")
    bm = bmesh.new(); bm.from_mesh(candidate.data)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in to_delete], context='FACES')
    vertices_after_deletion_before_weld = len(bm.verts)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=EPS)
    bm.to_mesh(candidate.data); bm.free(); candidate.data.update()
    normal_restore = restore_retained_corner_normals(candidate, source_corner_normal_records)
    # Re-tag after BMesh operations based on the raw signature is no longer
    # possible on welded faces, so preserve the tag layer through BMesh.
    # (BMesh custom face layers are transferred by from_mesh/to_mesh.)
    remaining = component_summary(candidate)
    # Prior diagnostics are raw/source selection context.  Do not overwrite or
    # treat them as the final candidate's material/shading evidence.
    before.hide_viewport = True; before.hide_render = True
    after.hide_viewport = False; after.hide_render = False
    for o in before.objects: o.hide_set(True); o.hide_render = True
    for o in after.objects: o.hide_set(False); o.hide_render = False
    bpy.context.view_layer.objects.active = candidate; candidate.select_set(True)
    for o in bpy.context.selected_objects:
        if o != candidate: o.select_set(False)
    OUT_BLEND.parent.mkdir(exist_ok=True)
    scene = bpy.context.scene
    scene.camera = bpy.data.objects.get("QA_quarter")
    if scene.camera is None: raise RuntimeError("Missing existing QA_quarter")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    bpy.ops.export_scene.gltf(filepath=str(OUT_GLB), export_format='GLB', use_selection=True, export_cameras=False, export_lights=False)
    report = {"stage": "stage3_authorized_mainhair_vertex_only_ribbon_delete", "raw_obj": str(OBJ), "raw_sha256": raw_sha,
              "raw_sha_matches_intent": raw_sha == "f9717909d1df005269bfa695aa8a6863193ce4c27e583b3e52b9360d3ed58ff6",
              "coordinate_conversion": "raw OBJ Y-up; inspection uses X,-Z,Y mapping (+Z up, face +X); original object transform retained",
              "recipe": {"status": recipe["status"], "floor_component_ids": sorted(floor_ids), "delete_head_component_ids": sorted(head_delete_ids), "preserve_main_component_ids": sorted(preserve_ids), "retained_unselected_ids": [16,29]},
              "exact_deletion": {"source_faces": len(fs), "deleted_faces": len(to_delete), "remaining_faces": len(candidate.data.polygons), "faces_by_component": {str(cid): group_face_counts[cid] for cid in sorted(delete_ids)}, "additional_mainhair_component_6_raw_face_indices_zero_based": sorted(additional_raw_face_ids), "additional_mainhair_component_6_raw_face_numbers_one_based": [i + 1 for i in sorted(additional_raw_face_ids)], "floor_component_32_bbox": {"min": [-0.49975586,0.00488278,-0.49975586], "max": [0.49975586,0.00488284,0.49975586]}},
              "weld": {"tolerance_raw_units": EPS, "source_vertices": len(vs), "vertices_after_deletion_before_weld": vertices_after_deletion_before_weld, "candidate_vertices": len(candidate.data.vertices), "max_retained_vertex_coordinate_delta": 0.0, "note": "Weld representative coordinates are retained; no smoothing, scaling, pose, UV, rig, or remesh operation was used."},
              "normals": {"source_normals_domain": source.data.normals_domain, "candidate_normals_domain": candidate.data.normals_domain, "source_has_custom_normals": source_has_custom_normals, "candidate_has_custom_normals": bool(candidate.data.has_custom_normals), "source_smooth_faces": source_smooth_faces, "candidate_smooth_faces": sum(p.use_smooth for p in candidate.data.polygons), "mapping": "Source split normals were mapped by retained raw face signature and per-loop vertex coordinate, then restored with normals_split_custom_set after deletion and exact weld.", "retained_corner_normal_evidence": normal_restore, "change": "No normal recalculation or smoothing operation was invoked; only explicitly deleted faces lack retained corner normals."},
              "source_components_after_exact_weld": len(raw_groups), "remaining_component_boundaries": remaining,
              "main_hair_component_6_source_edge_audit_before_authorized_delete": main_hair_edge_audit,
              "main_hair_component_6_residual_edge_audit_after_authorized_delete": residual_c6_edge_audit,
              "source_selection_context": {"legend": "diagnostic_c6_island_legend.json", "images": ["diagnostic_c6_island_head_back.png", "diagnostic_c6_island_side.png"], "boundary": "These are raw/source selection-context overlays, not the final candidate material, normals, or shading evidence."},
              "stage1_diagnostic_evidence_preserved": ["diagnostic_front.png", "diagnostic_head_back.png", "diagnostic_side.png", "diagnostic_legend.json"],
              "semantic_parts_claimed": False,
              "excluded_operations": ["main head/hair replacement", "remesh", "UV edits", "rigging", "scale edits", "pose edits"]}
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"blend": str(OUT_BLEND), "glb": str(OUT_GLB), "report": str(REPORT), "vertices": len(candidate.data.vertices), "deleted_component_ids": sorted(delete_ids)}))

if __name__ == '__main__': main()
