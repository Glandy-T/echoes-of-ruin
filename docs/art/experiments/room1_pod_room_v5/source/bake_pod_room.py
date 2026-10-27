"""Bake Room 1's existing ribbon light onto the revised P12 only.

The r9 room stays intact as an occluder/light source.  This deliberately does
not rewrite its shared UV2 atlas or irradiance: the new closed/open v4 pod is
given its own lightmap atlas and exported in local pod coordinates.
"""
from pathlib import Path
import bpy, json, hashlib, struct, os, runpy, time
from mathutils import Vector

HERE=Path(__file__).resolve().parents[1]
REPO=HERE.parents[3]
ROOM=REPO/'docs/art/experiments/room1_floor_palette_r9/room1_floor_palette_r9_packed.blend'
V4=REPO/'assets/art/room1_pod_volume_v4'
OUT=REPO/'assets/art/room1_pod_room_v5'
OUT.mkdir(parents=True,exist_ok=True)
P12=Vector((3.525,7.65,0.0)) # Godot (3.525,0,-7.65) -> Blender X,-Z,Y
OPAQUE=('glass','display')

def h(obj):
    digest=hashlib.sha256(); digest.update(obj.name.encode()); digest.update(bytes(str(list(obj.matrix_world)), 'utf8'))
    for mat in obj.data.materials:
        digest.update((mat.name if mat else '').encode())
        if mat and mat.use_nodes:
            for node in mat.node_tree.nodes:
                digest.update(node.bl_idname.encode())
                for socket in node.inputs:
                    if hasattr(socket,'default_value'):
                        value=socket.default_value
                        digest.update(repr(list(value) if hasattr(value,'__iter__') else value).encode())
    for v in obj.data.vertices: digest.update(bytes(repr(tuple(v.co)), 'utf8'))
    return digest.hexdigest()

def emitter_hashes():
    return {o.name:h(o) for o in bpy.data.objects if o.name.startswith('ContinuousRibbon_')}

def glb_doc(path):
    raw=path.read_bytes(); length=struct.unpack_from('<I',raw,12)[0]
    return json.loads(raw[20:20+length])

def delete_old_p12():
    old=[o for o in bpy.data.objects if o.name.startswith('Bake_P12_')]
    # Glass/display are present but hidden in r9; this confirms we are removing
    # every old P12 baking receiver rather than accidentally double-lighting it.
    info={'old_p12_count':len(old),'old_p12_names':[o.name for o in old],
          'old_hidden_render':[o.name for o in old if o.hide_render]}
    for o in old: bpy.data.objects.remove(o,do_unlink=True)
    return info

def import_pod(glb):
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    imported=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
    assert imported, glb
    root=bpy.data.objects.new('P12_V4_ROOM_LOCAL_ROOT',None); bpy.context.collection.objects.link(root)
    root.location=P12
    for o in imported:
        o.parent=root
        # glTF imports local coordinates; keep original transform under the room parent.
        original_uv=o.data.uv_layers[0].name
        for mat in o.data.materials:
            if not mat or not mat.use_nodes: continue
            for node in list(mat.node_tree.nodes):
                if node.type=='TEX_IMAGE' and not node.inputs['Vector'].is_linked:
                    uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map=original_uv
                    mat.node_tree.links.new(uv.outputs['UV'],node.inputs['Vector'])
    opaque=[]; excluded=[]
    for o in imported:
        low=o.name.lower()+' '+','.join(m.name.lower() for m in o.data.materials if m)
        if any(token in low for token in OPAQUE):
            o.hide_render=True; excluded.append(o.name)
        else: opaque.append(o)
    assert opaque
    return root,imported,opaque,excluded

def make_uv2(opaque):
    bpy.ops.object.select_all(action='DESELECT')
    for o in opaque: o.select_set(True)
    bpy.context.view_layer.objects.active=opaque[0]
    bpy.ops.object.join()
    pod=bpy.context.object; pod.name='P12_V4_BAKED_OPAQUE'
    # Work on a one-object atlas so charts cannot overlap between component meshes.
    if pod.data.uv_layers.get('LightmapUV'): pod.data.uv_layers.remove(pod.data.uv_layers['LightmapUV'])
    uv=pod.data.uv_layers.new(name='LightmapUV'); pod.data.uv_layers.active=uv; uv.active_render=True
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15192, margin_method='SCALED', island_margin=.006, area_weight=.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    return pod

def uv_report(mesh):
    uv=mesh.uv_layers['LightmapUV']; deg=over=out=tri=0; bounds=[1,1,0,0]
    triangles=[]
    for poly in mesh.polygons:
        ids=poly.loop_indices
        for i in range(1,len(ids)-1):
            pts=[uv.data[ids[x]].uv for x in (0,i,i+1)]
            area=abs((pts[1].x-pts[0].x)*(pts[2].y-pts[0].y)-(pts[2].x-pts[0].x)*(pts[1].y-pts[0].y))*.5
            deg+=area<1e-9; tri+=1
            triangles.append((area,[(p.x,p.y) for p in pts]))
        for li in ids:
            p=uv.data[li].uv; bounds=[min(bounds[0],p.x),min(bounds[1],p.y),max(bounds[2],p.x),max(bounds[3],p.y)]
            out+=p.x<-.00001 or p.y<-.00001 or p.x>1.00001 or p.y>1.00001
    # smart project islands are distinct; a full exact triangle-intersection pass
    # is disproportionate here, but non-degenerate, in-atlas output is asserted.
    return {'triangles':tri,'degenerate_triangles':deg,'out_of_atlas_vertices':out,'bounds':bounds,'positive_area_overlap_count':'not_sampled; single-object Smart UV Project atlas'}

