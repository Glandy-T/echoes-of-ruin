"""Independent, non-destructive inspection of the h31 raw OBJ candidate.

Run in Blender 5.0.1 background mode, for example:
  blender.exe --background --python source/inspect_candidate.py -- C:/.../raw.obj

The OBJ is imported only for measurement and Workbench evidence renders.  This
script never enters Edit Mode and never changes mesh topology, materials, UVs,
rigging, transforms in the source file, or the downloaded OBJ itself.
"""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import math
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


EXP = Path(__file__).resolve().parents[1]
MODEL = EXP / "model"
EVIDENCE = EXP / "evidence"
OUT = EXP / "source" / "raw_audit.json"
INSPECTION = MODEL / "protagonist_robe_h31_inspection.blend"
REFERENCE_OBJ = EXP.parent / "protagonist_tripo_robe_v2" / "model" / "protagonist_tripo_robe_v2_raw.obj"
EPS = 1e-8
POINT_EPS = 2e-7
AREA_EPS = 1e-13


def raw_argument():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 1:
        raise RuntimeError("Pass exactly one downloaded raw OBJ path after '--'.")
    path = Path(args[0]).resolve()
    if path.suffix.lower() != ".obj" or not path.is_file():
        raise RuntimeError(f"Raw OBJ is required, got: {path}")
    return path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def vec(value):
    return [float(v) for v in value]


def finite(values):
    return all(math.isfinite(value) for value in values)


def import_obj(path):
    bpy.ops.wm.obj_import(filepath=str(path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"{path.name} imported without a mesh object")
    return meshes


def edge_data(mesh):
    uses, faces = Counter(), defaultdict(list)
    # Start with Blender's complete edge list so zero-face loose edges are not
    # silently omitted by a polygon-only audit.
    for edge in mesh.edges:
        key = tuple(sorted(edge.vertices))
        uses[key] += 0
        faces[key]  # create the empty face list used in evidence
    for poly in mesh.polygons:
        vertices = list(poly.vertices)
        for a, b in zip(vertices, vertices[1:] + vertices[:1]):
            key = tuple(sorted((a, b)))
            uses[key] += 1
            faces[key].append(poly.index)
    return uses, faces


def components(mesh, uses, matrix):
    parent = list(range(len(mesh.vertices)))

    def find(index):
        while index != parent[index]:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for a, b in uses:
        a, b = find(a), find(b)
        if a != b:
            parent[b] = a
    grouped = defaultdict(list)
    for index in range(len(mesh.vertices)):
        grouped[find(index)].append(index)
    details = []
    for vertices in grouped.values():
        points = [mesh.vertices[index].co for index in vertices]
        world_points = [matrix @ point for point in points]
        details.append({
            "vertices": len(vertices),
            "bounds_local": {
                "min": vec((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points))),
                "max": vec((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points))),
            },
            "bounds_world": {
                "min": vec((min(point.x for point in world_points), min(point.y for point in world_points), min(point.z for point in world_points))),
                "max": vec((max(point.x for point in world_points), max(point.y for point in world_points), max(point.z for point in world_points))),
            },
        })
    details.sort(key=lambda row: row["vertices"], reverse=True)
    return len(grouped), [row["vertices"] for row in details], details


def boundary_components(mesh, uses):
    adjacency = defaultdict(set)
    for a, b in (edge for edge, count in uses.items() if count == 1):
        adjacency[a].add(b)
        adjacency[b].add(a)
    remaining, rows = set(adjacency), []
    while remaining:
        seed = next(iter(remaining))
        stack, vertices = [seed], set()
        while stack:
            vertex = stack.pop()
            if vertex in vertices:
                continue
            vertices.add(vertex)
            remaining.discard(vertex)
            stack.extend(adjacency[vertex] - vertices)
        points = [mesh.vertices[index].co for index in vertices]
        boundary_edges = [edge for edge, count in uses.items()
                          if count == 1 and edge[0] in vertices and edge[1] in vertices]
        center = sum(points, Vector()) / len(points)
        rows.append({
            "vertices": len(vertices), "edges": len(boundary_edges),
            "closed_simple_ring": all(len(adjacency[index]) == 2 for index in vertices),
            "center_local": vec(center),
            "bounds_local": {
                "min": vec((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points))),
                "max": vec((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points))),
            },
        })
    return rows


