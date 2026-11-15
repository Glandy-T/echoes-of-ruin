"""Make three untextured single-flight samples from the published review.

Blender metres, Z up. The new C section puts a recessed gripping edge into
an 80 mm prefabricated body located on the stairwell side of the tread edge.
"""
from pathlib import Path
import json
import math

import bmesh
import bpy
from mathutils import Vector

folder = Path(__file__).resolve().parent.parent
root = folder.parents[3]
output = root / "assets/art/cryo_handrail_integrated_v1"
output.mkdir(parents=True, exist_ok=True)
source = root / "docs/art/experiments/cryo_building_review_v1/model/interior_accessories.blend"
bpy.ops.wm.open_mainfile(filepath=str(source))
bpy.context.preferences.filepaths.save_version = 0

gray = bpy.data.materials.new("ShapeGray")
gray.use_nodes = True
gray.diffuse_color = (.30, .32, .31, 1)
shader = gray.node_tree.nodes.get("Principled BSDF")
shader.inputs["Base Color"].default_value = gray.diffuse_color
shader.inputs["Roughness"].default_value = .90
shader.inputs["Specular IOR Level"].default_value = .12

samples = []

def collection(name):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    samples.append(result)
    return result

def native_uv(data):
    layer = data.uv_layers.active or data.uv_layers.new(name="UV0_80px_m")
    for polygon in data.polygons:
        points = [data.vertices[i].co for i in polygon.vertices]
        origin = points[0]
        axis = next((p - origin).normalized() for p in points[1:] if (p - origin).length > 1e-6)
        across = polygon.normal.cross(axis).normalized()
        for loop, point in zip(polygon.loop_indices, points):
            delta = point - origin
            layer.data[loop].uv = (delta.dot(axis) * 80 / 256, delta.dot(across) * 80 / 256)

def object_mesh(target, name, vertices, faces):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    data.update()
    native_uv(data)
    data.materials.append(gray)
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    return obj

for variant in ("A", "B"):
    target = collection("HR_" + variant + "_SINGLE_FLIGHT")
    source_collection = bpy.data.collections["HR-" + variant]
    for obj in source_collection.all_objects:
        keep = "_Lower_" in obj.name or any(
            part in obj.name for part in ("_InnerGrip", "_GuardTop", "_TurnGuard")
        )
        if obj.type != "MESH" or not keep:
            continue
        copy = obj.copy()
        copy.data = obj.data.copy()
        copy.name = "SAMPLE_" + obj.name
        target.objects.link(copy)
        bm = bmesh.new()
        bm.from_mesh(copy.data)
        bmesh.ops.bisect_plane(
            bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces),
            plane_co=(0, 1.0, 0), plane_no=(0, 1, 0),
            clear_outer=True, clear_inner=False, dist=1e-7,
        )
        boundary = [edge for edge in bm.edges if edge.is_boundary]
        if boundary:
            bmesh.ops.holes_fill(bm, edges=boundary)
        if not bm.faces:
            bm.free()
            bpy.data.objects.remove(copy, do_unlink=True)
            continue
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(copy.data)
        bm.free()
        copy.data.materials.clear()
        copy.data.materials.append(gray)
        for polygon in copy.data.polygons:
            polygon.material_index = 0

target = collection("HR_C_INTEGRATED_SINGLE_FLIGHT")
# Walking side is y < 0.90. All body thickness lies inside the existing shaft.
# The lower re-entrant section lets fingers wrap under the 0.90 m gripping edge.
profile = [
    (.900, -.200), (.920, -.220), (.980, -.220),
    (.980, 1.100), (.920, 1.100), (.900, 1.080),
    (.900, 1.040), (.920, 1.020), (.967, 1.020),
    (.967, .900), (.910, .900), (.900, .890),
    (.900, .878), (.916, .866), (.950, .866),
    (.950, .820), (.900, .820),
]
cap_profile = [
    (.900, -.200), (.920, -.220), (.980, -.220),
    (.980, 1.100), (.920, 1.100), (.900, 1.080),
]

