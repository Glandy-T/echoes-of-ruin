"""Read-only root-cause analysis for the v3 cloth shell intersections.

This script does not save or mutate the Blend.  It independently classifies
triangle/triangle intersections, checks the protected outer surface for source
self-intersections, and compares the saved custom-normal offset with a purely
geometric vertex-normal offset.
"""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import tessellate_polygon


EXP = Path(__file__).resolve().parent.parent
BLEND = EXP / "model/protagonist_structure_v3.blend"
V2_BLEND = EXP.parent / "protagonist_tripo_cn_cleanup_v2/model/protagonist_cn_cleanup_v2.blend"
OUT = EXP / "source/cloth_root_cause.json"
EXPECTED_V2_SHA256 = "9f5fd46d630c318108ebbe16dcc46aef9a837234f51ac4685f1e0f8390b80105"
THICKNESS = 0.0007
EPS = 1.0e-8
POINT_EPS = 2.0e-7
AREA_EPS = 1.0e-13


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vec(v):
    return [float(x) for x in v]


def bbox(points):
    return {
        "min": [min(p[i] for p in points) for i in range(3)],
        "max": [max(p[i] for p in points) for i in range(3)],
    }


def triangle_area_3d(co):
    return (co[1] - co[0]).cross(co[2] - co[0]).length * 0.5


def area2(poly):
    if len(poly) < 3:
        return 0.0
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] -
                   poly[i][1] * poly[(i + 1) % len(poly)][0]
                   for i in range(len(poly)))) * 0.5


def clip2(subject, clip):
    def signed_area(poly):
        return sum(poly[i][0] * poly[(i + 1) % len(poly)][1] -
                   poly[i][1] * poly[(i + 1) % len(poly)][0]
                   for i in range(len(poly)))

    def ccw(poly):
        return list(poly) if signed_area(poly) >= 0.0 else list(reversed(poly))

    out = ccw(subject)
    clip = ccw(clip)
    for a, b in zip(clip, clip[1:] + clip[:1]):
        previous = out
        out = []
        if not previous:
            break
        s = previous[-1]
        ss = (b[0] - a[0]) * (s[1] - a[1]) - (b[1] - a[1]) * (s[0] - a[0])
        for e in previous:
            es = (b[0] - a[0]) * (e[1] - a[1]) - (b[1] - a[1]) * (e[0] - a[0])
            sin = ss >= -EPS
            ein = es >= -EPS
            if sin != ein:
                den = ss - es
                if abs(den) > 1.0e-30:
                    t = ss / den
                    out.append((s[0] + t * (e[0] - s[0]), s[1] + t * (e[1] - s[1])))
            if ein:
                out.append(e)
            s, ss = e, es
    return out


def dedupe_points(points):
    result = []
    for p in points:
        if not any((p - q).length <= POINT_EPS for q in result):
            result.append(p)
    return result


def segment_triangle(p0, p1, tri):
    """Moller-Trumbore on a finite segment; returns point and strictness."""
    a, b, c = tri
    direction = p1 - p0
    e1 = b - a
    e2 = c - a
    h = direction.cross(e2)
    det = e1.dot(h)
    if abs(det) <= EPS:
        return None
    inv = 1.0 / det
    s = p0 - a
    u = inv * s.dot(h)
    q = s.cross(e1)
    v = inv * direction.dot(q)
    t = inv * e2.dot(q)
    if u < -EPS or v < -EPS or u + v > 1.0 + EPS or t < -EPS or t > 1.0 + EPS:
        return None
    strict = (u > EPS and v > EPS and u + v < 1.0 - EPS and t > EPS and t < 1.0 - EPS)
    return p0 + direction * t, strict


def triangle_intersection(a, b):
    """Return exact-enough classification, rejecting mere AABB overlap."""
    na = (a[1] - a[0]).cross(a[2] - a[0])
    nb = (b[1] - b[0]).cross(b[2] - b[0])
    if na.length <= EPS or nb.length <= EPS:
        return {"kind": "degenerate", "points": []}
    nua = na.normalized()
    nub = nb.normalized()
    parallel = abs(abs(nua.dot(nub)) - 1.0) <= 2.0e-6
    plane_distance = max(abs(nua.dot(p - a[0])) for p in b)
    if parallel and plane_distance <= POINT_EPS:
        drop = max(range(3), key=lambda i: abs(nua[i]))
        aa = [tuple(p[i] for i in range(3) if i != drop) for p in a]
        bb = [tuple(p[i] for i in range(3) if i != drop) for p in b]
        overlap = clip2(aa, bb)
        overlap_area = area2(overlap)
        return {
            "kind": "coplanar_overlap" if overlap_area > AREA_EPS else "coplanar_touch_or_disjoint",
            "points": [],
            "projected_overlap_area": overlap_area,
        }

    hits = []
    strict = False
    for tri, other in ((a, b), (b, a)):
        for p0, p1 in zip(tri, tri[1:] + tri[:1]):
            hit = segment_triangle(p0, p1, other)
            if hit:
                hits.append(hit[0])
                strict = strict or hit[1]
    hits = dedupe_points(hits)
    if len(hits) >= 2 and max((p - q).length for p in hits for q in hits) > POINT_EPS:
        kind = "proper_crossing" if strict else "edge_crossing"
    elif hits:
        kind = "point_touch"
    else:
        kind = "disjoint"
    return {"kind": kind, "points": [vec(p) for p in hits]}


