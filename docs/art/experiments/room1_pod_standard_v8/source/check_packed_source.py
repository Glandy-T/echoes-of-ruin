"""Read the final authoring source independently, including packed runtime HDR."""
from pathlib import Path
import bpy,json,hashlib,runpy
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parents[1];REPO=HERE.parents[3]
OUT=REPO/'assets/art/cryopod_standard_v8'
bpy.ops.wm.open_mainfile(filepath=str(HERE/'room1_pod_standard_v8_packed.blend'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
assert len(meshes)==18
for obj in meshes:
    assert [u.name for u in obj.data.uv_layers]==['UV_GODOT_0','LightmapUV'],(obj.name,[u.name for u in obj.data.uv_layers])
    assert len(obj.data.materials)==1
assert bpy.data.objects['PodGlass'].type=='MESH'
assert bpy.data.objects['PodInterior'].type=='MESH'
assert bpy.data.objects['PodGlass'].parent.name=='LidMotion'
assert bpy.data.objects['PodLidInterior'].parent.name=='LidMotion'
assert bpy.data.objects['PodTubeDiffuser_L'].parent.name=='CryopodRoot'
assert bpy.data.objects['PodTubeDiffuser_R'].parent.name=='CryopodRoot'
atlas=runpy.run_path(str(REPO/'scripts/dev/room1_uv2_audit.py'))['audit_uv2_layout'](meshes)
for key in ['uv_degenerate_triangle_count','out_of_atlas_vertex_count','positive_area_overlap_count']:assert atlas[key]==0,(key,atlas[key])
colors={}
for key in ['lid','shell_side','shell_end','interior','mattress','glass','display','section']:
    material=bpy.data.materials['POD_V8_'+key]
    tex=[n for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and n.outputs['Color'].is_linked]
    assert len(tex)==1 and tex[0].image.packed_file
    packed=bytes(tex[0].image.packed_file.data)
    source=(REPO/'docs/art/experiments/room1_pod_volume_v4/textures'/f'{key}.png').read_bytes()
    assert hashlib.sha256(packed).digest()==hashlib.sha256(source).digest(),key
    colors[key]={'packed':True,'v4_png_bytes_unchanged':True}
maps={}
for pose in ['closed','open']:
    image=bpy.data.images['Runtime_P12_'+pose+'_irradiance'];assert image.packed_file
    digest=hashlib.sha256(bytes(image.packed_file.data)).hexdigest()
    assert digest==hashlib.sha256((OUT/f'{pose}_irradiance.exr').read_bytes()).hexdigest()
    maps[pose]={'packed':True,'final_exr_sha256':digest,'size':list(image.size),'colorspace':image.colorspace_settings.name}
motion=bpy.data.objects['LidMotion'];poses={}
for frame in [1,20,60]:
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
    poses[str(frame)]={'location':list(motion.location),'rotation_y':motion.rotation_euler.y}
assert abs(poses['20']['location'][2]-.67)<.00001
assert abs(poses['60']['location'][0]-.6115433)<.00001
assert abs(poses['60']['rotation_y']-.78539818)<.00001
def world_tree(obj):
    return BVHTree.FromPolygons([obj.matrix_world@v.co for v in obj.data.vertices],[tuple(p.vertices) for p in obj.data.polygons],all_triangles=True)
moving=[o for o in meshes if o.parent==motion];fixed=[o for o in meshes if o.parent!=motion];clearance=[]
for frame in [1,4,8,14,20,26,30,40,50,60]:
    bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
    trees={o.name:world_tree(o) for o in meshes};hits={}
    for a in moving:
        for b in fixed:
            count=len(trees[a.name].overlap(trees[b.name]))
            if count:hits[a.name+' / '+b.name]=count
    clearance.append({'frame':frame,'intersections':hits})
result={'real_meshes':[o.name for o in meshes],'color_images':colors,'final_runtime_maps':maps,'atlas':atlas,'poses':poses,'motion_action':motion.animation_data.action.name,'frame_20_lift_m':poses['20']['location'][2]-poses['1']['location'][2],'all_moving_vs_fixed_world_bvh':clearance}
(HERE/'source/packed_source_readback.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print('V8_PACKED_SOURCE_PASS: actual meshes, two UV layers, original pixels, final HDR, 12cm lift and 45deg endpoint')
