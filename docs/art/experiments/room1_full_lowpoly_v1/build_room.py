"""Build the complete Room 1 art assembly, without importing CAD geometry.

Blender 5.0.1 --background --factory-startup --python build_room.py
No arguments: build/save only. Add -- --render to also produce review images.
"""
import json
import math
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'room1_pod_reference_v4_1' / 'room1_pod_reference_v4_1.blend'
LAYOUT = json.loads((ROOT / 'source' / 'engineering_layout.json').read_text(encoding='utf-8-sig'))
EVIDENCE = ROOT / 'evidence'
UV_DIR = ROOT / 'uv_architecture'
EVIDENCE.mkdir(exist_ok=True)
UV_DIR.mkdir(exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'METERS'
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.render.image_settings.color_mode = 'RGB'
scene.render.image_settings.color_depth = '8'
scene.render.fps = 24
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.world = bpy.data.worlds.new('REVIEW_ambient_not_final_lighting')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .25, .28, 1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .65


def collection(name):
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    return col


architecture = collection('01_ARCHITECTURE_continuous_surfaces')
cutaway = collection('02_CUTAWAY_front_left_roof_hidden_for_review')
doors = collection('03_DOOR_AND_AUTH_PLACEHOLDERS_TBD')
pods = collection('04_PODS_20_shared_v4_1_meshes')
review = collection('90_REVIEW_cameras_and_lights_not_game_assets')
guides = collection('91_SCALE_REFERENCE_hidden_not_character')


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = .9
    bsdf.inputs['Specular IOR Level'].default_value = .15
    return mat


wall_mat = material('ARCH_wall_flat_review_only', (.47, .50, .51))
floor_mat = material('ARCH_floor_flat_review_only', (.20, .235, .25))
door_mat = material('DOOR_plain_placeholder_not_approved', (.32, .37, .39))
panel_mat = material('AUTH_blank_placeholder_no_UI', (.07, .105, .115))
scale_mat = material('SCALE_reference_only', (.55, .30, .18))


def box(name, low, high, col, mat):
    a, b = Vector(low), Vector(high)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(a + b) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = b - a
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    col.objects.link(obj)
    obj.data.materials.append(mat)
    obj['purpose'] = 'Plain low-poly architectural mass; surface detail deferred to pixel textures'
    # All six planar faces are separate UV islands, packed at equal density.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for edge in bm.edges:
        edge.seam = True
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.uv_layers.active.name = 'UV_ARCH_per_object_paint'
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=.02)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(margin=.02, rotate=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    uv = obj.data.uv_layers.active
    obj['UV_note'] = 'Non-overlapping planar islands per object; production atlas and texel density TBD'
    faces = [{'face': p.index, 'uv': [list(uv.data[i].uv) for i in p.loop_indices]} for p in obj.data.polygons]
    (UV_DIR / (name + '.json')).write_text(json.dumps({'object': name, 'faces': faces}, indent=2), encoding='utf-8')
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">',
           '<rect width="1024" height="1024" fill="#202932"/>']
    for face in faces:
        points = ' '.join(f'{u*1024:.3f},{(1-v)*1024:.3f}' for u, v in face['uv'])
        svg.append(f'<polygon points="{points}" fill="#a6b6b9" stroke="#202932" stroke-width="1"/>')
    svg.append('</svg>')
    (UV_DIR / (name + '.svg')).write_text('\n'.join(svg), encoding='utf-8')
    return obj


room = LAYOUT['room']
width = room['outer_envelope_m']['width_x']
depth = room['outer_envelope_m']['depth_y']
wall = room['wall_thickness_m']
height = room['visible_clear_height_m']
opening = LAYOUT['door']['opening_rect_xy_m']
door_height = LAYOUT['door']['clear_height_m']