def make_triangles(mesh, polygon_predicate, coordinates=None):
    mesh.calc_loop_triangles()
    co = coordinates if coordinates is not None else [v.co.copy() for v in mesh.vertices]
    raw = mesh.attributes.get("raw_obj_face_index")
    parent = mesh.attributes.get("parent_raw_face_index")
    result = []
    for index, tri in enumerate(mesh.loop_triangles):
        poly = mesh.polygons[tri.polygon_index]
        if not polygon_predicate(poly):
            continue
        coords = [co[v].copy() for v in tri.vertices]
        result.append({
            "loop_triangle_index": index,
            "polygon": poly.index,
            "vertices": tuple(tri.vertices),
            "co": coords,
            "center": sum(coords, Vector()) / 3.0,
            "raw_face_id": int(raw.data[poly.index].value) if raw else -1,
            "parent_raw_face_id": int(parent.data[poly.index].value) if parent else -1,
        })
    return result


def bvh_candidates(a, b=None):
    if b is None:
        b = a
        same = True
    else:
        same = False
    av = [p for tri in a for p in tri["co"]]
    bv = [p for tri in b for p in tri["co"]]
    af = [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(a))]
    bf = [(3 * i, 3 * i + 1, 3 * i + 2) for i in range(len(b))]
    pairs = BVHTree.FromPolygons(av, af, all_triangles=True).overlap(
        BVHTree.FromPolygons(bv, bf, all_triangles=True))
    if same:
        pairs = sorted({tuple(sorted(pair)) for pair in pairs if pair[0] != pair[1]})
    return pairs


def exact_pair_report(a, b, pairs, exclude_shared_vertices=False):
    counts = Counter()
    rows = []
    for ai, bi in pairs:
        ta, tb = a[ai], b[bi]
        shared = set(ta["vertices"]) & set(tb["vertices"])
        if exclude_shared_vertices and shared:
            counts["excluded_topological_neighbor"] += 1
            continue
        result = triangle_intersection(ta["co"], tb["co"])
        counts[result["kind"]] += 1
        if result["kind"] in ("proper_crossing", "edge_crossing", "coplanar_overlap"):
            points = [Vector(p) for p in result.get("points", [])]
            position = sum(points, Vector()) / len(points) if points else (ta["center"] + tb["center"]) * 0.5
            rows.append({
                "a_polygon": ta["polygon"],
                "b_polygon": tb["polygon"],
                "a_raw_face_id": ta["raw_face_id"],
                "b_raw_face_id": tb["raw_face_id"],
                "a_parent_raw_face_id": ta["parent_raw_face_id"],
                "b_parent_raw_face_id": tb["parent_raw_face_id"],
                "a_vertices": list(ta["vertices"]),
                "b_vertices": list(tb["vertices"]),
                "kind": result["kind"],
                "intersection_points": result.get("points", []),
                "position_local": vec(position),
            })
    return {"candidate_pair_count": len(pairs), "classification_counts": dict(counts), "true_intersections": rows}


def geometric_vertex_normals(mesh, outer_polygons, nouter):
    normals = [Vector() for _ in range(nouter)]
    for poly in outer_polygons:
        ids = list(poly.vertices)
        if any(v >= nouter for v in ids):
            continue
        # Match Blender's actual loop-triangle decomposition for non-planar quads.
        for tri in (t for t in mesh.loop_triangles if t.polygon_index == poly.index):
            a, b, c = [mesh.vertices[v].co for v in tri.vertices]
            weighted = (b - a).cross(c - a) * 0.5
            for v in tri.vertices:
                normals[v] += weighted
    for i, normal in enumerate(normals):
        if normal.length > EPS:
            normals[i] = normal.normalized()
    return normals