def bake_and_export(label):
    bpy.ops.wm.open_mainfile(filepath=str(ROOM))
    emit_before=emitter_hashes(); assert len(emit_before)==4
    old=delete_old_p12()
    root, imported, opaque, excluded=import_pod(V4/f'pod_{label}_v4.glb')
    pod=make_uv2(opaque)
    remaining=[pod]+[bpy.data.objects[name] for name in excluded]
    # Glass and display stay in source/export but are not bake receivers.  They
    # must also not occlude the light path while Cycles renders opaque surfaces.
    size=int(os.environ.get('P12_ROOM_BAKE_SIZE','2048'))
    image=bpy.data.images.new(f'P12V4_{label}_irradiance',width=size,height=size,alpha=False,float_buffer=True)
    image.colorspace_settings.name='Non-Color'
    for mat in pod.data.materials:
        if not mat or not mat.use_nodes: continue
        n=mat.node_tree.nodes.new('ShaderNodeTexImage'); n.image=image; mat.node_tree.nodes.active=n
    scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=int(os.environ.get('P12_ROOM_BAKE_SAMPLES','1024')); scene.cycles.use_adaptive_sampling=False
    scene.render.threads_mode='FIXED';scene.render.threads=8
    devices=[]
    try:
        pref=bpy.context.preferences.addons['cycles'].preferences
        pref.compute_device_type='OPTIX';pref.get_devices()
        devices=[d.name for d in pref.devices if d.type=='OPTIX']
        for device in pref.devices:device.use=device.type=='OPTIX'
        if devices:scene.cycles.device='GPU'
    except Exception as exc:print('GPU unavailable, bounded CPU fallback:',exc,flush=True)
    scene.cycles.max_bounces=3;scene.cycles.diffuse_bounces=2;scene.render.bake.margin=4
    bpy.context.view_layer.objects.active=pod; bpy.ops.object.select_all(action='DESELECT');pod.select_set(True)
    print('BAKE_BEGIN',label,scene.cycles.device,devices,flush=True)
    start=time.monotonic()
    bpy.ops.object.bake(type='DIFFUSE',pass_filter={'DIRECT','INDIRECT'},uv_layer='LightmapUV',use_clear=True,margin=4)
    print('BAKE_END',label,time.monotonic()-start,flush=True)
    exr=OUT/f'{label}_irradiance.exr';image.filepath_raw=str(exr);image.file_format='OPEN_EXR';image.save();image.pack()
    report=runpy.run_path(str(REPO/'scripts/dev/room1_uv2_audit.py'))['audit_uv2_layout']([pod])
    for key in ['uv_degenerate_triangle_count','positive_area_overlap_count','out_of_atlas_vertex_count']:assert report[key]==0,(key,report)
    # Lossless ZIP storage of the linear float irradiance; no display transform.
    scene.render.image_settings.file_format='OPEN_EXR';scene.render.image_settings.color_depth='32'
    scene.render.image_settings.color_mode='RGB';scene.render.image_settings.exr_codec='ZIP'
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
    image.save_render(str(exr),scene=scene)
    image.reload();image.pack()
    # Pack actual v4 textures and source references in this pose's reproducible room file.
    bpy.ops.file.pack_all()
    blend=HERE/f'room1_pod_{label}_room_v5_packed.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True,check_existing=False)
    # Export local mesh+glass+display: restore root to origin only for the GLB,
    # then restore it for source reproducibility.
    root.location=Vector((0,0,0)); bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    for o in remaining:
        o.hide_render=False;o.select_set(True)
        # Source color UV remains first; bake map must export as the second UV.
        o.data.uv_layers.active_index=0;o.data.uv_layers[0].active_render=True
        if len(o.data.uv_layers)<2:
            new=o.data.uv_layers.new(name='LightmapUV')
            for index,entry in enumerate(o.data.uv_layers[0].data):new.data[index].uv=entry.uv
    bpy.context.view_layer.objects.active=pod
    glb=OUT/f'pod_{label}_v5.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_image_format='AUTO',export_apply=False,export_animations=False,export_yup=True)
    root.location=P12
    assert emitter_hashes()==emit_before
    doc=glb_doc(glb)
    texcoords=[p.get('attributes',{}) for m in doc.get('meshes',[]) for p in m.get('primitives',[])]
    assert all('TEXCOORD_0' in p and 'TEXCOORD_1' in p for p in texcoords),texcoords
    return {'pose':label,'source_room':str(ROOM),'glb':str(glb),'irradiance':str(exr),'packed_blend':str(blend),'p12_blender_world':list(P12),'godot_parent_transform':[3.525,0,-7.65],'old_p12_removed':old,'excluded_from_bake':excluded,'uv2':report,'emitter_hashes':emit_before,'glb_primitives':len(texcoords),'cycles_device':scene.cycles.device,'samples':scene.cycles.samples,'scope':'P12 v4 only; r9 room, 19 v3 pods and four original ribbon emitters were retained as bake context. Existing r9 whole-room irradiance was not changed.'}

result={'version':'room1_pod_room_v5','poses':[]}
for label in ('closed','open'): result['poses'].append(bake_and_export(label))
(HERE/'source'/'bake_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('P12_ROOM_V5_BAKE_COMPLETE')
