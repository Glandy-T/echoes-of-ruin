"""Build the two authorized Room 1 floor-material review copies.

Run with Blender 5.0.1 in background mode from this directory.  Both variants
start from the same retained wall-v2 scene (not visually approved).  The script changes only the top
face assignment of Floor_continuous_no_tile_seams, appending a planar UV layer
and a new nearest-filtered matte material.  It does not alter the layout,
camera transforms, lights, wall/pod/door materials, or existing UV layers.
"""
from pathlib import Path
import json

import bpy


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "room1_wall_pixel_v2" / "room1_wall_pixel_v2.blend"
TEXTURES = ROOT / "textures"
EVIDENCE = ROOT / "evidence"
EVIDENCE.mkdir(exist_ok=True)

FLOOR_NAME = "Floor_continuous_no_tile_seams"
UV_NAME = "UV_FLOOR_PIXEL_COMPARE_V1_PLANAR"
CAMERAS = (
    ("CAM_01_full_room_overview_REVIEW", "overview"),
    ("CAM_02_low_angle_CANDIDATE", "low_angle"),
    ("CAM_03_top_plan_LAYOUT_ONLY", "top_plan"),
)
READBACKS = []


def object_snapshot(obj):
    """Capture only structural fields that this material pass must preserve."""
    if obj.type != "MESH":
        return {
            "matrix": [list(row) for row in obj.matrix_world],
            "hide_render": obj.hide_render,
            "materials": None,
            "vertices": None,
            "polygons": None,
            "uvs": None,
        }
    return {
        "matrix": [list(row) for row in obj.matrix_world],
        "hide_render": obj.hide_render,
        "materials": [material.name if material else None for material in obj.data.materials],
        "vertices": [list(vertex.co) for vertex in obj.data.vertices],
        "polygons": [list(polygon.vertices) for polygon in obj.data.polygons],
        "uvs": {
            layer.name: [list(data.uv) for data in layer.data]
            for layer in obj.data.uv_layers
        },
    }


def snapshot_scene():
    return {obj.name: object_snapshot(obj) for obj in bpy.data.objects}


def load_packed_image(filename):
    image = bpy.data.images.load(str(TEXTURES / filename), check_existing=False)
    if tuple(image.size) != (1680, 760):
        raise RuntimeError(
            "Expected 1680x760 floor texture for " + filename + "; got " + str(tuple(image.size))
        )
    image.colorspace_settings.name = "sRGB"
    image.pack()
    image.filepath = "//textures/" + filename
    return image


def make_floor_material(label, filename):
    material = bpy.data.materials.new("FLOOR_PIXEL_COMPARE_V1_" + label)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    principled = nodes.get("Principled BSDF")
    principled.inputs["Roughness"].default_value = 0.95
    principled.inputs["Specular IOR Level"].default_value = 0.08

    uv_map = nodes.new("ShaderNodeUVMap")
    uv_map.uv_map = UV_NAME
    image_texture = nodes.new("ShaderNodeTexImage")
    image_texture.image = load_packed_image(filename)
    image_texture.interpolation = "Closest"
    image_texture.extension = "EXTEND"
    links.new(uv_map.outputs["UV"], image_texture.inputs["Vector"])
    links.new(image_texture.outputs["Color"], principled.inputs["Base Color"])

    material["STATUS"] = (
        "Room 1 floor A/B material comparison. Continuous matte resilient floor; "
        "no geometry, route mesh, or height change."
    )
    material["UV_MAPPING"] = "Planar world-space x/21m, y/9.5m on the floor top face."
    material["REVIEW_VARIANT"] = label
    return material


def append_planar_top_uv_and_assign(floor, material):
    mesh = floor.data
    if mesh.uv_layers.get(UV_NAME):
        raise RuntimeError("The source floor already contains the candidate UV layer.")
    uv_layer = mesh.uv_layers.new(name=UV_NAME)
    uv_layer.active_render = True
    material_slot = len(mesh.materials)
    mesh.materials.append(material)

    top_faces = []
    world_normal_matrix = floor.matrix_world.to_3x3()
    for polygon in mesh.polygons:
        normal = (world_normal_matrix @ polygon.normal).normalized()
        if normal.z > 0.99:
            top_faces.append(polygon.index)
            polygon.material_index = material_slot
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            world_vertex = floor.matrix_world @ mesh.vertices[vertex_index].co
            uv_layer.data[loop_index].uv = (world_vertex.x / 21.0, world_vertex.y / 9.5)

    if not top_faces:
        raise RuntimeError("Floor top face selection found no upward-facing polygons.")
    return top_faces, material_slot


