"""Read-only UV/topology audit for character_fitting_draft_v5.blend.

Writes only audit/uv_topology_audit_v5.json.  Uses loop UVs from each mesh's
active layer; positive-area triangle intersections include containment and
ignore shared-edge/vertex contact.  This script never saves the .blend.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict, deque
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "character_fitting_draft_v5.blend"
OUTPUT = Path(__file__).resolve().parent / "uv_topology_audit_v5.json"
EPS = 1e-10
TARGETS = ("Body_165cm_CC0_pistachio", "Hair_Back_Fitted", "Hair_Front.L", "Hair_Front.R", "Robe_White_Fitted")


def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def area(tri):
    return abs(orient(tri[0], tri[1], tri[2])) * 0.5


def overlap_area(subject, clip):
    """Sutherland-Hodgman clipping, so complete containment is detected."""
    out = list(subject)
    if orient(clip[0], clip[1], clip[2]) < 0:
        clip = list(reversed(clip))
    for i, a in enumerate(clip):
        b = clip[(i + 1) % 3]
        if not out:
            return 0.0
        src, out = out, []
        for j, cur in enumerate(src):
            prev = src[j - 1]
            cp, pp = orient(a, b, cur), orient(a, b, prev)
            cin, pin = cp >= -EPS, pp >= -EPS
            if cin != pin:
                den = pp - cp
                if abs(den) > EPS:
                    t = pp / den
                    out.append((prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1])))
            if cin:
                out.append(cur)
    return abs(sum(out[i][0] * out[(i + 1) % len(out)][1] - out[(i + 1) % len(out)][0] * out[i][1] for i in range(len(out)))) * .5 if len(out) >= 3 else 0.0


def contains(tri, point):
    signs = [orient(tri[i], tri[(i + 1) % 3], point) for i in range(3)]
    return not (any(v > EPS for v in signs) and any(v < -EPS for v in signs))


def uv_islands(mesh, layer):
    # Polygons connect only through an edge whose two endpoint UVs agree.
    linked = defaultdict(list)
    for poly in mesh.polygons:
        loops = list(poly.loop_indices)
        for i, loop in enumerate(loops):
            nxt = loops[(i + 1) % len(loops)]
            va, vb = mesh.loops[loop].vertex_index, mesh.loops[nxt].vertex_index
            ua, ub = layer.data[loop].uv, layer.data[nxt].uv
            key = tuple(sorted((va, vb)))
            linked[key].append((poly.index, va, vb, (round(float(ua.x), 10), round(float(ua.y), 10)), (round(float(ub.x), 10), round(float(ub.y), 10))))
    adjacent = defaultdict(set)
    for refs in linked.values():
        for i, one in enumerate(refs):
            for two in refs[i + 1:]:
                # Reverse winding and matching endpoint loop UVs means no UV seam.
                if one[1] == two[2] and one[2] == two[1] and one[3] == two[4] and one[4] == two[3]:
                    adjacent[one[0]].add(two[0]); adjacent[two[0]].add(one[0])
    unseen, sizes = set(p.index for p in mesh.polygons), []
    while unseen:
        seed = unseen.pop(); queue = deque([seed]); count = 1
        while queue:
            for other in adjacent[queue.popleft()]:
                if other in unseen:
                    unseen.remove(other); queue.append(other); count += 1
        sizes.append(count)
    return {"count": len(sizes), "polygon_counts_desc": sorted(sizes, reverse=True), "single_polygon_islands": sum(v == 1 for v in sizes)}


def uv_audit(obj):
    mesh = obj.data
    layer = mesh.uv_layers.active
    if layer is None:
        return {"active_layer": None, "error": "no active UV layer"}
    mesh.calc_loop_triangles()
    tris, zero, outside = [], [], []
    for i, tri in enumerate(mesh.loop_triangles):
        points = [(float(layer.data[li].uv.x), float(layer.data[li].uv.y)) for li in tri.loops]
        if area(points) <= EPS:
            zero.append(i)
        if any(not math.isfinite(x) or not math.isfinite(y) or x < -EPS or x > 1 + EPS or y < -EPS or y > 1 + EPS for x, y in points):
            outside.append(i)
        tris.append((tri.polygon_index, points))
    # Uniform 24x24 bins provide a finite candidate set without missing large or contained triangles.
    bins, pairs = defaultdict(list), set()
    for i, (_, tri) in enumerate(tris):
        lo_u, hi_u = min(p[0] for p in tri), max(p[0] for p in tri)
        lo_v, hi_v = min(p[1] for p in tri), max(p[1] for p in tri)
        for x in range(max(0, int(math.floor(lo_u * 24))), min(23, int(math.floor(hi_u * 24))) + 1):
            for y in range(max(0, int(math.floor(lo_v * 24))), min(23, int(math.floor(hi_v * 24))) + 1):
                for other in bins[(x, y)]:
                    pairs.add((other, i))
                bins[(x, y)].append(i)
    hits, contained = [], 0
    for a, b in sorted(pairs):
        at, bt = tris[a][1], tris[b][1]
        z = overlap_area(at, bt)
        if z > EPS:
            a_in_b, b_in_a = all(contains(bt, p) for p in at), all(contains(at, p) for p in bt)
            contained += a_in_b or b_in_a
            if len(hits) < 20:
                hits.append({"triangles": [a, b], "polygons": [tris[a][0], tris[b][0]], "area": z, "a_fully_in_b": a_in_b, "b_fully_in_a": b_in_a})
    return {
        "active_layer": layer.name,
        "active_render_layer": next((u.name for u in mesh.uv_layers if u.active_render), None),
        "triangles": len(tris), "zero_area_triangle_count": len(zero), "zero_area_triangle_samples": zero[:20],
        "out_of_unit_square_triangle_count": len(outside), "out_of_unit_square_triangle_samples": outside[:20],
        "positive_area_overlap_pair_count": sum(1 for a, b in pairs if overlap_area(tris[a][1], tris[b][1]) > EPS),
        "contained_overlap_pair_count": contained, "overlap_samples": hits,
        "candidate_pair_count": len(pairs), "islands": uv_islands(mesh, layer),
    }


def hair_nonmanifold(obj):
    mesh = obj.data
    refs = defaultdict(list)
    for poly in mesh.polygons:
        vs = list(poly.vertices)
        for i, a in enumerate(vs):
            refs[tuple(sorted((a, vs[(i + 1) % len(vs)])))].append(poly.index)
    bad = []
    for edge, faces in refs.items():
        if len(faces) > 2:
            bad.append({
                "edge_vertices": list(edge),
                "adjoining_polygon_indices": sorted(faces),
                "edge_vertex_coordinates_object_space": [list(mesh.vertices[v].co) for v in edge],
                "adjoining_polygons": [
                    {
                        "index": face,
                        "vertices": list(mesh.polygons[face].vertices),
                        "normal_object_space": list(mesh.polygons[face].normal),
                        "center_object_space": list(mesh.polygons[face].center),
                    }
                    for face in sorted(faces)
                ],
            })
    return {"object": obj.name, "nonmanifold_edge_count": len(bad), "edges": bad}


def main():
    bpy.ops.wm.open_mainfile(filepath=str(INPUT), use_scripts=False)
    found = {name: bpy.data.objects.get(name) for name in TARGETS}
    report = {"input": str(INPUT), "scope": "Read-only active-UV and source-hair topology audit; no repair or fitting claim.", "objects": {}}
    for name, obj in found.items():
        if obj is None:
            report["objects"][name] = {"error": "missing from assembled draft"}
        elif obj.type != 'MESH':
            report["objects"][name] = {"error": f"not a mesh: {obj.type}"}
        else:
            report["objects"][name] = {"vertices": len(obj.data.vertices), "polygons": len(obj.data.polygons), "uv": uv_audit(obj)}
    back = found.get("Hair_Back_Fitted")
    report["source_hair_nonmanifold"] = hair_nonmanifold(back) if back else {"error": "Hair_Back_Fitted missing"}
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