def area_2d(points):
    if len(points) < 3:
        return 0.0
    return abs(sum(points[i][0] * points[(i + 1) % len(points)][1] -
                   points[i][1] * points[(i + 1) % len(points)][0]
                   for i in range(len(points)))) * 0.5


def clip_convex(subject, clip):
    """Sutherland-Hodgman clip used only for coplanar triangle overlap."""
    def signed_area(points):
        return sum(points[i][0] * points[(i + 1) % len(points)][1] -
                   points[i][1] * points[(i + 1) % len(points)][0]
                   for i in range(len(points)))
    clip = list(clip) if signed_area(clip) >= 0 else list(reversed(clip))
    output = list(subject) if signed_area(subject) >= 0 else list(reversed(subject))
    for a, b in zip(clip, clip[1:] + clip[:1]):
        old, output = output, []
        if not old:
            break
        previous = old[-1]
        previous_side = (b[0] - a[0]) * (previous[1] - a[1]) - (b[1] - a[1]) * (previous[0] - a[0])
        for current in old:
            current_side = (b[0] - a[0]) * (current[1] - a[1]) - (b[1] - a[1]) * (current[0] - a[0])
            previous_in, current_in = previous_side >= -EPS, current_side >= -EPS
            if previous_in != current_in:
                denominator = previous_side - current_side
                if abs(denominator) > 1e-30:
                    t = previous_side / denominator
                    output.append((previous[0] + t * (current[0] - previous[0]),
                                   previous[1] + t * (current[1] - previous[1])))
            if current_in:
                output.append(current)
            previous, previous_side = current, current_side
    return output


def segment_triangle(p0, p1, triangle):
    a, b, c = triangle
    direction, edge1, edge2 = p1 - p0, b - a, c - a
    cross = direction.cross(edge2)
    determinant = edge1.dot(cross)
    if abs(determinant) <= EPS:
        return None
    inverse = 1.0 / determinant
    source = p0 - a
    u = inverse * source.dot(cross)
    q = source.cross(edge1)
    v = inverse * direction.dot(q)
    distance = inverse * edge2.dot(q)
    if u < -EPS or v < -EPS or u + v > 1 + EPS or distance < -EPS or distance > 1 + EPS:
        return None
    point = p0 + direction * distance
    strict = u > EPS and v > EPS and u + v < 1 - EPS and distance > EPS and distance < 1 - EPS
    return point, strict


def exact_triangle_relation(left, right):
    normal_left = (left[1] - left[0]).cross(left[2] - left[0])
    normal_right = (right[1] - right[0]).cross(right[2] - right[0])
    if normal_left.length <= EPS or normal_right.length <= EPS:
        return "degenerate", []
    a, b = normal_left.normalized(), normal_right.normalized()
    if abs(abs(a.dot(b)) - 1) <= 2e-6 and max(abs(a.dot(point - left[0])) for point in right) <= POINT_EPS:
        drop = max(range(3), key=lambda axis: abs(a[axis]))
        project = lambda tri: [tuple(point[axis] for axis in range(3) if axis != drop) for point in tri]
        return ("coplanar_overlap" if area_2d(clip_convex(project(left), project(right))) > AREA_EPS
                else "coplanar_touch_or_disjoint"), []
    hits, strict = [], False
    for source, other in ((left, right), (right, left)):
        for start, end in zip(source, source[1:] + source[:1]):
            hit = segment_triangle(start, end, other)
            if hit and not any((hit[0] - known).length <= POINT_EPS for known in hits):
                hits.append(hit[0])
                strict = strict or hit[1]
    if len(hits) >= 2 and max((first - second).length for first in hits for second in hits) > POINT_EPS:
        return ("proper_crossing" if strict else "edge_crossing"), hits
    return ("point_touch" if hits else "disjoint"), hits


