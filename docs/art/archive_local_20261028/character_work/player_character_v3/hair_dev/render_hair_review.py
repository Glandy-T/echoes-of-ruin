"""Create an isolated body + hair review from the current v2 base file.

Run with Blender --background --factory-startup --disable-autoexec --python.
This only writes files inside hair_dev and never changes the source blend.
"""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
BASE = WORK / "player_character_v3.blend"
sys.path.insert(0, str(WORK))
from make_hair import build_hair, _validate

bpy.ops.wm.open_mainfile(filepath=str(BASE), use_scripts=False)
scene = bpy.context.scene
bpy.context.window.scene = scene
body = next(ob for ob in bpy.data.objects if ob.type == 'MESH' and ob.vertex_groups.get('head'))
rig = next(ob for ob in bpy.data.objects if ob.type == 'ARMATURE' and ob.data.bones.get('head'))
# The current production file may contain an older preview import.  Remove it
# only from this opened-in-memory review copy, so the render evaluates exactly
# this module's geometry.
for ob in list(bpy.data.objects):
    if ob.type == 'MESH' and ob.name.startswith('Hair_'):
        bpy.data.objects.remove(ob, do_unlink=True)
for ob in list(scene.objects):
    if ob.type not in {'MESH', 'ARMATURE'}:
        bpy.data.objects.remove(ob, do_unlink=True)
mat = bpy.data.materials.new("Hair_review_dark_blue_black")
mat.diffuse_color = (0.018, 0.027, 0.042, 1)
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
bsdf.inputs['Base Color'].default_value = (0.012, 0.022, 0.040, 1)
bsdf.inputs['Roughness'].default_value = 0.84
hair = build_hair(body, rig, scene.collection, mat)

# Ground-level, orthographic visual review: front (world -Y), side (world +X), rear.
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1500
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world = bpy.data.worlds.new("HairReviewWorld")
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.20,.23,.28,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .55

def add_cam(name, loc, focus):
    data = bpy.data.cameras.new(name)
    data.type = 'ORTHO'; data.ortho_scale = 2.05
    ob = bpy.data.objects.new(name, data); scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(focus)-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob
def light(name, pos, energy):
    d=bpy.data.lights.new(name,'AREA'); d.energy=energy; d.shape='DISK'; d.size=3
    o=bpy.data.objects.new(name,d); scene.collection.objects.link(o); o.location=pos
    o.rotation_euler=(Vector((0,0,1.0))-o.location).to_track_quat('-Z','Y').to_euler()
light('Key',(-3,-4,4),650); light('Fill',(3,-2,3),330); light('Rim',(1,3,4),400)
focus=(0,0,1.1)
for name, pos in [('front',(0,-7,1.15)),('side',(7,0,1.15)),('back',(0,7,1.15))]:
    scene.camera=add_cam('Camera_'+name,pos,focus)
    scene.render.filepath=str(ROOT / ('hair_'+name+'.png'))
    bpy.ops.render.render(write_still=True)

report = _validate(hair)
for obj in hair:
    report[obj.name]['head_weighted_vertices'] = len(obj.data.vertices)
    report[obj.name]['head_weight_sum_check'] = all(abs(sum(g.weight for g in v.groups)-1.0)<1e-8 for v in obj.data.vertices)
(ROOT / 'hair_validation.json').write_text(json.dumps(report, indent=2), encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'hair_review.blend'))
print(json.dumps(report, indent=2))