box('Floor_continuous_no_tile_seams', (0, 0, -.10), (width, depth, 0), architecture, floor_mat)
box('Wall_rear_left', (0, depth-wall, 0), (opening['x_min'], depth, height), architecture, wall_mat)
box('Wall_rear_right', (opening['x_max'], depth-wall, 0), (width, depth, height), architecture, wall_mat)
box('Wall_rear_door_header', (opening['x_min'], depth-wall, door_height),
    (opening['x_max'], depth, height), architecture, wall_mat)
box('Wall_right', (width-wall, wall, 0), (width, depth-wall, height), architecture, wall_mat)
box('Wall_left', (0, wall, 0), (wall, depth-wall, height), cutaway, wall_mat)
box('Wall_front', (0, 0, 0), (width, wall, height), cutaway, wall_mat)
box('Roof_hidden_for_cutaway', (0, 0, height), (width, depth, height+.15), cutaway, wall_mat)

door = box('MAIN_DOOR_PLACEHOLDER_NOT_APPROVED',
           (opening['x_min']+.015, depth-.11, .01),
           (opening['x_max']-.015, depth-.045, door_height-.01), doors, door_mat)
door['status'] = 'TBD main door art. Plain closed panel; no final frame, mechanism, texture or animation.'
door['opening_m'] = [1.4, 2.4]
panel = box('AUTH_PANEL_PLACEHOLDER_NOT_APPROVED', (11.4, 9.25, .95), (11.7, 9.30, 1.25), doors, panel_mat)
panel['status'] = 'Existing engineering position; blank functional placeholder, no final UI'

# Append only the approved-for-continuation pod candidate components.
# No imported reference GLB, CAD mesh, review cameras, lights or stage floor.
names = ['Reference_led_fixed_shell', 'ONE_PIECE_COVER_head_window',
         'Sleeping_surface', 'Foot_info_display_surface', 'Whole_lid_motion']
with bpy.data.libraries.load(str(SOURCE), link=False) as (available, imported):
    imported.objects = names
sources = {obj.name: obj for obj in imported.objects}
rig_source = sources['Whole_lid_motion']
rig_source.animation_data_clear()
rig_source.location = (0, 0, .55)
rig_source.rotation_euler = (0, 0, 0)
rig_source.scale = (1, 1, 1)

for entry in LAYOUT['pods']:
    root = bpy.data.objects.new(entry['id'] + '_POD_ROOT', None)
    pods.objects.link(root)
    root.empty_display_type = 'PLAIN_AXES'
    root.empty_display_size = .2
    root.location = (*entry['center_xy_m'], 0)
    root.rotation_euler.z = math.pi if entry['head'].startswith('front') else 0
    root['pod_id'] = entry['id']
    root['head_direction'] = entry['head']
    root['source'] = 'room1_pod_reference_v4_1; shared original mesh, material and UV data'
    copies = {}
    for name, src in sources.items():
        obj = src.copy()
        obj.animation_data_clear()
        obj.name = entry['id'] + '_' + name
        pods.objects.link(obj)
        obj.hide_render = False
        obj.hide_viewport = False
        obj.hide_set(False)
        copies[name] = obj
    for name, src in sources.items():
        obj = copies[name]
        if src.parent and src.parent.name in copies:
            obj.parent = copies[src.parent.name]
            obj.matrix_parent_inverse = src.matrix_parent_inverse.copy()
        else:
            obj.parent = root
            obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_basis = src.matrix_basis.copy()
    copies['Whole_lid_motion']['pose'] = 'Closed static assembly; opening action remains in individual v4.1 source'

for src in sources.values():
    bpy.data.objects.remove(src, do_unlink=True)

# A hidden engineering reference only, never an implied protagonist placement.
bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=.225, depth=1.68, location=(5.4, 4.25, .84))
ref = bpy.context.object
ref.name = 'REFERENCE_COLUMN_1_68m_NOT_CHARACTER'
for old in list(ref.users_collection):
    old.objects.unlink(ref)
