"""Read-only QA import of downloaded Tripo China P2.0 exports.

The GLB is required. When optional OBJ exists, it is the primary editable
inspection import because OBJ can retain quads. The GLB is audited separately.
"""
from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector

EXP = Path(__file__).resolve().parents[1]
RAW_GLB = EXP / "model" / "protagonist_tripo_cn_p20_v1_raw.glb"
RAW_OBJ = EXP / "model" / "protagonist_tripo_cn_p20_v1_raw.obj"
OUT_BLEND = EXP / "model" / "protagonist_cn_p20_inspection.blend"
AUDIT = EXP / "source" / "mesh_audit.json"
EVIDENCE = EXP / "evidence"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def finite_vec(values):
    return all(math.isfinite(value) for value in values)


def import_export(path):
    if path.suffix.lower() == ".glb":
        bpy.ops.import_scene.gltf(filepath=str(path))
    elif path.suffix.lower() == ".obj":
        bpy.ops.wm.obj_import(filepath=str(path))
    else:
        raise RuntimeError(f"Unsupported inspection export: {path}")


def mesh_audit(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    parents = list(range(len(mesh.vertices)))

    def find(index):
        while index != parents[index]:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for edge in mesh.edges:
        left, right = map(find, edge.vertices)
        if left != right:
            parents[right] = left
    components = {}
    for vertex in mesh.vertices:
        root = find(vertex.index)
        components[root] = components.get(root, 0) + 1

    edge_uses = [0] * len(mesh.edges)
    edge_lookup = {tuple(sorted(edge.vertices)): edge.index for edge in mesh.edges}
    for polygon in mesh.polygons:
        for edge_key in polygon.edge_keys:
            edge_uses[edge_lookup[tuple(sorted(edge_key))]] += 1
    uv_layers = []
    for layer in mesh.uv_layers:
        coords = [tuple(loop.uv) for loop in layer.data]
        uv_layers.append({
            "name": layer.name, "loops": len(coords),
            "finite_coordinates": all(finite_vec(coord) for coord in coords),
            "coordinates_outside_0_1": sum(any(v < -1e-5 or v > 1.00001 for v in coord) for coord in coords),
        })
    return {
        "object": obj.name, "vertices": len(mesh.vertices), "edges": len(mesh.edges),
        "polygons": len(mesh.polygons), "triangles_after_triangulation": len(mesh.loop_triangles),
        "triangle_polygons": sum(len(poly.vertices) == 3 for poly in mesh.polygons),
        "quad_polygons": sum(len(poly.vertices) == 4 for poly in mesh.polygons),
        "ngon_polygons": sum(len(poly.vertices) > 4 for poly in mesh.polygons),
        "connected_components": len(components),
        "component_vertex_counts_descending": sorted(components.values(), reverse=True),
        "boundary_edges": sum(count == 1 for count in edge_uses),
        "loose_edges": sum(count == 0 for count in edge_uses),
        "nonmanifold_edges_more_than_two_faces": sum(count > 2 for count in edge_uses),
        "degenerate_edges_near_zero": sum(
            (mesh.vertices[edge.vertices[0]].co - mesh.vertices[edge.vertices[1]].co).length < 1e-12
            for edge in mesh.edges
        ),
        "degenerate_faces_near_zero_area": sum(poly.area < 1e-12 for poly in mesh.polygons),
        "finite_vertex_coordinates": all(finite_vec(vertex.co) for vertex in mesh.vertices),
        "uv_layers": uv_layers,
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        "vertex_group_count": len(obj.vertex_groups),
        "shape_keys": list(mesh.shape_keys.key_blocks.keys()) if mesh.shape_keys else [],
        "armature_modifiers": [mod.name for mod in obj.modifiers if mod.type == "ARMATURE"],
    }


def snapshot_current_import(export_path):
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"{export_path.name} imported without mesh objects.")
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    minimum = Vector([min(point[axis] for point in points) for axis in range(3)])
    maximum = Vector([max(point[axis] for point in points) for axis in range(3)])
    armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
    return ({
        "file": export_path.name, "mesh_objects": len(meshes),
        "armatures": [{"object": obj.name, "bones": len(obj.data.bones)} for obj in armatures],
        "image_datablocks": len(bpy.data.images),
        "bounds_in_imported_units": {"min": list(minimum), "max": list(maximum), "dimensions": list(maximum - minimum)},
        "meshes": [mesh_audit(obj) for obj in meshes],
    }, meshes, minimum, maximum)


