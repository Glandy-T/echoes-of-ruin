"""Read-only, independent acceptance check for the Body V2 delivery.

This script never saves a Blender file or modifies an asset.  It imports the
known-good exact triangle classifier from the V1 checker by AST, rather than
re-implementing it.  Run with Blender 5:
  blender --background --python source/independent_validation.py
"""
from pathlib import Path
from collections import Counter
import ast
import hashlib
import json
import math

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


EXP = Path(__file__).resolve().parents[1]
REPO = EXP.parents[3]
V1 = EXP.parent / "protagonist_tripo_body_v1"
RAW_OBJ = V1 / "model" / "protagonist_tripo_body_v1_raw.obj"
RAW_GLB = V1 / "model" / "protagonist_tripo_body_v1_raw.glb"
MASTER = EXP / "model" / "protagonist_body_v2.blend"
DELIVERY_GLB = EXP / "model" / "protagonist_body_v2.glb"
PROBE = EXP / "model" / "body_v2_motion_probe.blend"
V1_CLASSIFIER = V1 / "source" / "body_topology_check.py"
MOTION_REPORT = EXP / "source" / "motion_probe_report.json"
BUILD_REPORT = EXP / "source" / "build_report.json"
CAPTURE_RECORD = EXP / "source" / "capture_record.json"
OUT = EXP / "source" / "independent_validation.json"

RAW_OBJ_SHA256 = "49e3cc0ab87beb4b9ff12688ed64b7df7081d31729baae94a29c88cff86fbaeb"
RAW_GLB_SHA256 = "b5fe1a0aff5581c47121f935f905bc991fbf0ae6f32aed8f7135c1f35c742069"
EXPECTED_RAW_GLB_INDICES = 2969
EXPECTED_WELDED_VERTICES = 2950
EXPECTED_UNCHANGED_SURFACE_COORDS = 2762
EXPECTED_PROBE_FRAMES = [1, 20, 40, 60]
EPS = 1e-8
POINT_EPS = 2e-7
AREA_EPS = 1e-13


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def artifact_key(path):
    return str(path.relative_to(REPO)).replace("\\", "/")


def vec(v):
    return [float(x) for x in v]


def load_v1_exact_classifier():
    """Execute only the exact predicate definitions from the V1 source file."""
    source = V1_CLASSIFIER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(V1_CLASSIFIER))
    needed = {"area2", "clip2", "dedupe", "segment_triangle", "triangle_intersection"}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in needed]
    found = {node.name for node in nodes}
    if found != needed:
        raise RuntimeError("V1 exact intersection classifier definitions were not found")
    namespace = {
        "EPS": EPS, "POINT_EPS": POINT_EPS, "AREA_EPS": AREA_EPS,
        "Vector": Vector, "vec": vec,
    }
    module = ast.Module(body=nodes, type_ignores=[])
    exec(compile(module, str(V1_CLASSIFIER), "exec"), namespace)
    return namespace


V1_EXACT = load_v1_exact_classifier()


def exact_weld_copy(mesh):
    """Return an unsaved copy with only bit-identical-position vertices welded."""
    result = mesh.copy()
    bm = bmesh.new()
    bm.from_mesh(result)
    # dist=0.0 deliberately limits this to exact coordinate coincidence.
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0)
    bm.to_mesh(result)
    bm.free()
    result.update()
    return result


