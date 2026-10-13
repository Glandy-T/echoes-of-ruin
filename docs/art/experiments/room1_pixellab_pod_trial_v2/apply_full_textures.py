"""Integrate the v2 PixelLab pod texture set without changing source geometry.

Run from this directory with Blender 5:
  blender --background --python apply_full_textures.py -- --render

Without --render the script only writes the packed review blend.  --guide is an
explicit preview mode that reads matching files from guides/; final mode never
substitutes a guide texture for a missing final PNG.
"""
from pathlib import Path
import sys
import bpy

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "room1_pod_reference_v4_1" / "room1_pod_reference_v4_1.blend"
TEXTURES = ROOT / ("guides" if "--guide" in sys.argv else "textures")
OUT = ROOT / "evidence"
RENDER = "--render" in sys.argv
GUIDE = "--guide" in sys.argv
TRIAL = "UV_TRIAL_V2_"

FILES = {
    "lid": ("lid.png", 128, 256),
    "shell_side": ("shell_side.png", 256, 80),
    "shell_end": ("shell_end.png", 128, 80),
    "interior": ("interior.png", 128, 256),
    "mattress": ("mattress.png", 128, 256),
    "glass": ("glass.png", 128, 256),
    "display": ("display.png", 128, 48),
}


def fail(message):
    raise RuntimeError(message)


def load_images():
    images = {}
    for key, (filename, width, height) in FILES.items():
        path = TEXTURES / filename
        if not path.is_file():
            mode = "guide" if GUIDE else "final"
            fail(f"Missing {mode} texture: {path}")
        image = bpy.data.images.load(str(path), check_existing=False)
        if tuple(image.size) != (width, height):
            fail(f"Unexpected size for {path.name}: {image.size[:]} (expected {width}x{height})")
        image.colorspace_settings.name = "sRGB"
        image.pack()
        image.filepath = "//" + str(path.relative_to(ROOT)).replace("\\", "/")
        images[key] = image
    return images


def new_uv(mesh, suffix):
    name = TRIAL + suffix
    return mesh.uv_layers.get(name) or mesh.uv_layers.new(name=name)


def assign_uv(mesh, layer, mapper):
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            layer.data[loop_index].uv = mapper(vertex)


def planar_xy(vertex):
    # Same physical extents for lid, interior, mattress and head glazing.
    return ((vertex.x + 0.575) / 1.15, (vertex.y + 1.15) / 2.30)


def shell_side(vertex):
    return ((vertex.y + 1.15) / 2.30, vertex.z / 0.71875)


def shell_end(vertex):
    return ((vertex.x + 0.575) / 1.15, vertex.z / 0.71875)


