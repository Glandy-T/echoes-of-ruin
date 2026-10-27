"""Reopen packed source, audit unchanged UV2/geometry and linear HDR data."""
import bpy,hashlib,json,runpy
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
OUT=ROOT/'assets/art/room1_floor_palette_r9';OLD=ROOT/'assets/art/room1_floor_contact_r8'
bpy.ops.wm.open_mainfile(filepath=str(HERE/'room1_floor_palette_r9_packed.blend'))
objects=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Bake_') and not o.hide_render]
assert len(objects)==129
scope=json.loads((HERE/'source_scope.json').read_text(encoding='utf-8'))
assert scope['geometry_uv_before']==scope['geometry_uv_after']
assert scope['emitter_before']==scope['emitter_after']
def geometry_hash(objects):
    h=hashlib.sha256()
    for obj in sorted(objects,key=lambda x:x.name):
        h.update(obj.name.encode());h.update(repr([tuple(r) for r in obj.matrix_world]).encode())
        for v in obj.data.vertices:h.update(repr(tuple(v.co)).encode())
        for p in obj.data.polygons:h.update(repr((tuple(p.vertices),p.material_index,p.use_smooth)).encode())
        for layer in obj.data.uv_layers:
            h.update(layer.name.encode())
            for uv in layer.data:h.update(repr(tuple(uv.uv)).encode())
    return h.hexdigest()
assert geometry_hash(objects)==scope['geometry_uv_after']
assert (OUT/'room1_baked_uv2_r3.glb').read_bytes()==(OLD/'room1_baked_uv2_r3.glb').read_bytes()
assert (OUT/'mesh_mapping.json').read_bytes()==(OLD/'mesh_mapping.json').read_bytes()
audit=runpy.run_path(str(ROOT/'scripts/dev/room1_uv2_audit.py'))['audit_uv2_layout'](objects)
for key in ['uv_degenerate_triangle_count','positive_area_overlap_count','out_of_atlas_vertex_count']:assert audit[key]==0
materials=[]
for obj in objects:
    for slot in obj.material_slots:
        if not slot.material or '_R7_' not in slot.material.name:continue
        node=slot.material.node_tree.nodes['R7_WORLD_PIXEL_COLOR'];assert node.image.packed_file and node.interpolation=='Closest'
        bounds=[obj.matrix_world@v.co for v in obj.data.vertices]
        materials.append({'object':obj.name,'material':slot.material.name,'image':node.image.name,'size':list(node.image.size),'packed':bool(node.image.packed_file),'sampling':node.interpolation,'world_aabb_min':[min(v[i] for v in bounds) for i in range(3)],'world_aabb_max':[max(v[i] for v in bounds) for i in range(3)]})
assert len(materials)==7
def pixels(path):
    if path.exists():image=bpy.data.images.load(str(path),check_existing=False)
    else:
        assert path.name=='strip_irradiance.exr'
        image=bpy.data.images.get('FloorPaletteR9Irradiance')
        assert image is not None and image.packed_file,'raw must be present locally or packed in the source'
    image.colorspace_settings.name='Non-Color'
    assert tuple(image.size)==(2048,2048)
    data=np.empty(2048*2048*4,dtype=np.float32);image.pixels.foreach_get(data)
    rgb=data.reshape(2048,2048,4)[:,:,:3];assert np.isfinite(rgb).all() and rgb.min()>=0
    return rgb
raw=pixels(OUT/'strip_irradiance.exr');new=pixels(OUT/'strip_irradiance_denoised.exr');old=pixels(OLD/'strip_irradiance_denoised.exr')
valid=np.any(old>1e-5,axis=2)&np.any(new>1e-5,axis=2)
delta=np.abs(old-new)
stats={'raw_min':float(raw.min()),'raw_max':float(raw.max()),'new_min':float(new.min()),'new_max':float(new.max()),'old_max':float(old.max()),'finite_nonnegative':True,'valid_pixel_count':int(valid.sum()),'changed_pixels':int(np.any(delta>1e-6,axis=2).sum()),'mean_abs_delta_valid':float(delta[valid].mean()),'mean_old_valid':float(old[valid].mean()),'mean_new_valid':float(new[valid].mean()),'p99_abs_delta':float(np.quantile(delta[valid],.99))}
assert stats['valid_pixel_count']>100000 and stats['changed_pixels']>0
(HERE/'source_readback.json').write_text(json.dumps({'receiver_count':len(objects),'mesh_objects':len([o for o in bpy.data.objects if o.type=='MESH']),'emitters':len([o for o in bpy.data.objects if o.name.startswith('ContinuousRibbon_')]),'samples':bpy.context.scene.cycles.samples,'materials':materials,'glb_exact_r8':True,'mapping_exact_r8':True,'uv2_audit':audit,'hdr_stats':stats},ensure_ascii=False,indent=2),encoding='utf-8')
print('R9_READBACK_COMPLETE',json.dumps(stats),flush=True)
