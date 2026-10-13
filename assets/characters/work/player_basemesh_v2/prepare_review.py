"""Prepare a reversible 165 cm body-only review from pistachio's CC0 base mesh.

Run with Blender 5.0 --background --factory-startup --disable-autoexec --python.
No external scripts execute; original archive and blend are never overwritten.
"""
import bpy
import bmesh
import json
import math
import hashlib
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT / 'source/original/Human Basemeshes.blend'
warning = None
try:
    bpy.ops.wm.open_mainfile(filepath=str(ORIGINAL), use_scripts=False)
except RuntimeError as exc:
    if "ShapeKey KEKey.000 has an invalid 'from' pointer" not in str(exc) or 'basemesh_female' not in bpy.data.objects:
        raise
    warning = str(exc).strip()

body = bpy.data.objects['basemesh_female']
rig = bpy.data.objects['basemesh_female_rig']
original_shape_values = {k.name: k.value for k in body.data.shape_keys.key_blocks}
for ob in list(bpy.data.objects):
    if ob not in (body, rig):
        bpy.data.objects.remove(ob, do_unlink=True)
master = bpy.data.scenes.new('01_BODY_MASTER_165cm')
master.collection.objects.link(body)
master.collection.objects.link(rig)
bpy.context.window.scene = master
for sc in list(bpy.data.scenes):
    if sc != master:
        bpy.data.scenes.remove(sc)
master.use_nodes = False
master.unit_settings.system = 'METRIC'
master.unit_settings.scale_length = 1
bpy.context.preferences.filepaths.save_version = 0
body.name = 'Body_165cm_CC0_pistachio'
rig.name = 'Body_Rig_original'
body.hide_set(False)
body.hide_viewport = False
body.hide_render = False
rig.hide_set(False)
rig.hide_viewport = False
rig.hide_render = False
rig.show_in_front = True
rig.data.pose_position = 'POSE'
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
for m in body.modifiers:
    if m.type == 'SUBSURF':
        m.show_viewport = True
        m.show_render = True
        m.levels = 1
        m.render_levels = 1
        m.name = 'OPTIONAL_Subdivision_preview_level_1'
for p in body.data.polygons:
    p.use_smooth = True

def bounds(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(dg)
    me = evaluated.to_mesh()
    points = [evaluated.matrix_world @ v.co for v in me.vertices]
    evaluated.to_mesh_clear()
    return [[min(p[i] for p in points), max(p[i] for p in points)] for i in range(3)]

bpy.context.view_layer.update()
before = bounds(body)
scale = 1.65 / (before[2][1] - before[2][0])
rig.scale *= scale
bpy.context.view_layer.update()
rig.location.z -= bounds(body)[2][0]
bpy.context.view_layer.update()
after = bounds(body)
assert abs(after[2][1] - after[2][0] - 1.65) < 0.00001, repr({'before':before, 'after':after, 'scale':list(rig.scale), 'rig_constraints':[c.type for c in rig.constraints], 'body_constraints':[c.type for c in body.constraints], 'inherit_scale':body.parent_type})

def material(name, color, emission=False):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    shader = nodes.new('ShaderNodeEmission' if emission else 'ShaderNodeBsdfPrincipled')
    if emission:
        shader.inputs['Color'].default_value = (*color, 1)
    else:
        shader.inputs['Base Color'].default_value = (*color, 1)
        shader.inputs['Roughness'].default_value = 0.88
        shader.inputs['Specular IOR Level'].default_value = 0.2
    out = nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(shader.outputs[0], out.inputs['Surface'])
    return mat

clay = material('REVIEW_neutral_clay_no_texture', (.40, .45, .46))
body.data.materials.clear()
body.data.materials.append(clay)
body['status'] = 'BODY-ONLY candidate; natural source proportions retained; not approved protagonist'
body['source'] = 'https://opengameart.org/content/human-basemeshes'
body['license'] = 'CC0; pistachio'
body['height_m'] = 1.65
body['future_parts'] = 'Hair and long garment will be separate meshes and UVs. Not built in this review.'
body['animation_status'] = 'Original weights retained. No motion or deformation validation.'

# UV/topology/weight checks on the actual source cage.
body.data.calc_loop_triangles()
bm = bmesh.new()
bm.from_mesh(body.data)
topology = {'vertices': len(bm.verts), 'edges': len(bm.edges), 'faces': len(bm.faces),
            'triangles': len(body.data.loop_triangles),
            'boundary_edges': sum(e.is_boundary for e in bm.edges),
            'nonmanifold_edges': sum(not e.is_manifold for e in bm.edges),
            'loose_vertices': sum(not v.link_edges for v in bm.verts),
            'zero_area_faces': sum(f.calc_area() < 1e-12 for f in bm.faces)}
bm.free()
deform_ids = {g.index for g in body.vertex_groups if g.name in rig.data.bones and rig.data.bones[g.name].use_deform}
unweighted = [v.index for v in body.data.vertices if sum(g.weight for g in v.groups if g.group in deform_ids) < 1e-6]
uv = body.data.uv_layers.active
uv_points = [(loop.uv.x, loop.uv.y) for loop in uv.data]
report = {'source_page': body['source'], 'source_author': 'pistachio', 'license': 'CC0',
          'source_archive_sha256': hashlib.sha256((ROOT / 'source/Human Basemeshes.zip').read_bytes()).hexdigest(),
          'source_blend_sha256': hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),
          'github_main_checked': '4c201289a5cb1f730897017d2186765f8d1ca470',
          'art_direction_version': '0.44', 'blender_version': bpy.app.version_string,
          'load_warning': warning, 'original_shape_values': original_shape_values,
          'height_m': after[2][1] - after[2][0], 'uniform_scale': scale,
          'bounds_m': after, 'topology': topology, 'uv_layer': uv.name,
          'uv_loops': len(uv_points), 'uv_range': [[min(p[i] for p in uv_points), max(p[i] for p in uv_points)] for i in range(2)],
          'rig_bones': len(rig.data.bones), 'unweighted_vertices': unweighted,
          'subdivision_preview_level': 1,
          'changes': ['isolate female mesh and its rig', 'uniform scaling and ground placement',
                      'retain one optional subdivision level matching source viewport', 'neutral clay review material'],
          'limitations': ['No anatomy edits', 'No hair or garment yet', 'No animation/deformation test',
                          'No Godot runtime test', 'Source preview likeness and protagonist approval remain separate']}
