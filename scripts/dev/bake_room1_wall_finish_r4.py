"""Fix front UV0 and continuous rear UV2, then rebake at high quality."""
import bpy
import hashlib
import json
import os
import runpy
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = ROOT / 'assets/art/room1_corner_quality_r3'
OUTPUT = ROOT / 'assets/art/room1_wall_finish_r4'
HERE = ROOT / 'docs/art/experiments/room1_wall_finish_r4'
SAMPLES = 1024
OUTPUT.mkdir(parents=True, exist_ok=True)
HERE.mkdir(parents=True, exist_ok=True)
layout = json.loads((PREVIOUS / 'uv2_layout_record.json').read_text(encoding='utf8'))
for field in ('uv_degenerate_triangle_count','positive_area_overlap_count','out_of_atlas_vertex_count'):
    assert layout[field] == 0, (field,layout[field])
assert layout['uv0_preserved'] and all(layout['planar_wall_diagonals_continuous'].values())
if (OUTPUT / 'strip_irradiance_denoised.exr').exists() and os.environ.get('ROOM1_WALL_FINISH_ALLOW_OVERWRITE') != '1':
    raise RuntimeError('Refusing to overwrite completed r4; set ROOM1_WALL_FINISH_ALLOW_OVERWRITE=1 for an explicit rebuild')
bpy.ops.wm.open_mainfile(filepath=str(ROOT / 'docs/art/experiments/room1_corner_quality_r3/room1_corner_quality_r3_packed.blend'))
front = bpy.data.objects['Bake_Shell_Wall_front']
front_uv0_changes = 0
for polygon in front.data.polygons:
    if 'MATERIAL_REVISION' not in front.data.materials[polygon.material_index].name:
        continue
    for index in polygon.loop_indices:
        uv = front.data.uv_layers['UVMap'].data[index].uv
        uv.x += .5
        uv.y += .5  # Blender V is opposite to glTF V.
        front_uv0_changes += 1
assert front_uv0_changes == 6, front_uv0_changes
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
# Reserve a continuous chart for the three coplanar rear inner faces.
for obj in receivers:
    layer = obj.data.uv_layers['LightmapUV']
    for value in layer.data:
        value.uv.x = .005+.875*value.uv.x
        value.uv.y = .12+.875*value.uv.y
    if obj.name in ('Bake_Shell_Wall_rear_left','Bake_Shell_Wall_rear_right','Bake_Shell_Wall_rear_door_header'):
        for polygon in obj.data.polygons:
            if 'MATERIAL_REVISION' not in obj.data.materials[polygon.material_index].name:
                continue
            for index in polygon.loop_indices:
                world = obj.matrix_world @ obj.data.vertices[obj.data.loops[index].vertex_index].co
                x,y = round(world.x,5),round(world.z,5)
                layer.data[index].uv = (.02+x/21.0*.61, 1-(.89+(1-y/3.4)*.09876))
new_layout = runpy.run_path(str(ROOT/'scripts/dev/room1_uv2_audit.py'))['audit_uv2_layout'](receivers)
assert new_layout['uv_degenerate_triangle_count']==0, new_layout['uv_degenerate_triangle_count']
assert new_layout['out_of_atlas_vertex_count']==0
assert new_layout['positive_area_overlap_count']==0
assert new_layout['uv_non_degenerate_triangle_count']==new_layout['geometry_non_degenerate_triangle_count']
print('WALL_FINISH_UV2_GATE_PASSED',new_layout['uv_non_degenerate_triangle_count'],flush=True)
def uv_hash():
    digest = hashlib.sha256()
    for obj in sorted(receivers, key=lambda o:o.name):
        digest.update(obj.name.encode())
        for layer in obj.data.uv_layers:
            for uv in layer.data:
                digest.update(('%0.10f,%0.10f;' % tuple(uv.uv)).encode())
    return digest.hexdigest()
