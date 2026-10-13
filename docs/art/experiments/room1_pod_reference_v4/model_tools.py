"""Small Blender helpers for the hand-built, reference-led pod candidate."""
import bpy
import bmesh
import math
import json
from mathutils import Vector

def material(name,color):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=.85
    p.inputs['Specular IOR Level'].default_value=.18
    return m

def mesh(name,verts,faces,collection,mats,regions=None):
    data=bpy.data.meshes.new(name+'_mesh')
    data.from_pydata(verts,[],faces)
    data.update()
    obj=bpy.data.objects.new(name,data)
    collection.objects.link(obj)
    for mat in mats:
        data.materials.append(mat)
    for i,face in enumerate(data.polygons):
        face.use_smooth=False
        if regions:
            face.material_index=regions[i]
    bm=bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    obj['status']='REFERENCE-LED LOW-POLY CANDIDATE / not yet approved'
    return obj

def box(name,center,dimensions,col,mat,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=center)
    obj=bpy.context.object
    obj.name=name
    obj.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)
    obj.data.materials.append(mat)
    if bevel:
        mod=obj.modifiers.new('Small_structural_edge_cut','BEVEL')
        mod.width=bevel
        mod.segments=1
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj

def unwrap(obj,directory):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active=obj
    bm=bmesh.new()
    bm.from_mesh(obj.data)
    for e in bm.edges:
        e.seam=(len({f.material_index for f in e.link_faces})>1
                or any(len(f.verts)>4 for f in e.link_faces)
                or (e.is_manifold and e.calc_face_angle()>math.radians(42)))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.uv_layers.new(name='UV_PAINT_candidate')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.unwrap(method='ANGLE_BASED',margin=.02)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(margin=.03,rotate=True)
    bpy.ops.object.mode_set(mode='OBJECT')
    layer=obj.data.uv_layers.active
    layer.active_render=True
    faces=[{'material':p.material_index,'uv':[list(layer.data[i].uv) for i in p.loop_indices]} for p in obj.data.polygons]
    directory.mkdir(exist_ok=True)
    (directory/(obj.name+'.json')).write_text(json.dumps({'object':obj.name,'template_pixels':[1024,1024],'faces':faces},indent=2),encoding='utf-8')
    colors=['#b9c9cd','#8fabad','#d0c5a0','#a1aab9','#788c95','#9daeb0']
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">','<rect width="1024" height="1024" fill="#202932"/>']
    for face in faces:
        points=' '.join(f'{u*1024:.3f},{(1-v)*1024:.3f}' for u,v in face['uv'])
        svg.append(f'<polygon points="{points}" fill="{colors[face["material"]%len(colors)]}" stroke="#26353b" stroke-width="1"/>')
    svg.append('</svg>')
    (directory/(obj.name+'.svg')).write_text('\n'.join(svg),encoding='utf-8')
    obj['UV_status']='seam-based unwrap; per-object 0-1 map; 1024px guide only, production texel density TBD'

def camera(name,target,offset,scale,col):
    data=bpy.data.cameras.new(name)
    data.type='ORTHO'
    data.ortho_scale=scale
    obj=bpy.data.objects.new(name,data)
    col.objects.link(obj)
    obj.location=Vector(target)+Vector(offset)
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
    return obj
