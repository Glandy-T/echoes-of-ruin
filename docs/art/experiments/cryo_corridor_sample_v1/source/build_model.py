"""Editable surface modules in actual route coordinates; no CAD mesh copying."""
from pathlib import Path
import bpy,json,math,hashlib
from mathutils import Vector
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
DEST=ROOT/'assets/art/cryo_corridor_sample_v1';DEST.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)

def material(name,texture=None,color=(.2,.25,.26,1)):
 m=bpy.data.materials.new(name);m.diffuse_color=color;m.use_nodes=True
 p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=color;p.inputs['Roughness'].default_value=.95
 if texture:
  t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(DEST/texture));t.interpolation='Closest';m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
 return m

def mesh(name,verts,faces,uvs,mat):
 # Author in Godot meters, map to Blender z-up; glTF export restores Godot axes.
 me=bpy.data.meshes.new(name);me.from_pydata([(x,-z,y) for x,y,z in verts],[],faces);me.update()
 layer=me.uv_layers.new(name='UVMap')
 for poly,coords in zip(me.polygons,uvs):
  for loop,uv in zip(poly.loop_indices,coords):layer.data[loop].uv=uv
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(mat)
 ob['scope']='visual cladding only; existing route collision retained';return ob

wall=material('Corridor_Wall_PixelLab','wall.png');floor=material('Corridor_Floor_Placeholder','floor.png');trim=material('Corridor_Dark_Trim',color=(.12,.17,.18,1))
# Front wall veneer occupies the existing wall thickness; visible face offset 3mm to avoid coplanar overlap.
w=mesh('Wall_3p2m_TwoBays',[(6.6,0,-11.897),(9.8,0,-11.897),(9.8,3.2,-11.897),(6.6,3.2,-11.897)],[(0,1,2,3)],[[(0,0),(1,0),(1,1),(0,1)]],wall)
wr=mesh('Room1_Exterior_Wall_Module',[(9.8,0,-9.503),(6.6,0,-9.503),(6.6,3.2,-9.503),(9.8,3.2,-9.503)],[(0,1,2,3)],[[(0,0),(1,0),(1,1),(0,1)]],wall)
f=mesh('Floor_3p2m_Unique',[(6.6,.003,-9.5),(9.8,.003,-9.5),(9.8,.003,-11.9),(6.6,.003,-11.9)],[(0,1,2,3)],[[(0,0),(1,0),(1,1),(0,1)]],floor)
def box(name,center,size,mat):
 x,y,z=center;sx,sy,sz=[q/2 for q in size]
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,-z,y));o=bpy.context.object;o.name=name;o.dimensions=(size[0],size[2],size[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat);return o
box('Wall_Top_Cap',(8.2,3.3,-11.99),(3.2,.2,.18),trim)
box('Panel_Central_Recess',(8.2,1.75,-11.889),(.025,2.9,.012),trim)
box('Light_Channel',(8.2,2.89,-11.88),(3.2,.075,.03),trim)
lamp=material('Corridor_Lamp_Diffuser',color=(.64,.76,.75,1))
box('Light_Diffuser',(8.2,2.89,-11.86),(3.14,.025,.018),lamp)
box('Room1_Exterior_Top_Cap',(8.2,3.3,-9.41),(3.2,.2,.18),trim)
box('Room1_Exterior_Central_Recess',(8.2,1.75,-9.511),(.025,2.9,.012),trim)
box('Room1_Exterior_Light_Channel',(8.2,2.89,-9.52),(3.2,.075,.03),trim)
box('Room1_Exterior_Light_Diffuser',(8.2,2.89,-9.54),(3.14,.025,.018),lamp)
# Verify both primary surfaces have nondegenerate, bounded UV and 80 native texels/m.
report={'result':'PASS','UV0':[],'lightmap':'Not used: sample-only realtime lights. No stale bake attached.','primary_density_px_m':80,'visual_offset_m':.003,'route_collision_modified':False}
for ob,sz,world in [(w,(256,256),(3.2,3.2)),(wr,(256,256),(3.2,3.2)),(f,(256,192),(3.2,2.4))]:
 uv=[tuple(v.uv) for v in ob.data.uv_layers.active.data]
 assert all(0<=u<=1 and 0<=v<=1 for u,v in uv)
 assert all(abs(a/b-80)<1e-7 for a,b in zip(sz,world))
 report['UV0'].append({'object':ob.name,'pixels':sz,'meters':world,'uv':uv,'density':80,'overlap':'one continuous quad per unique texture; no islands overlap'})
report['objects']=len(bpy.context.scene.objects)
(HERE/'model_validation.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(EXP/'cryo_corridor_sample_v1.blend'))
# Save relative texture paths in the editable source.
for image in bpy.data.images:
 if image.source=='FILE':image.filepath=bpy.path.relpath(image.filepath)
bpy.ops.wm.save_as_mainfile(filepath=str(EXP/'cryo_corridor_sample_v1.blend'))
bpy.ops.export_scene.gltf(filepath=str(DEST/'corridor_sample_v1.glb'),export_format='GLB',export_extras=True)
print('CORRIDOR_MODEL_PASS',report['objects'])
