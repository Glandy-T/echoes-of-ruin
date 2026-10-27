"""Resume the audited layout; join disposable bake copies, export originals."""
from pathlib import Path
import bpy, json, os, runpy, time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'assets/art/room1_open_hero_uv2_r2_joined_work'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(HERE / 'room1_open_hero_uv2_r2_packed.blend'))
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 64
scene.cycles.max_bounces = 3
scene.cycles.diffuse_bounces = 2
scene.world.use_nodes = True
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value = 0
scene.render.bake.use_pass_color = False
scene.render.bake.use_pass_direct = True
scene.render.bake.use_pass_indirect = True
scene.render.bake.margin = 4
image = bpy.data.images['ContinuousStripIrradiance']
originals = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Bake_')]
receivers = [o for o in originals if not o.hide_render]
assert len(receivers) == 129, len(receivers)
mapping = json.loads((ROOT / 'assets/art/room1_open_hero_bake_r1/mesh_mapping.json').read_text(encoding='utf8'))
assert set(mapping) == {o.name for o in originals}, 'Source mapping does not match editable scene'
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
joined.name = 'Temporary_Joined_Bake_Receiver'
joined.data.uv_layers.active_index = list(joined.data.uv_layers).index(joined.data.uv_layers['LightmapUV'])
for material in joined.data.materials:
    if material and material.use_nodes:
        candidates = [n for n in material.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image == image]
        assert candidates, material.name
        material.node_tree.nodes.active = candidates[0]
print('JOINED_BAKE_BEGIN', len(receivers), 'original receivers; CPU; 64 samples; 2048', flush=True)
started = time.monotonic()
bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT','INDIRECT'}, uv_layer='LightmapUV', use_clear=True, margin=4)
print('JOINED_BAKE_FINISHED_SECONDS', time.monotonic() - started, flush=True)
image.filepath_raw = str(OUT / 'strip_irradiance.exr')
image.file_format = 'OPEN_EXR'
image.save()
bpy.data.objects.remove(joined, do_unlink=True)
for original in receivers:
    original.hide_render = False
image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(HERE / 'room1_open_hero_uv2_r2_joined_packed.blend'), compress=True, check_existing=False)
for obj in list(bpy.data.objects):
    if obj.name.startswith('ContinuousRibbon_'):
        bpy.data.objects.remove(obj, do_unlink=True)
    elif obj.type == 'MESH':
        obj.hide_render = False
for material in bpy.data.materials:
    if material.use_nodes:
        for node in list(material.node_tree.nodes):
            if node.type == 'TEX_IMAGE' and node.image == image:
                material.node_tree.nodes.remove(node)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(OUT/'room1_baked_uv2_r3.glb'), export_format='GLB', export_texcoords=True, export_normals=True, export_materials='EXPORT')
(OUT/'mesh_mapping.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2),encoding='utf8')
(OUT/'bake_manifest.json').write_text(json.dumps({
    'blender':bpy.app.version_string, 'receiver_meshes':129, 'emitting_ribbons':4,
    'light_objects':0, 'open_pod':'P12', 'ribbon_width_m':.06, 'ribbon_energy':20,
    'samples':64, 'atlas_size':2048, 'uv2_layout_record':'uv2_layout_record.json',
    'uv2_pack_margin_per_side_px_nominal':6.144, 'uv2_bake_margin_px':4,
    'cycles_device':'CPU', 'bake_seconds':time.monotonic()-started,
    'bake_optimization':'One disposable joined receiver; original independent objects exported unchanged',
    'type':'diffuse direct and indirect irradiance without albedo'
},indent=2),encoding='utf8')
os.environ['ROOM1_BAKE_OUTPUT'] = str(OUT.relative_to(ROOT))
runpy.run_path(str(ROOT/'scripts/dev/denoise_room1_strip_r3.py'),run_name='__main__')
print('JOINED_PIPELINE_COMPLETE', flush=True)