def point_camera(collection, name, location, target, ortho_scale):
    data = bpy.data.cameras.new(name)
    camera = bpy.data.objects.new(name, data)
    collection.objects.link(camera)
    camera.location = location
    camera.rotation_euler = (target - location).to_track_quat("-Z", "Y").to_euler()
    data.type = "ORTHO"
    data.ortho_scale = ortho_scale
    data.clip_end = max((location - target).length * 10, 100)
    return camera


if not RAW_GLB.is_file():
    raise RuntimeError(f"Downloaded raw GLB is required at {RAW_GLB}; no substitute will be generated.")
# This approved orientation-only rerun intentionally overwrites this script's own
# QA outputs; raw source integrity remains protected by pre/post hash checks.
hashes_before = {RAW_GLB.name: sha256(RAW_GLB)}
if RAW_OBJ.is_file():
    hashes_before[RAW_OBJ.name] = sha256(RAW_OBJ)
EVIDENCE.mkdir(parents=True, exist_ok=True)

# Audit GLB alone, so exported triangles cannot be conflated with Tripo UI quads.
bpy.ops.wm.read_factory_settings(use_empty=True)
import_export(RAW_GLB)
glb_snapshot, _, _, _ = snapshot_current_import(RAW_GLB)

# A clean scene holds only one primary export: OBJ when available, otherwise GLB.
primary = RAW_OBJ if RAW_OBJ.is_file() else RAW_GLB
bpy.ops.wm.read_factory_settings(use_empty=True)
import_export(primary)
primary_snapshot, meshes, minimum, maximum = snapshot_current_import(primary)
center = (minimum + maximum) / 2
span = maximum - minimum
height = max(span.z, 0.01)
width = max(span.x, span.y, 0.01)
distance = max(height, width) * 4

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "SINGLE"
scene.display.shading.single_color = (0.62, 0.65, 0.65)
scene.display.shading.background_type = "WORLD"
scene.world = bpy.data.worlds.new("QA Review Background")
scene.world.color = (0.045, 0.055, 0.06)
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "BOTH"
scene.display.shading.show_specular_highlight = False
qa = bpy.data.collections.new("QA_CAMERAS_ONLY")
scene.collection.children.link(qa)
full_scale = max(height * 1.22 * (1280 / 720), width * 1.22)
view_specs = [
    ("front", (1, 0, 0), center, full_scale),
    ("side", (0, -1, 0), center, full_scale),
    ("back", (-1, 0, 0), center, full_scale),
    ("quarter", (0.8, -1, 0.25), center, full_scale),
]
head_center = Vector((center.x, center.y, maximum.z - height * 0.16))
view_specs.append(("head_back", (-1, 0, 0), head_center, max(height * 0.42 * (1280 / 720), width * 0.28)))
for name, direction, target, ortho_scale in view_specs:
    camera = point_camera(qa, f"QA_{name}", target + Vector(direction).normalized() * distance, target, ortho_scale)
    scene.camera = camera
    scene.render.filepath = str(EVIDENCE / f"blender_{name}.png")
    bpy.ops.render.render(write_still=True)
scene.camera = bpy.data.objects["QA_quarter"]

hashes_after = {RAW_GLB.name: sha256(RAW_GLB)}
if RAW_OBJ.is_file():
    hashes_after[RAW_OBJ.name] = sha256(RAW_OBJ)
if hashes_after != hashes_before:
    raise RuntimeError("Raw export hash changed during inspection; outputs were not accepted.")
report = {
    "blender_version": bpy.app.version_string,
    "provider_ui_reported_target": "3020 Quad / 3218 verts (provider UI observation; not independently verified by this audit)",
    "primary_rendered_and_saved_export": primary.name,
    "primary_import_axis_note": "Anatomical orientation was visually checked from the unedited first QA render: upright +Z, face toward +X. Cameras use +X front, -X back, -Y side; no mesh rotation was applied.",
    "primary_export": primary_snapshot,
    "glb_export_inspected_separately": glb_snapshot,
    "raw_sha256_before": hashes_before, "raw_sha256_after": hashes_after,
    "raw_files_unchanged_during_inspection": True,
    "limits": [
        "Connected components do not establish semantic body, gown, hair, or accessory separation.",
        "UV layer presence and finite coordinates do not test UV overlap, texel density, seams, or paint readiness.",
        "GLB triangle totals and OBJ polygon totals are intentionally reported separately; neither proves the provider UI count.",
        "No cleanup, retopology, UV edits, texture edits, rigging, animation, or Godot validation was performed.",
        "Workbench evidence is an inspection aid, not user art acceptance.",
    ],
}
AUDIT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
print("CN_P20_INSPECTED; primary export saved without edits; raw export hashes unchanged.")
