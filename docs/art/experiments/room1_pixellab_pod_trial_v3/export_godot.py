"""Export static, Godot-oriented Room 1 pod v3 GLBs.

Run with Blender 5.0.1:
  blender --background --factory-startup --python export_godot.py

This script never saves the editable v3 blend.  It opens that file, builds
temporary split export meshes, and exports only those meshes.  The splitting
is deliberate: each glTF primitive needs one actually-used TEXCOORD_0 map,
while the Blender review mesh has several named UV layers for different
surface materials.
"""
from pathlib import Path
import json
import struct
import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "room1_pixellab_pod_trial_v3.blend"
OUT = ROOT / "godot_export"

COMPONENTS = {
    "ONE_PIECE_COVER_head_window": {
        "lid": "UV_TRIAL_V3_LID_XY",
        "interior": "UV_TRIAL_V3_INTERIOR_XY",
        "glass": "UV_TRIAL_V3_GLASS_XY",
    },
    "Reference_led_fixed_shell": {
        "shell_side": "UV_TRIAL_V3_SHELL_SIDE",
        "shell_end": "UV_TRIAL_V3_SHELL_END",
        "interior": "UV_TRIAL_V3_INTERIOR_XY",
    },
    "Sleeping_surface": {"mattress": "UV_TRIAL_V3_MATTRESS_XY"},
    "Foot_info_display_surface": {"display": "UV_SCREEN_0_1"},
}

TEXTURES = {
    "lid": "lid.png", "shell_side": "shell_side.png", "shell_end": "shell_end.png",
    "interior": "interior.png", "mattress": "mattress.png", "glass": "glass.png",
    "display": "display.png",
}


def fail(message):
    raise RuntimeError(message)


def classify(material):
    name = material.name.lower() if material else ""
    for key in TEXTURES:
        if ("_" + key + "_") in name:
            return key
    return None


def make_godot_materials():
    materials = {}
    for key, filename in TEXTURES.items():
        path = ROOT / "textures" / filename
        if not path.is_file():
            fail(f"Missing v3 texture: {path}")
        image = bpy.data.images.load(str(path), check_existing=False)
        image.colorspace_settings.name = "sRGB"
        material = bpy.data.materials.new("GODOT_V3_" + key)
        material.use_nodes = True
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        nodes.clear()
        out = nodes.new("ShaderNodeOutputMaterial")
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Roughness"].default_value = 0.86
        bsdf.inputs["Specular IOR Level"].default_value = 0.10
        tex = nodes.new("ShaderNodeTexImage")
        tex.image = image
        # Blender's glTF exporter writes a nearest sampler for Closest images.
        tex.interpolation = "Closest"
        tex.extension = "EXTEND"
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        materials[key] = material
    return materials


def keep_one_uv(mesh, uv_name):
    if not mesh.uv_layers.get(uv_name):
        fail(f"{mesh.name} does not contain required UV map {uv_name}")
    # Removing a layer invalidates Blender's RNA wrapper for the remaining
    # items, so re-resolve it by name on every pass.
    for layer_name in [layer.name for layer in mesh.uv_layers if layer.name != uv_name]:
        mesh.uv_layers.remove(mesh.uv_layers[layer_name])
    mesh.uv_layers.active = mesh.uv_layers[uv_name]
    if len(mesh.uv_layers) != 1:
        fail(f"{mesh.name} did not reduce to exactly one export UV")


def temporary_piece(obj, key, uv_name, material, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    source_mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph,
                                                   preserve_all_data_layers=True)
    wanted = []
    for polygon in source_mesh.polygons:
        source_material = source_mesh.materials[polygon.material_index]
        if classify(source_material) == key:
            wanted.append(polygon.index)
    if not wanted:
        bpy.data.meshes.remove(source_mesh)
        return None

    bm = bmesh.new()
    bm.from_mesh(source_mesh)
    unwanted = [face for face in bm.faces if face.index not in wanted]
    bmesh.ops.delete(bm, geom=unwanted, context="FACES")
    bm.to_mesh(source_mesh)
    bm.free()
    if not source_mesh.polygons:
        bpy.data.meshes.remove(source_mesh)
        return None
    keep_one_uv(source_mesh, uv_name)
    source_mesh.materials.clear()
    source_mesh.materials.append(material)
    for polygon in source_mesh.polygons:
        polygon.material_index = 0
    piece = bpy.data.objects.new("pod_v3_" + key, source_mesh)
    bpy.context.scene.collection.objects.link(piece)
    # The source lid is parented to its animation controller.  Baking the
    # evaluated world matrix into this export-only object preserves either
    # static state without exporting the controller or an animation track.
    piece.matrix_world = evaluated.matrix_world.copy()
    return piece


def bounds(objects):
    points = []
    for obj in objects:
        for corner in obj.bound_box:
            points.append(obj.matrix_world @ Vector(corner))
    return {
        "min_m": [round(min(point[i] for point in points), 6) for i in range(3)],
        "max_m": [round(max(point[i] for point in points), 6) for i in range(3)],
    }


