"""Blender CLI: continuous emissive ribbon bake, never a chain of light bulbs."""
import bpy
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'assets/art/room1_revision_20261013'
OUTPUT = ROOT / 'assets/art/room1_continuous_bake_r3'
OUTPUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE / 'room1_shell_full_r1.glb'))
mapping = {}
receivers = []
for obj in list(bpy.data.objects):
    if obj.type != 'MESH':
        continue
    original_name = obj.name
    obj.name = 'Bake_Shell_' + original_name
    mapping[obj.name] = {'group': 'Shell', 'mesh': original_name}
    if original_name == 'Wall_left':
        for uv in obj.data.uv_layers[0].data:
            uv.uv.x += 4.75 / 9.1
            uv.uv.y -= 0.5
    receivers.append(obj)

placement = json.loads((SOURCE / 'pod_placement_godot.json').read_text(encoding='utf-8'))
print('PLACEMENT_FORMAT', type(placement).__name__, flush=True)
# The existing Godot trial uses this confirmed grid; preserve its transforms.
xs = [1.775, 3.525, 5.275, 7.025, 8.775, 12.225, 13.975, 15.725, 17.475, 19.225]
for index in range(20):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE / 'pod_closed_v3.glb'))
    imported = set(bpy.data.objects) - before
    parent = bpy.data.objects.new('PodPlacement_%02d' % (index + 1), None)
    bpy.context.collection.objects.link(parent)
    for obj in imported:
        if obj.parent not in imported:
            obj.parent = parent
    parent.location = (xs[index % 10], 1.85 if index < 10 else 7.65, 0.0)
    parent.rotation_euler.z = math.pi if index < 10 else 0.0
    for obj in imported:
        if obj.type != 'MESH':
            continue
        original_name = obj.name
        obj.name = 'Bake_P%02d_%s' % (index + 1, original_name)
        mapping[obj.name] = {'group': 'P%02d' % (index + 1), 'mesh': original_name}
        if original_name in ('pod_v3_glass', 'pod_v3_display'):
            obj.hide_render = True
        else:
            receivers.append(obj)

for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    nodes = mat.node_tree.nodes
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'UVMap'
    for node in list(nodes):
        if node.type == 'TEX_IMAGE':
            mat.node_tree.links.new(uv.outputs['UV'], node.inputs['Vector'])
        if node.type == 'BSDF_PRINCIPLED':
            for socket in ('Emission Color', 'Emission Strength'):
                if socket in node.inputs:
                    for link in list(node.inputs[socket].links):
                        mat.node_tree.links.remove(link)
            node.inputs['Emission Strength'].default_value = 0.0

for obj in receivers:
    obj.data.uv_layers[0].name = 'UVMap'
    obj.data.uv_layers.new(name='LightmapUV')
    obj.data.uv_layers.active_index = 1
    obj.data.uv_layers[0].active_render = True
bpy.ops.object.select_all(action='DESELECT')
for obj in receivers:
    obj.select_set(True)
bpy.context.view_layer.objects.active = receivers[0]
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0015)
bpy.ops.object.mode_set(mode='OBJECT')

emission = bpy.data.materials.new('Continuous_Ribbon_Emitter_Only')
emission.use_nodes = True
emission.node_tree.nodes.clear()
output = emission.node_tree.nodes.new('ShaderNodeOutputMaterial')
node = emission.node_tree.nodes.new('ShaderNodeEmission')
node.inputs['Color'].default_value = (0.67, 0.80, 0.86, 1.0)
node.inputs['Strength'].default_value = 20.0
emission.node_tree.links.new(node.outputs[0], output.inputs['Surface'])
bands = [
    [(0.205, 0.205, 3.02), (20.795, 0.205, 3.02), (20.795, 0.205, 3.08), (0.205, 0.205, 3.08)],
    [(20.795, 9.295, 3.02), (0.205, 9.295, 3.02), (0.205, 9.295, 3.08), (20.795, 9.295, 3.08)],
    [(0.205, 9.295, 3.02), (0.205, 0.205, 3.02), (0.205, 0.205, 3.08), (0.205, 9.295, 3.08)],
    [(20.795, 0.205, 3.02), (20.795, 9.295, 3.02), (20.795, 9.295, 3.08), (20.795, 0.205, 3.08)],
]
emitters = []
for index, vertices in enumerate(bands):
    mesh = bpy.data.meshes.new('RibbonMesh_%d' % index)
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new('ContinuousRibbon_%d' % index, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(emission)
    emitters.append(obj)

image = bpy.data.images.new('ContinuousStripIrradiance', width=2048, height=2048, alpha=False, float_buffer=True)
image.colorspace_settings.name = 'Non-Color'
for mat in {slot.material for obj in receivers for slot in obj.material_slots if slot.material}:
    bake_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    bake_node.image = image
    mat.node_tree.nodes.active = bake_node

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 3
scene.cycles.diffuse_bounces = 2
scene.world.color = (0.0, 0.0, 0.0)
scene.world.use_nodes = True
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value = 0.0
scene.render.bake.use_pass_color = False
scene.render.bake.use_pass_direct = True
scene.render.bake.use_pass_indirect = True
scene.render.bake.margin = 4
print('BAKE_BEGIN', len(receivers), 'meshes, 4 continuous emitting ribbons, 0 light objects', flush=True)
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT'}, uv_layer='LightmapUV', use_clear=True, margin=4)
image.filepath_raw = str(OUTPUT / 'strip_irradiance.exr')
image.file_format = 'OPEN_EXR'
image.save()
for obj in emitters:
    bpy.data.objects.remove(obj, do_unlink=True)
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj.hide_render = False
for mat in bpy.data.materials:
    if mat.use_nodes:
        for node in list(mat.node_tree.nodes):
            if node.type == 'TEX_IMAGE' and node.image == image:
                mat.node_tree.nodes.remove(node)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(OUTPUT / 'room1_baked_uv2_r3.glb'), export_format='GLB', export_texcoords=True, export_normals=True, export_materials='EXPORT')
(OUTPUT / 'mesh_mapping.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding='utf-8')
(OUTPUT / 'bake_manifest.json').write_text(json.dumps({'blender': bpy.app.version_string, 'receiver_meshes': len(receivers), 'emitting_ribbons': 4, 'light_objects': 0, 'ribbon_width_m': 0.06, 'ribbon_energy': 20.0, 'samples': 64, 'atlas_size': 2048, 'type': 'diffuse direct and indirect irradiance without albedo', 'scope': 'Static room and pod shadows; dynamic shadows not implemented.'}, indent=2), encoding='utf-8')
print('BAKE_COMPLETE', OUTPUT, flush=True)
