from pathlib import Path
import bpy,json
p=Path(__file__).resolve().parent/'room1_open_hero_uv2_r2_packed.blend'
bpy.ops.wm.open_mainfile(filepath=str(p))
for o in bpy.data.objects:
 if o.type!='MESH' or not o.name.startswith('Bake_'):continue
 if o.name not in ['Bake_Shell_Wall_left','Bake_Shell_Floor_continuous_no_tile_seams','Bake_P02_pod_v3_shell_side']:continue
 print('PROBE',o.name,len(o.data.vertices),len(o.data.polygons),'active',o.data.uv_layers.active_index)
 for l in o.data.uv_layers:
  coords=[tuple(x.uv) for x in l.data]
  print(l.name,'render',l.active_render,'range',[(min(x[i] for x in coords),max(x[i] for x in coords)) for i in (0,1)],'first',coords[:8])
