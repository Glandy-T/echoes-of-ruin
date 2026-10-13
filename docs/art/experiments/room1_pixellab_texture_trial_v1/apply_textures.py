"""Apply unchanged PixelLab PNG outputs to a review copy of Room 1 v1.1.
Blender 5.0.1 --background --factory-startup --python apply_textures.py
"""
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'room1_full_lowpoly_v1_1'
OUT = ROOT / 'evidence'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE / 'room1_full_lowpoly_v1_1.blend'))
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
TILE_METERS = 4.0  # Wall region: 126px/4m; floor: 64px/2m. Trial only.
UV_NAME = 'UV_TRIAL_WORLD_32px_per_m_NOT_FINAL'


def material(name, filename, atlas_region=None):
    image = bpy.data.images.load(str(ROOT / 'textures' / filename), check_existing=True)
    image.colorspace_settings.name = 'sRGB'
    image.pack()
    image.filepath = '//textures/' + filename
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = .9
    bsdf.inputs['Specular IOR Level'].default_value = .15
    uv = mat.node_tree.nodes.new('ShaderNodeUVMap')
    uv.uv_map = UV_NAME
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = image
    tex.interpolation = 'Closest'
    tex.extension = 'REPEAT'
    if atlas_region:
        # Pro returned four variants in one PNG. Address one interior region
        # without modifying the raw AI image or including the grid divider.
        wrap = mat.node_tree.nodes.new('ShaderNodeVectorMath')
        wrap.operation = 'FRACTION'
        scale = mat.node_tree.nodes.new('ShaderNodeVectorMath')
        scale.operation = 'MULTIPLY'
        scale.inputs[1].default_value = (126/256, 126/256, 1)
        offset = mat.node_tree.nodes.new('ShaderNodeVectorMath')
        offset.operation = 'ADD'
        offset.inputs[1].default_value = (1/256, 129/256, 0)
        mat.node_tree.links.new(uv.outputs['UV'], wrap.inputs[0])
        mat.node_tree.links.new(wrap.outputs['Vector'], scale.inputs[0])
        mat.node_tree.links.new(scale.outputs['Vector'], offset.inputs[0])
        mat.node_tree.links.new(offset.outputs['Vector'], tex.inputs['Vector'])
        mat['atlas_region'] = 'Top-left 128px variant interior: PNG x[1,127), y[1,127); 126px per 4m, 31.5 texels/m'
    else:
        mat.node_tree.links.new(uv.outputs['UV'], tex.inputs['Vector'])
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    mat['status'] = 'PixelLab web trial: raw AI base-color texture, not approved production material'
    mat['trial_density'] = ('126px / 4m = 31.5 texels/m' if atlas_region
                            else '64px / 2m = 32 texels/m') + '; repeat and edge quality require visual review'
    return mat


wall = material('TRIAL_PixelLab_PRO_wall', 'wall_attempt03_pro.png', atlas_region=True)
floor = material('TRIAL_PixelLab_PRO_FLASH_floor', 'floor_attempt02_pro_flash.png')
for obj in list(bpy.data.objects):
    if obj.type != 'MESH' or not obj.data.materials:
        continue
    old = obj.data.materials[0].name
    if old not in ('ARCH_wall_flat_review_only', 'ARCH_floor_flat_review_only'):
        continue
    layer = obj.data.uv_layers.new(name=UV_NAME)
    layer.active_render = True
    for poly in obj.data.polygons:
        normal = obj.matrix_world.to_3x3() @ poly.normal
        normal = [abs(a) for a in normal]
        dominant = normal.index(max(normal))
        axes = (0, 1) if dominant == 2 else ((0, 2) if dominant == 1 else (1, 2))
        for idx in poly.loop_indices:
            vertex = obj.matrix_world @ obj.data.vertices[obj.data.loops[idx].vertex_index].co
            meters = 2.0 if old == 'ARCH_floor_flat_review_only' else TILE_METERS
            layer.data[idx].uv = (vertex[axes[0]] / meters, vertex[axes[1]] / meters)
    obj.data.materials[0] = floor if old == 'ARCH_floor_flat_review_only' else wall
    obj['texture_trial'] = 'Additional world-scale planar UV, original paint UV retained; no geometry change'

review = bpy.data.collections['90_REVIEW_cameras_and_lights_not_game_assets']
data = bpy.data.cameras.new('CAM_TRIAL_surface_close')
data.type = 'ORTHO'
data.ortho_scale = 6.4
close = bpy.data.objects.new('CAM_TRIAL_surface_close', data)
review.objects.link(close)
target = Vector((7.7, 7.55, .75))
close.location = target + Vector((-3.5, -7, 4.8))
close.rotation_euler = (target-close.location).to_track_quat('-Z', 'Y').to_euler()
close['status'] = 'Surface inspection camera only; not final gameplay camera'
scene['STATUS'] = 'PixelLab web texture trial v1: wall and floor only; awaiting visual review'
scene['BASE_SCENE'] = 'room1_full_lowpoly_v1_1; room/pods/door positions and geometry inherited'
scene['TEXTURE_SCOPE'] = 'Raw PixelLab Pro wall and Pro Flash floor. Pods, door and head windows retain gray review materials.'
scene['PARAMETERS_TBD'] = 'Palette, UV density, lighting, pixel presentation and final textures remain provisional'
scene.camera = bpy.data.objects['CAM_01_full_room_overview_REVIEW']
scene.render.filepath = '//evidence/02_textured_full.png'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'room1_pixellab_texture_trial_v1.blend'))
for cam, filename in [('CAM_01_full_room_overview_REVIEW', '02_textured_full.png'),
                      ('CAM_02_low_angle_CANDIDATE', '03_textured_low.png'),
                      ('CAM_TRIAL_surface_close', '04_surface_close.png')]:
    scene.camera = bpy.data.objects[cam]
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)
scene.camera = bpy.data.objects['CAM_01_full_room_overview_REVIEW']
scene.render.filepath = '//evidence/02_textured_full.png'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'room1_pixellab_texture_trial_v1.blend'))