def section_at(x, section):
    level = (x + 1.65) * 1.9 / 3.3
    return [(x, y, level + z) for y, z in section]

def swept_object(name, rings):
    count = len(rings[0])
    vertices = [point for ring in rings for point in ring]
    faces = [tuple(reversed(range(count)))]
    for i in range(len(rings) - 1):
        for j in range(count):
            k = (j + 1) % count
            faces.append((i * count + j, i * count + k,
                          (i + 1) * count + k, (i + 1) * count + j))
    faces.append(tuple(range((len(rings) - 1) * count, len(rings) * count)))
    return object_mesh(target, name, vertices, faces)

for i in range(3):
    start = -1.65 + i * 1.10 + (.003 if i else 0)
    end = -1.65 + (i + 1) * 1.10 - (.003 if i < 2 else 0)
    rings = [section_at(start, profile), section_at(end, profile)]
    if i == 2:
        for step in range(1, 9):
            angle = -math.pi / 2 + step * math.pi / 16
            rings.append([
                (1.65 + (1.0 - y) * math.cos(angle),
                 1.0 + (1.0 - y) * math.sin(angle), 1.90 + z)
                for y, z in profile
            ])
    swept_object("HR_C_PrefabModule_" + str(i + 1), rings)

# Recessed backing keeps the two 6 mm assembly joints closed in silhouette.
back_profile = [(.970, -.200), (.980, -.200), (.980, 1.075), (.970, 1.075)]
swept_object("HR_C_JointBacking", [section_at(-1.65, back_profile), section_at(1.65, back_profile)])
swept_object("HR_C_ClosedEntranceEnd", [section_at(-1.65, cap_profile), section_at(-1.59, cap_profile)])

checks = []
for sample, variant in zip(samples, ("A", "B", "C")):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in sample.objects:
        data = obj.data
        data.calc_loop_triangles()
        bm = bmesh.new()
        bm.from_mesh(data)
        openings = sum(not edge.is_manifold for edge in bm.edges)
        volume = bm.calc_volume(signed=True)
        bm.free()
        degenerate = sum(triangle.area < 1e-10 for triangle in data.loop_triangles)
        assert openings == 0 and degenerate == 0 and volume > 0, (obj.name, openings, degenerate, volume)
        if variant == "C":
            assert min(vertex.co.y for vertex in data.vertices) >= .89999
        checks.append({"object": obj.name, "closed": True, "volume_m3": volume})
        obj.select_set(True)
    bpy.context.view_layer.objects.active = next(iter(sample.objects))
    bpy.ops.export_scene.gltf(
        filepath=str(output / ("HR_" + variant + "_gray.glb")), export_format="GLB",
        use_selection=True, export_texcoords=True, export_extras=True,
    )

# Keep the delivered Blender file focused on this comparison.
for other in list(bpy.data.collections):
    if other not in samples:
        bpy.data.collections.remove(other)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.object.select_all(action="SELECT")
settings = {
    "source_commit": "1133379c9ba4330081a153424c369c4e180023f9",
    "run_m": 3.30, "rise_m": 1.90,
    "guard_height_above_slope_m": 1.10,
    "gripping_edge_above_slope_m": .90,
    "C_body_thickness_m": .080,
    "C_walkway_intrusion_m": 0,
    "C_module_length_m": 1.10,
    "C_joint_width_m": .006,
    "C_hand_recess_depth_m": .067,
    "C_hand_recess_height_m": .120,
    "surface": "untextured shape comparison",
    "layout": "one lower flight and a return cut at the shaft centre",
    "limits": "Shape candidate. Wall-side grip, formal net width and full landing integration require a later pass.",
    "checks": checks,
}
(folder / "model_manifest.json").write_text(json.dumps(settings, indent=2) + "\n", encoding="utf8")
bpy.ops.wm.save_as_mainfile(filepath=str(folder / "model/handrail_integrated_v1.blend"))
