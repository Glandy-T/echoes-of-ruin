"""Render actual Blender animation frames for the small review GIF."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'room1_pod_reference_v4.blend'))
scene=bpy.context.scene
scene.camera=bpy.data.objects['Camera_motion_opposite_side']
scene.render.resolution_x=720
scene.render.resolution_y=500
cache=ROOT/'.preview_frames'
cache.mkdir(exist_ok=True)
for frame in range(1,109,3):
    scene.frame_set(frame)
    scene.render.filepath=str(cache/f'{frame:03d}.png')
    bpy.ops.render.render(write_still=True)
print('Motion preview frames saved')
