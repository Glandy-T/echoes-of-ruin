"""Pack new material candidates into a COPY of the existing standard-pod source."""
from pathlib import Path
from array import array
import bpy,json,hashlib,struct,runpy
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
SOURCE=ROOT/'docs/art/experiments/room1_pod_standard_v8/room1_pod_standard_v8_packed.blend'
TARGET=EXP/'room1_pod_pixellab_r16_packed.blend'
ASSET=ROOT/'assets/art/room1_pod_pixellab_r16'
KEYS=['lid','shell_side','shell_end','interior','mattress','section']
EXTERNAL=['lid','shell_side','shell_end']
def signature():
    result={}
    for obj in bpy.data.objects:
        if obj.type!='MESH':continue
        h=hashlib.sha256()
        for v in obj.data.vertices:h.update(struct.pack('<3f',*v.co))
        for p in obj.data.polygons:h.update(struct.pack('<II',len(p.vertices),p.material_index));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
        uvs={}
        for uv in obj.data.uv_layers:
            values=array('f',[0.0])*(len(uv.data)*2);uv.data.foreach_get('uv',values)
            uvs[uv.name]=hashlib.sha256(values.tobytes()).hexdigest()
        result[obj.name]={'geometry':h.hexdigest(),'uv':uvs,'material_slots':[m.name for m in obj.data.materials],'matrix_basis':[list(row) for row in obj.matrix_basis],'parent':obj.parent.name if obj.parent else None}
    return result
def poses():
    old=bpy.context.scene.frame_current;out={};motion=bpy.data.objects['LidMotion']
    for f in [1,20,60]:
        bpy.context.scene.frame_set(f);bpy.context.view_layer.update()
        out[str(f)]={'location':list(motion.location),'rotation':list(motion.rotation_euler)}
    bpy.context.scene.frame_set(old);return out
def protected():
    result={}
    for key in ['glass','display']:
        mat=bpy.data.materials['POD_V8_'+key]
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.outputs['Color'].is_linked:
                result[key]=hashlib.sha256(bytes(node.image.packed_file.data)).hexdigest()
    for name in ['Runtime_P12_closed_irradiance','Runtime_P12_open_irradiance']:
        result[name]=hashlib.sha256(bytes(bpy.data.images[name].packed_file.data)).hexdigest()
    return result
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
before=signature();original_poses=poses();original_protected=protected()
images={};packed={}
for folder in ['variant_a','variant_b','variant_c','variant_d','shared']:
    for key in EXTERNAL if folder!='shared' else ['interior','mattress','section']:
        path=ASSET/folder/f'{key}.png';assert path.exists(),path
        name='POD_R16_'+folder+'_'+key
        image=bpy.data.images.load(str(path),check_existing=False);image.name=name
        image.colorspace_settings.name='sRGB';image.alpha_mode='STRAIGHT';image.use_fake_user=True;image.pack()
        digest=hashlib.sha256(bytes(image.packed_file.data)).hexdigest()
        assert digest==hashlib.sha256(path.read_bytes()).hexdigest()
        image.filepath=bpy.path.relpath(str(path),start=str(EXP))
        images[folder+'_'+key]=image;packed[name]=digest
for key in KEYS:
    folder='variant_a' if key in EXTERNAL else 'shared'
    material=bpy.data.materials['POD_V8_'+key]
    nodes=[n for n in material.node_tree.nodes if n.type=='TEX_IMAGE' and n.outputs['Color'].is_linked]
    assert len(nodes)==1,(key,len(nodes))
    nodes[0].image=images[folder+'_'+key];nodes[0].interpolation='Closest'
switch=bpy.data.texts.new('R16_switch_variant.py')
switch.write("# Material-only switch; choose a, b, c or d.\nimport bpy\nvariant='a'\nfor key in ['lid','shell_side','shell_end']:\n    mat=bpy.data.materials['POD_V8_'+key]\n    for node in mat.node_tree.nodes:\n        if node.type=='TEX_IMAGE' and node.outputs['Color'].is_linked:\n            node.image=bpy.data.images['POD_R16_variant_'+variant+'_'+key]\n")
note=bpy.data.texts.new('README_R16')
note.write('Room 1 单舱材质候选 r16。模型、UV、动画与玻璃/屏幕源保持v8。默认显示A，其他三套外壳和共用内腔PNG全部打包；可在R16_switch_variant.py中切换。Godot使用原v8 GLB＋新版PNG绑定，动态屏幕/玻璃和实际房间光照以Godot审图为准。原P12光照图保留，新材质间接反射未重烘。本文件不是20舱推广或完整房间工程。')
assert signature()==before
assert poses()==original_poses
assert protected()==original_protected
atlas=runpy.run_path(str(ROOT/'scripts/dev/room1_uv2_audit.py'))['audit_uv2_layout']([o for o in bpy.data.objects if o.type=='MESH'])
for key in ['uv_degenerate_triangle_count','out_of_atlas_vertex_count','positive_area_overlap_count']:assert atlas[key]==0,(key,atlas[key])
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),check_existing=False,compress=True)
bpy.ops.wm.open_mainfile(filepath=str(TARGET))
assert signature()==before and poses()==original_poses and protected()==original_protected
for name,digest in packed.items():assert hashlib.sha256(bytes(bpy.data.images[name].packed_file.data)).hexdigest()==digest
report={'source':str(SOURCE.relative_to(ROOT)).replace('\\','/'),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'geometry_uv_material_slots_unchanged':True,'mesh_count':len(before),'mesh_signature':before,'animation_poses_unchanged':original_poses,'protected_glass_display_and_hdr_unchanged':original_protected,'packed_candidates':packed,'uv2_audit':atlas,'new_bake':False,'scope':'Single existing model, material-image bindings only; four exterior sets and shared interior textures packed.'}
(HERE/'blender_readback.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('R16_BLENDER_SOURCE_PASS: geometry, both UVs, animation, glass/display/HDR unchanged; all candidate PNGs packed.')
