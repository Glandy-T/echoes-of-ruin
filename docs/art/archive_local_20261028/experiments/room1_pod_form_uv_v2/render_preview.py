"""Blender: render sampled animation PNGs to ignored local cache."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CACHE=ROOT/'.preview_frames'
CACHE.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'room1_pod_form_uv_v2.blend'))
scene=bpy.context.scene
scene.render.resolution_x=720
scene.render.resolution_y=500
scene.render.resolution_percentage=100
for frame in range(1,109,3):
    scene.frame_set(frame)
    scene.render.filepath=str(CACHE/f'{frame:03d}.png')
    bpy.ops.render.render(write_still=True)
print('PREVIEW_PNGS_READY',CACHE)