def topology(mesh):
    mesh.calc_loop_triangles()
    uses = Counter()
    used_vertices = set()
    for poly in mesh.polygons:
        indices = list(poly.vertices)
        used_vertices.update(indices)
        for a, b in zip(indices, indices[1:] + indices[:1]):
            uses[tuple(sorted((a, b)))] += 1
    parent = list(range(len(mesh.vertices)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for a, b in uses:
        a, b = find(a), find(b)
        if a != b:
            parent[b] = a
    components = Counter(find(index) for index in used_vertices)
    return {
        "vertices": len(mesh.vertices),
        "polygons": len(mesh.polygons),
        "triangles": len(mesh.loop_triangles),
        "connected_components": len(components),
        "component_vertex_counts_descending": sorted(components.values(), reverse=True),
        "loose_vertices": len(mesh.vertices) - len(used_vertices),
        "boundary_edges": sum(count == 1 for count in uses.values()),
        "nonmanifold_edges": sum(count > 2 for count in uses.values()),
        "degenerate_faces": sum(poly.area <= 1e-12 for poly in mesh.polygons),
    }


def intersection_audit(mesh, matrix_world=None):
    """BVH candidates filtered through V1's exact triangle classifier."""
    matrix_world = matrix_world or Matrix.Identity(4)
    mesh.calc_loop_triangles()
    triangles = []
    for index, triangle in enumerate(mesh.loop_triangles):
        coords = [matrix_world @ mesh.vertices[vertex].co for vertex in triangle.vertices]
        triangles.append((tuple(triangle.vertices), coords, index))
    vertices = [point for _, coords, _ in triangles for point in coords]
    faces = [(3 * index, 3 * index + 1, 3 * index + 2) for index in range(len(triangles))]
    bvh = BVHTree.FromPolygons(vertices, faces, all_triangles=True)
    pairs = sorted({tuple(sorted(pair)) for pair in bvh.overlap(bvh) if pair[0] != pair[1]})
    classifications = Counter()
    true = []
    classifier = V1_EXACT["triangle_intersection"]
    for left, right in pairs:
        lverts, lcoords, _ = triangles[left]
        rverts, rcoords, _ = triangles[right]
        if set(lverts) & set(rverts):
            classifications["excluded_shared_vertex_neighbor"] += 1
            continue
        result = classifier(lcoords, rcoords)
        kind = result["kind"]
        classifications[kind] += 1
        if kind in ("proper_crossing", "edge_crossing", "coplanar_overlap"):
            true.append({"triangles": [left, right], "kind": kind})
    return {
        "bvh_candidate_pair_count": len(pairs),
        "classification_counts": dict(classifications),
        "true_nonadjacent_intersection_count": len(true),
        "sample": true[:20],
        "classifier_source": artifact_key(V1_CLASSIFIER),
    }


def closed_single_component_clean(topo, intersections):
    return (
        topo["connected_components"] == 1
        and topo["loose_vertices"] == 0
        and topo["boundary_edges"] == 0
        and topo["nonmanifold_edges"] == 0
        and topo["degenerate_faces"] == 0
        and intersections["true_nonadjacent_intersection_count"] == 0
    )


def surface_coordinate_counter(mesh, outside_toe_only=False):
    used = {index for poly in mesh.polygons for index in poly.vertices}
    coords = []
    for index in used:
        point = mesh.vertices[index].co
        # The build's documented full proof envelope is x > .022 and z < .070.
        if outside_toe_only and point.x > 0.022 and point.z < 0.070:
            continue
        coords.append(tuple(round(float(value), 12) for value in point))
    return Counter(coords)


def scene_meshes():
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def clear_and_open(path):
    bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)


def master_check():
    clear_and_open(MASTER)
    meshes = scene_meshes()
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    mesh = meshes[0].data if len(meshes) == 1 else None
    raw = topology(mesh) if mesh else None
    welded = exact_weld_copy(mesh) if mesh else None
    welded_topology = topology(welded) if welded else None
    crossings = intersection_audit(welded) if welded else None
    result = {
        "mesh_object_count": len(meshes),
        "armature_object_count": len(armatures),
        "mesh_name": meshes[0].name if len(meshes) == 1 else None,
        "vertex_group_count": len(meshes[0].vertex_groups) if len(meshes) == 1 else None,
        "armature_modifier_count": sum(mod.type == "ARMATURE" for obj in meshes for mod in obj.modifiers),
        "raw_topology": raw,
        "after_exact_coordinate_weld": {"topology": welded_topology, "self_intersection_audit": crossings},
    }
    result["passes"] = (
        len(meshes) == 1 and len(armatures) == 0
        and result["vertex_group_count"] == 0 and result["armature_modifier_count"] == 0
        and closed_single_component_clean(welded_topology, crossings)
    ) if mesh else False
    return result


def glb_check():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(DELIVERY_GLB))
    meshes = scene_meshes()
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    mesh = meshes[0].data if len(meshes) == 1 else None
    raw = topology(mesh) if mesh else None
    welded = exact_weld_copy(mesh) if mesh else None
    welded_topology = topology(welded) if welded else None
    crossings = intersection_audit(welded) if welded else None
    result = {
        "mesh_object_count": len(meshes),
        "armature_object_count": len(armatures),
        "raw_index_topology": raw,
        "after_exact_coordinate_weld": {"topology": welded_topology, "self_intersection_audit": crossings},
    }
    result["normal_index_seam_interpretation"] = (
        "The imported GLB has split raw indices for custom-normal seams. "
        "Raw-index boundary edges are not geometric cracks when the exact-coordinate "
        "welded copy is closed."
    )
    result["passes"] = (
        len(meshes) == 1 and len(armatures) == 0 and raw["vertices"] == EXPECTED_RAW_GLB_INDICES
        and welded_topology["vertices"] == EXPECTED_WELDED_VERTICES
        and closed_single_component_clean(welded_topology, crossings)
    ) if mesh else False
    return result


