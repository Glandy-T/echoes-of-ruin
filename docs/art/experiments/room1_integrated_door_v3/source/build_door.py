"""Make the independent low-poly integrated Room 1 door and UV0 material.

The Blender objects are intentionally simple: one sliding leaf and four
stationary jamb-light surfaces. The existing Room 1 wall supplies the opening.
"""
from pathlib import Path
import bpy

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[3]
ART = ROOT / "assets/art/room1_integrated_door_v3"
ART.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

WIDTH, HEIGHT, DEPTH = 1.37, 2.30, 0.085

image = bpy.data.images.load(str(ART / "door_front.png"), check_existing=False)
image.name = "DoorFront_128x256_original_pixels"
image.filepath = str(ART / "door_front.png")
image.pack()

front_mat = bpy.data.materials.new("M_DoorFront_Pixel")
front_mat.use_nodes = True
front_mat.diffuse_color = (0.77, 0.82, 0.77, 1)
nodes = front_mat.node_tree.nodes
nodes.clear()
bsdf = nodes.new("ShaderNodeBsdfPrincipled")
out = nodes.new("ShaderNodeOutputMaterial")
front_mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
bsdf.inputs["Roughness"].default_value = 0.93
bsdf.inputs["Metallic"].default_value = 0.0
tex = nodes.new("ShaderNodeTexImage")
tex.image = image
tex.interpolation = 'Closest'
front_mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

edge_mat = bpy.data.materials.new("M_DoorEdge_MineralComposite")
edge_mat.diffuse_color = (0.62, 0.69, 0.66, 1)
edge_mat.use_nodes = True
edge_mat.node_tree.nodes.clear()
edge_bsdf = edge_mat.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
edge_out = edge_mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
edge_mat.node_tree.links.new(edge_bsdf.outputs["BSDF"], edge_out.inputs["Surface"])
edge_bsdf.inputs["Base Color"].default_value = (0.62, 0.69, 0.66, 1)
edge_bsdf.inputs["Roughness"].default_value = 0.91

groove_mat = bpy.data.materials.new("M_JambRecess_Off")
groove_mat.diffuse_color = (0.12, 0.17, 0.18, 1)

hw, hh, hd = WIDTH / 2, HEIGHT / 2, DEPTH / 2
vertices = [(-hw,-hd,-hh),(hw,-hd,-hh),(hw,-hd,hh),(-hw,-hd,hh),
            (-hw,hd,-hh),(hw,hd,-hh),(hw,hd,hh),(-hw,hd,hh)]
faces = [(0,1,2,3),(4,7,6,5),(4,5,1,0),(3,2,6,7),(4,0,3,7),(1,5,6,2)]
mesh = bpy.data.meshes.new("DoorPanel_mesh")
mesh.from_pydata(vertices, [], faces)
mesh.materials.append(front_mat)
mesh.materials.append(edge_mat)
mesh.uv_layers.new(name="UVMap")
mesh.update()
for poly in mesh.polygons:
    poly.material_index = 0 if poly.index == 0 else 1
    for loop_index in poly.loop_indices:
        vertex = mesh.vertices[mesh.loops[loop_index].vertex_index].co
        if poly.index == 0:
            uv = ((vertex.x + hw) / WIDTH, (vertex.z + hh) / HEIGHT)
        else:
            uv = ((vertex.x + hw) / WIDTH, (vertex.z + hh) / HEIGHT)
        mesh.uv_layers.active.data[loop_index].uv = uv
panel = bpy.data.objects.new("DoorPanel", mesh)
bpy.context.scene.collection.objects.link(panel)

# Four continuous surfaces in the *inner* jamb, not wall-mounted lamps.
# Godot switches their shared unshaded material during an authorized pass.
def jamb(name, x, y, z, sx, sy, sz):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x,y,z))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (sx,sy,sz)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(groove_mat)
    return obj

inner_y = -0.10
jamb("JambLight_Left", -0.690, inner_y, 0, 0.016, 0.016, 2.356)
jamb("JambLight_Right", 0.690, inner_y, 0, 0.016, 0.016, 2.356)
jamb("JambLight_Top", 0, inner_y, 1.178, 1.438, 0.016, 0.016)
jamb("JambLight_Bottom", 0, inner_y, -1.178, 1.438, 0.016, 0.016)

for obj in bpy.context.scene.objects:
    obj.select_set(obj.type == 'MESH')
bpy.context.view_layer.objects.active = panel
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / "room1_integrated_door_v3.blend"))
bpy.ops.export_scene.gltf(filepath=str(ART / "room1_integrated_door_v3.glb"),
                          export_format='GLB', use_selection=True,
                          export_apply=True)
print("DOOR_V3_EXPORTED", len([o for o in bpy.context.scene.objects if o.type == 'MESH']))
