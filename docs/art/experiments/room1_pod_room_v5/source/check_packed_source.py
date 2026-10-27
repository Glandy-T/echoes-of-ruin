"""Reopen each final room source, restore review visibility and read back maps."""
from pathlib import Path
import bpy,json,hashlib
HERE=Path(__file__).resolve().parents[1];REPO=HERE.parents[3]
OUT=REPO/'assets/art/room1_pod_room_v5';rows=[]
for pose in ['closed','open']:
    path=HERE/f'room1_pod_{pose}_room_v5_packed.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path))
    receivers=[o for o in bpy.data.objects if o.type=='MESH' and o.name=='P12_V4_BAKED_OPAQUE']
    assert len(receivers)==1
    receiver=receivers[0];receiver.data.uv_layers[0].active_render=True
    pane=bpy.data.objects['pod_v4_glass'];screen=bpy.data.objects['pod_v4_display']
    pane.hide_render=False;screen.hide_render=False
    lightmap=bpy.data.images[f'P12V4_{pose}_irradiance']
    assert lightmap.packed_file
    packed_hash=hashlib.sha256(bytes(lightmap.packed_file.data)).hexdigest()
    assert packed_hash==hashlib.sha256((OUT/f'{pose}_irradiance.exr').read_bytes()).hexdigest()
    maps=[]
    for material in receiver.data.materials:
        for node in material.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image and node.outputs['Color'].is_linked:
                assert node.image.packed_file,(material.name,node.image.name)
                maps.append(node.image.name)
    origin=receiver.parent.matrix_world.translation
    assert abs(origin.x-3.525)<.00001 and abs(origin.y-7.65)<.00001
    bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True,check_existing=False)
    rows.append({'pose':pose,'source':path.name,'active_packed_color_maps':maps,'packed_final_exr_sha256':packed_hash,'receiver_uv_layers':[l.name for l in receiver.data.uv_layers],'p12_blender_origin':list(origin),'original_ribbon_emitters':len([o for o in bpy.data.objects if o.name.startswith('ContinuousRibbon_')]),'new_glass_screen_visible_for_review':True})
(HERE/'source/packed_source_readback.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
print('PACKED_ROOM_SOURCE_PASS')