def assert_scope(before, floor_name, top_faces, material_slot):
    after = snapshot_scene()
    if set(before) != set(after):
        raise RuntimeError("Object inventory changed during floor material application.")

    for name, snapshot in before.items():
        current = after[name]
        if name != floor_name and current != snapshot:
            raise RuntimeError("Non-floor object changed: " + name)
        if name == floor_name:
            for key in ("matrix", "hide_render", "vertices", "polygons"):
                if current[key] != snapshot[key]:
                    raise RuntimeError("Floor structural field changed: " + key)
            for uv_name, source_uv in snapshot["uvs"].items():
                if current["uvs"].get(uv_name) != source_uv:
                    raise RuntimeError("Existing floor UV layer changed: " + uv_name)
            if UV_NAME not in current["uvs"]:
                raise RuntimeError("Candidate planar UV was not added to the floor.")

            # Only the selected upper faces may point to the appended material slot.
            floor = bpy.data.objects[floor_name]
            for polygon in floor.data.polygons:
                if polygon.index in top_faces:
                    if polygon.material_index != material_slot:
                        raise RuntimeError("A selected floor-top polygon lost its material assignment.")
                elif polygon.material_index == material_slot:
                    raise RuntimeError("A floor side or underside received the candidate material.")

    return {
        "source_object_count": len(before),
        "source_geometry_transforms_visibility_unchanged": True,
        "source_uv_layers_unchanged": True,
        "all_nonfloor_objects_unchanged": True,
        "floor_top_face_indices": top_faces,
        "new_objects": [],
    }


def render_variant(scene, label):
    for camera_name, view_name in CAMERAS:
        scene.camera = bpy.data.objects[camera_name]
        scene.render.filepath = str(EVIDENCE / (label + "_" + view_name + ".png"))
        bpy.ops.render.render(write_still=True)


def build_variant(label, filename, output_name):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    before = snapshot_scene()

    floor = bpy.data.objects.get(FLOOR_NAME)
    if floor is None or floor.type != "MESH":
        raise RuntimeError("Expected floor mesh was not found: " + FLOOR_NAME)

    material = make_floor_material(label, filename)
    top_faces, material_slot = append_planar_top_uv_and_assign(floor, material)
    readback = assert_scope(before, FLOOR_NAME, top_faces, material_slot)

    scene["STATUS"] = "Room 1 floor comparison " + label + "; awaiting visual review."
    scene["SCOPE"] = (
        "Only Floor_continuous_no_tile_seams top-face material assignment and an appended "
        "planar UV changed. Walls, pods, door, floor sides, geometry, lights and source cameras retained."
    )
    scene["FLOOR_VARIANT"] = label
    scene.camera = bpy.data.objects["CAM_01_full_room_overview_REVIEW"]
    scene.render.filepath = "//evidence/" + label + "_overview.png"
    destination = ROOT / output_name
    bpy.ops.wm.save_as_mainfile(filepath=str(destination))
    render_variant(scene, label)
    scene.camera = bpy.data.objects["CAM_01_full_room_overview_REVIEW"]
    scene.render.filepath = "//evidence/" + label + "_overview.png"
    bpy.ops.wm.save_as_mainfile(filepath=str(destination))
    readback.update({
        "variant": label,
        "source": str(SOURCE.name),
        "texture": filename,
        "output": output_name,
        "scope": (
            "Floor top-face material and appended planar UV only; structural checks do not "
            "validate final art, lighting, or Godot presentation."
        ),
    })
    READBACKS.append(readback)
    print("FLOOR_VARIANT_SAVED", destination, "top_faces", top_faces)


build_variant("A_uniform", "floor_A_albedo.png", "floor_A_uniform_v1.blend")
build_variant("B_tonal_zones", "floor_B_albedo.png", "floor_B_tonal_zones_v1.blend")
(ROOT / "structural_readback.json").write_text(
    json.dumps({"variants": READBACKS}, indent=2), encoding="utf-8"
)
