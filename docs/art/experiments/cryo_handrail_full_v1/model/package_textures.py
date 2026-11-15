"""Bind native maps, pack the editable blend and refresh the portable GLB.

Run after build_full.py. Material multipliers match the independent Godot view.
This does not paint or alter the PixelLab image.
"""
from pathlib import Path
import hashlib
import json
import bpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
ASSETS = ROOT / 'assets/art/cryo_handrail_full_v1'
OLD = ROOT / 'assets/art/cryo_building_review_v1/textures'
bpy.ops.wm.open_mainfile(filepath=str(HERE / 'handrail_full_v1.blend'))
bpy.context.preferences.filepaths.save_version = 0
mapping = {
    'M01_STAIR': (OLD / 'M06-01.png', (1,1,1,1)),
    'M03_STAIR': (OLD / 'M06-03.png', (180/255,186/255,192/255,1)),
    'M01': (OLD / 'M01.png', (1,1,1,1)),
    'M09': (OLD / 'M09.png', (1,1,1,1)),
    'M05-D': (OLD / 'M05-D.png', (1,1,1,1)),
    'M10': (OLD / 'M10.png', (1,1,1,1)),
    'C_BODY': (ASSETS / 'textures/C_BODY.png', (1,1,1,1)),
    'C_SLOT': (ASSETS / 'textures/C_SLOT.png', (152/255,164/255,160/255,1)),
}
entries = []
for name, (path, multiplier) in mapping.items():
    material = bpy.data.materials.get(name)
    if material is None:
        continue
    nodes = material.node_tree.nodes
    shader = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)
    if shader is None:
        shader = nodes.new('ShaderNodeBsdfPrincipled')
        output = next((node for node in nodes if node.type == 'OUTPUT_MATERIAL'), None) or nodes.new('ShaderNodeOutputMaterial')
        material.node_tree.links.new(shader.outputs['BSDF'], output.inputs['Surface'])
    for node in list(nodes):
        if node != shader and node.type != 'OUTPUT_MATERIAL': nodes.remove(node)
    image = bpy.data.images.load(str(path), check_existing=True)
    image.pack()
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = image
    texture.interpolation = 'Closest'
    texture.extension = 'REPEAT'
    texture.location = (-450,0)
    shader.inputs['Base Color'].default_value = multiplier
    material.node_tree.links.new(texture.outputs['Color'], shader.inputs['Base Color'])
    # glTF base factor remains explicit without baking tint into the native art.
    material.diffuse_color = multiplier
    if multiplier != (1,1,1,1):
        multiply = nodes.new('ShaderNodeMixRGB')
        multiply.blend_type = 'MULTIPLY'
        multiply.inputs[0].default_value = 1
        multiply.inputs[2].default_value = multiplier
        multiply.location = (-220,0)
        material.node_tree.links.new(texture.outputs['Color'], multiply.inputs[1])
        material.node_tree.links.new(multiply.outputs[0], shader.inputs['Base Color'])
    shader.inputs['Roughness'].default_value = .88
    shader.inputs['Metallic'].default_value = 0
    shader.inputs['Specular IOR Level'].default_value = .12
    entries.append({'material':name, 'image':path.relative_to(ROOT).as_posix(),
                    'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'native_px':list(image.size),
                    'multiplier':list(multiplier), 'packed':bool(image.packed_file)})
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(ASSETS / 'cryo_handrail_full_v1.glb'),
                          export_format='GLB', use_selection=True, export_texcoords=True, export_extras=True)
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'handrail_full_v1.blend'))
(HERE.parent / 'source/packed_materials.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PACKED_NATIVE_MATERIALS', len(entries))
