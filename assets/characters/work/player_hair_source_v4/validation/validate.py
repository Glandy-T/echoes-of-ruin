"""Independent Blender-side validation for the v4 static source-hair review.

Run from the asset root:
  blender --background --factory-startup --disable-autoexec hair_front_locks_v4.blend --python validation/validate.py

This script never saves the input .blend.  It writes only validation/report.json
and validation/uv_pixel_draft.svg beside itself.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict, deque
from pathlib import Path

import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "validation"
SOURCE = ROOT / "source" / "original" / "source" / "Long hair.blend"
EXPECTED_SCENE = "SOURCE_SCALE_HAIR_REVIEW__STATIC"
NAMES = ("Hair_Back_SOURCE_UNCHANGED", "Hair_Front.L", "Hair_Front.R")
EPS = 1e-7


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def world_mesh_data(obj):
    """Return evaluated world-space vertices, triangles, and triangle loop ids."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    temporary = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    try:
        mesh = temporary.copy()
        mesh.calc_loop_triangles()
        vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
        triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
        tri_loops = [tuple(triangle.loops) for triangle in mesh.loop_triangles]
        polygons = [tuple(poly.vertices) for poly in mesh.polygons]
        edges = [tuple(edge.vertices) for edge in mesh.edges]
        return mesh, vertices, triangles, tri_loops, polygons, edges
    finally:
        evaluated.to_mesh_clear()


def triangle_area(a, b, c):
    return ((b - a).cross(c - a)).length * 0.5


def mesh_topology(vertices, triangles, polygons, edges):
    edge_faces = defaultdict(list)
    for face_index, polygon in enumerate(polygons):
        for index, start in enumerate(polygon):
            end = polygon[(index + 1) % len(polygon)]
            edge_faces[tuple(sorted((start, end)))].append((face_index, start, end))
    boundary = [edge for edge, refs in edge_faces.items() if len(refs) == 1]
    nonmanifold = [edge for edge, refs in edge_faces.items() if len(refs) > 2]
    winding_conflicts = []
    for edge, refs in edge_faces.items():
        if len(refs) != 2:
            continue
        lo, hi = edge
        directions = [1 if (start, end) == (lo, hi) else -1 for _, start, end in refs]
        if directions[0] == directions[1]:
            winding_conflicts.append(edge)
    degenerate = [index for index, tri in enumerate(triangles)
                  if triangle_area(vertices[tri[0]], vertices[tri[1]], vertices[tri[2]]) <= 1e-12]
    return {
        "boundary_edges": len(boundary),
        "nonmanifold_edges": len(nonmanifold),
        "winding_conflicts": len(winding_conflicts),
        "degenerate_triangles": len(degenerate),
        "closed_manifold": not boundary and not nonmanifold and not winding_conflicts,
    }


def components(vertex_count, edges):
    adjacent = [[] for _ in range(vertex_count)]
    for a, b in edges:
        adjacent[a].append(b)
        adjacent[b].append(a)
    seen, count = set(), 0
    for first in range(vertex_count):
        if first in seen:
            continue
        count += 1
        queue = deque([first]); seen.add(first)
        while queue:
            current = queue.popleft()
            for other in adjacent[current]:
                if other not in seen:
                    seen.add(other); queue.append(other)
    return count


def bounds_overlap(a, b, eps=EPS):
    amin, amax, bmin, bmax = a[0], a[1], b[0], b[1]
    return all(amin[i] <= bmax[i] + eps and bmin[i] <= amax[i] + eps for i in range(3))


def tri_bounds(tri):
    return tuple(min(p[i] for p in tri) for i in range(3)), tuple(max(p[i] for p in tri) for i in range(3))


