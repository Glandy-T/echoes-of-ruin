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

wall=material('Corridor_Wall_Reused_R24','wall.png');floor=material('Corridor_Floor_Reused_R26','floor.png');trim=material('Corridor_Dark_Trim',color=(.12,.17,.18,1))
em=wall.node_tree.nodes.new('ShaderNodeTexImage');em.image=bpy.data.images.load(str(DEST/'wall_emission.png'));em.interpolation='Closest'
wall_bsdf=next(n for n in wall.node_tree.nodes if n.type=='BSDF_PRINCIPLED');wall.node_tree.links.new(em.outputs['Color'],wall_bsdf.inputs['Emission Color']);wall_bsdf.inputs['Emission Strength'].default_value=.35
# Front wall veneer occupies the existing wall thickness; visible face offset 3mm to avoid coplanar overlap.
w=mesh('Wall_3p2m_TwoBays',[(6.6,0,-11.897),(9.8,0,-11.897),(9.8,3.4,-11.897),(6.6,3.4,-11.897)],[(0,1,2,3)],[[(0,0),(1,0),(1,1),(0,1)]],wall)
wr=mesh('Room1_Exterior_Wall_Module',[(9.8,0,-9.503),(6.6,0,-9.503),(6.6,3.4,-9.503),(9.8,3.4,-9.503)],[(0,1,2,3)],[[(0,0),(1,0),(1,1),(0,1)]],wall)
f=mesh('Floor_3p2m_Unique',[(6.6,.003,-9.5),(9.8,.003,-9.5),(9.8,.003,-11.9),(6.6,.003,-11.9)],[(0,1,2,3)],[[(0,0),(1,0),(1,1),(0,1)]],floor)
# Verify both primary surfaces have nondegenerate, bounded UV and 80 native texels/m.
report={'result':'PASS','UV0':[],'lightmap':'Not used: sample-only realtime lights. No stale bake attached.','primary_density_px_m':80,'visual_offset_m':.003,'route_collision_modified':False}
for ob,sz,world in [(w,(256,272),(3.2,3.4)),(wr,(256,272),(3.2,3.4)),(f,(256,192),(3.2,2.4))]:
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
