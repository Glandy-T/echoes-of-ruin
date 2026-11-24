"""Blender background review of untouched Tripo GLBs. Supply a GLB path after --."""
from pathlib import Path
import sys,json,math
import bpy
from mathutils import Vector
p=Path(sys.argv[-1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p))
s=bpy.context.scene
meshes=[o for o in s.objects if o.type=='MESH']
def bounds(objects):
    pts=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    return [Vector([f(v[i] for v in pts) for i in range(3)]) for f in (min,max)]
character=[m for m in meshes if m.name.startswith('tripo_part_')] or meshes
for m in meshes:
    if m not in character: m.hide_render=True
def pose_bounds():
    graph=bpy.context.evaluated_depsgraph_get()
    return bounds([m.evaluated_get(graph) for m in character])
lo,hi=pose_bounds()
h=hi.z-lo.z
center=(lo+hi)/2
data=[]
for o in meshes:
    o.data.calc_loop_triangles()
    data.append(dict(name=o.name,triangles=len(o.data.loop_triangles),bounds=[list(v) for v in bounds([o])],groups=len(o.vertex_groups)))
acts=[{'name':a.name,'frames':list(a.frame_range)} for a in bpy.data.actions]
(p.parent/(p.stem+'_metrics.json')).write_text(json.dumps({'parts':data,'triangles':sum(m['triangles'] for m in data if m['name'] in {o.name for o in character}),'bones':[len(o.data.bones) for o in s.objects if o.type=='ARMATURE'],'actions':acts},indent=2))
s.render.engine='BLENDER_WORKBENCH'
s.display.shading.light='STUDIO'
s.display.shading.color_type='SINGLE'
s.display.shading.single_color=(.7,.7,.7)
s.display.shading.show_cavity=True
s.display.shading.cavity_type='WORLD'
s.render.film_transparent=True
s.render.image_settings.color_mode='RGBA'
s.render.resolution_x=s.render.resolution_y=600
s.render.resolution_percentage=100
cam=bpy.data.cameras.new('review');cam.type='ORTHO';cam.ortho_scale=h*1.12
o=bpy.data.objects.new('review',cam);s.collection.objects.link(o);s.camera=o
def render(name,d):
    o.location=center+Vector(d).normalized()*h*3
    o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(p.parent/(p.stem+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
render('front',(1,0,0));render('side',(0,-1,0))
render('back',(-1,0,0));render('oblique',(1,-.65,.06))
if p.stem.startswith('parts'):
    for i,m in enumerate(meshes):
        for other in meshes: other.hide_render=other!=m
        render('piece_%02d'%i,(1,-.5,.08))
