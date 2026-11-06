"""Diagnose a bounded outer-shell extraction route for the generated robe.

This script is intentionally diagnostic: it never overwrites source assets.  It
labels raw robe faces by two independent geometric signals:

1. garment normal versus the direction to the nearest body surface; and
2. a short ray through the garment thickness to an approximately opposing face.

The output is a JSON evidence bundle and, when the classification is decisive,
an optional scratch .blend containing labelled face sets for visual inspection.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


EXP = Path(__file__).resolve().parents[1]
ROBE = EXP.parent / "protagonist_tripo_robe_v2/model/protagonist_tripo_robe_v2_raw.glb"
BODY = EXP.parent / "protagonist_tripo_body_v2/model/protagonist_body_v2.glb"
OUT = EXP / "source/robe_repair_diagnosis.json"
SCRATCH = EXP / "scratch/robe_outer_classification.blend"
QA_LIBRARY = EXP.parent / "protagonist_tripo_body_v1/source/body_topology_check.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values, q):
    if not values:
        return None
    rows = sorted(values)
    pos = (len(rows) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return float(rows[lo])
    return float(rows[lo] * (hi - pos) + rows[hi] * (pos - lo))


def summary(values):
    return {
        "count": len(values),
        "min": float(min(values)) if values else None,
        "p05": percentile(values, 0.05),
        "p25": percentile(values, 0.25),
        "median": percentile(values, 0.5),
        "p75": percentile(values, 0.75),
        "p95": percentile(values, 0.95),
        "max": float(max(values)) if values else None,
    }


def import_single_mesh(path: Path, label: str):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    meshes = [o for o in set(bpy.context.scene.objects) - before if o.type == "MESH"]
    if len(meshes) != 1:
        raise RuntimeError(f"Expected one mesh in {path}, got {len(meshes)}")
    obj = meshes[0]
    obj.name = label
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.select_set(False)
    obj.data.calc_loop_triangles()
    return obj


def bvh_for_object(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    verts = [obj.matrix_world @ v.co for v in mesh.vertices]
    faces = [tuple(t.vertices) for t in mesh.loop_triangles]
    return BVHTree.FromPolygons(verts, faces, all_triangles=True)


def face_adjacency(mesh):
    edge_faces = defaultdict(list)
    for poly in mesh.polygons:
        for key in poly.edge_keys:
            edge_faces[tuple(sorted(key))].append(poly.index)
    neighbors = defaultdict(set)
    for faces in edge_faces.values():
        for a in faces:
            neighbors[a].update(b for b in faces if b != a)
    return edge_faces, neighbors


def connected_face_components(face_ids, neighbors):
    remaining = set(face_ids)
    out = []
    while remaining:
        seed = next(iter(remaining))
        comp = set()
        queue = [seed]
        while queue:
            f = queue.pop()
            if f not in remaining:
                continue
            remaining.remove(f)
            comp.add(f)
            queue.extend(neighbors[f] & remaining)
        out.append(comp)
    return sorted(out, key=len, reverse=True)


def safe_unit(v):
    return v.normalized() if v.length > 1e-12 else Vector((0, 0, 0))


def make_material(name, rgba):
    material = bpy.data.materials.new(name)
    material.diffuse_color = rgba
    return material


def assign_labels(obj, labels):
    colors = {
        "outer": (0.08, 0.55, 0.18, 1.0),
        "inner": (0.7, 0.08, 0.08, 1.0),
        "rim": (0.85, 0.5, 0.05, 1.0),
        "unresolved": (0.25, 0.25, 0.8, 1.0),
    }
    slots = {}
    for label, rgba in colors.items():
        slots[label] = len(obj.data.materials)
        obj.data.materials.append(make_material(f"diagnostic_{label}", rgba))
    for poly in obj.data.polygons:
        poly.material_index = slots[labels[poly.index]]


def make_face_subset(source_obj, face_ids, name):
    """Create a scratch-only subset while retaining raw vertex coordinates."""
    wanted = sorted(face_ids)
    used = sorted({v for f in wanted for v in source_obj.data.polygons[f].vertices})
    remap = {old: new for new, old in enumerate(used)}
    vertices = [source_obj.data.vertices[i].co.copy() for i in used]
    faces = [[remap[i] for i in source_obj.data.polygons[f].vertices] for f in wanted]
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def boundary_summary(mesh):
    uses = Counter()
    for poly in mesh.polygons:
        for edge in poly.edge_keys:
            uses[tuple(sorted(edge))] += 1
    boundary = [edge for edge, count in uses.items() if count == 1]
    adjacency = defaultdict(set)
    for a, b in boundary:
        adjacency[a].add(b)
        adjacency[b].add(a)
    remaining = set(adjacency)
    components = []
    while remaining:
        seed = next(iter(remaining))
        vertices = set()
        queue = [seed]
        while queue:
            vertex = queue.pop()
            if vertex in vertices:
                continue
            vertices.add(vertex)
            remaining.discard(vertex)
            queue.extend(adjacency[vertex] - vertices)
        edges = [edge for edge in boundary if edge[0] in vertices and edge[1] in vertices]
        coords = [mesh.vertices[v].co for v in vertices]
        components.append(
            {
                "vertices": len(vertices),
                "edges": len(edges),
                "closed_simple_loop": all(len(adjacency[v]) == 2 for v in vertices),
                "branch_vertices": sum(len(adjacency[v]) != 2 for v in vertices),
                "bounds": {
                    "min": [float(min(p[i] for p in coords)) for i in range(3)],
                    "max": [float(max(p[i] for p in coords)) for i in range(3)],
                },
            }
        )
    return sorted(components, key=lambda row: row["edges"], reverse=True)


def candidate_audit(source_obj, face_ids, name, qa):
    ordered = sorted(face_ids)
    obj = make_face_subset(source_obj, ordered, name)
    obj.hide_viewport = True
    obj.hide_render = True
    obj.data.calc_loop_triangles()
    crossings = qa["self_intersections"](obj.data, obj.matrix_world)
    implicated_subset_faces = sorted(
        {
            row[key]
            for row in crossings["true_nonadjacent_intersections_sample"]
            for key in ("polygon_a", "polygon_b")
        }
    )
    implicated_source_faces = [ordered[i] for i in implicated_subset_faces]
    coords = [vertex.co for vertex in obj.data.vertices]
    return obj, {
        "source_face_count": len(face_ids),
        "topology": qa["topology"](obj.data),
        "crossings": crossings,
        "crossing_implicated_source_face_count": len(implicated_source_faces),
        "crossing_implicated_source_faces": implicated_source_faces,
        "boundary_components": boundary_summary(obj.data),
        "bounds": {
            "min": [float(min(p[i] for p in coords)) for i in range(3)],
            "max": [float(max(p[i] for p in coords)) for i in range(3)],
        },
    }


def main():
    source_hashes = {"robe": sha256(ROBE), "body": sha256(BODY)}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    robe = import_single_mesh(ROBE, "Robe_Raw_Diagnostic")
    body = import_single_mesh(BODY, "BodyV2_Diagnostic")
    body.hide_render = True

    robe_bvh = bvh_for_object(robe)
    body_bvh = bvh_for_object(body)
    mesh = robe.data
    edge_faces, neighbors = face_adjacency(mesh)
    qa_source = QA_LIBRARY.read_text(encoding="utf-8").split("\nbefore={'glb':")[0]
    qa = {"__file__": str(QA_LIBRARY), "__name__": "robe_repair_qa"}
    exec(compile(qa_source, str(QA_LIBRARY), "exec"), qa)

    # A short hit through -normal should find the opposing thickness sheet.  The
    # maximum 0.04 is intentionally far below body/sleeve scale but above the
    # observed generated garment thickness.
    ray_epsilon = 2e-5
    max_thickness = 0.04
    rows = []
    for poly in mesh.polygons:
        center = robe.matrix_world @ poly.center
        normal = safe_unit(robe.matrix_world.to_3x3() @ poly.normal)
        nearest, body_normal, body_tri, body_dist = body_bvh.find_nearest(center)
        to_body = safe_unit(nearest - center) if nearest is not None else Vector()
        body_alignment = float(normal.dot(to_body)) if nearest is not None else 0.0

        hit, hit_normal, hit_tri, thickness = robe_bvh.ray_cast(
            center - normal * ray_epsilon, -normal, max_thickness
        )
        # BVH triangle id maps to loop triangle order, not necessarily polygon id.
        opposing_polygon = None
        opposing_dot = None
        if hit is not None and hit_tri is not None:
            opposing_polygon = int(mesh.loop_triangles[int(hit_tri)].polygon_index)
            opposing_dot = float(normal.dot(safe_unit(hit_normal)))

        rows.append(
            {
                "face": poly.index,
                "center": [float(x) for x in center],
                "z": float(center.z),
                "area": float(poly.area),
                "body_distance": float(body_dist) if body_dist is not None else None,
                "normal_to_body_alignment": body_alignment,
                "opposing_face": opposing_polygon,
                "opposing_normal_dot": opposing_dot,
                "thickness_hit": float(thickness) if hit is not None else None,
            }
        )

    # Pairwise evidence: members of an opposing pair should have opposite normals;
    # whichever is farther from the body is the outer member.  Require both a
    # useful thickness gap and a margin in body distance to avoid guessing.
    by_face = {r["face"]: r for r in rows}
    pair_votes = defaultdict(list)
    accepted_pairs = set()
    for row in rows:
        other_id = row["opposing_face"]
        if other_id is None or other_id == row["face"] or other_id not in by_face:
            continue
        other = by_face[other_id]
        pair = tuple(sorted((row["face"], other_id)))
        if row["opposing_normal_dot"] is None or row["opposing_normal_dot"] > -0.35:
            continue
        if row["thickness_hit"] is None or not (0.00015 <= row["thickness_hit"] <= max_thickness):
            continue
        delta = row["body_distance"] - other["body_distance"]
        if abs(delta) < max(0.00035, 0.10 * row["thickness_hit"]):
            continue
        outer, inner = (row["face"], other_id) if delta > 0 else (other_id, row["face"])
        pair_votes[outer].append("outer")
        pair_votes[inner].append("inner")
        accepted_pairs.add(pair)

    # Independent normal-to-body evidence works well away from connectors.  A
    # strong negative dot means the normal points away from the body (outer);
    # strong positive means it points toward the body (inner).  Weak alignment
    # is expected on rim/connector walls and is kept out of the outer shell.
    labels = {}
    conflict_faces = []
    for row in rows:
        votes = pair_votes[row["face"]]
        pair_label = Counter(votes).most_common(1)[0][0] if votes else None
        pair_conflict = len(set(votes)) > 1
        align = row["normal_to_body_alignment"]
        normal_label = "outer" if align <= -0.35 else "inner" if align >= 0.35 else None
        if pair_conflict or (pair_label and normal_label and pair_label != normal_label):
            labels[row["face"]] = "unresolved"
            conflict_faces.append(row["face"])
        elif pair_label:
            labels[row["face"]] = pair_label
        elif normal_label:
            labels[row["face"]] = normal_label
        elif abs(align) < 0.20:
            labels[row["face"]] = "rim"
        else:
            labels[row["face"]] = "unresolved"

    for row in rows:
        row["classification"] = labels[row["face"]]

    # Never silently bridge an outer region through ambiguous connector faces.
    label_counts = Counter(labels.values())
    components = {
        label: [len(c) for c in connected_face_components({f for f, x in labels.items() if x == label}, neighbors)]
        for label in ("outer", "inner", "rim", "unresolved")
    }

    # Evaluate two non-destructive extraction hypotheses.  The zero-sign version
    # tests whether normal/body orientation alone already separates the sheets.
    # The strict version deliberately omits connector/uncertain faces.
    sign_outer = {r["face"] for r in rows if r["normal_to_body_alignment"] < 0.0}
    strict_outer = {f for f, label in labels.items() if label == "outer"}
    filled_labels = {
        f: label for f, label in labels.items() if label in {"outer", "inner"}
    }
    pending = set(range(len(mesh.polygons))) - set(filled_labels)
    while pending:
        progressed = False
        for face in sorted(pending):
            neighbor_labels = [filled_labels[n] for n in neighbors[face] if n in filled_labels]
            counts = Counter(neighbor_labels)
            if counts["outer"] != counts["inner"] and neighbor_labels:
                filled_labels[face] = "outer" if counts["outer"] > counts["inner"] else "inner"
                pending.remove(face)
                progressed = True
        if not progressed:
            for face in sorted(pending):
                filled_labels[face] = (
                    "outer" if by_face[face]["normal_to_body_alignment"] < 0 else "inner"
                )
            pending.clear()
    filled_outer = {f for f, label in filled_labels.items() if label == "outer"}
    sign_obj, sign_audit = candidate_audit(robe, sign_outer, "Candidate_SignOuter", qa)
    strict_obj, strict_audit = candidate_audit(robe, strict_outer, "Candidate_StrictOuter", qa)
    strict_crossing_faces = set(strict_audit["crossing_implicated_source_faces"])
    strict_minus_crossings = strict_outer - strict_crossing_faces
    clean_obj, clean_audit = candidate_audit(
        robe, strict_minus_crossings, "Candidate_StrictOuter_MinusCrossingFaces", qa
    )
    filled_obj, filled_audit = candidate_audit(robe, filled_outer, "Candidate_FilledOuter", qa)
    filled_minus_crossings = filled_outer - set(filled_audit["crossing_implicated_source_faces"])
    filled_clean_obj, filled_clean_audit = candidate_audit(
        robe, filled_minus_crossings, "Candidate_FilledOuter_MinusCrossingFaces", qa
    )

    # Characterize each interface so a downstream repair can delete/regenerate
    # precisely at labelled cuts rather than using coordinate thresholds.
    interfaces = Counter()
    interface_edges = defaultdict(list)
    for edge, faces in edge_faces.items():
        if len(faces) == 2:
            a, b = sorted((labels[faces[0]], labels[faces[1]]))
            if a != b:
                key = f"{a}--{b}"
                interfaces[key] += 1
                if len(interface_edges[key]) < 24:
                    interface_edges[key].append(list(edge))

    z_bands = [(0.0, 0.55), (0.55, 0.70), (0.70, 0.86), (0.86, 1.01)]
    band_stats = []
    for lo, hi in z_bands:
        subset = [r for r in rows if lo <= r["z"] < hi]
        band_stats.append(
            {
                "z_range": [lo, hi],
                "faces": len(subset),
                "labels": dict(Counter(labels[r["face"]] for r in subset)),
                "body_distance": summary([r["body_distance"] for r in subset]),
                "normal_to_body_alignment": summary([r["normal_to_body_alignment"] for r in subset]),
            }
        )

    assign_labels(robe, labels)
    body.display_type = "WIRE"
    SCRATCH.parent.mkdir(exist_ok=True)
    bpy.context.view_layer.objects.active = robe
    robe.select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(SCRATCH))

    after_hashes = {"robe": sha256(ROBE), "body": sha256(BODY)}
    result = {
        "status": "DIAGNOSTIC_CLASSIFICATION_ONLY",
        "source_hashes_before": source_hashes,
        "source_hashes_after": after_hashes,
        "source_files_unchanged": source_hashes == after_hashes,
        "inputs": {"robe": str(ROBE), "body": str(BODY)},
        "parameters": {
            "ray_epsilon": ray_epsilon,
            "max_thickness": max_thickness,
            "opposing_normal_dot_max": -0.35,
            "strong_body_alignment": 0.35,
            "body_distance_pair_margin_min": 0.00035,
            "body_distance_pair_margin_fraction_of_hit": 0.10,
        },
        "mesh_counts": {"robe_faces": len(mesh.polygons), "robe_vertices": len(mesh.vertices)},
        "signals": {
            "body_distance": summary([r["body_distance"] for r in rows]),
            "normal_to_body_alignment": summary([r["normal_to_body_alignment"] for r in rows]),
            "thickness_hits": summary([r["thickness_hit"] for r in rows if r["thickness_hit"] is not None]),
            "opposing_face_pairs_accepted": len(accepted_pairs),
            "faces_with_pair_votes": sum(bool(pair_votes[f]) for f in range(len(mesh.polygons))),
            "pair_or_normal_conflicts": len(conflict_faces),
            "conflict_face_sample": conflict_faces[:64],
        },
        "classification": {
            "face_counts": dict(label_counts),
            "face_components_descending": components,
            "interfaces": dict(interfaces),
            "interface_edge_samples": dict(interface_edges),
            "z_bands": band_stats,
        },
        "candidate_audits": {
            "normal_to_body_alignment_lt_zero": sign_audit,
            "strict_outer_only": strict_audit,
            "strict_outer_minus_crossing_faces": clean_audit,
            "filled_outer": filled_audit,
            "filled_outer_minus_crossing_faces": filled_clean_audit,
        },
        "face_rows": rows,
        "scratch_blend": str(SCRATCH),
        "scope": [
            "Labels are diagnostic and do not constitute a production repair.",
            "The scratch blend preserves the raw face geometry and only assigns diagnostic materials.",
            "No rigging, deformation, UV, texture, or visual-art approval is claimed.",
        ],
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"counts": dict(label_counts), "pairs": len(accepted_pairs), "conflicts": len(conflict_faces)}))


if __name__ == "__main__":
    main()