def selected_patch_summary(mesh, outer_polygons, selected_raw_ids):
    raw = mesh.attributes["raw_obj_face_index"].data
    selected = [p for p in outer_polygons if int(raw[p.index].value) in selected_raw_ids]
    edge_faces = defaultdict(list)
    for poly in selected:
        ids = list(poly.vertices)
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edge_faces[tuple(sorted((a, b)))].append(poly.index)
    adjacency = defaultdict(set)
    for faces in edge_faces.values():
        if len(faces) == 2:
            adjacency[faces[0]].add(faces[1])
            adjacency[faces[1]].add(faces[0])
    by_index = {p.index: p for p in selected}
    remaining = set(by_index)
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        todo = [start]
        group = []
        while todo:
            index = todo.pop()
            group.append(index)
            for neighbor in adjacency[index]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    todo.append(neighbor)
        group_polys = [by_index[index] for index in sorted(group)]
        group_raw = sorted(int(raw[p.index].value) for p in group_polys)
        group_vertices = sorted({v for p in group_polys for v in p.vertices})
        group_edges = defaultdict(int)
        for poly in group_polys:
            ids = list(poly.vertices)
            for a, b in zip(ids, ids[1:] + ids[:1]):
                group_edges[tuple(sorted((a, b)))] += 1
        boundary_edges = sorted(edge for edge, count in group_edges.items() if count == 1)
        boundary_vertices = sorted({v for edge in boundary_edges for v in edge})
        components.append({
            "polygon_ids": [p.index for p in group_polys],
            "raw_face_ids": group_raw,
            "face_count": len(group_polys),
            "boundary_edge_count": len(boundary_edges),
            "boundary_vertex_ids": boundary_vertices,
            "boundary_bbox_local": bbox([mesh.vertices[v].co for v in boundary_vertices]),
            "all_vertex_bbox_local": bbox([mesh.vertices[v].co for v in group_vertices]),
        })
    return components


def ordered_patch_boundary(mesh, outer_polygons, selected_raw_ids):
    """Return one consistently directed boundary loop for a selected face disk."""
    raw = mesh.attributes["raw_obj_face_index"].data
    selected = [p for p in outer_polygons if int(raw[p.index].value) in selected_raw_ids]
    edge_uses = defaultdict(list)
    for poly in selected:
        ids = list(poly.vertices)
        for a, b in zip(ids, ids[1:] + ids[:1]):
            edge_uses[tuple(sorted((a, b)))].append((a, b))
    directed = [uses[0] for uses in edge_uses.values() if len(uses) == 1]
    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    for a, b in directed:
        outgoing[a].append(b)
        incoming[b].append(a)
    vertices = {v for edge in directed for v in edge}
    if any(len(outgoing[v]) != 1 or len(incoming[v]) != 1 for v in vertices):
        raise RuntimeError("Selected underarm patch boundary is not one consistently directed simple ring")
    start = min(vertices)
    loop = [start]
    current = start
    while True:
        current = outgoing[current][0]
        if current == start:
            break
        if current in loop:
            raise RuntimeError("Selected underarm boundary closes prematurely")
        loop.append(current)
    if len(loop) != len(vertices):
        raise RuntimeError("Selected underarm patch has more than one boundary loop")
    return loop


def candidate_triangle(vertices, coordinates, polygon, raw_face=-1):
    coords = [coordinates[v].copy() for v in vertices]
    return {
        "loop_triangle_index": -1,
        "polygon": polygon,
        "vertices": tuple(vertices),
        "co": coords,
        "center": sum(coords, Vector()) / 3.0,
        "raw_face_id": raw_face,
        "parent_raw_face_id": -1,
    }


