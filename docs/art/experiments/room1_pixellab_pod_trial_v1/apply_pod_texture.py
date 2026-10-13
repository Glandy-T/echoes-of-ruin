"""Apply a PixelLab lid candidate to copies of the unchanged v4.1 pod and room.
Blender --background --python apply_pod_texture.py -- --guide-preview
Remove --guide-preview after downloading textures/lid_edit02.png.
"""
from pathlib import Path
import sys
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'evidence'
OUT.mkdir(exist_ok=True)
GUIDE = '--guide-preview' in sys.argv
IMAGE = ROOT / ('source/lid_planar_color_GUIDE.png' if GUIDE else 'textures/lid_edit02.png')
UV = 'UV_LID_PLANAR_TRIAL_NOT_FINAL'

def apply_lid(objects):
    image = bpy.data.images.load(str(IMAGE), check_existing=True)
    image.pack()
    image.filepath = '//'+str(IMAGE.relative_to(ROOT)).replace('\\','/')
    mat = bpy.data.materials.new('GUIDE_ONLY_lid' if GUIDE else 'TRIAL_PixelLab_lid_base_color')
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = .85
    bsdf.inputs['Specular IOR Level'].default_value = .18
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = image
    tex.interpolation = 'Closest'
    tex.extension = 'EXTEND'
    uv_node = mat.node_tree.nodes.new('ShaderNodeUVMap')
    uv_node.uv_map = UV
    mat.node_tree.links.new(uv_node.outputs['UV'], tex.inputs['Vector'])
    mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    seen = set()
    for obj in objects:
        if obj.type != 'MESH' or 'ONE_PIECE_COVER_head_window' not in obj.name:
            continue
        mesh = obj.data
        if mesh.name in seen:
            continue
        seen.add(mesh.name)
        layer = mesh.uv_layers.get(UV) or mesh.uv_layers.new(name=UV)
        xs = [v.co.x for v in mesh.vertices]
        ys = [v.co.y for v in mesh.vertices]
        for poly in mesh.polygons:
            for i in poly.loop_indices:
                co = mesh.vertices[mesh.loops[i].vertex_index].co
                layer.data[i].uv = ((co.x-min(xs))/(max(xs)-min(xs)),
                                    (co.y-min(ys))/(max(ys)-min(ys)))
        mesh.materials[0] = mat
        obj['texture_scope'] = 'Exterior lid only; separate head glazing and inner materials retained'
        obj['UV_trial'] = 'Extra local XY planar UV; original seam unwrap retained, side density not validated'

def render(camera, filename):
    bpy.context.scene.camera = bpy.data.objects[camera]
    bpy.context.scene.render.filepath = str(OUT/filename)
    bpy.ops.render.render(write_still=True)

bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.open_mainfile(filepath=str(ROOT.parent/'room1_pod_reference_v4_1/room1_pod_reference_v4_1.blend'))
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.frame_set(1)
if not GUIDE:
    render('Camera_oblique', '01_gray_pod.png')
apply_lid(list(bpy.data.objects))
render('Camera_oblique', 'guide_preview.png' if GUIDE else '02_textured_pod.png')
if not GUIDE:
    scene.frame_set(60)
    render('Camera_motion_opposite_side', '03_textured_open.png')
    scene.frame_set(1)
    scene.camera = bpy.data.objects['Camera_oblique']
    scene['STATUS'] = 'PixelLab lid texture candidate only; no geometry, motion or screen UI redesign'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'room1_pixellab_pod_trial_v1.blend'))
    bpy.ops.wm.open_mainfile(filepath=str(ROOT.parent/'room1_pixellab_texture_trial_v1/room1_pixellab_texture_trial_v1.blend'))
    bpy.context.preferences.filepaths.save_version = 0
    apply_lid(list(bpy.data.objects))
    render('CAM_02_low_angle_CANDIDATE', '04_textured_room_context.png')
    scene = bpy.context.scene
    scene.camera = bpy.data.objects['CAM_01_full_room_overview_REVIEW']
    scene['STATUS'] = 'Same room/architecture/pod geometry and lights; exterior lid texture trial only'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'room1_context_pod_texture_trial_v1.blend'))
