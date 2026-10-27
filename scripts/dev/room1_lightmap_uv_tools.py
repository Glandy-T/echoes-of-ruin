"""Room 1 r2 lightmap bake with an explicit, globally packed UV2 layout.

Unlike the legacy r3 script, a single temporary mesh projects and packs every bake
receiver into one shared atlas. A pre-bake triangle audit makes an
overlapping UV2 layout a hard failure rather than baking a corrupt lightmap.
"""
import bpy
import hashlib
import json
import math
import os
import time
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / os.environ.get('ROOM1_BAKE_OUTPUT', 'assets/art/room1_open_hero_uv2_r2')
EXPERIMENT = ROOT / 'docs/art/experiments/room1_left_wall_uv2_fix_r2'
ATLAS_SIZE = 2048
SMART_PROJECT_MARGIN = 0.006
BAKE_MARGIN_PX = 4
UV_EPSILON = 1.0e-8


def sha256_uv_layer(mesh, layer_name):
    """Stable UV-coordinate hash used to prove UV0 survived UV2 processing."""
    layer = mesh.uv_layers.get(layer_name)
    if layer is None:
        raise RuntimeError('%s has no %s' % (mesh.name, layer_name))
    digest = hashlib.sha256()
    for loop in layer.data:
        digest.update(('%0.10f,%0.10f;' % (loop.uv.x, loop.uv.y)).encode('ascii'))
    return digest.hexdigest()


def positive_polygon_area(points):
    return abs(sum(points[i][0] * points[(i + 1) % len(points)][1] -
                   points[(i + 1) % len(points)][0] * points[i][1]
                   for i in range(len(points))) * 0.5) if points else 0.0


def cross(a, b, c):
    return ((b[0] - a[0]) * (c[1] - a[1]) -
            (b[1] - a[1]) * (c[0] - a[0]))


def segment_line_intersection(start, end, clip_a, clip_b):
    # Infinite-line intersection; caller only uses it after opposite signs.
    edge_x = end[0] - start[0]
    edge_y = end[1] - start[1]
    clip_x = clip_b[0] - clip_a[0]
    clip_y = clip_b[1] - clip_a[1]
    denominator = edge_x * clip_y - edge_y * clip_x
    if abs(denominator) <= UV_EPSILON:
        return end
    t = ((clip_a[0] - start[0]) * clip_y -
         (clip_a[1] - start[1]) * clip_x) / denominator
    return (start[0] + t * edge_x, start[1] + t * edge_y)


def triangle_overlap_area(subject, clip):
    """Positive-area overlap only; a shared edge/corner is deliberately zero."""
    orientation = 1.0 if cross(clip[0], clip[1], clip[2]) >= 0.0 else -1.0
    polygon = list(subject)
    for edge_index in range(3):
        if not polygon:
            return 0.0
        clip_a = clip[edge_index]
        clip_b = clip[(edge_index + 1) % 3]
        input_polygon = polygon
        polygon = []
        previous = input_polygon[-1]
        previous_inside = orientation * cross(clip_a, clip_b, previous) >= -UV_EPSILON
        for current in input_polygon:
            current_inside = orientation * cross(clip_a, clip_b, current) >= -UV_EPSILON
            if current_inside != previous_inside:
                polygon.append(segment_line_intersection(previous, current, clip_a, clip_b))
            if current_inside:
                polygon.append(current)
            previous = current
            previous_inside = current_inside
    return positive_polygon_area(polygon)