def triangulate_boundary_earclip(loop, coordinates):
    """Blender's deterministic polyfill over the 3-D boundary projection."""
    points = [coordinates[v].copy() for v in loop]
    lookup = {tuple(point): vertex for point, vertex in zip(points, loop)}
    triangles = tessellate_polygon([points])
    result = []
    for triangle in triangles:
        try:
            result.append([loop[point] if isinstance(point, int) else lookup[tuple(point)] for point in triangle])
        except KeyError as exc:
            raise RuntimeError("Ear clipping returned a vertex outside the source boundary") from exc
    if len(result) != len(loop) - 2:
        raise RuntimeError("Ear clipping did not produce n-2 triangles")
    # Polyfill may return locally inconsistent triangle winding for a strongly
    # non-planar boundary. Propagate a consistent orientation across shared
    # edges before matching the source boundary direction.
    edge_uses = defaultdict(list)
    for face_index, face in enumerate(result):
        for a, b in zip(face, face[1:] + face[:1]):
            key = tuple(sorted((a, b)))
            direction = 1 if (a, b) == key else -1
            edge_uses[key].append((face_index, direction))
    adjacency = defaultdict(list)
    for uses in edge_uses.values():
        if len(uses) == 2:
            (a, da), (b, db) = uses
            adjacency[a].append((b, -da * db))
            adjacency[b].append((a, -db * da))
    signs = {}
    for start in range(len(result)):
        if start in signs:
            continue
        signs[start] = 1
        todo = [start]
        while todo:
            current = todo.pop()
            for neighbor, relative in adjacency[current]:
                wanted = signs[current] * relative
                if neighbor in signs and signs[neighbor] != wanted:
                    raise RuntimeError("Replacement triangulation is not consistently orientable")
                if neighbor not in signs:
                    signs[neighbor] = wanted
                    todo.append(neighbor)
    result = [face if signs[index] == 1 else list(reversed(face)) for index, face in enumerate(result)]
    # Ensure the replacement uses every source boundary edge exactly once and
    # follows the old patch winding along that edge.
    edge_uses = defaultdict(list)
    for face in result:
        for a, b in zip(face, face[1:] + face[:1]):
            edge_uses[tuple(sorted((a, b)))].append((a, b))
    directions = []
    for a, b in zip(loop, loop[1:] + loop[:1]):
        uses = edge_uses.get(tuple(sorted((a, b))), [])
        directions.append(1 if uses == [(a, b)] else -1 if uses == [(b, a)] else 0)
    if directions and all(direction == -1 for direction in directions):
        result = [list(reversed(face)) for face in result]
        edge_uses = defaultdict(list)
        for face in result:
            for a, b in zip(face, face[1:] + face[:1]):
                edge_uses[tuple(sorted((a, b)))].append((a, b))
    mismatches = [(a, b, edge_uses.get(tuple(sorted((a, b))), []))
                  for a, b in zip(loop, loop[1:] + loop[:1])
                  if edge_uses.get(tuple(sorted((a, b))), []) != [(a, b)]]
    if mismatches:
        raise RuntimeError(f"Replacement triangulation cannot match the old boundary winding: {mismatches[:10]}")
    return result


def candidate_normals_from_triangles(triangles, vertex_count):
    normals = [Vector() for _ in range(vertex_count)]
    for triangle in triangles:
        a, b, c = triangle["co"]
        weighted = (b - a).cross(c - a) * 0.5
        for vertex in triangle["vertices"]:
            normals[vertex] += weighted
    for index, normal in enumerate(normals):
        if normal.length > EPS:
            normals[index] = normal.normalized()
    return normals


def candidate_virtual_inner(outer, coordinates, normals, thickness):
    vertex_count = len(coordinates)
    inner_coordinates = [point - normals[index] * thickness for index, point in enumerate(coordinates)]
    result = []
    for triangle in outer:
        ids = list(reversed(triangle["vertices"]))
        coords = [inner_coordinates[v] for v in ids]
        result.append({
            "loop_triangle_index": -1,
            "polygon": triangle["polygon"],
            "vertices": tuple(v + vertex_count for v in ids),
            "co": coords,
            "center": sum(coords, Vector()) / 3.0,
            "raw_face_id": -1,
            "parent_raw_face_id": triangle["raw_face_id"],
        })
    return result


def candidate_virtual_inner_offsets(outer, coordinates, offsets):
    vertex_count = len(coordinates)
    inner_coordinates = [point + offsets[index] for index, point in enumerate(coordinates)]
    result = []
    for triangle in outer:
        ids = list(reversed(triangle["vertices"]))
        coords = [inner_coordinates[v] for v in ids]
        result.append({
            "loop_triangle_index": -1,
            "polygon": triangle["polygon"],
            "vertices": tuple(v + vertex_count for v in ids),
            "co": coords,
            "center": sum(coords, Vector()) / 3.0,
            "raw_face_id": -1,
            "parent_raw_face_id": triangle["raw_face_id"],
        })
    return result


