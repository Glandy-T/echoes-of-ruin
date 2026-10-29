"""Export the 4F plan and West stair through 1F for Godot readback.

This is a deliberately bounded review GLB, not a replacement for the game
level. The complete editable 20-level geometry stays in the v2 Blender file.
"""
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "docs/art/experiments/cryo_building_stairs_v2/cryo_building_stairs_v2.blend"
DEST = ROOT / "assets/art/cryo_building_stairs_v2/cryo_building_route_4f_to_1f_v2.glb"
DEST.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.ops.object.select_all(action='DESELECT')
selected = []
for obj in bpy.data.objects:
    if obj.type != 'MESH':
        continue
    names = {c.name for c in obj.users_collection}
    if '4F' in names or 'STAIRS_4F' in names or obj.name == 'F4_SW01_AnchorFloorOutline':
        selected.append(obj)
    elif any(name in names for name in ('STAIRS_1F','STAIRS_2F','STAIRS_3F')) and obj.get('stair_id') == 'West_Stair':
        selected.append(obj)
    elif obj.get('level') in ('1F','2F','3F') and obj.get('door_id') in ('D077','D078'):
        selected.append(obj)
for obj in selected:
    obj.hide_render = False
    obj.hide_set(False)
    obj.select_set(True)
bpy.context.view_layer.objects.active = selected[0]
bpy.ops.export_scene.gltf(filepath=str(DEST), export_format='GLB', use_selection=True,
                          export_apply=True, export_extras=True)
print(f'GODOT_ROUTE_GLTF_SELECTED_MESHES={len(selected)}; BYTES={DEST.stat().st_size}', flush=True)
