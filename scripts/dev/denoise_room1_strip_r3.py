"""Blender 5 native compositor denoising of linear HDR lightmap, not pixel art."""
import bpy
import os
from pathlib import Path

root = Path(__file__).resolve().parents[2]
folder = root / os.environ.get('ROOM1_BAKE_OUTPUT', 'assets/art/room1_continuous_bake_r3')
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 16
scene.render.resolution_y = 16
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
group = bpy.data.node_groups.new('ContinuousStripDenoise', 'CompositorNodeTree')
scene.compositing_node_group = group
source = group.nodes.new('CompositorNodeImage')
source.image = bpy.data.images.load(str(folder / 'strip_irradiance.exr'))
source.image.colorspace_settings.name = 'Non-Color'
denoise = group.nodes.new('CompositorNodeDenoise')
group.links.new(source.outputs['Image'], denoise.inputs['Image'])
output = group.nodes.new('CompositorNodeOutputFile')
output.directory = str(folder)
output.file_name = 'strip_irradiance_denoised'
output.file_output_items.new('RGBA', 'Irradiance')
output.format.media_type = 'IMAGE'
output.format.file_format = 'OPEN_EXR'
output.format.color_mode = 'RGB'
output.format.color_depth = '32'
output.format.exr_codec = 'ZIP'
output.save_as_render = False
group.links.new(denoise.outputs['Image'], output.inputs[0])
bpy.ops.render.render()
target = folder / 'strip_irradiance_denoised.exr'
generated = folder / 'strip_irradiance_denoisedIrradiance.exr'
assert generated.exists(), generated
generated.replace(target)
check = bpy.data.images.load(str(target), check_existing=False)
assert tuple(check.size) == (2048, 2048), tuple(check.size)
print('DENOISE_COMPLETE', target, flush=True)