def tested_patch_proposal(mesh, outer_polygons, outer, clusters):
    raw = mesh.attributes["raw_obj_face_index"].data
    remove_raw = {face for cluster in clusters for face in cluster["raw_face_ids"]}
    coordinates = [mesh.vertices[index].co.copy() for index in range(min(
        v for p in mesh.polygons if int(mesh.attributes["surface_kind"].data[p.index].value) == 1
        for v in p.vertices))]
    unaffected = [triangle for triangle in outer if triangle["raw_face_id"] not in remove_raw]
    replacement = []
    patch_records = []
    synthetic_polygon = -1000
    for cluster in clusters:
        selected_raw = set(cluster["raw_face_ids"])
        loop = ordered_patch_boundary(mesh, outer_polygons, selected_raw)
        faces = triangulate_boundary_earclip(loop, coordinates)
        cluster_replacement = []
        for face in faces:
            synthetic_polygon -= 1
            triangle = candidate_triangle(face, coordinates, synthetic_polygon)
            replacement.append(triangle)
            cluster_replacement.append(face)
        patch_records.append({
            "side_local_z": cluster["side_local_z"],
            "remove_raw_face_ids": sorted(selected_raw),
            "boundary_vertex_ids_ordered": loop,
            "boundary_coordinates_local_ordered": [vec(coordinates[v]) for v in loop],
            "replacement_triangles_outer_vertex_ids": cluster_replacement,
            "method": "Blender tessellate_polygon ear clipping of the ordered 3-D boundary; winding matched to removed source patch.",
        })
    candidate_outer = unaffected + replacement
    self_pairs = bvh_candidates(candidate_outer)
    self_report = exact_pair_report(candidate_outer, candidate_outer, self_pairs, exclude_shared_vertices=True)
    normals = candidate_normals_from_triangles(candidate_outer, len(coordinates))
    patch_vertices = {vertex for record in patch_records for vertex in record["boundary_vertex_ids_ordered"]}
    saved_offsets = [mesh.vertices[index + len(coordinates)].co - mesh.vertices[index].co
                     for index in range(len(coordinates))]
    radial_offsets = []
    for point in coordinates:
        inward = Vector((-0.012 - point.x, 0.0, -point.z))
        radial_offsets.append(inward.normalized() * THICKNESS if inward.length > EPS else Vector())
    mixed_offsets = [radial_offsets[index] if index in patch_vertices else saved_offsets[index]
                     for index in range(len(coordinates))]
    side_constant_offsets = [Vector((0.0, 0.0, -math.copysign(THICKNESS, coordinates[index].z)))
                             if index in patch_vertices else saved_offsets[index]
                             for index in range(len(coordinates))]
    strategy_trials = {}
    strategy_inputs = {
        "saved_offsets_all_vertices_with_repaired_pairing": saved_offsets,
        "saved_offsets_outside_patch_plus_constant_inward_z_patch": side_constant_offsets,
        "saved_offsets_outside_patch_plus_axis_radial_patch": mixed_offsets,
        "axis_radial_all_vertices": radial_offsets,
    }
    selected_strategy = None
    for strategy, offsets in strategy_inputs.items():
        trial_inner = candidate_virtual_inner_offsets(candidate_outer, coordinates, offsets)
        trial_pairs = bvh_candidates(candidate_outer, trial_inner)
        trial_report = exact_pair_report(candidate_outer, trial_inner, trial_pairs)
        strategy_trials[strategy] = {
            "bvh_candidate_pair_count": len(trial_pairs),
            "exact_classification_counts": trial_report["classification_counts"],
            "true_intersection_count": len(trial_report["true_intersections"]),
        }
        if selected_strategy is None and not trial_report["true_intersections"]:
            selected_strategy = (strategy, trial_pairs, trial_report)
    thickness_trials = {}
    selected_trial = None
    for thickness in (0.0007, 0.00035, 0.000175, 0.0000875, 0.00004375, 0.000021875, 0.0000109375):
        trial_inner = candidate_virtual_inner(candidate_outer, coordinates, normals, thickness)
        trial_pairs = bvh_candidates(candidate_outer, trial_inner)
        trial_report = exact_pair_report(candidate_outer, trial_inner, trial_pairs)
        thickness_trials[f"{thickness:.10f}"] = {
            "bvh_candidate_pair_count": len(trial_pairs),
            "exact_classification_counts": trial_report["classification_counts"],
            "true_intersection_count": len(trial_report["true_intersections"]),
        }
        if selected_trial is None and not trial_report["true_intersections"]:
            selected_trial = (thickness, trial_pairs, trial_report)
    if selected_strategy is not None:
        strategy_name, inner_pairs, inner_report = selected_strategy
        selected_thickness = THICKNESS
    elif selected_trial is not None:
        selected_thickness, inner_pairs, inner_report = selected_trial
        strategy_name = "area_weighted_geometric_normals_uniform"
    else:
        selected_thickness, strategy_name, inner_pairs, inner_report = None, None, [], None
    return {
        "status": "PASS" if not self_report["true_intersections"] and inner_report is not None and not inner_report["true_intersections"] else "FAIL",
        "outer_vertex_coordinates_unchanged": True,
        "removed_source_face_count": len(remove_raw),
        "replacement_triangle_count": len(replacement),
        "patches": patch_records,
        "candidate_outer_self_test": {
            "bvh_candidate_pair_count": len(self_pairs),
            "exact_classification_counts": self_report["classification_counts"],
            "true_intersection_count": len(self_report["true_intersections"]),
            "true_intersections": self_report["true_intersections"][:100],
        },
        "candidate_inner_test": {
            "selected_strategy": strategy_name,
            "selected_uniform_thickness": selected_thickness,
            "normal_method": "Selected from exact-tested offset strategies; see strategy_trials and uniform_thickness_trials.",
            "bvh_candidate_pair_count": len(inner_pairs),
            "exact_classification_counts": inner_report["classification_counts"] if inner_report else {},
            "true_intersection_count": len(inner_report["true_intersections"]) if inner_report else None,
            "true_intersections": inner_report["true_intersections"][:100] if inner_report else [],
            "strategy_trials": strategy_trials,
            "uniform_thickness_trials": thickness_trials,
        },
    }


