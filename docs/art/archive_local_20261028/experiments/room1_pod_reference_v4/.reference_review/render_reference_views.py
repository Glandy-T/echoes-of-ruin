"""Read-only visual study of the user-supplied GLB.

This script imports the reference only into a temporary Blender session and
renders neutral inspection images. It never saves, exports, or alters the
source mesh.  The resulting PNGs are visual evidence, not deliverable assets.
"""
import bpy
from mathutils import Vector

REFERENCE = r"C:\\Users\\Glandy\\Downloads\\scifi_-_cryogenic_sleep.glb"
OUTPUT = r"G:\\卒業制作\\echoes-of-ruin\\docs\\art\\experiments\\room1_pod_reference_v4\\.reference_review"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=REFERENCE)

# Only inspect the outer shell and the transparent cover.  The source's person,
# bed and its default presentation cube are excluded to make the silhouette legible.
keep = {"base_branca_m_brancos_0", "tampa_m_acrilico_0"}
for obj in list(bpy.context.scene.objects):
    if obj.type == "MESH" and obj.name not in keep:
        bpy.data.objects.remove(obj, do_unlink=True)

def mat(name, rgba, metallic=0.0, roughness=0.65):
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = rgba
    p.inputs["Roughness"].default_value = roughness
    p.inputs["Metallic"].default_value = metallic
    return m

body_mat = mat("Inspection grey shell", (0.34, 0.37, 0.39, 1), 0.0, 0.72)
lid_mat = mat("Inspection pale cover", (0.16, 0.20, 0.23, 1), 0.0, 0.58)
bpy.data.objects["base_branca_m_brancos_0"].data.materials.clear()
bpy.data.objects["base_branca_m_brancos_0"].data.materials.append(body_mat)
bpy.data.objects["tampa_m_acrilico_0"].data.materials.clear()
bpy.data.objects["tampa_m_acrilico_0"].data.materials.append(lid_mat)

# Geometric bounds from the imported meshes.
points = []
for obj in [bpy.data.objects[n] for n in keep]:
    points.extend(obj.matrix_world @ v.co for v in obj.data.vertices)
mn = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
mx = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
center = (mn + mx) / 2
span = mx - mn

world = bpy.context.scene.world or bpy.data.worlds.new("InspectionWorld")
bpy.context.scene.world = world
world.color = (0.035, 0.035, 0.04)

def area(name, loc, power, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = power
    data.shape = "DISK"
    data.size = size
    o = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(o)
    o.location = loc
    return o

def point_at(o, target):
    o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z', 'Y').to_euler()

key = area("Key", center + Vector((span.x * 1.8, -span.y * .8, span.z * 4)), 460, span.y * 1.5)
fill = area("Fill", center + Vector((-span.x * 2.2, span.y * .9, span.z * 1.8)), 210, span.y)
rim = area("Rim", center + Vector((0, span.y * 1.9, span.z * 2.1)), 300, span.x * 2)
for light in (key, fill, rim):
    point_at(light, center)

cam_data = bpy.data.cameras.new("InspectionCamera")
cam = bpy.data.objects.new("InspectionCamera", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.data.type = 'ORTHO'

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.studio_light = 'paint.sl'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'WORLD'
scene.display.shading.cavity_ridge_factor = 1.4
scene.display.shading.cavity_valley_factor = 1.2
scene.render.resolution_x = 1400
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.look = 'AgX - Medium High Contrast'

def render(name, location, ortho):
    cam.location = location
    cam.data.ortho_scale = ortho
    point_at(cam, center + Vector((0, 0, span.z * .04)))
    scene.render.filepath = OUTPUT + "\\" + name
    bpy.ops.render.render(write_still=True)

# Side has length horizontal and height vertical; end verifies width/height;
# oblique makes the continuous upper frame visible.
render("01_side_silhouette.png", center + Vector((span.x * 5.0, 0, span.z * .35)), span.y * 1.18)
render("02_end_profile.png", center + Vector((0, -span.y * 3.6, span.z * .18)), span.x * 1.48)
render("03_oblique_shell_and_cover.png", center + Vector((span.x * 3.5, -span.y * 3.0, span.z * 2.1)), span.y * 1.26)

print("Rendered neutral reference inspection views; source GLB was not saved or exported.")
