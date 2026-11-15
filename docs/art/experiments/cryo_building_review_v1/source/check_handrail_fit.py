"""Run in Blender with the delivered interior_accessories.blend open."""
from pathlib import Path
import json
import math

import bmesh
import bpy
from mathutils.bvhtree import BVHTree

review = Path(bpy.data.filepath).resolve().parent.parent
report = {"variants": {}, "units": "metres"}

for variant in ("HR-A", "HR-B"):
    collection = bpy.data.collections[variant]
    mesh_checks = []
    for obj in collection.all_objects:
        if obj.type != "MESH":
            continue
        data = obj.data
        data.calc_loop_triangles()
        bm = bmesh.new()
        bm.from_mesh(data)
        non_manifold = sum(not edge.is_manifold for edge in bm.edges)
        bm.free()
        degenerate = sum(triangle.area < 1e-10 for triangle in data.loop_triangles)
        assert non_manifold == 0, (obj.name, "open edges", non_manifold)
        assert degenerate == 0, (obj.name, "degenerate triangles", degenerate)

        if any(part in obj.name for part in ("Grip", "GuardTop", "LowerRail")) and "Bracket" not in obj.name:
            vertices = [vertex.co.copy() for vertex in data.vertices]
            triangles = [tuple(triangle.vertices) for triangle in data.loop_triangles]
            tree = BVHTree.FromPolygons(vertices, triangles, all_triangles=True, epsilon=1e-7)
            crossings = [(a, b) for a, b in tree.overlap(tree)
                         if a < b and not set(triangles[a]).intersection(triangles[b])]
            assert not crossings, (obj.name, "self-crossing triangles", crossings[:5])
        mesh_checks.append(obj.name)

    posts = []
    for side in ("Lower", "Upper"):
        side_posts = [obj for obj in collection.all_objects if f"_{side}_Post_" in obj.name]
        assert len(side_posts) == 4
        locations = []
        for obj in side_posts:
            vertices = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
            x = (min(p.x for p in vertices) + max(p.x for p in vertices)) / 2
            run = x + 1.65 if side == "Lower" else 1.65 - x
            step = min(10, math.floor((run + 1e-6) / .30))
            expected = (0 if side == "Lower" else 1.9) + (step + 1) * 1.9 / 12
            actual = min(p.z for p in vertices)
            assert abs(actual - expected) < 1e-5, (obj.name, actual, expected)
            for point in vertices:
                local_run = point.x + 1.65 if side == "Lower" else 1.65 - point.x
                assert math.floor((local_run + 1e-6) / .30) == step, (obj.name, "straddles a riser")
            locations.append(x)
            posts.append({"object": obj.name, "tread": step + 1, "bottom_z_m": actual})
        locations.sort()
        assert max(b - a for a, b in zip(locations, locations[1:])) <= 1.10001

    def span(name, low_x=-1.70, high_x=1.40):
        obj = bpy.data.objects[name]
        points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
        return [p.y for p in points if low_x < p.x < high_x]

    wall = span(variant + "_WallGrip")
    inner = span(variant + "_InnerGrip")
    lower_clear = min(p for p in inner if p < 1) - max(p for p in wall if p < 1)
    upper_clear = min(p for p in wall if p > 2) - max(p for p in inner if p > 1)
    assert min(lower_clear, upper_clear) > 1.60
    report["variants"][variant] = {
        "closed_meshes_checked": len(mesh_checks),
        "tube_self_intersections": 0,
        "structural_posts": posts,
        "lower_grip_clear_width_m": round(lower_clear, 4),
        "upper_grip_clear_width_m": round(upper_clear, 4),
        "target_clear_width_m": 1.80,
        "status": "independent candidate, clearance conflict remains",
    }

destination = review / "evidence/handrail_fit_20261115.json"
destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
print(json.dumps(report, ensure_ascii=False, indent=2))