def glb_json(path):
    with path.open("rb") as handle:
        header = handle.read(12)
        magic, version, length = struct.unpack("<4sII", header)
        if magic != b"glTF" or version != 2:
            fail(f"{path.name} is not a glTF 2.0 GLB")
        chunk_length, chunk_kind = struct.unpack("<I4s", handle.read(8))
        if chunk_kind != b"JSON":
            fail(f"{path.name} starts without a JSON chunk")
        payload = handle.read(chunk_length).decode("utf-8").rstrip(" \t\r\n\0")
    return json.loads(payload)


def verify_glb(path, state, expected_bounds):
    data = glb_json(path)
    primitives = [primitive for mesh in data.get("meshes", []) for primitive in mesh.get("primitives", [])]
    attrs = [primitive.get("attributes", {}) for primitive in primitives]
    sampler_values = data.get("samplers", [])
    textures = data.get("textures", [])
    materials = data.get("materials", [])
    if not primitives or len(textures) != len(TEXTURES) or len(materials) != len(TEXTURES):
        fail(f"{path.name} missing expected mesh/material/texture data")
    if any(set(a) - {"POSITION", "NORMAL", "TEXCOORD_0"} for a in attrs):
        fail(f"{path.name} exported unsupported unexpected vertex attributes: {attrs}")
    if any("TEXCOORD_0" not in a for a in attrs):
        fail(f"{path.name} has a primitive without its required active UV")
    if any("TEXCOORD_1" in a for a in attrs):
        fail(f"{path.name} unexpectedly retained a secondary UV")
    if data.get("cameras") or data.get("animations") or data.get("extensions", {}).get("KHR_lights_punctual"):
        fail(f"{path.name} unexpectedly includes cameras, animations, or lights")
    if not sampler_values:
        fail(f"{path.name} has no explicit texture sampler")
    nearest = {9728, 9984, 9986}
    if any(sampler.get("magFilter") != 9728 or sampler.get("minFilter") not in nearest for sampler in sampler_values):
        fail(f"{path.name} did not export nearest texture sampling: {sampler_values}")
    return {
        "file": path.name,
        "state": state,
        "bytes": path.stat().st_size,
        "nodes": [node.get("name") for node in data.get("nodes", [])],
        "mesh_count": len(data.get("meshes", [])),
        "primitive_count": len(primitives),
        "material_count": len(materials),
        "texture_count": len(textures),
        "samplers": sampler_values,
        "all_primitives_use_only_texcoord_0": True,
        "embedded_images": all("bufferView" in image for image in data.get("images", [])),
        "bounds_m": expected_bounds,
    }


def export_state(state, frame, materials):
    bpy.context.scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    objects = []
    for object_name, mappings in COMPONENTS.items():
        obj = bpy.data.objects.get(object_name)
        if not obj or obj.type != "MESH":
            fail(f"Missing expected source mesh component: {object_name}")
        for key, uv_name in mappings.items():
            piece = temporary_piece(obj, key, uv_name, materials[key], depsgraph)
            if piece:
                objects.append(piece)
    expected_pieces = sum(len(mapping) for mapping in COMPONENTS.values())
    if len(objects) != expected_pieces:
        fail(f"{state} export expected {expected_pieces} surface pieces, got {len(objects)}")
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    result = OUT / ("pod_closed_v3.glb" if state == "closed" else "pod_open_v3.glb")
    bpy.ops.export_scene.gltf(
        filepath=str(result), export_format="GLB", use_selection=True,
        export_texcoords=True, export_normals=True, export_materials="EXPORT",
        export_image_format="AUTO", export_cameras=False, export_lights=False,
        export_animations=False, export_yup=True, export_apply=False,
        export_unused_images=False, export_unused_textures=False,
    )
    state_bounds = bounds(objects)
    for obj in objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    return verify_glb(result, state, state_bounds)


def main():
    if not SOURCE.is_file():
        fail(f"Missing v3 source blend: {SOURCE}")
    OUT.mkdir(exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    materials = make_godot_materials()
    manifest = {
        "source_blend": SOURCE.name,
        "target": "Godot 4.6 glTF/GLB import candidate",
        "units": "Blender meters; source horizontal origin retained at pod center",
        "material_conversion": "v3 review-only emission materials replaced in export copy with Principled Base Color materials; no lighting baked",
        "texture_sampling": "glTF sampler verifies magFilter 9728 (NEAREST) and minFilter 9984 (NEAREST_MIPMAP_NEAREST); Godot import should still explicitly set BaseMaterial3D texture_filter to NEAREST",
        "texture_embedding": "GLB embeds source v3 texture images",
        "uv_policy": "export-only mesh pieces are separated per required surface map and each has exactly one actual TEXCOORD_0; Blender source has additional UV layers that are intentionally not exported",
        "animation": "No animation GLB supplied. closed uses source frame 1; open uses existing source frame 60 (45-degree review terminal pose).",
        "source_unchanged": True,
        "exports": [
            export_state("closed", 1, materials),
            export_state("open", 60, materials),
        ],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