def segment_triangle(p0, p1, a, b, c):
    # Moller-Trumbore, with endpoints included. Coplanar triangles are handled separately.
    direction = p1 - p0
    edge1, edge2 = b - a, c - a
    pvec = direction.cross(edge2)
    determinant = edge1.dot(pvec)
    if abs(determinant) <= EPS:
        return False
    inverse = 1.0 / determinant
    tvec = p0 - a
    u = tvec.dot(pvec) * inverse
    if u < -EPS or u > 1.0 + EPS:
        return False
    qvec = tvec.cross(edge1)
    v = direction.dot(qvec) * inverse
    if v < -EPS or u + v > 1.0 + EPS:
        return False
    t = edge2.dot(qvec) * inverse
    return -EPS <= t <= 1.0 + EPS


def orient2(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def on_segment2(a, b, p):
    return (min(a[0], b[0]) - EPS <= p[0] <= max(a[0], b[0]) + EPS and
            min(a[1], b[1]) - EPS <= p[1] <= max(a[1], b[1]) + EPS)


def segment_intersects2(a, b, c, d):
    ab_c, ab_d = orient2(a, b, c), orient2(a, b, d)
    cd_a, cd_b = orient2(c, d, a), orient2(c, d, b)
    if ((ab_c > EPS and ab_d < -EPS) or (ab_c < -EPS and ab_d > EPS)) and ((cd_a > EPS and cd_b < -EPS) or (cd_a < -EPS and cd_b > EPS)):
        return True
    return ((abs(ab_c) <= EPS and on_segment2(a, b, c)) or
            (abs(ab_d) <= EPS and on_segment2(a, b, d)) or
            (abs(cd_a) <= EPS and on_segment2(c, d, a)) or
            (abs(cd_b) <= EPS and on_segment2(c, d, b)))


def point_in_tri2(point, tri):
    a, b, c = tri
    signs = [orient2(a, b, point), orient2(b, c, point), orient2(c, a, point)]
    return not (any(sign > EPS for sign in signs) and any(sign < -EPS for sign in signs))


def polygon_area2(points):
    return 0.5 * sum(points[index][0] * points[(index + 1) % len(points)][1] - points[(index + 1) % len(points)][0] * points[index][1] for index in range(len(points)))


def triangle_overlap_area2(subject, clip):
    """Positive shared area only; edge/vertex contact is deliberately zero."""
    output = list(subject)
    clip = list(clip)
    if polygon_area2(clip) < 0:
        clip.reverse()
    for index, start in enumerate(clip):
        end = clip[(index + 1) % len(clip)]
        if not output:
            return 0.0
        input_points, output = output, []
        for point_index, current in enumerate(input_points):
            previous = input_points[(point_index - 1) % len(input_points)]
            current_inside = orient2(start, end, current) >= -EPS
            previous_inside = orient2(start, end, previous) >= -EPS
            if current_inside != previous_inside:
                previous_side = orient2(start, end, previous)
                current_side = orient2(start, end, current)
                divisor = previous_side - current_side
                if abs(divisor) > EPS:
                    ratio = previous_side / divisor
                    output.append((previous[0] + ratio * (current[0] - previous[0]), previous[1] + ratio * (current[1] - previous[1])))
            if current_inside:
                output.append(current)
    return abs(polygon_area2(output)) if len(output) >= 3 else 0.0


def triangles_overlap2(a, b):
    if not bounds_overlap((Vector((min(p[0] for p in a), min(p[1] for p in a), 0)), Vector((max(p[0] for p in a), max(p[1] for p in a), 0))),
                          (Vector((min(p[0] for p in b), min(p[1] for p in b), 0)), Vector((max(p[0] for p in b), max(p[1] for p in b), 0)))):
        return False
    for i in range(3):
        for j in range(3):
            if segment_intersects2(a[i], a[(i + 1) % 3], b[j], b[(j + 1) % 3]):
                return True
    return point_in_tri2(a[0], b) or point_in_tri2(b[0], a)


def triangles_overlap3(a, b):
    if not bounds_overlap(tri_bounds(a), tri_bounds(b)):
        return False
    normal_a = (a[1] - a[0]).cross(a[2] - a[0])
    normal_b = (b[1] - b[0]).cross(b[2] - b[0])
    if normal_a.length <= EPS or normal_b.length <= EPS:
        return False
    # Coplanar intersection needs a projected 2D test, including full containment.
    if normal_a.cross(normal_b).length <= EPS and max(abs(normal_a.dot(point - a[0])) for point in b) <= EPS:
        axis = max(range(3), key=lambda i: abs(normal_a[i]))
        keep = [i for i in range(3) if i != axis]
        return triangles_overlap2([tuple(point[i] for i in keep) for point in a], [tuple(point[i] for i in keep) for point in b])
    for tri_a, tri_b in ((a, b), (b, a)):
        for index in range(3):
            if segment_triangle(tri_a[index], tri_a[(index + 1) % 3], *tri_b):
                return True
    return False


def point_inside_mesh(point, bvh):
    # Majority vote among three non-axis rays; avoid double-counting a hit by stepping forward.
    results = []
    for direction in (Vector((1.0, .271, .137)).normalized(), Vector((.193, 1.0, .347)).normalized(), Vector((.229, .311, 1.0)).normalized()):
        start, hits = point + direction * 1e-6, 0
        for _ in range(512):
            location, _, _, _ = bvh.ray_cast(start, direction, 1000.0)
            if location is None:
                break
            hits += 1
            start = location + direction * 1e-6
        results.append(hits % 2 == 1)
    return sum(results) >= 2


def geometric_pair(a_name, a, b_name, b):
    _, a_vertices, a_triangles, _, _, _ = a
    _, b_vertices, b_triangles, _, _, _ = b
    bvh_a = BVHTree.FromPolygons(a_vertices, a_triangles, all_triangles=True)
    bvh_b = BVHTree.FromPolygons(b_vertices, b_triangles, all_triangles=True)
    candidates = bvh_a.overlap(bvh_b)
    intersections = [(ai, bi) for ai, bi in candidates if triangles_overlap3(
        [a_vertices[index] for index in a_triangles[ai]], [b_vertices[index] for index in b_triangles[bi]])]
    return {
        "objects": [a_name, b_name],
        "candidate_triangle_pairs": len(candidates),
        "intersecting_triangle_pairs": len(intersections),
        "sample_intersections": [list(pair) for pair in intersections[:20]],
        "a_vertices_inside_b": sum(point_inside_mesh(vertex, bvh_b) for vertex in a_vertices),
        "b_vertices_inside_a": sum(point_inside_mesh(vertex, bvh_a) for vertex in b_vertices),
        "a_fully_inside_b": bool(a_vertices) and all(point_inside_mesh(vertex, bvh_b) for vertex in a_vertices),
        "b_fully_inside_a": bool(b_vertices) and all(point_inside_mesh(vertex, bvh_a) for vertex in b_vertices),
    }


def uv_triangles(mesh, tri_loops):
    layer = mesh.uv_layers.get("UV_Pixel_Draft")
    if layer is None:
        return [], {"layer_present": False, "finite": False, "within_unit_square": False}
    values = [(float(loop.uv.x), float(loop.uv.y)) for loop in layer.data]
    finite = all(math.isfinite(u) and math.isfinite(v) for u, v in values)
    inside = finite and all(-EPS <= u <= 1.0 + EPS and -EPS <= v <= 1.0 + EPS for u, v in values)
    triangles = [[values[loop] for loop in loops] for loops in tri_loops]
    return triangles, {
        "layer_present": True,
        "finite": finite,
        "within_unit_square": inside,
        "active": mesh.uv_layers.active.name if mesh.uv_layers.active else None,
        "active_render": next((layer.name for layer in mesh.uv_layers if layer.active_render), None),
        "uv_loops": len(values),
    }


def uv_pair(a_name, a_tris, b_name, b_tris):
    overlaps = []
    for ai, tri_a in enumerate(a_tris):
        for bi, tri_b in enumerate(b_tris):
            area = triangle_overlap_area2(tri_a, tri_b)
            if area > 1e-12:
                overlaps.append((ai, bi, area, all(point_in_tri2(point, tri_b) for point in tri_a), all(point_in_tri2(point, tri_a) for point in tri_b), tri_a, tri_b))
    return {
        "objects": [a_name, b_name],
        "positive_area_overlapping_triangle_pairs": len(overlaps),
        "fully_contained_triangle_pairs": sum(a_in_b or b_in_a for _, _, _, a_in_b, b_in_a, _, _ in overlaps),
        "sample_overlaps": [{"triangles": [ai, bi], "area": area, "a_fully_in_b": a_in_b, "b_fully_in_a": b_in_a, "a_uv": tri_a, "b_uv": tri_b} for ai, bi, area, a_in_b, b_in_a, tri_a, tri_b in overlaps[:20]],
    }


def uv_within_object(name, triangles):
    degenerate = [index for index, tri in enumerate(triangles) if abs(polygon_area2(tri)) * 0.5 <= 1e-12]
    overlaps = []
    for ai, tri_a in enumerate(triangles):
        for bi in range(ai + 1, len(triangles)):
            tri_b = triangles[bi]
            area = triangle_overlap_area2(tri_a, tri_b)
            if area > 1e-12:
                overlaps.append((ai, bi, area, all(point_in_tri2(point, tri_b) for point in tri_a), all(point_in_tri2(point, tri_a) for point in tri_b), tri_a, tri_b))
    return {
        "object": name,
        "uv_degenerate_triangles": len(degenerate),
        "positive_area_overlapping_triangle_pairs": len(overlaps),
        "fully_contained_triangle_pairs": sum(a_in_b or b_in_a for _, _, _, a_in_b, b_in_a, _, _ in overlaps),
        "sample_overlaps": [{"triangles": [ai, bi], "area": area, "a_fully_in_b": a_in_b, "b_fully_in_a": b_in_a, "a_uv": tri_a, "b_uv": tri_b} for ai, bi, area, a_in_b, b_in_a, tri_a, tri_b in overlaps[:20]],
    }


def write_svg(uv_data):
    # Raster-free review of the actual draft atlas; each loop triangle is drawn with no simplification.
    width, padding, atlas = 860, 54, 720
    colors = {"Hair_Back_SOURCE_UNCHANGED": "#787878", "Hair_Front.L": "#f28e2b", "Hair_Front.R": "#4e9af1"}
    escaped = []
    for name in NAMES:
        for tri in uv_data[name][0]:
            points = " ".join(f"{padding + u * atlas:.3f},{padding + (1 - v) * atlas:.3f}" for u, v in tri)
            escaped.append(f'<polygon points="{points}" fill="{colors[name]}" fill-opacity="0.42" stroke="{colors[name]}" stroke-width="0.55"/>')
    labels = []
    for index, name in enumerate(NAMES):
        labels.append(f'<rect x="{padding + index * 218}" y="796" width="13" height="13" fill="{colors[name]}"/>')
        labels.append(f'<text x="{padding + 19 + index * 218}" y="807" font-size="15">{name}</text>')
    payload = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="835" viewBox="0 0 {width} 835">
  <rect width="100%" height="100%" fill="#ffffff"/>
  <text x="{padding}" y="27" font-family="sans-serif" font-size="18" font-weight="bold">UV_Pixel_Draft atlas (actual loop triangles)</text>
  <rect x="{padding}" y="{padding}" width="{atlas}" height="{atlas}" fill="#fcfcfc" stroke="#1d1d1d" stroke-width="1.2"/>
  <path d="M {padding + atlas / 2} {padding} V {padding + atlas} M {padding} {padding + atlas / 2} H {padding + atlas}" stroke="#d4d4d4" stroke-width="0.8"/>
  <g font-family="sans-serif" font-size="14" fill="#1d1d1d"><text x="{padding - 18}" y="{padding + 5}">1</text><text x="{padding - 18}" y="{padding + atlas + 5}">0</text><text x="{padding - 4}" y="{padding + atlas + 24}">0</text><text x="{padding + atlas - 4}" y="{padding + atlas + 24}">1</text></g>
  {''.join(escaped)}
  <g font-family="sans-serif" fill="#1d1d1d">{''.join(labels)}</g>
</svg>
'''
    (OUT / "uv_pixel_draft.svg").write_text(payload, encoding="utf-8")


def load_source_object():
    with bpy.data.libraries.load(str(SOURCE), link=False) as (source, destination):
        destination.objects = ["Plain.001"]
    source_obj = destination.objects[0]
    if source_obj is None:
        raise RuntimeError("Plain.001 could not be loaded from the preserved source blend")
    collection = bpy.data.collections.new("__VALIDATION_SOURCE_TEMP__")
    bpy.context.scene.collection.children.link(collection)
    collection.objects.link(source_obj)
    bpy.context.view_layer.update()
    return source_obj


def source_comparison(back):
    source = load_source_object()
    source_mesh, source_vertices, source_tris, _, source_polys, source_edges = world_mesh_data(source)
    _, back_vertices, back_tris, _, back_polys, back_edges = world_mesh_data(back)
    transformed_source = [Matrix.Translation((-.6, 0.0, 0.0)) @ vertex for vertex in source_vertices]
    coordinate_error = max((source_vertex - back_vertex).length for source_vertex, back_vertex in zip(transformed_source, back_vertices)) if len(transformed_source) == len(back_vertices) else float("inf")
    return {
        "source_object": "Plain.001",
        "expected_translation": [-0.6, 0.0, 0.0],
        "source_vertices": len(source_vertices),
        "edited_back_vertices": len(back_vertices),
        "source_triangles": len(source_tris),
        "edited_back_triangles": len(back_tris),
        "identical_polygon_topology": source_polys == back_polys,
        "maximum_world_coordinate_error": coordinate_error,
        "source_topology": mesh_topology(source_vertices, source_tris, source_polys, source_edges),
        "edited_back_topology": mesh_topology(back_vertices, back_tris, back_polys, back_edges),
        "pass": len(source_vertices) == len(back_vertices) and source_tris == back_tris and source_polys == back_polys and coordinate_error <= EPS,
    }


def main():
    OUT.mkdir(exist_ok=True)
    scene = bpy.data.scenes.get(EXPECTED_SCENE)
    if scene is None:
        raise RuntimeError(f"Required scene {EXPECTED_SCENE!r} is missing")
    bpy.context.window.scene = scene
    exact = {name: [obj for obj in scene.objects if obj.name == name] for name in NAMES}
    objects = {name: entries[0] for name, entries in exact.items() if len(entries) == 1}
    report = {
        "validator": "validate.py",
        "input_blend": "hair_front_locks_v4.blend",
        "input_blend_sha256": sha256(ROOT / "hair_front_locks_v4.blend"),
        "source_blend_sha256": sha256(SOURCE),
        "scene": EXPECTED_SCENE,
        "scope": "Static source-scale hair review only; no fitting, rig, animation, Godot, or texture acceptance is asserted.",
        "checks": {}, "objects": {}, "geometry_cross_object": [], "uv_within_object": [], "uv_cross_object": [], "failures": [], "warnings": [],
    }
    report["checks"]["exact_object_names"] = {name: len(entries) for name, entries in exact.items()}
    if set(objects) != set(NAMES):
        report["failures"].append("The review scene does not contain exactly one of every required hair object name.")
        (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return
    meshes, uv_data = {}, {}
    for name, obj in objects.items():
        if obj.type != "MESH":
            report["failures"].append(f"{name} is not a mesh object.")
            continue
        data = world_mesh_data(obj)
        meshes[name] = data
        mesh, vertices, triangles, tri_loops, polygons, edges = data
        topology = mesh_topology(vertices, triangles, polygons, edges)
        source_layers = [layer.name for layer in mesh.uv_layers]
        uvs, uv_check = uv_triangles(mesh, tri_loops)
        uv_data[name] = (uvs, uv_check)
        report["uv_within_object"].append(uv_within_object(name, uvs))
        has_armature_modifier = any(modifier.type == "ARMATURE" for modifier in obj.modifiers)
        normal_lengths = [poly.normal.length for poly in mesh.polygons]
        report["objects"][name] = {
            "vertices": len(vertices), "polygons": len(polygons), "triangles": len(triangles),
            "connected_components": components(len(vertices), edges), "topology": topology,
            "uv_layers": source_layers, "uv_pixel_draft": uv_check,
            "zero_length_polygon_normals": sum(length <= EPS for length in normal_lengths),
            "parent": obj.parent.name if obj.parent else None,
            "has_armature_modifier": has_armature_modifier,
            "find_armature": obj.find_armature().name if obj.find_armature() else None,
            "has_animation_data": obj.animation_data is not None,
        }
        if topology["degenerate_triangles"]:
            report["failures"].append(f"{name} has degenerate evaluated triangles.")
        if name != "Hair_Back_SOURCE_UNCHANGED" and (topology["boundary_edges"] or topology["nonmanifold_edges"] or topology["winding_conflicts"]):
            report["failures"].append(f"{name} is not a closed consistently wound manifold.")
        if report["objects"][name]["zero_length_polygon_normals"]:
            report["failures"].append(f"{name} has zero-length polygon normals.")
        if (has_armature_modifier or obj.find_armature() or obj.animation_data is not None):
            report["failures"].append(f"{name} is unexpectedly rigged or animated.")
        if not (uv_check["layer_present"] and uv_check["finite"] and uv_check["within_unit_square"] and uv_check["active_render"] == "UV_Pixel_Draft"):
            report["failures"].append(f"{name} does not have a valid active-render UV_Pixel_Draft layer.")
    if len(meshes) == 3:
        comparison = source_comparison(objects["Hair_Back_SOURCE_UNCHANGED"])
        report["checks"]["back_geometry_source_comparison"] = comparison
        if not comparison["pass"]:
            report["failures"].append("The evaluated back hair differs from original Plain.001 after the specified -0.6m X translation.")
        if not comparison["edited_back_topology"]["closed_manifold"]:
            if comparison["source_topology"] == comparison["edited_back_topology"]:
                report["warnings"].append("Hair_Back_SOURCE_UNCHANGED retains the original Plain.001 topology issue: one nonmanifold edge. Retained in this shape-review draft; repair is deferred before production fitting/rigging.")
            else:
                report["failures"].append("The edited back hair has a topology issue that is not identical to the original source.")
        for index, a_name in enumerate(NAMES):
            for b_name in NAMES[index + 1:]:
                report["geometry_cross_object"].append(geometric_pair(a_name, meshes[a_name], b_name, meshes[b_name]))
                report["uv_cross_object"].append(uv_pair(a_name, uv_data[a_name][0], b_name, uv_data[b_name][0]))
        for pair in report["uv_cross_object"]:
            if pair["positive_area_overlapping_triangle_pairs"]:
                report["failures"].append(f"UV_Pixel_Draft overlaps across {pair['objects']}.")
        for check in report["uv_within_object"]:
            if check["uv_degenerate_triangles"] or check["positive_area_overlapping_triangle_pairs"]:
                report["failures"].append(f"{check['object']} has degenerate or overlapping UV_Pixel_Draft triangles.")
        write_svg(uv_data)
    report["checks"]["global_armature_objects_in_review_scene"] = [obj.name for obj in scene.objects if obj.type == "ARMATURE"]
    if report["checks"]["global_armature_objects_in_review_scene"]:
        report["failures"].append("The review scene contains an Armature object.")
    report["status"] = "pass" if not report["failures"] else "fail"
    (OUT / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"status": report["status"], "failures": report["failures"]}, indent=2))


if __name__ == "__main__":
    main()