def build_material(name, image, uv_name, preview=False):
    material = bpy.data.materials.new(name=name)
    # Both variants remain selectable in the editable .blend after the active
    # slots are switched to the review preview variant.
    material.use_fake_user = True
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Closest"
    texture.extension = "EXTEND"
    uv = nodes.new("ShaderNodeUVMap")
    uv.uv_map = uv_name
    links.new(uv.outputs["UV"], texture.inputs["Vector"])

    if not preview:
        shader = nodes.new("ShaderNodeBsdfPrincipled")
        shader.inputs["Roughness"].default_value = 0.86
        shader.inputs["Specular IOR Level"].default_value = 0.10
        links.new(texture.outputs["Color"], shader.inputs["Base Color"])
        links.new(shader.outputs["BSDF"], output.inputs["Surface"])
        return material

    # Review-only controlled 3-tone shading.  It is an emission shader, not a
    # Godot implementation and does not bake or modify the source lighting.
    normal = nodes.new("ShaderNodeNewGeometry")
    dot = nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = (0.35, -0.45, 0.82)
    threshold_mid = nodes.new("ShaderNodeMath")
    threshold_mid.operation = "GREATER_THAN"
    threshold_mid.inputs[1].default_value = -0.15
    threshold_high = nodes.new("ShaderNodeMath")
    threshold_high.operation = "GREATER_THAN"
    threshold_high.inputs[1].default_value = 0.45
    mid_weight = nodes.new("ShaderNodeMath")
    mid_weight.operation = "MULTIPLY"
    mid_weight.inputs[1].default_value = 0.21
    high_weight = nodes.new("ShaderNodeMath")
    high_weight.operation = "MULTIPLY"
    high_weight.inputs[1].default_value = 0.22
    add_mid = nodes.new("ShaderNodeMath")
    add_mid.operation = "ADD"
    add_mid.inputs[0].default_value = 0.57
    add_high = nodes.new("ShaderNodeMath")
    add_high.operation = "ADD"
    multiply = nodes.new("ShaderNodeMixRGB")
    multiply.blend_type = "MULTIPLY"
    multiply.inputs[0].default_value = 1.0
    emission = nodes.new("ShaderNodeEmission")
    links.new(normal.outputs["Normal"], dot.inputs[0])
    links.new(dot.outputs["Value"], threshold_mid.inputs[0])
    links.new(dot.outputs["Value"], threshold_high.inputs[0])
    links.new(threshold_mid.outputs["Value"], mid_weight.inputs[0])
    links.new(threshold_high.outputs["Value"], high_weight.inputs[0])
    links.new(mid_weight.outputs["Value"], add_mid.inputs[1])
    links.new(add_mid.outputs["Value"], add_high.inputs[0])
    links.new(high_weight.outputs["Value"], add_high.inputs[1])
    links.new(texture.outputs["Color"], multiply.inputs[1])
    links.new(add_high.outputs["Value"], multiply.inputs[2])
    links.new(multiply.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    material["review_only"] = "Emission three-tone normal-direction shading; not a Godot shader or bake."
    return material


def add_slots(mesh, materials):
    """Append trial slots while leaving every source slot and its index intact."""
    indices = {}
    for key, material in materials.items():
        mesh.materials.append(material)
        indices[key] = len(mesh.materials) - 1
    return indices


def slot_name(mesh, polygon):
    if polygon.material_index >= len(mesh.materials):
        return ""
    material = mesh.materials[polygon.material_index]
    return material.name if material else ""


def apply_cover(obj, image_materials):
    mesh = obj.data
    uv_lid = new_uv(mesh, "LID_XY")
    uv_interior = new_uv(mesh, "INTERIOR_XY")
    uv_glass = new_uv(mesh, "GLASS_XY")
    for layer in (uv_lid, uv_interior, uv_glass):
        assign_uv(mesh, layer, planar_xy)
    slots = add_slots(mesh, {
        "lid": image_materials["lid"],
        "interior": image_materials["interior"],
        "glass": image_materials["glass"],
    })
    for polygon in mesh.polygons:
        name = slot_name(mesh, polygon).lower()
        # Evaluate original names before this script has appended any trial slots.
        if "head_window" in name:
            polygon.material_index = slots["glass"]
        elif "interior" in name:
            polygon.material_index = slots["interior"]
        else:
            polygon.material_index = slots["lid"]


def apply_shell(obj, image_materials):
    mesh = obj.data
    uv_side = new_uv(mesh, "SHELL_SIDE")
    uv_end = new_uv(mesh, "SHELL_END")
    uv_interior = new_uv(mesh, "INTERIOR_XY")
    assign_uv(mesh, uv_side, shell_side)
    # Keep printed identifiers readable from either boarding side. Reversing
    # a geometric side must not leave UNIT 01 as a mirrored bitmap.
    for polygon in mesh.polygons:
        if polygon.normal.x < 0 and abs(polygon.normal.x) > max(abs(polygon.normal.y), abs(polygon.normal.z)):
            for loop_index in polygon.loop_indices:
                uv_side.data[loop_index].uv.x = 1.0 - uv_side.data[loop_index].uv.x
    assign_uv(mesh, uv_end, shell_end)
    assign_uv(mesh, uv_interior, planar_xy)
    slots = add_slots(mesh, {
        "side": image_materials["shell_side"],
        "end": image_materials["shell_end"],
        "interior": image_materials["interior"],
    })
    for polygon in mesh.polygons:
        name = slot_name(mesh, polygon).lower()
        if "interior" in name:
            polygon.material_index = slots["interior"]
            continue
        normal = polygon.normal
        # Side faces use the long side map; end caps use the narrow end map.
        # Horizontal exterior faces are deliberately assigned by their nearest
        # Y end rather than a random planar grid, because no dedicated top map
        # was generated for this trial.
        if abs(normal.x) > max(abs(normal.y), abs(normal.z)):
            polygon.material_index = slots["side"]
        elif abs(normal.y) > max(abs(normal.x), abs(normal.z)):
            polygon.material_index = slots["end"]
        elif abs(polygon.center.y) > 0.78:
            polygon.material_index = slots["end"]
        else:
            polygon.material_index = slots["side"]


def apply_mattress(obj, image_material):
    mesh = obj.data
    uv = new_uv(mesh, "MATTRESS_XY")
    assign_uv(mesh, uv, planar_xy)
    slots = add_slots(mesh, {"mattress": image_material})
    for polygon in mesh.polygons:
        polygon.material_index = slots["mattress"]


def apply_display(obj, image_material):
    mesh = obj.data
    # The source 0-1 display UV is deliberately retained and used directly.
    uv_name = "UV_SCREEN_0_1"
    if not mesh.uv_layers.get(uv_name):
        fail(f"{obj.name} is missing its source display UV {uv_name}")
    slots = add_slots(mesh, {"display": image_material})
    for polygon in mesh.polygons:
        polygon.material_index = slots["display"]


def make_material_sets(images):
    standard = {}
    preview = {}
    uv_names = {
        "lid": TRIAL + "LID_XY",
        "shell_side": TRIAL + "SHELL_SIDE",
        "shell_end": TRIAL + "SHELL_END",
        "interior": TRIAL + "INTERIOR_XY",
        "mattress": TRIAL + "MATTRESS_XY",
        "glass": TRIAL + "GLASS_XY",
        "display": "UV_SCREEN_0_1",
    }
    prefix = "GUIDE_ONLY_" if GUIDE else "TRIAL_V2_"
    for key, image in images.items():
        standard[key] = build_material(prefix + key + "_Principled", image, uv_names[key])
        preview[key] = build_material(prefix + key + "_PixelPreview", image, uv_names[key], preview=True)
    return standard, preview


def set_mesh_variant(objects, old_to_new):
    for obj in objects:
        if obj.type != "MESH":
            continue
        for index, material in enumerate(obj.data.materials):
            if material in old_to_new:
                obj.data.materials[index] = old_to_new[material]


def render(camera_name, filename, frame=1):
    camera = bpy.data.objects.get(camera_name)
    if not camera:
        fail(f"Source camera missing: {camera_name}")
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.camera = camera
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    OUT.mkdir(exist_ok=True)
    scene = bpy.context.scene
    scene.frame_set(1)

    # Baseline is rendered from untouched source materials and lights.
    if RENDER:
        render("Camera_oblique", "01_gray_baseline.png")

    images = load_images()
    standard, preview = make_material_sets(images)
    objects = list(bpy.data.objects)
    cover = bpy.data.objects.get("ONE_PIECE_COVER_head_window")
    shell = bpy.data.objects.get("Reference_led_fixed_shell")
    mattress = bpy.data.objects.get("Sleeping_surface")
    display = bpy.data.objects.get("Foot_info_display_surface")
    if not all((cover, shell, mattress, display)):
        fail("One or more named v4.1 pod mesh components are missing")

    apply_cover(cover, standard)
    apply_shell(shell, standard)
    apply_mattress(mattress, standard["mattress"])
    apply_display(display, standard["display"])

    # The second material set is created after mapping so source material slots
    # are retained and only trial slots are replaced for preview renders.
    old_to_preview = {
        standard[key]: preview[key] for key in standard
    }

    if RENDER:
        render("Camera_oblique", "02_full_texture_same_lighting.png")
    set_mesh_variant((cover, shell, mattress, display), old_to_preview)
    if RENDER:
        render("Camera_oblique", "03_pixel_shading_same_camera.png")
        render("Camera_motion_opposite_side", "04_open_pixel_shading.png", frame=60)
        render("Camera_display_close", "05_display_close.png")
        scene.render.resolution_x = 720
        scene.render.resolution_y = 500
        scene.render.resolution_percentage = 100
        render("Camera_oblique", "06_pixel_native.png")

    # Preserve the project's requested review state rather than leaving the
    # save file on the display close-up, open-pod frame, or native-size check.
    scene.render.resolution_x = 1440
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.frame_set(1)
    scene.camera = bpy.data.objects["Camera_oblique"]
    scene["texture_trial_scope"] = "v2 full-pod texture integration only; source geometry, transforms, motion, source UVs, cameras and lights unchanged"
    scene["pixel_preview_scope"] = "Review-only emission three-tone shader. It is not a verified Godot shader or lighting bake."
    scene["shell_mapping_caveat"] = "No generated top shell map: horizontal exterior faces use a deterministic side/end choice based on Y position."
    destination = ROOT / "room1_pixellab_pod_trial_v2.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(destination))


if __name__ == "__main__":
    main()