(ROOT / 'evidence/inspection.json').write_text(json.dumps(report, indent=2), encoding='utf8')

# Editable UV wire guide; this is geometry-derived vector data, not a painted image.
segments = []
for poly in body.data.polygons:
    points = [uv.data[i].uv for i in poly.loop_indices]
    coords = ' '.join(f'{p.x*1024:.3f},{(1-p.y)*1024:.3f}' for p in points)
    segments.append(f'<polygon points="{coords}" fill="none" stroke="#677a87" stroke-width="1"/>')
(ROOT / 'evidence/body_uv.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024">' + ''.join(segments) + '</svg>', encoding='utf8')

# Three copies are presentation-only; the original rigged body remains in scene 01.
dg = bpy.context.evaluated_depsgraph_get()
review_mesh = bpy.data.meshes.new_from_object(body.evaluated_get(dg))
review_mesh.transform(body.matrix_world)
review_mesh.name = 'REVIEW_ONLY_baked_display_geometry'
review_mesh.calc_loop_triangles()
report['preview_triangles'] = len(review_mesh.loop_triangles)
(ROOT / 'evidence/inspection.json').write_text(json.dumps(report, indent=2), encoding='utf8')
review = bpy.data.scenes.new('02_FRONT_SIDE_3QUARTER_REVIEW')
review.unit_settings.system = 'METRIC'
review.unit_settings.scale_length = 1
review.render.engine = 'BLENDER_EEVEE'
review.render.resolution_x = 1800
review.render.resolution_y = 1080
review.render.resolution_percentage = 100
review.render.image_settings.file_format = 'PNG'
review.render.film_transparent = False
review.view_settings.view_transform = 'AgX'
world = bpy.data.worlds.new('Review_neutral_world')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.22, .25, .28, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0.65
review.world = world
master.world = world

def add_object(name, data, loc=(0,0,0)):
    ob = bpy.data.objects.new(name, data)
    review.collection.objects.link(ob)
    ob.location = loc
    return ob

for label, x, angle in [('FRONT', -1.30, 0), ('SIDE', 0.02, math.pi/2), ('THREE QUARTER', 1.24, math.radians(-28))]:
    ob = add_object('DISPLAY_ONLY_' + label, review_mesh, (x,0,0))
    ob.rotation_euler.z = angle

text_mat = material('Review_labels', (.72,.79,.82), emission=True)
def label(text, x, z, size, align='CENTER'):
    data = bpy.data.curves.new('Label_' + text, 'FONT')
    data.body = text
    data.size = size
    data.align_x = align
    ob = add_object(data.name, data, (x,-.55,z))
    ob.rotation_euler.x = math.pi/2
    data.materials.append(text_mat)
    return ob

label('BODY BASE / 165 cm', -1.96, 1.99, .095, 'LEFT')
label('v2   |   source proportions   |   subdivision preview: level 1   |   no textures', -1.96, 1.86, .040, 'LEFT')
for text, x in [('FRONT', -1.30), ('SIDE', .02), ('THREE QUARTER', 1.24)]:
    label(text, x, -.15, .050)
label(f'pistachio / CC0  |  base: 1,158 triangles  |  preview: {report["preview_triangles"]:,}  |  original UV + rig', -1.96, -.31, .038, 'LEFT')

camera_data = bpy.data.cameras.new('Camera_orthographic_review')
camera_data.type = 'ORTHO'
camera_data.ortho_scale = 4.28
cam = add_object(camera_data.name, camera_data, (0,-8,.85))
cam.rotation_euler = (Vector((0,0,.85)) - cam.location).to_track_quat('-Z','Y').to_euler()
review.camera = cam
for name, pos, energy, size in [('Key',(-3,-4,5),480,4),('Fill',(3,-2,3),250,4),('Rim',(1,3,4),350,3)]:
    ld = bpy.data.lights.new(name,'AREA')
    ld.energy = energy
    ld.shape = 'DISK'
    ld.size = size
    lo = add_object(name,ld,pos)
    lo.rotation_euler = (Vector((0,0,.9))-lo.location).to_track_quat('-Z','Y').to_euler()

# Native file opens directly on the review, with a separate master scene for editing.
bpy.context.window.scene = review
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.shading.type = 'MATERIAL'
review.render.filepath = str(ROOT / 'evidence/body_165cm_review.png')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'body_165cm_review_v2.blend'))
bpy.ops.render.render(write_still=True, scene=review.name)
print(json.dumps({'height_m':report['height_m'], 'topology':topology,
                  'bones':report['rig_bones'], 'unweighted_vertices':len(unweighted),
                  'source_shapes':original_shape_values,
                  'output':str(ROOT / 'body_165cm_review_v2.blend')}, indent=2))