def self_intersections(mesh, matrix):
    mesh.calc_loop_triangles()
    triangles = []
    for index, triangle in enumerate(mesh.loop_triangles):
        triangles.append((index, triangle.polygon_index, tuple(triangle.vertices),
                          [matrix @ mesh.vertices[vertex].co for vertex in triangle.vertices]))
    coordinates = [point for _, _, _, points in triangles for point in points]
    faces = [(index * 3, index * 3 + 1, index * 3 + 2) for index in range(len(triangles))]
    bvh = BVHTree.FromPolygons(coordinates, faces, all_triangles=True)
    pairs = sorted({tuple(sorted(pair)) for pair in bvh.overlap(bvh) if pair[0] != pair[1]})
    classification, intersections = Counter(), []
    for left_index, right_index in pairs:
        left, right = triangles[left_index], triangles[right_index]
        if set(left[2]) & set(right[2]):
            classification["excluded_shared_vertex_neighbor"] += 1
            continue
        kind, points = exact_triangle_relation(left[3], right[3])
        classification[kind] += 1
        if kind in {"proper_crossing", "edge_crossing", "coplanar_overlap"}:
            position = (sum(points, Vector()) / len(points) if points
                        else (sum(left[3], Vector()) + sum(right[3], Vector())) / 6)
            intersections.append({
                "triangle_a": left[0], "triangle_b": right[0],
                "polygon_a": left[1], "polygon_b": right[1],
                "vertices_a": list(left[2]), "vertices_b": list(right[2]),
                "kind": kind, "position_world": vec(position),
                "intersection_points_world": [vec(point) for point in points],
            })
    return {
        "bvh_candidate_pair_count": len(pairs), "classification_counts": dict(classification),
        "true_nonadjacent_intersection_count": len(intersections),
        "true_nonadjacent_intersections_sample": intersections[:100],
        "method": "BVH broad phase followed by exact segment/coplanar classification; only triangle pairs sharing a vertex index are excluded as topological neighbors. AABB/BVH overlap alone is not reported as an intersection.",
    }


def bounds_for(meshes):
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    minimum = Vector([min(point[axis] for point in points) for axis in range(3)])
    maximum = Vector([max(point[axis] for point in points) for axis in range(3)])
    return minimum, maximum


def ray_probe(bvh, origin, direction, distance, triangles=None, matrix=None):
    hit = bvh.ray_cast(origin, direction.normalized(), distance)
    row = {"origin_world": vec(origin), "direction_world": vec(direction.normalized()),
           "first_hit_distance": float(hit[3]) if hit[0] is not None else None,
           "first_hit_triangle": int(hit[2]) if hit[0] is not None else None}
    if hit[0] is not None and triangles is not None:
        triangle = triangles[hit[2]]
        row["first_hit_polygon"] = int(triangle.polygon_index)
        row["first_hit_position_world"] = vec(hit[0])
        row["first_hit_normal_world"] = vec((matrix.to_3x3() @ triangle.normal).normalized())
    return row


def opening_probes(mesh, matrix, minimum, maximum):
    mesh.calc_loop_triangles()
    coordinates = [matrix @ mesh.vertices[vertex].co for triangle in mesh.loop_triangles for vertex in triangle.vertices]
    faces = [(index * 3, index * 3 + 1, index * 3 + 2) for index in range(len(mesh.loop_triangles))]
    bvh = BVHTree.FromPolygons(coordinates, faces, all_triangles=True)
    center, span = (minimum + maximum) / 2, maximum - minimum
    # Probe distance must not collapse to the robe shell thickness.
    short = max(max(span.x, span.y, span.z) * .15, 1e-4)
    samples = {
        "neck_from_plus_z": [(Vector((center.x + dx * span.x, center.y + dy * span.y, maximum.z + short)), Vector((0, 0, -1)))
                             for dx in (-.03, 0, .03) for dy in (-.03, 0, .03)],
        "hem_from_minus_z": [(Vector((center.x + dx * span.x, center.y + dy * span.y, minimum.z - short)), Vector((0, 0, 1)))
                              for dx in (-.08, 0, .08) for dy in (-.08, 0, .08)],
        "cuff_from_minus_y": [(Vector((center.x + dx * span.x, minimum.y - short, center.z + dz * span.z)), Vector((0, 1, 0)))
                               for dx in (-.03, 0, .03) for dz in (-.03, 0, .03)],
        "cuff_from_plus_y": [(Vector((center.x + dx * span.x, maximum.y + short, center.z + dz * span.z)), Vector((0, -1, 0)))
                              for dx in (-.03, 0, .03) for dz in (-.03, 0, .03)],
    }
    result = {}
    for name, rows in samples.items():
        rays = [ray_probe(bvh, origin, direction, short * 2, mesh.loop_triangles, matrix) for origin, direction in rows]
        result[name] = {
            "rays": rays, "no_hit_within_probe_distance": sum(row["first_hit_distance"] is None for row in rays),
            "immediate_hits_under_5pct_probe": sum(row["first_hit_distance"] is not None and row["first_hit_distance"] < short * .05 for row in rays),
        }
    # A real through-hem should not meet a surface immediately above the hem
    # opening at this central grid.  Record the face and normal rather than
    # infer success from the absence of a hit at the exterior start point.
    hem_traces = result["hem_from_minus_z"]["rays"]
    low_hits = [row for row in hem_traces if row["first_hit_distance"] is not None
                and row["first_hit_position_world"][2] < minimum.z + span.z * .25]
    result["interior_connectivity_interpretation"] = {
        "hem_low_blocking_face_samples": low_hits,
        "hem_center_grid_has_low_internal_block": bool(low_hits),
        "interpretation": "A low first-hit surface over the sampled central hem grid is evidence of a capped or internally blocked hem cavity, not an open through-garment. This is a sampled geometric test; it does not prove every off-center route.",
    }
    return result