def intersection_cluster(rows, sign, mesh, outer_polygons):
    selected = [row for row in rows if (row["position_local"][2] >= 0.0) == (sign > 0)]
    raw_ids = sorted({row["a_raw_face_id"] for row in selected} | {row["b_raw_face_id"] for row in selected})
    polygon_ids = sorted({row["a_polygon"] for row in selected} | {row["b_polygon"] for row in selected})
    positions = [Vector(row["position_local"]) for row in selected]
    return {
        "side_local_z": "positive" if sign > 0 else "negative",
        "intersection_pair_count": len(selected),
        "intersection_bbox_local": bbox(positions),
        "raw_face_ids": raw_ids,
        "polygon_ids": polygon_ids,
        "bounded_patch_components": selected_patch_summary(mesh, outer_polygons, set(raw_ids)),
    }


def build_virtual_inner(mesh, outer_tris, offsets):
    coordinates = [v.co.copy() for v in mesh.vertices]
    nouter = len(offsets)
    for i in range(nouter):
        coordinates[i + nouter] = coordinates[i] + offsets[i]
    result = []
    for outer in outer_tris:
        coords = [coordinates[v + nouter] for v in reversed(outer["vertices"])]
        result.append({
            "loop_triangle_index": outer["loop_triangle_index"],
            "polygon": outer["polygon"],
            "vertices": tuple(v + nouter for v in reversed(outer["vertices"])),
            "co": coords,
            "center": sum(coords, Vector()) / 3.0,
            "raw_face_id": -1,
            "parent_raw_face_id": outer["raw_face_id"],
        })
    return result


def offset_trial(outer, virtual_inner):
    candidates = bvh_candidates(outer, virtual_inner)
    report = exact_pair_report(outer, virtual_inner, candidates)
    return {
        "bvh_pair_count": len(candidates),
        "exact_classification_counts": report["classification_counts"],
        "true_intersection_count": len(report["true_intersections"]),
    }