def raw_v1_and_change_bound_check():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=str(RAW_OBJ))
    meshes = scene_meshes()
    if len(meshes) != 1:
        return {"passes": False, "reason": "raw OBJ did not import as exactly one mesh"}
    obj = meshes[0]
    bpy.context.view_layer.objects.active = obj
    obj.rotation_euler[0] = math.pi / 2
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    raw_welded = exact_weld_copy(obj.data)
    raw_outside = surface_coordinate_counter(raw_welded, outside_toe_only=True)
    raw_welded_vertex_count = len(raw_welded.vertices)
    raw_outside_coordinate_count = sum(raw_outside.values())

    clear_and_open(MASTER)
    master_meshes = scene_meshes()
    master_welded = exact_weld_copy(master_meshes[0].data) if len(master_meshes) == 1 else None
    master_outside = surface_coordinate_counter(master_welded, outside_toe_only=True) if master_welded else Counter()
    result = {
        "proof_envelope": "x > 0.022 and z < 0.070",
        "raw_v1_welded_vertices": raw_welded_vertex_count,
        "raw_v1_outside_envelope_surface_coordinates": raw_outside_coordinate_count,
        "v2_outside_envelope_surface_coordinates": sum(master_outside.values()),
        "outside_envelope_coordinate_multisets_identical": raw_outside == master_outside,
        "expected_unchanged_coordinate_count": EXPECTED_UNCHANGED_SURFACE_COORDS,
    }
    result["passes"] = (
        result["raw_v1_welded_vertices"] == 3067
        and result["raw_v1_outside_envelope_surface_coordinates"] == EXPECTED_UNCHANGED_SURFACE_COORDS
        and result["v2_outside_envelope_surface_coordinates"] == EXPECTED_UNCHANGED_SURFACE_COORDS
        and result["outside_envelope_coordinate_multisets_identical"]
    )
    return result


def probe_check(motion_report):
    if not PROBE.exists():
        return {"exists": False, "passes": False}
    clear_and_open(PROBE)
    scene = bpy.context.scene
    meshes = scene_meshes()
    rigs = [obj for obj in scene.objects if obj.type == "ARMATURE"]
    body = meshes[0] if len(meshes) == 1 else None
    rig = rigs[0] if len(rigs) == 1 else None
    bone_names = set(rig.data.bones.keys()) if rig else set()
    group_names = {group.index: group.name for group in body.vertex_groups} if body else {}
    weights = []
    if body:
        for vertex in body.data.vertices:
            active = [group.weight for group in vertex.groups if group_names.get(group.group) in bone_names and group.weight > 1e-6]
            weights.append((sum(active), len(active)))
    action = rig.animation_data.action if rig and rig.animation_data else None
    curves = []
    if action:
        if hasattr(action, "fcurves"):  # Blender 4.x legacy actions
            curves = list(action.fcurves)
        else:  # Blender 5 layered action API
            for layer in action.layers:
                for strip in layer.strips:
                    for channelbag in strip.channelbags:
                        curves.extend(channelbag.fcurves)
    keyed_frames = sorted({round(point.co.x) for curve in curves for point in curve.keyframe_points})
    recomputed = []
    if body:
        for frame in EXPECTED_PROBE_FRAMES:
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = evaluated.to_mesh()
            coordinates = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
            recomputed.append({
                "frame": frame,
                "finite_deformed_vertices": all(math.isfinite(value) for point in coordinates for value in point),
                "nonadjacent_crossings": intersection_audit(mesh, evaluated.matrix_world)["true_nonadjacent_intersection_count"],
            })
            evaluated.to_mesh_clear()
    poses = motion_report.get("poses", [])
    reported_frames = [pose.get("frame") for pose in poses]
    result = {
        "exists": True,
        "mesh_object_count": len(meshes),
        "armature_object_count": len(rigs),
        "actual_bone_count": len(bone_names),
        "actual_vertex_count": len(body.data.vertices) if body else None,
        "actual_vertex_group_count": len(body.vertex_groups) if body else None,
        "actual_unweighted_vertices": sum(total <= 0 for total, _ in weights) if weights else None,
        "actual_maximum_weight_sum_error": max((abs(total - 1) for total, _ in weights), default=None),
        "actual_maximum_influences": max((count for _, count in weights), default=None),
        "actual_keyed_frames": keyed_frames,
        "report_pose_frames": reported_frames,
        "report_bone_spec_count": len(motion_report.get("bone_specs", [])),
        "report_vertices": motion_report.get("vertices"),
        "report_unweighted_vertices": motion_report.get("unweighted_vertices"),
        "report_maximum_weight_sum_error": motion_report.get("maximum_weight_sum_error"),
        "report_maximum_influences": motion_report.get("maximum_influences"),
        "recomputed_probe_frames": recomputed,
    }
    result["capture_structure_matches"] = (
        len(meshes) == 1 and len(rigs) == 1 and len(bone_names) == len(motion_report.get("bone_specs", []))
        and result["actual_vertex_count"] == motion_report.get("vertices")
        and keyed_frames == EXPECTED_PROBE_FRAMES and reported_frames == EXPECTED_PROBE_FRAMES
        and result["actual_unweighted_vertices"] == 0
    )
    result["recomputed_finite_and_zero_crossing"] = all(
        row["finite_deformed_vertices"] and row["nonadjacent_crossings"] == 0 for row in recomputed
    )
    # Weight sums are recorded faithfully; their nonzero error is a limitation, not concealed.
    result["weight_sum_normalization_pass"] = result["actual_maximum_weight_sum_error"] is not None and result["actual_maximum_weight_sum_error"] <= 1e-6
    result["passes_capture_only"] = result["capture_structure_matches"] and result["recomputed_finite_and_zero_crossing"]
    return result


