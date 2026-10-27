from pathlib import Path
import bpy,json
HERE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(HERE/'room1_open_hero_uv2_r2_packed.blend'))
out={}
for obj in bpy.data.objects:
 if obj.type!='MESH' or not obj.name.startswith('Bake_') or not obj.data.uv_layers.get('LightmapUV'):continue
 mesh=obj.data;mesh.calc_loop_triangles();rows=[]
 for tri in mesh.loop_triangles:
  corners=[]
  for loop_index in tri.loops:
   v=mesh.vertices[mesh.loops[loop_index].vertex_index].co
   uv=mesh.uv_layers['UVMap'].data[loop_index].uv
   light=mesh.uv_layers['LightmapUV'].data[loop_index].uv
   corners.append([v.x,v.z,-v.y,uv.x,1-uv.y,light.x,1-light.y])
  rows.append(corners)
 out[obj.name]={'layers':[(l.name,l.active_render) for l in mesh.uv_layers], 'triangles':rows}
(HERE/'probe_source_uv2.json').write_text(json.dumps(out),encoding='utf8')
print('UV2_SOURCE_EXTRACTED',len(out),flush=True)
