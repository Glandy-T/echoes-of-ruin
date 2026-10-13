"""Remove the wall authentication panel from full-room v1; preserve its geometry.

Blender 5.0.1 --background --factory-startup --python revise_room.py -- --render
The original v1 remains available, including its old panel and UV guide.
"""
from pathlib import Path
import sys
import bpy

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'room1_full_lowpoly_v1'
OUT = ROOT / 'evidence'
OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE / 'room1_full_lowpoly_v1.blend'))
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
panel = bpy.data.objects.get('AUTH_PANEL_PLACEHOLDER_NOT_APPROVED')
if panel:
    mesh = panel.data
    bpy.data.objects.remove(panel, do_unlink=True)
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
mat = bpy.data.materials.get('AUTH_blank_placeholder_no_UI')
if mat and mat.users == 0:
    bpy.data.materials.remove(mat)
bpy.data.collections['03_DOOR_AND_AUTH_PLACEHOLDERS_TBD'].name = '03_AUTO_CHIP_DOOR_PLACEHOLDER_TBD'
door = bpy.data.objects['MAIN_DOOR_PLACEHOLDER_NOT_APPROVED']
door['interaction_direction'] = 'Door-front automatic personal-chip recognition and permission check; no separate wall authentication panel'
door['interaction_status'] = 'Design direction only; detection range, feedback and runtime logic TBD'
scene['STATUS'] = 'Room 1 full low-poly v1.1 / wall authentication panel removed / automatic chip door direction'
scene['DOOR_INTERACTION'] = 'Current Room 1 direction: approach doorway, read personal chip, open on valid permission. No runtime implementation.'
scene['REVISION_SCOPE'] = 'Removed only the separate authentication panel. Room, 20 pods, door opening, door mesh, cameras and lighting inherited from v1.'

overview = bpy.data.objects['CAM_01_full_room_overview_REVIEW']
scene.camera = overview
scene.render.filepath = '//evidence/01_full_room.png'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'room1_full_lowpoly_v1_1.blend'))
if '--render' in sys.argv:
    cutaway = bpy.data.collections['02_CUTAWAY_front_left_roof_hidden_for_review']
    roof = bpy.data.objects['Roof_hidden_for_cutaway']
    header = bpy.data.objects['Wall_rear_door_header']
    for name, filename in [('CAM_01_full_room_overview_REVIEW', '01_full_room.png'),
                           ('CAM_02_low_angle_CANDIDATE', '02_low_angle.png'),
                           ('CAM_03_top_plan_LAYOUT_ONLY', '03_top_plan.png')]:
        scene.camera = bpy.data.objects[name]
        if name == 'CAM_03_top_plan_LAYOUT_ONLY':
            cutaway.hide_render = False
            roof.hide_render = True
            header.hide_render = True
        scene.render.filepath = str(OUT / filename)
        bpy.ops.render.render(write_still=True)
    cutaway.hide_render = True
    roof.hide_render = False
    header.hide_render = False
    scene.camera = overview
    scene.render.filepath = '//evidence/01_full_room.png'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'room1_full_lowpoly_v1_1.blend'))
print('SAVED_ROOM_V1_1', ROOT)
