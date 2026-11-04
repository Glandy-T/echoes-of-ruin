from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[5]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'docs/art/experiments/cryo_building_stairs_v2/cryo_building_stairs_v2.blend'))
bpy.ops.object.select_all(action='DESELECT');chosen=[]
for ob in bpy.data.objects:
 if ob.type=='MESH' and ob.get('level')=='4F' and ob.get('stair_id') in ['East_Stair','North_Stair','South_Stair']:
  ob.hide_render=False;ob.hide_set(False);ob.select_set(True);chosen.append(ob)
bpy.context.view_layer.objects.active=chosen[0]
bpy.ops.export_scene.gltf(filepath=str(ROOT/'assets/art/cryo_4f_complete_v3/other_4f_stairs.glb'),export_format='GLB',use_selection=True,export_extras=True)
print('OTHER_4F_STAIRS',len(chosen))
