"""Read-only inventory and review renders for the downloaded Long hair blend."""
import bpy, json
from collections import defaultdict, deque
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
SOURCE=OUT.parent/'source'/'original'/'source'/'Long hair.blend'

def bbox(points):
    return [[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)] if points else None
def bounds_dict(points):
    b=bbox(points)
    return {'min':[round(v,6) for v in (b[0][0],b[1][0],b[2][0])], 'max':[round(v,6) for v in (b[0][1],b[1][1],b[2][1])],
            'dimensions':[round(b[i][1]-b[i][0],6) for i in range(3)]} if b else None

def components(mesh,world):
    adjacency=defaultdict(set)
    for edge in mesh.edges:
        a,b=edge.vertices;adjacency[a].add(b);adjacency[b].add(a)
    seen=set();out=[]
    for start in range(len(mesh.vertices)):
        if start in seen:continue
        queue=deque([start]);seen.add(start);vertices=[]
        while queue:
            v=queue.popleft();vertices.append(v)
            for nxt in adjacency[v]:
                if nxt not in seen:seen.add(nxt);queue.append(nxt)
        vset=set(vertices); polys=[p.index for p in mesh.polygons if all(v in vset for v in p.vertices)]
        out.append({'vertex_count':len(vertices),'polygon_count':len(polys),'triangle_count':sum(len(mesh.polygons[i].vertices)-2 for i in polys),
                    'vertex_indices':vertices[:24],'world_bounds':bounds_dict([world@mesh.vertices[i].co for i in vertices]),
                    'material_indices':sorted(set(mesh.polygons[i].material_index for i in polys))})
    return sorted(out,key=lambda item:-item['vertex_count'])

def material_info(material):
    result={'name':material.name,'diffuse_color':[round(v,6) for v in material.diffuse_color],'use_nodes':material.use_nodes}
    if material.use_nodes:
        result['images']=[{'node':node.name,'image':node.image.name,'filepath':node.image.filepath} for node in material.node_tree.nodes if node.type=='TEX_IMAGE' and node.image]
        result['shader_colors']=[{'node':node.name,'type':node.type,'base_color':[round(v,6) for v in node.inputs['Base Color'].default_value] if node.type=='BSDF_PRINCIPLED' and not node.inputs['Base Color'].is_linked else None,
          'base_color_link':node.inputs['Base Color'].links[0].from_node.name if node.type=='BSDF_PRINCIPLED' and node.inputs['Base Color'].is_linked else None,
          'color':[round(v,6) for v in node.outputs['Color'].default_value] if node.type=='RGB' else None} for node in material.node_tree.nodes if node.type in {'BSDF_PRINCIPLED','RGB'}]
        result['group_color_inputs']=[{'node':node.name,'node_group':node.node_tree.name if node.node_tree else None,
          'color':[round(v,6) for v in node.inputs['Color'].default_value] if node.inputs.get('Color') and not node.inputs['Color'].is_linked else None} for node in material.node_tree.nodes if node.type=='GROUP']
    return result

def uv_summary(mesh):
    uv=mesh.uv_layers.active
    if not uv:return {'active_layer':None}
    mesh.calc_loop_triangles();zero=outside=0;coords=defaultdict(int)
    for triangle in mesh.loop_triangles:
        points=[uv.data[index].uv for index in triangle.loops]
        signed=.5*sum(points[i].x*points[(i+1)%3].y-points[(i+1)%3].x*points[i].y for i in range(3))
        if abs(signed)<1e-9:zero+=1
        if any(p.x<-1e-9 or p.x>1+1e-9 or p.y<-1e-9 or p.y>1+1e-9 for p in points):outside+=1
        coords[tuple(sorted((round(p.x,7),round(p.y,7)) for p in points))]+=1
    return {'active_layer':uv.name,'triangles':len(mesh.loop_triangles),'zero_area_triangles':zero,'outside_0_1_triangles':outside,
      'identical_triangle_uv_stacks':sum(value-1 for value in coords.values() if value>1)}