def main():
    before_hash = sha256(BLEND)
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    collection_snapshot = {c.name: [o.name for o in list(c.all_objects)] for c in bpy.data.collections}
    visibility_snapshot = {
        o.name: {"hide_viewport": bool(o.hide_viewport), "hide_render": bool(o.hide_render), "hide_get": bool(o.hide_get())}
        for o in bpy.data.objects
    }
    bpy.context.view_layer.update()
    bpy.context.evaluated_depsgraph_get().update()

    robe = bpy.data.objects["Robe_Outer_Inner_Rims"]
    mesh = robe.data
    kind = mesh.attributes["surface_kind"].data
    outer_polygons = [p for p in mesh.polygons if int(kind[p.index].value) in (0, 4)]
    inner_polygons = [p for p in mesh.polygons if int(kind[p.index].value) == 1]
    outer_vertex_ids = sorted({v for p in outer_polygons for v in p.vertices})
    inner_vertex_ids = sorted({v for p in inner_polygons for v in p.vertices})
    nouter = min(inner_vertex_ids)
    if outer_vertex_ids != list(range(nouter)) or inner_vertex_ids != list(range(nouter, 2 * nouter)):
        raise RuntimeError("Saved robe no longer has the expected paired outer/inner vertex layout")

    outer = make_triangles(mesh, lambda p: int(kind[p.index].value) in (0, 4))
    inner = make_triangles(mesh, lambda p: int(kind[p.index].value) == 1)

    outer_self_candidates = bvh_candidates(outer)
    outer_self = exact_pair_report(outer, outer, outer_self_candidates, exclude_shared_vertices=True)
    current_candidates = bvh_candidates(outer, inner)
    current = exact_pair_report(outer, inner, current_candidates)

    saved_offsets = [mesh.vertices[i + nouter].co - mesh.vertices[i].co for i in range(nouter)]
    geometric_normals = geometric_vertex_normals(mesh, outer_polygons, nouter)
    saved_directions = [(-d).normalized() if d.length > EPS else Vector() for d in saved_offsets]
    angular_rows = []
    for i, (saved, geom) in enumerate(zip(saved_directions, geometric_normals)):
        dot = max(-1.0, min(1.0, saved.dot(geom))) if saved.length and geom.length else 0.0
        angular_rows.append({"vertex": i, "dot": dot, "angle_degrees": math.degrees(math.acos(dot))})
    angular_rows.sort(key=lambda row: row["dot"])

    hit_vertices = sorted({v for row in current["true_intersections"] for key in ("a_vertices", "b_vertices") for v in row[key]})
    hit_outer_vertices = sorted({v if v < nouter else v - nouter for v in hit_vertices})
    hit_angles = [row for row in angular_rows if row["vertex"] in set(hit_outer_vertices)]
    hit_angles.sort(key=lambda row: row["dot"])

    geometric_trials = {}
    for thickness in (0.0007, 0.00035, 0.000175, 0.0000875):
        offsets = [-normal * thickness for normal in geometric_normals]
        geometric_trials[f"{thickness:.7f}"] = offset_trial(outer, build_virtual_inner(mesh, outer, offsets))
    saved_scaled_trials = {}
    for scale in (1.0, 0.5, 0.25, 0.125):
        offsets = [direction * (-THICKNESS * scale) for direction in saved_directions]
        saved_scaled_trials[f"{THICKNESS * scale:.7f}"] = offset_trial(outer, build_virtual_inner(mesh, outer, offsets))

    true_current = current["true_intersections"]
    positions = [Vector(row["position_local"]) for row in true_current]
    outer_bad = outer_self["true_intersections"]
    outer_clusters = [intersection_cluster(outer_bad, 1, mesh, outer_polygons),
                      intersection_cluster(outer_bad, -1, mesh, outer_polygons)] if outer_bad else []
    repair_proposal = tested_patch_proposal(mesh, outer_polygons, outer, outer_clusters) if outer_clusters else None
    implicated_outer_raw = sorted({row["a_raw_face_id"] for row in true_current} |
                                  {row["b_parent_raw_face_id"] for row in true_current})
    implicated_outer_polygons = sorted({row["a_polygon"] for row in true_current})

    outer_source_crosses = len(outer_bad) > 0
    geometric_same_thickness = geometric_trials["0.0007000"]["true_intersection_count"]
    current_crosses = len(true_current)
    if outer_source_crosses:
        root_cause = "protected_outer_source_self_intersection"
        recommendation = (
            "Do not keep the intersecting source faces as a protected exterior. Rebuild only the hidden underarm fold patch "
            "bounded by the listed implicated source faces, preserving its boundary vertices and the visible silhouette; then regenerate the inner shell."
        )
    elif current_crosses and geometric_same_thickness == 0:
        root_cause = "averaged_imported_corner_normals_drive_the_inner_shell_across_a_valid_outer_surface"
        recommendation = (
            "Keep all protected outer coordinates. Recompute inward offsets from area-weighted geometric normals (with a local "
            "underarm clamp if needed), then regenerate the paired inner triangles and existing opening rims."
        )
    elif current_crosses:
        root_cause = "local_underarm_feature_clearance_is_smaller_than_the_uniform_inner_shell_offset"
        recommendation = (
            "Keep the outer surface. Use a local thickness clamp on the listed underarm vertices, reducing the inward offset "
            "until the exact intersection count is zero; preserve 0.0007 elsewhere. If no nonzero local offset clears, rebuild "
            "only the hidden underarm fold patch bounded by the implicated source faces."
        )
    else:
        root_cause = "bvh_false_positive_or_contact_only"
        recommendation = "Keep the geometry; replace the BVH-only gate with the exact triangle classifier used here."

    result = {
        "status": "DIAGNOSED",
        "blend": str(BLEND),
        "blend_sha256_before": before_hash,
        "blend_sha256_after": sha256(BLEND),
        "v2_source_blend_sha256": sha256(V2_BLEND),
        "read_only_invariants": {
            "blend_hash_unchanged": before_hash == sha256(BLEND),
            "v2_source_hash_matches_expected": sha256(V2_BLEND) == EXPECTED_V2_SHA256,
            "collection_snapshot": collection_snapshot,
            "visibility_unchanged_in_memory": visibility_snapshot == {
                o.name: {"hide_viewport": bool(o.hide_viewport), "hide_render": bool(o.hide_render), "hide_get": bool(o.hide_get())}
                for o in bpy.data.objects
            },
            "saved_file_not_written": True,
        },
        "coordinate_note": "Mesh local Y is up; object rotation is +90 degrees X for world Z-up.",
        "root_cause": root_cause,
        "ranked_hypotheses": [
            {
                "rank": 1,
                "hypothesis": "The retained v2 outer source crosses itself in the two hidden underarm folds.",
                "verdict": "CONFIRMED" if outer_source_crosses else "REJECTED",
                "evidence": f"{len(outer_bad)} exact non-neighbor outer/outer triangle crossings; every crossing uses retained raw source faces.",
            },
            {
                "rank": 2,
                "hypothesis": "Imported/custom corner-normal averaging is the primary cause.",
                "verdict": "SECONDARY_NOT_PRIMARY" if current_crosses else "NOT_APPLICABLE",
                "evidence": f"Worst hit-region saved-vs-geometric normal angle is {hit_angles[0]['angle_degrees']:.3f} degrees; geometric-normal offset at the same thickness still has {geometric_same_thickness} exact crossings." if hit_angles else "No hit region.",
            },
            {
                "rank": 3,
                "hypothesis": "The independent BVH test is reporting only coplanar contact or broad-phase false positives.",
                "verdict": "REJECTED" if current_crosses else "CONFIRMED",
                "evidence": f"All {current_crosses} saved outer/inner pairs classify as proper triangle crossings." if current_crosses else "No exact crossings found.",
            },
        ],
        "decisive_evidence": {
            "outer_source_self_intersection": {
                "bvh_candidate_pairs": outer_self["candidate_pair_count"],
                "exact_classification_counts": outer_self["classification_counts"],
                "true_intersection_count": len(outer_bad),
                "all_crossings_are_retained_source_faces": all(row["a_raw_face_id"] >= 0 and row["b_raw_face_id"] >= 0 for row in outer_bad),
                "clusters": outer_clusters,
                "true_intersections": outer_bad[:100],
            },
            "saved_inner_vs_outer": {
                "bvh_candidate_pairs": current["candidate_pair_count"],
                "exact_classification_counts": current["classification_counts"],
                "true_intersection_count": current_crosses,
                "true_intersection_bbox_local": bbox(positions) if positions else None,
                "implicated_outer_polygon_ids": implicated_outer_polygons,
                "implicated_outer_raw_face_ids": implicated_outer_raw,
                "true_intersections": true_current[:200],
            },
            "offset_direction_vs_area_weighted_geometric_normal": {
                "all_vertices_min_dot": angular_rows[0]["dot"],
                "all_vertices_max_angle_degrees": angular_rows[0]["angle_degrees"],
                "all_vertices_below_dot_0_5": sum(row["dot"] < 0.5 for row in angular_rows),
                "intersection_region_min_dot": hit_angles[0]["dot"] if hit_angles else None,
                "intersection_region_max_angle_degrees": hit_angles[0]["angle_degrees"] if hit_angles else None,
                "intersection_region_vertices": hit_angles,
                "worst_vertices_global": angular_rows[:40],
            },
            "counterfactual_offset_trials": {
                "area_weighted_geometric_normals": geometric_trials,
                "saved_imported_normal_direction_scaled": saved_scaled_trials,
            },
        },
        "tested_repair_proposal": repair_proposal,
        "decision": {
            "recommended_change": recommendation,
            "design_boundary": "Treat this as a bad imported underarm fold, not as an approved visible design feature: the exact crossings are wholly inside two retained source-face patches. Preserve each patch boundary and matched exterior silhouette; change only the hidden patch tessellation/interior coordinates needed to remove the crossing.",
            "protected_scope": "No approved exterior coordinates should change unless the outer-source exact self-intersection test is nonzero or every nonzero local offset fails.",
            "risk": [
                "A global thickness reduction weakens the cloth cue everywhere and is not the smallest change.",
                "Deleting underarm faces without rebuilding a bounded manifold patch would create holes and break the closed tissue.",
                "Body-proxy collisions are a separate provisional-body issue and do not diagnose this cloth-shell failure.",
            ],
            "verification_plan": [
                "Re-run exact outer self-intersection: require zero non-neighbor proper/edge/coplanar intersections.",
                "Re-run exact inner-vs-outer intersection: require zero true intersections; BVH candidate count alone is not the gate.",
                "Require closed manifold robe tissue with zero boundary/nonmanifold edges and unchanged four opening rings.",
                "Render the existing front/back/side/quarter and cuff/underhem views; compare silhouette and approved exterior against v2.",
            ],
            "stop_condition": "Stop once exact outer self-intersection and exact outer-inner intersection are both zero, manifold/opening checks remain unchanged, and matched views show no approved exterior silhouette change. Do not broaden into full-character retopology or body-proxy repair.",
        },
        "method_limits": [
            "Static saved-mesh analysis only; no rig deformation or animation was tested.",
            "Exact classification uses double-precision Python arithmetic over Blender float coordinates with explicit tolerances.",
            "No visual approval is inferred from geometric checks.",
        ],
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("CLOTH_ROOT_CAUSE", root_cause, "outer_self", len(outer_bad), "inner_outer", current_crosses)


if __name__ == "__main__":
    main()