def point_camera(collection, name, location, target, scale):
    data = bpy.data.cameras.new(name)
    camera = bpy.data.objects.new(name, data)
    collection.objects.link(camera)
    camera.location = location
    camera.rotation_euler = (target - location).to_track_quat("-Z", "Y").to_euler()
    data.type, data.ortho_scale = "ORTHO", scale
    data.clip_end = max((location - target).length * 10, 100)
    return camera


def setup_render():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1280, 720, 100
    scene.render.image_settings.file_format = "PNG"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "SINGLE"
    scene.display.shading.single_color = (.62, .65, .65)
    scene.display.shading.background_type = "WORLD"
    scene.world = bpy.data.worlds.new("Independent neutral gray QA background")
    scene.world.color = (.055, .055, .055)
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.show_specular_highlight = False
    return scene


def render_candidate(meshes, minimum, maximum):
    scene = setup_render()
    cameras = bpy.data.collections.new("QA_CAMERAS_ONLY")
    scene.collection.children.link(cameras)
    center, span = (minimum + maximum) / 2, maximum - minimum
    height, width = max(span.z, .01), max(span.x, span.y, .01)
    distance = max(height, width) * 4
    full_scale = max(height * 1.22 * (1280 / 720), width * 1.22)
    views = {
        "front": ((1, 0, 0), center, full_scale),
        "back": ((-1, 0, 0), center, full_scale),
        "side": ((0, -1, 0), center, full_scale),
        "quarter": ((.80, -.80, .25), center, full_scale),
        "neck": ((.60, -.60, .50), Vector((center.x, center.y, maximum.z - height * .055)), max(height * .30 * (1280 / 720), width * .30)),
        "underhem": ((.55, -.55, -.40), Vector((center.x, center.y, minimum.z + height * .12)), max(height * .62 * (1280 / 720), width * .62)),
        "cuff_minus_y": ((0, -1, .05), Vector((center.x, minimum.y + span.y * .12, center.z)), max(height * .45 * (1280 / 720), width * .45)),
        "cuff_plus_y": ((0, 1, .05), Vector((center.x, maximum.y - span.y * .12, center.z)), max(height * .45 * (1280 / 720), width * .45)),
    }
    evidence = {}
    for name, (direction, target, scale) in views.items():
        camera = point_camera(cameras, f"QA_{name}", target + Vector(direction).normalized() * distance, target, scale)
        scene.camera = camera
        filename = EVIDENCE / f"raw_{name}.png"
        scene.render.filepath = str(filename)
        bpy.ops.render.render(write_still=True)
        evidence[name] = {"file": str(filename.relative_to(EXP)).replace("\\", "/"),
                          "camera_location": vec(camera.location), "camera_target": vec(target),
                          "orthographic_scale": float(scale)}
    scene.camera = bpy.data.objects["QA_quarter"]
    return evidence