def collect_uv_triangles(receivers):
    triangles = []
    geometry_non_degenerate = 0
    uv_non_degenerate = 0
    uv_degenerate = 0
    out_of_atlas_vertices = []
    for obj in receivers:
        layer = obj.data.uv_layers.get('LightmapUV')
        if layer is None:
            raise RuntimeError('%s missing LightmapUV' % obj.name)
        for polygon in obj.data.polygons:
            loops = list(polygon.loop_indices)
            for index in range(1, len(loops) - 1):
                vertex_indices = (loops[0], loops[index], loops[index + 1])
                points = []
                for loop_index in vertex_indices:
                    uv = layer.data[loop_index].uv
                    points.append((float(uv.x), float(uv.y)))
                    if (uv.x < -UV_EPSILON or uv.y < -UV_EPSILON or
                            uv.x > 1.0 + UV_EPSILON or uv.y > 1.0 + UV_EPSILON):
                        if len(out_of_atlas_vertices) < 100:
                            out_of_atlas_vertices.append({
                                'object': obj.name, 'polygon': polygon.index,
                                'uv': [float(uv.x), float(uv.y)],
                            })
                vertices = [obj.data.vertices[obj.data.loops[loop_index].vertex_index].co
                            for loop_index in vertex_indices]
                geometric_area = (vertices[1] - vertices[0]).cross(vertices[2] - vertices[0]).length * 0.5
                if geometric_area <= UV_EPSILON:
                    continue
                geometry_non_degenerate += 1
                area = positive_polygon_area(points)
                if area <= 1.0e-12:
                    uv_degenerate += 1
                    continue
                uv_non_degenerate += 1
                triangles.append({
                    'object': obj.name,
                    'polygon': polygon.index,
                    'points': points,
                    'bbox': (min(point[0] for point in points), min(point[1] for point in points),
                             max(point[0] for point in points), max(point[1] for point in points)),
                })
    return triangles, {
        'geometry_non_degenerate_triangle_count': geometry_non_degenerate,
        'uv_non_degenerate_triangle_count': uv_non_degenerate,
        'uv_degenerate_triangle_count': uv_degenerate,
        'out_of_atlas_vertex_count': len(out_of_atlas_vertices),
        'out_of_atlas_vertices': out_of_atlas_vertices,
    }


def audit_uv2_layout(receivers):
    """Audit all receiver triangles, not merely the previously affected wall."""
    triangles, coverage = collect_uv_triangles(receivers)
    cells = {}
    grid_size = 64
    for index, triangle in enumerate(triangles):
        min_x, min_y, max_x, max_y = triangle['bbox']
        # Clamp exactly-atlas-edge coordinates into the final valid cell.
        x0 = max(0, min(grid_size - 1, int(math.floor(min_x * grid_size))))
        y0 = max(0, min(grid_size - 1, int(math.floor(min_y * grid_size))))
        x1 = max(0, min(grid_size - 1, int(math.floor(max_x * grid_size))))
        y1 = max(0, min(grid_size - 1, int(math.floor(max_y * grid_size))))
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                cells.setdefault((x, y), []).append(index)
    pairs = set()
    for contents in cells.values():
        for left_index in range(len(contents)):
            for right_index in range(left_index + 1, len(contents)):
                a, b = contents[left_index], contents[right_index]
                pairs.add((a, b) if a < b else (b, a))
    overlaps = []
    for a, b in pairs:
        first, second = triangles[a], triangles[b]
        a0, b0, a1, b1 = first['bbox']
        c0, d0, c1, d1 = second['bbox']
        # Strict AABB overlap makes touching bounds an accepted non-overlap.
        if max(a0, c0) >= min(a1, c1) - UV_EPSILON or max(b0, d0) >= min(b1, d1) - UV_EPSILON:
            continue
        area = triangle_overlap_area(first['points'], second['points'])
        if area > UV_EPSILON:
            overlaps.append({
                'a': {'object': first['object'], 'polygon': first['polygon']},
                'b': {'object': second['object'], 'polygon': second['polygon']},
                'uv_overlap_area': area,
            })
            if len(overlaps) >= 100:
                break
    return {
        'receiver_triangle_count': len(triangles),
        'candidate_triangle_pairs': len(pairs),
        'positive_area_overlap_count': len(overlaps),
        'positive_area_overlaps': overlaps,
        **coverage,
    }


def uv2_ranges(receivers):
    """Compact before/after evidence; ranges are not used as an overlap proof."""
    per_object = {}
    all_points = []
    for obj in receivers:
        layer = obj.data.uv_layers.get('LightmapUV')
        points = [(float(loop.uv.x), float(loop.uv.y)) for loop in layer.data]
        all_points.extend(points)
        per_object[obj.name] = {
            'loops': len(points),
            'range': [min(point[0] for point in points), min(point[1] for point in points),
                      max(point[0] for point in points), max(point[1] for point in points)],
        }
    return {
        'global_range': [min(point[0] for point in all_points), min(point[1] for point in all_points),
                         max(point[0] for point in all_points), max(point[1] for point in all_points)],
        'per_object': per_object,
    }


