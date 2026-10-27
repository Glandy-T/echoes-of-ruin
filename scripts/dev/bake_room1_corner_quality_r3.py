"""Rebake the exact r2 UV layout with adequate samples, without changing art."""
import bpy
import hashlib
import json
import os
import runpy
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = ROOT / 'assets/art/room1_open_hero_uv2_r2'
OUTPUT = ROOT / 'assets/art/room1_corner_quality_r3'
HERE = ROOT / 'docs/art/experiments/room1_corner_quality_r3'
SAMPLES = 1024
OUTPUT.mkdir(parents=True, exist_ok=True)
HERE.mkdir(parents=True, exist_ok=True)
layout = json.loads((PREVIOUS / 'uv2_layout_record.json').read_text(encoding='utf8'))
for field in ('uv_degenerate_triangle_count','positive_area_overlap_count','out_of_atlas_vertex_count'):
    assert layout[field] == 0, (field,layout[field])
assert layout['uv0_preserved'] and all(layout['planar_wall_diagonals_continuous'].values())
if (OUTPUT / 'strip_irradiance_denoised.exr').exists() and os.environ.get('ROOM1_CORNER_ALLOW_OVERWRITE') != '1':
    raise RuntimeError('Refusing to overwrite completed r3; set ROOM1_CORNER_ALLOW_OVERWRITE=1 for an explicit rebuild')
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'docs/art/experiments/room1_left_wall_uv2_fix_r2/room1_open_hero_uv2_r2_packed.blend'))
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_adaptive_sampling = False
scene.cycles.max_bounces = 3
scene.cycles.diffuse_bounces = 2
scene.render.bake.use_pass_color = False
scene.render.bake.use_pass_direct = True
scene.render.bake.use_pass_indirect = True
scene.render.bake.margin = 4
receivers = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Bake_') and not o.hide_render]
assert len(receivers) == 129
assert sum(o.name.startswith('ContinuousRibbon_') for o in bpy.data.objects) == 4
def uv_hash():
    digest = hashlib.sha256()
    for obj in sorted(receivers, key=lambda o:o.name):
        digest.update(obj.name.encode())
        for layer in obj.data.uv_layers:
            for uv in layer.data:
                digest.update(('%0.10f,%0.10f;' % tuple(uv.uv)).encode())
    return digest.hexdigest()
before = uv_hash()
image = bpy.data.images.new('CornerQualityIrradiance', width=2048, height=2048, alpha=False, float_buffer=True)
image.colorspace_settings.name = 'Non-Color'
for material in {s.material for o in receivers for s in o.material_slots if s.material}:
    for node in list(material.node_tree.nodes):
        if node.type == 'TEX_IMAGE' and node.image and node.image.name == 'ContinuousStripIrradiance':
            material.node_tree.nodes.remove(node)
    node = material.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = image
    material.node_tree.nodes.active = node
bpy.ops.object.select_all(action='DESELECT')
copies = []
for original in receivers:
    copy = original.copy()
    copy.data = original.data.copy()
    copy.parent = None
    copy.matrix_world = original.matrix_world.copy()
    bpy.context.collection.objects.link(copy)
    copy.hide_render = False
    copy.select_set(True)
    original.hide_render = True
    copies.append(copy)
bpy.context.view_layer.objects.active = copies[0]
bpy.ops.object.join()
joined = bpy.context.object
joined.data.uv_layers.active_index = list(joined.data.uv_layers).index(joined.data.uv_layers['LightmapUV'])
joined.data.uv_layers['LightmapUV'].active_render = True
print('CORNER_BAKE_BEGIN', SAMPLES, 'samples, unchanged UV2/emitters; CPU', flush=True)
started = time.monotonic()
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT','INDIRECT'}, uv_layer='LightmapUV', use_clear=True, margin=4)
elapsed = time.monotonic() - started
print('CORNER_BAKE_FINISHED', elapsed, flush=True)
bpy.data.objects.remove(joined, do_unlink=True)
for original in receivers:
    original.hide_render = False
assert before == uv_hash()
image.filepath_raw = str(OUTPUT / 'strip_irradiance.exr')
image.file_format = 'OPEN_EXR'
image.save()
image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'room1_corner_quality_r3_packed.blend'), compress=True, check_existing=False)
for filename in ('room1_baked_uv2_r3.glb','mesh_mapping.json','uv2_layout_record.json'):
    shutil.copyfile(PREVIOUS / filename, OUTPUT / filename)
(OUTPUT / 'bake_manifest.json').write_text(json.dumps({
    'blender':bpy.app.version_string,'samples':SAMPLES,'adaptive_sampling':False,
    'atlas_size':2048,'bake_margin_px':4,'receiver_meshes':129,'emitting_ribbons':4,
    'light_objects':0,'bake_seconds':elapsed,'cycles_device':'CPU',
    'uv0_uv2_preserved':before == uv_hash(),'source_uv_hash':before,
    'geometry_sha256':hashlib.sha256((OUTPUT/'room1_baked_uv2_r3.glb').read_bytes()).hexdigest(),
    'geometry_source':'assets/art/room1_open_hero_uv2_r2/room1_baked_uv2_r3.glb',
    'scope':'Only sampling quality changed; exact r2 GLB and mapping copied, emitter geometry/material unchanged.'
},ensure_ascii=False,indent=2),encoding='utf8')
os.environ['ROOM1_BAKE_OUTPUT'] = str(OUTPUT.relative_to(ROOT))
runpy.run_path(str(ROOT / 'scripts/dev/denoise_room1_strip_r3.py'),run_name='__main__')
print('CORNER_QUALITY_COMPLETE', flush=True)