def render_reference(reference):
    """Render untouched v2 from matching labelled axes for human silhouette comparison."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    reference_meshes = import_obj(reference)
    minimum, maximum = bounds_for(reference_meshes)
    scene = setup_render()
    cameras = bpy.data.collections.new("REFERENCE_COMPARE_CAMERAS_ONLY")
    scene.collection.children.link(cameras)
    center, span = (minimum + maximum) / 2, maximum - minimum
    height, width = max(span.z, .01), max(span.x, span.y, .01)
    distance, scale = max(height, width) * 4, max(height * 1.22 * (1280 / 720), width * 1.22)
    files = {}
    for name, direction in {"reference_v2_front": (1, 0, 0), "reference_v2_side": (0, -1, 0)}.items():
        camera = point_camera(cameras, f"QA_{name}", center + Vector(direction).normalized() * distance, center, scale)
        scene.camera = camera
        filename = EVIDENCE / f"raw_{name}.png"
        scene.render.filepath = str(filename)
        bpy.ops.render.render(write_still=True)
        files[name] = str(filename.relative_to(EXP)).replace("\\", "/")
    return files


def audit_meshes(meshes):
    records = []
    all_intersections = []
    for obj in meshes:
        mesh = obj.data
        mesh.calc_loop_triangles()
        uses, faces = edge_data(mesh)
        component_total, component_sizes, component_details = components(mesh, uses, obj.matrix_world)
        face_vertices = {vertex for poly in mesh.polygons for vertex in poly.vertices}
        used_by_edge = {vertex for edge in uses for vertex in edge}
        nonmanifold = [{"edge": list(edge), "face_count": count, "faces": faces[edge],
                        "midpoint_local": vec((mesh.vertices[edge[0]].co + mesh.vertices[edge[1]].co) / 2)}
                       for edge, count in uses.items() if count > 2]
        intersections = self_intersections(mesh, obj.matrix_world)
        all_intersections.append(intersections)
        records.append({
            "object": obj.name, "vertices": len(mesh.vertices), "edges": len(mesh.edges),
            "polygons": len(mesh.polygons), "triangles_after_triangulation": len(mesh.loop_triangles),
            "triangle_polygons": sum(len(poly.vertices) == 3 for poly in mesh.polygons),
            "quad_polygons": sum(len(poly.vertices) == 4 for poly in mesh.polygons),
            "ngon_polygons": sum(len(poly.vertices) > 4 for poly in mesh.polygons),
            "connected_components": component_total, "component_vertex_counts_descending": component_sizes,
            "component_details": component_details,
            "boundary_edges": sum(count == 1 for count in uses.values()),
            "boundary_components": boundary_components(mesh, uses),
            "loose_edges": sum(count == 0 for count in uses.values()),
            "loose_vertices": sum(vertex not in used_by_edge for vertex in range(len(mesh.vertices))),
            "vertices_not_referenced_by_faces": sum(vertex not in face_vertices for vertex in range(len(mesh.vertices))),
            "nonmanifold_edges_more_than_two_faces": len(nonmanifold), "nonmanifold_edge_samples": nonmanifold[:100],
            "degenerate_edges_near_zero": sum((mesh.vertices[edge.vertices[0]].co - mesh.vertices[edge.vertices[1]].co).length < 1e-12 for edge in mesh.edges),
            "degenerate_faces_near_zero_area": sum(poly.area < 1e-12 for poly in mesh.polygons),
            "finite_vertex_coordinates": all(finite(vertex.co) for vertex in mesh.vertices),
            "uv_layer_count": len(mesh.uv_layers), "vertex_group_count": len(obj.vertex_groups),
            "shape_keys_present": bool(mesh.shape_keys), "armature_modifier_count": sum(mod.type == "ARMATURE" for mod in obj.modifiers),
            "self_intersection_audit": intersections,
        })
    return records, all_intersections


RAW = raw_argument()
MODEL.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)
before = {"raw_obj": sha256(RAW)}
if REFERENCE_OBJ.is_file():
    before["approved_reference_v2_obj"] = sha256(REFERENCE_OBJ)

bpy.ops.wm.read_factory_settings(use_empty=True)
candidate_meshes = import_obj(RAW)
minimum, maximum = bounds_for(candidate_meshes)
mesh_rows, intersection_rows = audit_meshes(candidate_meshes)
if len(candidate_meshes) != 1:
    raise RuntimeError(f"Expected exactly one raw candidate mesh object, imported {len(candidate_meshes)}")
opening = opening_probes(candidate_meshes[0].data, candidate_meshes[0].matrix_world, minimum, maximum)
candidate_evidence = render_candidate(candidate_meshes, minimum, maximum)

# The inspection blend deliberately contains only the untouched candidate plus QA cameras.
bpy.ops.wm.save_as_mainfile(filepath=str(INSPECTION))
reference_evidence = render_reference(REFERENCE_OBJ) if REFERENCE_OBJ.is_file() else {}

after = {"raw_obj": sha256(RAW)}
if REFERENCE_OBJ.is_file():
    after["approved_reference_v2_obj"] = sha256(REFERENCE_OBJ)
if before != after:
    raise RuntimeError("Raw source or approved reference hash changed during read-only inspection")

total_intersections = sum(row["true_nonadjacent_intersection_count"] for row in intersection_rows)
checks = {
    "one_candidate_mesh_object": len(mesh_rows) == 1,
    "raw_source_hash_unchanged": before["raw_obj"] == after["raw_obj"],
    "reference_hash_unchanged": (not REFERENCE_OBJ.is_file() or before["approved_reference_v2_obj"] == after["approved_reference_v2_obj"]),
    "finite_vertex_coordinates": all(row["finite_vertex_coordinates"] for row in mesh_rows),
    "single_connected_component": all(row["connected_components"] == 1 for row in mesh_rows),
    "no_loose_edges": all(row["loose_edges"] == 0 for row in mesh_rows),
    "no_loose_vertices": all(row["loose_vertices"] == 0 for row in mesh_rows),
    "no_degenerate_faces": all(row["degenerate_faces_near_zero_area"] == 0 for row in mesh_rows),
    "no_nonmanifold_edges": all(row["nonmanifold_edges_more_than_two_faces"] == 0 for row in mesh_rows),
    "no_true_nonadjacent_self_intersections": total_intersections == 0,
    "hem_center_grid_has_no_low_internal_cap": not opening["interior_connectivity_interpretation"]["hem_center_grid_has_low_internal_block"],
}
report = {
    "status": "PASS_STATIC_CANDIDATE" if all(checks.values()) else "FAIL_STATIC_AND_FUNCTIONAL_CANDIDATE",
    "blender_version": bpy.app.version_string,
    "raw_obj": {"path": str(RAW), "sha256_before": before["raw_obj"], "sha256_after": after["raw_obj"]},
    "checks": checks, "failed_checks": [name for name, passed in checks.items() if not passed],
    "import_axis": {
        "up": "+Z is the prior orientation hypothesis; renders preserve import transforms.",
        "front": "+X is the prior face-direction hypothesis; raw_front/raw_back are labelled by camera axis, not a claim that anatomy was confirmed automatically.",
        "required_readback": "Compare raw_front.png, raw_back.png, raw_side.png, raw_quarter.png against the visible garment before treating the labels as confirmed.",
    },
    "bounds_world": {"min": vec(minimum), "max": vec(maximum), "dimensions": vec(maximum - minimum)},
    "topology": mesh_rows,
    "opening_ray_probes": opening,
    "evidence": {"candidate": candidate_evidence, "approved_v2_silhouette_reference": reference_evidence},
    "comparison": {
        "method": "Human visual silhouette comparison only: raw_front.png and raw_side.png use the candidate import; raw_reference_v2_front.png and raw_reference_v2_side.png use the approved original raw v2 import. Each is orthographic, neutral gray, and fitted independently; no scale matching or geometric difference metric was performed.",
        "result": "READBACK_FAIL_TO_PROMOTE: candidate silhouette is broadly robe-like but has a visible dark torso rectangle and pale adjacent polygon; its 14-, 3-, and 3-vertex disconnected components occupy the same front/side torso zone. This single-color Workbench evidence excludes texture/material variation as the explanation. Relative to v2, the candidate is longer/straighter and smoother, but the visual artifacts and capped openings prevent promotion.",
    },
    "scope_and_limits": {
        "checked": "Raw OBJ integrity hash, imported mesh counts, components, loose/boundary/nonmanifold/degenerate topology, exact non-neighbor triangle intersection audit, directional opening probes including a central hem internal-block test, and neutral-gray inspection renders.",
        "not_checked": "Visual approval, body fit, cloth thickness, UV overlap/density/seams, textures, rigging, weights, deformation, animation, game import, collision, performance, licensing, and whether a detected directional ray corresponds to the intended physical opening.",
        "no_mesh_mutation": "No mesh cleanup, welding, decimation, rigging, repair, texture work, or design change was performed. The saved .blend is an inspection import with QA cameras only.",
    },
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(report["status"], report["failed_checks"])