def camera(scene,name,location,target,scale,path):
    data=bpy.data.cameras.new(name);data.type='ORTHO';data.ortho_scale=scale
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=location;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();scene.camera=ob
    scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);bpy.data.objects.remove(ob,do_unlink=True)

bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False)
scene=bpy.context.scene
meshes=[];all_points=[]
for ob in bpy.data.objects:
    item={'name':ob.name,'type':ob.type,'location':[round(v,6) for v in ob.location],'rotation_euler':[round(v,6) for v in ob.rotation_euler],
          'scale':[round(v,6) for v in ob.scale],'parent':ob.parent.name if ob.parent else None,'hidden_viewport':ob.hide_viewport,'hidden_render':ob.hide_render}
    if ob.type=='MESH':
        me=ob.data;me.calc_loop_triangles();points=[ob.matrix_world@v.co for v in me.vertices];all_points.extend(points)
        item.update({'mesh':me.name,'vertices':len(me.vertices),'edges':len(me.edges),'polygons':len(me.polygons),'triangles':len(me.loop_triangles),
            'world_bounds':bounds_dict(points),'uv_layers':[uv.name for uv in me.uv_layers],'vertex_groups':[g.name for g in ob.vertex_groups],
            'materials':[slot.material.name if slot.material else None for slot in ob.material_slots],
            'modifiers':[{'name':m.name,'type':m.type,'object':getattr(getattr(m,'object',None),'name',None)} for m in ob.modifiers],
            'components':components(me,ob.matrix_world),'raw_uv':uv_summary(me),
            'mirror_modifiers':[{'name':m.name,'axis':list(m.use_axis),'merge_threshold':m.merge_threshold,'use_mirror_merge':m.use_mirror_merge} for m in ob.modifiers if m.type=='MIRROR']})
        evaluated=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); evaluated_mesh=evaluated.to_mesh()
        item['evaluated_after_modifiers']={'vertices':len(evaluated_mesh.vertices),'triangles':sum(len(poly.vertices)-2 for poly in evaluated_mesh.polygons),
          'world_bounds':bounds_dict([evaluated.matrix_world @ vertex.co for vertex in evaluated_mesh.vertices]),'uv':uv_summary(evaluated_mesh)}
        evaluated.to_mesh_clear()
        meshes.append(item)
    elif ob.type=='ARMATURE':
        item['bones']=[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':[round(v,6) for v in b.head_local],'tail':[round(v,6) for v in b.tail_local],'deform':b.use_deform} for b in ob.data.bones]
    item['data_name']=ob.data.name if ob.data else None
    meshes.append(item) if ob.type!='MESH' else None

report={'source':str(SOURCE),'blender_version':bpy.app.version_string,'scene':scene.name,'scene_objects':[ob.name for ob in scene.objects],
  'all_mesh_world_bounds':bounds_dict(all_points),'objects':meshes,'materials':[material_info(mat) for mat in bpy.data.materials],
  'actions':[action.name for action in bpy.data.actions]}
# Workbench review only; source is not saved.
scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True
scene.render.resolution_x=1100;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
world=bpy.data.worlds.new('AUDIT_WORLD');world.color=(.08,.08,.08);scene.world=world
b=bbox(all_points);center=[(b[i][0]+b[i][1])/2 for i in range(3)];largest=max(b[i][1]-b[i][0] for i in range(3));scale=largest*1.3
camera(scene,'AUDIT_FRONT',(center[0],b[1][0]-largest*2.3,center[2]),center,scale,OUT/'source_front.png')
camera(scene,'AUDIT_3Q',(center[0]+largest*1.5,b[1][0]-largest*2.0,center[2]+largest*.35),center,scale,OUT/'source_three_quarter.png')
(OUT/'source_inventory.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