def write_layout_record(record):
    EXPERIMENT.mkdir(parents=True, exist_ok=True)
    (EXPERIMENT / 'uv2_layout_record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / 'uv2_layout_record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')


def active_lightmap(obj):
    layer = obj.data.uv_layers.get('LightmapUV')
    if layer is None:
        raise RuntimeError('%s missing LightmapUV' % obj.name)
    obj.data.uv_layers.active_index = list(obj.data.uv_layers).index(layer)
    layer.active_render = True


def deselect_all():
    bpy.ops.object.select_all(action='DESELECT')


def globally_pack_lightmap(receivers):
    """Project continuous planes in one temporary mesh, transfer only UV2 back."""
    deselect_all()
    loop_sources = []
    copies = []
    for original in receivers:
        copy = original.copy()
        copy.data = original.data.copy()
        copy.parent = None
        copy.matrix_world = original.matrix_world.copy()
        bpy.context.collection.objects.link(copy)
        copy.select_set(True)
        attr = copy.data.attributes.new('UV2SourceLoop', 'INT', 'CORNER')
        for index in range(len(copy.data.loops)):
            attr.data[index].value = len(loop_sources)
            loop_sources.append((original,index))
        copies.append(copy)
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.join()
    joined = bpy.context.object
    active_lightmap(joined)
    bpy.ops.object.mode_set(mode='EDIT')
    try:
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=SMART_PROJECT_MARGIN,
            area_weight=0.0, correct_aspect=True, scale_to_bounds=True)
    finally:
        bpy.ops.object.mode_set(mode='OBJECT')
    attr = joined.data.attributes['UV2SourceLoop']
    layer = joined.data.uv_layers['LightmapUV']
    assert len(attr.data) == len(loop_sources)
    seen = set()
    for index, value in enumerate(attr.data):
        source_id = value.value
        assert source_id not in seen
        seen.add(source_id)
        original, original_loop = loop_sources[source_id]
        original.data.uv_layers['LightmapUV'].data[original_loop].uv = layer.data[index].uv
    bpy.data.objects.remove(joined, do_unlink=True)
    for original in receivers:
        original.select_set(True)
    bpy.context.view_layer.objects.active = receivers[0]


def shared_uv_edges(receivers):
    """Count joined physical edges whose UV endpoints are also shared."""
    total = 0
    for obj in receivers:
        mesh = obj.data
        uv = mesh.uv_layers['LightmapUV']
        edges = {}
        for face in mesh.polygons:
            loops = list(face.loop_indices)
            for i, j in zip(loops, loops[1:]+loops[:1]):
                pair = []
                for index in (i,j):
                    co = mesh.vertices[mesh.loops[index].vertex_index].co
                    pair.append(tuple(round(float(x),6) for x in (*co,*uv.data[index].uv)))
                key = tuple(sorted(pair))
                edges[key] = edges.get(key,0)+1
        total += sum(value > 1 for value in edges.values())
    return total


def bake_joined_receivers(receivers):
    """One bake target avoids repeating the atlas job for every mesh.

    Copies share the original UV coordinates and world-space triangles.
    Originals are temporarily hidden, then restored and exported separately.
    CPU with this path completed the actual 2048/64-sample bake in about 12s.
    """
    scene = bpy.context.scene
    scene.cycles.device = 'CPU'
    deselect_all()
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
    active_lightmap(joined)
    started = time.monotonic()
    try:
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT'},
                            uv_layer='LightmapUV', use_clear=True, margin=BAKE_MARGIN_PX)
    finally:
        bpy.data.objects.remove(joined, do_unlink=True)
        for original in receivers:
            original.hide_render = False
            original.select_set(True)
        bpy.context.view_layer.objects.active = receivers[0]
    return {'selected': 'CPU', 'temporary_joined_receiver': True,
            'bake_seconds': time.monotonic() - started}


def ensure_fresh_output():
    protected = ('room1_baked_uv2_r3.glb', 'strip_irradiance.exr', 'strip_irradiance_denoised.exr')
    existing = [name for name in protected if (OUTPUT / name).exists()]
    if existing and os.environ.get('ROOM1_UV2_R2_ALLOW_OVERWRITE') != '1':
        raise RuntimeError('Refusing to overwrite r2 bake outputs: %s' % ', '.join(existing))


ensure_fresh_output()
OUTPUT.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
# Existing UV2 islands are continuous; only their global placement is wrong.
LEGACY = ROOT / 'assets/art/room1_open_hero_bake_r1'
bpy.ops.import_scene.gltf(filepath=str(LEGACY / 'room1_baked_uv2_r3.glb'))
mapping = json.loads((LEGACY / 'mesh_mapping.json').read_text(encoding='utf8'))
receivers = []
for obj in bpy.data.objects:
    if obj.type != 'MESH' or obj.name not in mapping:
        continue
    if mapping[obj.name]['mesh'] in ('pod_v3_glass', 'pod_v3_display'):
        obj.hide_render = True
    else:
        receivers.append(obj)
assert len(receivers) == 129
bpy.context.view_layer.update()