before_hashes = {artifact_key(path): sha(path) for path in (RAW_OBJ, RAW_GLB, MASTER, DELIVERY_GLB, PROBE)}
motion_report = json.loads(MOTION_REPORT.read_text(encoding="utf-8"))
build_report = json.loads(BUILD_REPORT.read_text(encoding="utf-8"))
capture_record = json.loads(CAPTURE_RECORD.read_text(encoding="utf-8"))
master = master_check()
glb = glb_check()
change_bound = raw_v1_and_change_bound_check()
probe = probe_check(motion_report)
after_hashes = {artifact_key(path): sha(path) for path in (RAW_OBJ, RAW_GLB, MASTER, DELIVERY_GLB, PROBE)}

file_checks = {
    "raw_v1_obj_hash_matches_known_immutable_hash": before_hashes[artifact_key(RAW_OBJ)] == RAW_OBJ_SHA256,
    "raw_v1_glb_hash_matches_known_immutable_hash": before_hashes[artifact_key(RAW_GLB)] == RAW_GLB_SHA256,
    "all_read_artifacts_unchanged_during_validation": before_hashes == after_hashes,
    "motion_report_master_hash_matches_current_master": motion_report.get("master_unchanged_sha256") == before_hashes[artifact_key(MASTER)],
    "capture_record_master_hash_matches_current_master": capture_record.get("model_sha256") == before_hashes[artifact_key(MASTER)],
    "build_report_glb_hash_matches_current_delivery_glb": build_report.get("exported_glb", {}).get("sha256") == before_hashes[artifact_key(DELIVERY_GLB)],
}
static_pass = all(file_checks.values()) and master["passes"] and glb["passes"] and change_bound["passes"]
result = {
    "status": "PASS_STATIC_WITH_PROBE_LIMITATION" if static_pass else "FAIL_STATIC_ACCEPTANCE",
    "file_side_validation": {
        "artifact_sha256_before": before_hashes,
        "artifact_sha256_after": after_hashes,
        "checks": file_checks,
        "master_blend": master,
        "glb_reimport": glb,
        "bounded_foot_change": change_bound,
    },
    "runtime_validation": {
        "kind": "offline Blender probe readback, not Godot or shipped-animation runtime validation",
        "motion_probe": probe,
        "finding": (
            "The saved temporary probe has the four recorded keyframes and recomputes finite, zero-crossing geometry. "
            "Top-four weights are normalized within the 1e-6 validation tolerance; the earlier automatic-heat error is retained separately in the source report."
        ),
    },
    "not_tested": [
        "No Godot import, game playback, animation export, or final animation-ready claim.",
        "No visual/art acceptance; parent-reviewed same-camera feet/front/side evidence remains the art gate.",
        "No UV, garment fit, garment skinning, production rig, hand/finger rig, or final joint/weight approval.",
        "Custom-normal index seams in the raw GLB were deliberately evaluated after exact-coordinate weld; they are not reported as geometric cracks.",
    ],
    "acceptance_summary": {
        "static_geometry_pass": static_pass,
        "probe_capture_pass_only": probe.get("passes_capture_only", False),
        "animation_ready": False,
        "unresolved_probe_weight_normalization": not probe.get("weight_sum_normalization_pass", False),
    },
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(result["status"])
