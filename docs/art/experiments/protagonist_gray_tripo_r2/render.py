from pathlib import Path
import bpy, math
from mathutils import Vector
import numpy as np
p=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p/'original.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
coords=[]
for obj in meshes:
    v=np.empty(len(obj.data.vertices)*3,np.float32)
    obj.data.vertices.foreach_get('co',v)
    mat=np.array(obj.matrix_world)
    coords.append(v.reshape(-1,3)@mat[:3,:3].T+mat[:3,3])
v=np.concatenate(coords)
lo=v.min(0);hi=v.max(0);height=hi[2]-lo[2];center=Vector((lo+hi)/2)
print('RANGE',lo,hi,'OBJECTS',len(meshes),'TRIS',sum(len(o.data.polygons) for o in meshes),flush=True)

sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO'
sc.display.shading.color_type='SINGLE'
sc.display.shading.single_color=(.65,.65,.65)
sc.display.shading.show_shadows=True
sc.display.shading.show_cavity=True
sc.display.shading.cavity_type='WORLD'
sc.render.film_transparent=True
sc.render.image_settings.color_mode='RGBA'
sc.render.resolution_x=512;sc.render.resolution_y=512;sc.render.resolution_percentage=100
camdata=bpy.data.cameras.new('Review');camdata.type='ORTHO';camdata.ortho_scale=height*1.08
cam=bpy.data.objects.new('Review',camdata);sc.collection.objects.link(cam);sc.camera=cam
for name,direction in [('front',(1,0,0)),('right',(0,-1,0)),('back',(-1,0,0)),('oblique',(1,-1,.12)),('underside',(.18,-.2,-1))]:
    cam.location=center+Vector(direction).normalized()*height*3
    cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(p/(name+'.png'))
    bpy.ops.render.render(write_still=True)
import json
stats={}
for obj in meshes:
    edges=np.empty(len(obj.data.edges)*2,np.int32)
    obj.data.edges.foreach_get('vertices',edges)
    parents=list(range(len(obj.data.vertices)))
    def root(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]]
            i=parents[i]
        return i
    for a,b in edges.reshape(-1,2).tolist():
        ra,rb=root(a),root(b)
        if ra!=rb: parents[rb]=ra
    from collections import Counter
    sizes=Counter(root(i) for i in range(len(parents)))
    loop_edges=np.empty(len(obj.data.loops),np.int32)
    obj.data.loops.foreach_get('edge_index',loop_edges)
    uses=np.bincount(loop_edges,minlength=len(edges)//2)
    stats[obj.name]={'boundary_edges':int(np.sum(uses==1)),'nonmanifold_edges':int(np.sum(uses!=2)),'vertices':len(parents),'faces':len(obj.data.polygons),'components':len(sizes),'largest_vertex_counts':sizes.most_common(5)}
def band(row,pad):
    z=hi[2]-(row-3)/124*height
    return v[np.abs(v[:,2]-z)<pad*height/124]
sleeves=band(40,2)
shoulder=np.ptp(sleeves[:,1])
chest=band(46,0.75)
chest=chest[np.abs(chest[:,1]-center.y)<0.18*shoulder]
depth=np.ptp(chest[:,0])
(p/'metrics.json').write_text(json.dumps({'blender_bounds':[lo.tolist(),hi.tolist()],'shoulder':shoulder,'chest_depth':depth,'ratio':depth/shoulder,'meshes':stats},indent=2,default=float))