for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    nodes = mat.node_tree.nodes
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = 'UVMap'
    for node in list(nodes):
        if node.type == 'TEX_IMAGE':
            mat.node_tree.links.new(uv.outputs['UV'], node.inputs['Vector'])
        if node.type == 'BSDF_PRINCIPLED':
            for socket in ('Emission Color', 'Emission Strength'):
                if socket in node.inputs:
                    for link in list(node.inputs[socket].links):
                        mat.node_tree.links.remove(link)
            node.inputs['Emission Strength'].default_value = 0.0

uv0_hashes = {}
for obj in receivers:
    obj.data.uv_layers[0].name = 'UVMap'
    uv0_hashes[obj.name] = sha256_uv_layer(obj.data, 'UVMap')
    if len(obj.data.uv_layers) != 2:
        raise RuntimeError('Expected existing UV0 and UV2: '+obj.name)
    obj.data.uv_layers[1].name = 'LightmapUV'
    active_lightmap(obj)

uv2_before_projection = uv2_ranges(receivers)
shared_edges_before = shared_uv_edges(receivers)
globally_pack_lightmap(receivers)
shared_edges_after = shared_uv_edges(receivers)
wall_diagonals = {}
for obj in receivers:
    if obj.name not in ('Bake_Shell_Wall_left', 'Bake_Shell_Wall_right'):
        continue
    layer = obj.data.uv_layers['LightmapUV']
    pairs = [set(tuple(round(float(x),8) for x in layer.data[i].uv) for i in obj.data.polygons[p].loop_indices) for p in (10,11)]
    wall_diagonals[obj.name] = len(pairs[0] & pairs[1]) == 2
uv2_after_pack = uv2_ranges(receivers)
after_uv0_hashes = {obj.name: sha256_uv_layer(obj.data, 'UVMap') for obj in receivers}
uv0_preserved = uv0_hashes == after_uv0_hashes
layout = audit_uv2_layout(receivers)
layout.update({
    'layout_version': 'room1_open_hero_uv2_r2',
    'atlas_size_px': ATLAS_SIZE,
    'projection': 'Single temporary mesh Smart Project; continuous planar charts; transfer UV2 by corner source IDs',
    'pack_operator': 'uv.smart_project in single-mesh EDIT mode, margin 0.006',
    'pack_in_one': True,
    'shared_uv_edges_before': shared_edges_before,
    'shared_uv_edges_after': shared_edges_after,
    'planar_wall_diagonals_continuous': wall_diagonals,
    'uv_area_degenerate_epsilon': 1.0e-12,
    'overlap_area_epsilon': UV_EPSILON,
    'smart_project_island_margin_fraction': 0.006,
    'margin_note': 'Smart Project margin is a packing control, not a measured final pixel gap.',
    'bake_dilation_margin_px': BAKE_MARGIN_PX,
    'uv0_preserved': uv0_preserved,
    'uv0_hashes_before': uv0_hashes,
    'uv0_hashes_after': after_uv0_hashes,
    'uv2_before_projection': uv2_before_projection,
    'uv2_after_pack': uv2_after_pack,
})
write_layout_record(layout)
valid_uv_coverage = (
    layout['geometry_non_degenerate_triangle_count'] > 0 and
    layout['uv_non_degenerate_triangle_count'] == layout['geometry_non_degenerate_triangle_count'] and
    layout['uv_degenerate_triangle_count'] == 0
)
if (not uv0_preserved or not all(wall_diagonals.values()) or not valid_uv_coverage or
        layout['positive_area_overlap_count'] or layout['out_of_atlas_vertex_count']):
    raise RuntimeError('UV2 layout gate failed; no Cycles bake was started. See %s' % (EXPERIMENT / 'uv2_layout_record.json'))

if os.environ.get('ROOM1_UV2_LAYOUT_ONLY') == '1':
    print('UV2_LAYOUT_ONLY_COMPLETE', EXPERIMENT / 'uv2_layout_record.json', flush=True)
    raise SystemExit(0)

