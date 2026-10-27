"""Bake v8 P12 direct+indirect irradiance from the unchanged r9 room context."""
from pathlib import Path
import bpy, os, json, time,runpy,numpy as np
from mathutils import Vector,Matrix

HERE=Path(__file__).resolve().parents[1]; REPO=HERE.parents[3]
ROOM=REPO/'docs/art/experiments/room1_floor_palette_r9/room1_floor_palette_r9_packed.blend'
ASSET=REPO/'assets/art/cryopod_standard_v8'; OUT=ASSET
P12=Vector((3.525,7.65,0))

def remove_old():
    for o in list(bpy.data.objects):
        if o.name.startswith(('Bake_P12_','P12_V8_')): bpy.data.objects.remove(o,do_unlink=True)

def bake(label):
    bpy.ops.wm.open_mainfile(filepath=str(ROOM)); remove_old()
    helper=runpy.run_path(str(HERE/'source/frozen_glb_pose.py'))['load_frozen_pose']
    imported=helper(ASSET/f'cryopod_standard_v8_{label}.glb',HERE/'room1_pod_standard_v8_packed.blend',P12)
    opaque=[]
    for o in imported:
        keys=' '.join(m.name.lower() for m in o.data.materials if m)
        if any(x in keys for x in ('glass','display','tube_diffuser')): o.hide_render=True
        else: opaque.append(o)
    bpy.context.view_layer.update()
    actual_bounds=[[min((o.matrix_world@Vector(c))[i] for o in imported for c in o.bound_box) for i in range(3)],
                   [max((o.matrix_world@Vector(c))[i] for o in imported for c in o.bound_box) for i in range(3)]]
    expected=json.loads((HERE/'source/standard_v8_validation.json').read_text())['bounds'][label]
    for axis in range(3):
        assert abs(actual_bounds[0][axis]-(expected['min'][axis]+P12[axis]))<.0001,(label,'min',actual_bounds,expected)
        assert abs(actual_bounds[1][axis]-(expected['max'][axis]+P12[axis]))<.0001,(label,'max',actual_bounds,expected)
    excluded_names=[o.name for o in imported if o.hide_render]
    opaque_count=len(opaque)
    opaque_bounds=[[min((o.matrix_world@Vector(c))[i] for o in opaque for c in o.bound_box) for i in range(3)],
                   [max((o.matrix_world@Vector(c))[i] for o in opaque for c in o.bound_box) for i in range(3)]]
    bpy.ops.object.select_all(action='DESELECT')
    for o in opaque:o.select_set(True)
    bpy.context.view_layer.objects.active=opaque[0]; bpy.ops.object.join(); receiver=bpy.context.object; receiver.name='Bake_P12_V8_Receiver'
    bpy.context.view_layer.update()
    joined_bounds=[[min((receiver.matrix_world@Vector(c))[i] for c in receiver.bound_box) for i in range(3)],
                   [max((receiver.matrix_world@Vector(c))[i] for c in receiver.bound_box) for i in range(3)]]
    if os.environ.get('P12_V8_INSPECT_ONLY')=='1':
        print('V8_POST_JOIN_INSPECT',label,'opaque_before',opaque_bounds,'after',joined_bounds,flush=True)
        return {'pose':label,'inspection':True,'before':actual_bounds,'after':joined_bounds}
    for axis in range(3):
        assert abs(joined_bounds[0][axis]-opaque_bounds[0][axis])<.0001,('join changed pose min',label,joined_bounds,opaque_bounds)
        assert abs(joined_bounds[1][axis]-opaque_bounds[1][axis])<.0001,('join changed pose max',label,joined_bounds,opaque_bounds)
    # GLB preserves our global LightmapUV; use that exact second atlas.
    lm=receiver.data.uv_layers.get('LightmapUV') or receiver.data.uv_layers[-1]; lm.name='LightmapUV'; receiver.data.uv_layers.active=lm
    size=int(os.environ.get('P12_V8_BAKE_SIZE','2048')); image=bpy.data.images.new(f'P12V8_{label}',width=size,height=size,alpha=False,float_buffer=True); image.colorspace_settings.name='Non-Color'
    for mat in receiver.data.materials:
        if mat and mat.use_nodes:
            for tex in list(mat.node_tree.nodes):
                if tex.type=='TEX_IMAGE' and not tex.inputs['Vector'].is_linked:
                    uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map=receiver.data.uv_layers[0].name
                    mat.node_tree.links.new(uv.outputs['UV'],tex.inputs['Vector'])
            node=mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image=image; mat.node_tree.nodes.active=node
    scene=bpy.context.scene; scene.render.engine='CYCLES';scene.cycles.samples=int(os.environ.get('P12_V8_BAKE_SAMPLES','1024'));scene.cycles.use_adaptive_sampling=False;scene.render.threads_mode='FIXED';scene.render.threads=8
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices();devs=[d for d in prefs.devices if d.type=='OPTIX'];
        for d in prefs.devices:d.use=d.type=='OPTIX'
        if devs:scene.cycles.device='GPU'
    except Exception as exc: print('GPU fallback',exc,flush=True)
    scene.cycles.max_bounces=3;scene.cycles.diffuse_bounces=2;scene.render.bake.margin=8;scene.render.image_settings.file_format='OPEN_EXR';scene.render.image_settings.color_depth='32';scene.render.image_settings.exr_codec='ZIP';scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    bpy.context.view_layer.objects.active=receiver;bpy.ops.object.select_all(action='DESELECT');receiver.select_set(True)
    print('V8_BAKE_BEGIN',label,scene.cycles.device,scene.cycles.samples,size,flush=True); start=time.monotonic()
    path=OUT/f'{label}_irradiance.exr'
    reused=label=='closed' and os.environ.get('P12_V8_REUSE_CLOSED')=='1' and path.exists()
    if reused:
        cached=bpy.data.images.load(str(path),check_existing=False)
        values=np.empty(len(cached.pixels),dtype=np.float32);cached.pixels.foreach_get(values)
        reused=bool(np.isfinite(values).all() and values.reshape(-1,4)[:,:3].max()>.01)
        print('V8_CACHE_CHECK',label,reused,float(values.reshape(-1,4)[:,:3].max()),flush=True)
    if not reused:
        bpy.ops.object.bake(type='DIFFUSE',pass_filter={'DIRECT','INDIRECT'},uv_layer='LightmapUV',use_clear=True,margin=8)
        image.filepath_raw=str(path);image.file_format='OPEN_EXR';image.save_render(str(path),scene=scene)
    print('V8_BAKE_END',label,time.monotonic()-start,path,flush=True)
    return {'pose':label,'image':str(path),'seconds':time.monotonic()-start,'device':scene.cycles.device,'samples':scene.cycles.samples,'size':size,'pose_world_bounds':actual_bounds,'opaque_world_bounds':opaque_bounds,'joined_opaque_bounds':joined_bounds,'expected_pose_bounds_matched':True,'opaque_mesh_count':opaque_count,'excluded_nonopaque':excluded_names,'reused_already_completed_raw':reused}

labels=(os.environ.get('P12_V8_BAKE_LABEL') or 'closed,open').split(',')
new=[bake(label.strip()) for label in labels if label.strip()]
existing=[]
audit=HERE/'source'/'bake_validation.json'
if audit.is_file():
    try: existing=json.loads(audit.read_text(encoding='utf8')).get('result',[])
    except Exception: existing=[]
by_pose={entry['pose']:entry for entry in existing}; by_pose.update({entry['pose']:entry for entry in new})
result={'version':'v8','p12_blender':[3.525,7.65,0],'result':[by_pose[key] for key in sorted(by_pose)]}
if os.environ.get('P12_V8_INSPECT_ONLY')!='1':audit.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('V8_BAKES_COMPLETE',json.dumps(result,ensure_ascii=False),flush=True)