before = uv_hash()
image = bpy.data.images.new('WallFinishIrradiance', width=2048, height=2048, alpha=False, float_buffer=True)
image.colorspace_settings.name = 'Non-Color'
for material in {s.material for o in receivers for s in o.material_slots if s.material}:
    for node in list(material.node_tree.nodes):
        if node.type == 'TEX_IMAGE' and node.image and node.image.name in ('ContinuousStripIrradiance','CornerQualityIrradiance'):
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
print('WALL_FINISH_BAKE_BEGIN', SAMPLES, 'samples, continuous rear UV2, original emitters; CPU', flush=True)
started = time.monotonic()
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT','INDIRECT'}, uv_layer='LightmapUV', use_clear=True, margin=4)
elapsed = time.monotonic() - started
print('WALL_FINISH_BAKE_FINISHED', elapsed, flush=True)
bpy.data.objects.remove(joined, do_unlink=True)
for original in receivers:
    original.hide_render = False
assert before == uv_hash()
image.filepath_raw = str(OUTPUT / 'strip_irradiance.exr')
image.file_format = 'OPEN_EXR'
image.save()
image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'room1_wall_finish_r4_packed.blend'), compress=True, check_existing=False)
uv_fix = runpy.run_path(str(ROOT / 'scripts/dev/fix_room1_wall_uv_r4.py'))['repair_wall_package'](PREVIOUS / 'room1_baked_uv2_r3.glb', OUTPUT / 'room1_baked_uv2_r3.glb')
shutil.copyfile(PREVIOUS / 'mesh_mapping.json', OUTPUT / 'mesh_mapping.json')
new_layout.update({'layout_version':'room1_wall_finish_r4','atlas_size_px':2048,
    'uv0_change_scope':'Front inner face +.5U/-.5V in glTF; all other UV0 preserved',
    'uv2_change_scope':'Other charts uniformly .875 scale +.005 offset in glTF; rear inner plane one continuous chart',
    'rear_chart_gltf':[.02,.89,.63,.98876],'bake_dilation_margin_px':4,
    'uv_area_degenerate_epsilon':1e-12,'overlap_area_epsilon':1e-8})
(OUTPUT/'uv2_layout_record.json').write_text(json.dumps(new_layout,ensure_ascii=False,indent=2),encoding='utf8')
(HERE/'uv2_layout_record.json').write_text(json.dumps(new_layout,ensure_ascii=False,indent=2),encoding='utf8')
(HERE/'front_uv0_fix.json').write_text(json.dumps(uv_fix,indent=2),encoding='utf8')
(OUTPUT / 'bake_manifest.json').write_text(json.dumps({
    'blender':bpy.app.version_string,'samples':SAMPLES,'adaptive_sampling':False,
    'atlas_size':2048,'bake_margin_px':4,'receiver_meshes':129,'emitting_ribbons':4,
    'light_objects':0,'bake_seconds':elapsed,'cycles_device':'CPU',
    'uv0_uv2_preserved_during_bake':before == uv_hash(),'source_uv_hash':before,
    'geometry_sha256':hashlib.sha256((OUTPUT/'room1_baked_uv2_r3.glb').read_bytes()).hexdigest(),
    'geometry_source':'assets/art/room1_corner_quality_r3/room1_baked_uv2_r3.glb',
    'uniform_strip_emission':True, 'diffuser_radiance_scale':20.0*.06/.225,
    'diffuser_scale_basis':'Existing emitter strength20 x .06m / visible diffuser .225m; original display multiplier retained',
    'front_uv0_changes':front_uv0_changes,
    'scope':'Front UV0 corrected; rear inner UV2 made continuous, other charts uniformly scaled. Positions/normals/UV0 elsewhere/mapping unchanged.1024-sample rebake; self-emitting diffuser excludes received GI.'
},ensure_ascii=False,indent=2),encoding='utf8')
os.environ['ROOM1_BAKE_OUTPUT'] = str(OUTPUT.relative_to(ROOT))
runpy.run_path(str(ROOT / 'scripts/dev/denoise_room1_strip_r3.py'),run_name='__main__')
print('WALL_FINISH_COMPLETE', flush=True)