emission = bpy.data.materials.new('Continuous_Ribbon_Emitter_Only')
emission.use_nodes = True
emission.node_tree.nodes.clear()
output = emission.node_tree.nodes.new('ShaderNodeOutputMaterial')
node = emission.node_tree.nodes.new('ShaderNodeEmission')
node.inputs['Color'].default_value = (0.67, 0.80, 0.86, 1.0)
node.inputs['Strength'].default_value = 20.0
emission.node_tree.links.new(node.outputs[0], output.inputs['Surface'])
bands = [
    [(0.205, 0.205, 3.02), (20.795, 0.205, 3.02), (20.795, 0.205, 3.08), (0.205, 0.205, 3.08)],
    [(20.795, 9.295, 3.02), (0.205, 9.295, 3.02), (0.205, 9.295, 3.08), (20.795, 9.295, 3.08)],
    [(0.205, 9.295, 3.02), (0.205, 0.205, 3.02), (0.205, 0.205, 3.08), (0.205, 9.295, 3.08)],
    [(20.795, 0.205, 3.02), (20.795, 9.295, 3.02), (20.795, 9.295, 3.08), (20.795, 0.205, 3.08)],
]
emitters = []
for index, vertices in enumerate(bands):
    mesh = bpy.data.meshes.new('RibbonMesh_%d' % index)
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new('ContinuousRibbon_%d' % index, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(emission)
    emitters.append(obj)

image = bpy.data.images.new('ContinuousStripIrradiance', width=ATLAS_SIZE, height=ATLAS_SIZE, alpha=False, float_buffer=True)
image.colorspace_settings.name = 'Non-Color'
for mat in {slot.material for obj in receivers for slot in obj.material_slots if slot.material}:
    bake_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    bake_node.image = image
    mat.node_tree.nodes.active = bake_node

# A compact editable scene lets a later artist reproduce the exact r2 layout.
EXPERIMENT.mkdir(parents=True, exist_ok=True)
try:
    bpy.ops.file.pack_all()
except RuntimeError as exc:
    print('PACK_WARNING', exc, flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(EXPERIMENT / 'room1_open_hero_uv2_r2_packed.blend'), compress=True, check_existing=False)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 3
scene.cycles.diffuse_bounces = 2
scene.world.color = (0.0, 0.0, 0.0)
scene.world.use_nodes = True
scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value = 0.0
scene.render.bake.use_pass_color = False
scene.render.bake.use_pass_direct = True
scene.render.bake.use_pass_indirect = True
scene.render.bake.margin = BAKE_MARGIN_PX
print('BAKE_BEGIN', len(receivers), 'original meshes, one disposable bake receiver, CPU', flush=True)
device_info = bake_joined_receivers(receivers)
print('BAKE_CALCULATION_COMPLETE', device_info, flush=True)
image.filepath_raw = str(OUTPUT / 'strip_irradiance.exr')
image.file_format = 'OPEN_EXR'
image.save()
image.pack()
# Save the completed editable bake with actual Cycles/device settings and all
# emitters still present. The later GLB export deliberately excludes emitters.
bpy.ops.wm.save_as_mainfile(filepath=str(EXPERIMENT / 'room1_open_hero_uv2_r2_packed.blend'), compress=True, check_existing=False)
for obj in emitters:
    bpy.data.objects.remove(obj, do_unlink=True)
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj.hide_render = False
for mat in bpy.data.materials:
    if mat.use_nodes:
        for node in list(mat.node_tree.nodes):
            if node.type == 'TEX_IMAGE' and node.image == image:
                mat.node_tree.nodes.remove(node)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(OUTPUT / 'room1_baked_uv2_r3.glb'), export_format='GLB', export_texcoords=True, export_normals=True, export_materials='EXPORT')
normal_restore = runpy.run_path(str(ROOT / 'scripts/dev/room1_restore_glb_normals.py'))['restore_normals'](LEGACY / 'room1_baked_uv2_r3.glb', OUTPUT / 'room1_baked_uv2_r3.glb')
(OUTPUT / 'mesh_mapping.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding='utf-8')
(OUTPUT / 'bake_manifest.json').write_text(json.dumps({
    'blender': bpy.app.version_string,
    'receiver_meshes': len(receivers),
    'emitting_ribbons': 4,
    'light_objects': 0,
    'open_pod': os.environ.get('ROOM1_OPEN_POD'),
    'ribbon_width_m': 0.06,
    'ribbon_energy': 20.0,
    'samples': 64,
    'atlas_size': ATLAS_SIZE,
    'uv2_layout_record': 'uv2_layout_record.json',
    'uv2_smart_project_margin_fraction': 0.006,
    'uv2_bake_margin_px': BAKE_MARGIN_PX,
    'cycles_device': device_info,
    'normal_restore': normal_restore,
    'type': 'diffuse direct and indirect irradiance without albedo',
    'scope': 'Static room and pod shadows. Runtime actor shadow is handled separately.',
}, ensure_ascii=False, indent=2), encoding='utf-8')
print('BAKE_COMPLETE', OUTPUT, flush=True)
