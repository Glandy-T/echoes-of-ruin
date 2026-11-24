"""Frontal material readback under neutral lighting."""
import bpy
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parent.parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(Path(__import__('sys').argv[-1]).resolve()))
s=bpy.context.scene
for o in s.objects:
    if o.type=='ARMATURE':o.data.pose_position='REST'
    if o.type=='MESH' and not o.vertex_groups:o.hide_render=True
s.render.engine='BLENDER_WORKBENCH'
s.display.shading.color_type='TEXTURE';s.display.shading.light='FLAT'
s.render.image_settings.color_mode='RGB'
s.render.resolution_x=320;s.render.resolution_y=320;s.render.resolution_percentage=100
cam=bpy.data.cameras.new('orthographic');cam.type='ORTHO';cam.ortho_scale=.27
o=bpy.data.objects.new('review',cam);s.collection.objects.link(o);s.camera=o
tag='before' if 'skin_v1' in __import__('sys').argv[-1] else 'after'
for label,direction in [('front',(1,0,0)),('three_quarter',(1,-.7,0)),('side',(0,-1,0))]:
    c=Vector((.008,0,.90))
    o.location=c+Vector(direction).normalized()*2
    o.rotation_euler=(c-o.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(p/(tag+'_'+label+'.png'))
    bpy.ops.render.render(write_still=True)