guides.objects.link(ref)
ref.data.materials.append(scale_mat)
ref['status'] = 'Engineering scale guide only; not an approved character or character position'
guides.hide_render = True
guides.hide_viewport = True
cutaway.hide_render = True
cutaway.hide_viewport = True


def camera(name, target, offset, scale):
    data = bpy.data.cameras.new(name)
    data.type = 'ORTHO'
    data.ortho_scale = scale
    data.clip_end = 300
    obj = bpy.data.objects.new(name, data)
    review.objects.link(obj)
    obj.location = Vector(target) + Vector(offset)
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()
    obj['status'] = 'Review camera candidate; not the final game camera'
    return obj


cam_overview = camera('CAM_01_full_room_overview_REVIEW', (10.5, 4.75, 1.0), (-6, -30, 20), 25.2)
cam_low = camera('CAM_02_low_angle_CANDIDATE', (10.5, 4.75, 1.0), (-3, -30, 13), 24.0)
cam_top = camera('CAM_03_top_plan_LAYOUT_ONLY', (10.5, 4.75, 0), (0, 0, 32), 23.2)


def area(name, loc, target, power, size):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.shape = 'DISK'
    data.size = size
    obj = bpy.data.objects.new(name, data)
    review.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z', 'Y').to_euler()


area('REVIEW_soft_key', (7, 1, 13), (10.5, 4.5, 0), 3100, 10)
area('REVIEW_soft_fill', (20, 1, 8), (12, 5, 0), 2100, 8)
area('REVIEW_rear_fill', (7, 9, 10), (10, 3, 0), 1700, 7)
scene.camera = cam_overview
scene.frame_set(1)
scene['STATUS'] = 'Room 1 full low-poly v1 / awaiting user visual review / textures and main door art TBD'
scene['GEOMETRY_AUTHORITY'] = 'Latest main engineering dimensions; no FreeCAD geometric shapes copied'
scene['SOURCE_COMMIT'] = '16405cf08a06bebd84b45509d988ec83e7a68a66'
scene['REVIEW_CUTAWAY'] = 'Collection 02 contains real front wall, left wall and roof; hidden only for visibility'
scene['POD_POSE'] = 'All 20 closed. Opening sweep, side clearance and boarding not evaluated in this assembly.'
scene['UV_STATUS'] = 'Pod v4.1 UV preserved; architecture planar UV islands; final atlas/density TBD'

bpy.ops.object.select_all(action='DESELECT')
door.select_set(True)
bpy.context.view_layer.objects.active = door
for screen in bpy.data.screens:
    for area_ui in screen.areas:
        if area_ui.type == 'VIEW_3D':
            space = area_ui.spaces.active
            space.region_3d.view_perspective = 'CAMERA'
            space.overlay.show_overlays = False
            space.shading.type = 'MATERIAL'

scene.render.filepath = '//evidence/01_full_room.png'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'room1_full_lowpoly_v1.blend'))

if '--render' in sys.argv:
    for cam, filename in [(cam_overview, '01_full_room.png'),
                          (cam_low, '02_low_angle.png'),
                          (cam_top, '03_top_plan.png')]:
        scene.camera = cam
        # Plan view cuts the roof and door header so the doorway is legible.
        if cam == cam_top:
            cutaway.hide_render = False
            bpy.data.objects['Roof_hidden_for_cutaway'].hide_render = True
            bpy.data.objects['Wall_rear_door_header'].hide_render = True
        scene.render.filepath = str(EVIDENCE / filename)
        bpy.ops.render.render(write_still=True)
    cutaway.hide_render = True
    bpy.data.objects['Roof_hidden_for_cutaway'].hide_render = False
    bpy.data.objects['Wall_rear_door_header'].hide_render = False
    scene.camera = cam_overview
    scene.render.filepath = '//evidence/01_full_room.png'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'room1_full_lowpoly_v1.blend'))
print('FULL_ROOM_SAVED', ROOT)
