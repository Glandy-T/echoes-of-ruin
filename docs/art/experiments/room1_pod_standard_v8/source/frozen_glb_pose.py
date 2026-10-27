"""Build bake-only world meshes directly from serialized GLB geometry.

The exact matrices/UVs rendered by Godot are authoritative here. This avoids
Blender glTF import/parent evaluation changing a static animated-part pose.
"""
import json,struct
import bpy,numpy as np
from mathutils import Matrix,Vector,Quaternion

def load_frozen_pose(glb,source_blend,offset):
    raw=glb.read_bytes();length=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+length]);binary=raw[28+length:]
    def array(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
        n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        return np.ndarray((a['count'],n),dtype=dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*dt.itemsize),dt.itemsize)).copy()
    with bpy.data.libraries.load(str(source_blend),link=False) as (src,dst):
        dst.materials=[n for n in src.materials if n.startswith('POD_V8_')]
    materials={m.name:m for m in dst.materials}
    conversion=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
    shift=Matrix.Translation(offset);objects=[]
    def visit(index,parent):
        node=doc['nodes'][index]
        if 'matrix' in node:local=Matrix([node['matrix'][i:i+4] for i in range(0,16,4)]).transposed()
        else:
            q=node.get('rotation',[0,0,0,1]);local=Matrix.Translation(node.get('translation',[0,0,0]))@Quaternion((q[3],q[0],q[1],q[2])).to_matrix().to_4x4()@Matrix.Diagonal([*node.get('scale',[1,1,1]),1])
        world=parent@local
        if 'mesh' in node:
            for primitive in doc['meshes'][node['mesh']]['primitives']:
                attr=primitive['attributes'];matrix=shift@conversion@world
                verts=[matrix@Vector(v) for v in array(attr['POSITION'])]
                indices=array(primitive['indices']).reshape(-1) if 'indices' in primitive else np.arange(len(verts))
                faces=[tuple(int(x) for x in indices[i:i+3]) for i in range(0,len(indices),3)]
                mesh=bpy.data.meshes.new('Frozen_'+node['name']);mesh.from_pydata(verts,[],faces);mesh.update()
                for uv_name,key in [('UV_GODOT_0','TEXCOORD_0'),('LightmapUV','TEXCOORD_1')]:
                    values=array(attr[key]);layer=mesh.uv_layers.new(name=uv_name)
                    for loop in mesh.loops:
                        u,v=values[loop.vertex_index];layer.data[loop.index].uv=(float(u),1.0-float(v))
                mesh.uv_layers[0].active_render=True;mesh.uv_layers.active_index=0
                if 'NORMAL' in attr:
                    normal_matrix=matrix.to_3x3().inverted().transposed()
                    normals=[(normal_matrix@Vector(n)).normalized() for n in array(attr['NORMAL'])]
                    for face in mesh.polygons:face.use_smooth=True
                    mesh.normals_split_custom_set_from_vertices(normals)
                key=doc['materials'][primitive['material']]['name']
                material=materials[key];mesh.materials.append(material)
                obj=bpy.data.objects.new('BakeV8_'+node['name'],mesh);bpy.context.collection.objects.link(obj)
                obj.matrix_world=Matrix.Identity(4);objects.append(obj)
        for child in node.get('children',[]):visit(child,world)
    for index in doc['scenes'][doc.get('scene',0)]['nodes']:visit(index,Matrix.Identity(4))
    bpy.context.view_layer.update()
    return objects
