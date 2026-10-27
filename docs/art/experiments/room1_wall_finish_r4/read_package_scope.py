"""Readback: only front UV0 and declared UV2 attributes may differ from r3."""
from pathlib import Path
import json,struct,hashlib

ROOT=Path(__file__).resolve().parents[4]
OLD=ROOT/'assets/art/room1_corner_quality_r3'
NEW=ROOT/'assets/art/room1_wall_finish_r4'
old=(OLD/'room1_baked_uv2_r3.glb').read_bytes()
new=(NEW/'room1_baked_uv2_r3.glb').read_bytes()
size,_=struct.unpack_from('<II',old,12)
doc=json.loads(old[20:20+size]);base=28+size
assert len(old)==len(new) and old[:base]==new[:base]
allowed=set();front_count=0;uv2_count=0
def ranges(index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    assert a['componentType']==5126
    width={'VEC2':2,'VEC3':3}[a['type']]
    return a['count'],base+v.get('byteOffset',0)+a.get('byteOffset',0),v.get('byteStride',width*4)
seen=set()
for node in doc['nodes']:
    if 'mesh' not in node:continue
    for p in doc['meshes'][node['mesh']]['primitives']:
        attrs=p['attributes'];colored='MATERIAL_REVISION' in doc['materials'][p['material']]['name']
        if node['name']=='Bake_Shell_Wall_front' and colored:
            count,offset,stride=ranges(attrs['TEXCOORD_0'])
            for i in range(count):
                u,v=struct.unpack_from('<ff',old,offset+i*stride)
                assert new[offset+i*stride:offset+i*stride+8]==struct.pack('<ff',u+.5,v-.5)
                allowed.update(range(offset+i*stride,offset+i*stride+8));front_count+=1
        if 'TEXCOORD_1' not in attrs:continue
        index=attrs['TEXCOORD_1']
        if index in seen:continue
        seen.add(index)
        count,offset,stride=ranges(index)
        _,po,ps=ranges(attrs['POSITION'])
        rear=node['name'] in {'Bake_Shell_Wall_rear_left','Bake_Shell_Wall_rear_right','Bake_Shell_Wall_rear_door_header'} and colored
        for i in range(count):
            u,v=struct.unpack_from('<ff',old,offset+i*stride)
            target=(.005+.875*u,.005+.875*v)
            if rear:
                x,y,_=struct.unpack_from('<fff',old,po+i*ps)
                x=round(x+node['translation'][0],5);y=round(y+node['translation'][1],5)
                target=(.02+x/21*.61,.89+(1-y/3.4)*.09876)
            assert new[offset+i*stride:offset+i*stride+8]==struct.pack('<ff',*target),(node['name'],i)
            allowed.update(range(offset+i*stride,offset+i*stride+8));uv2_count+=1
different={i for i,(a,b) in enumerate(zip(old,new)) if a!=b}
assert not different-allowed
assert front_count==6
assert (OLD/'mesh_mapping.json').read_bytes()==(NEW/'mesh_mapping.json').read_bytes()
layout=json.loads((NEW/'uv2_layout_record.json').read_text())
assert all(layout[k]==0 for k in ['uv_degenerate_triangle_count','positive_area_overlap_count','out_of_atlas_vertex_count'])
report={'changed_front_uv0_corners':front_count,'declared_uv2_corners':uv2_count,
    'changed_bytes':len(different),'changed_bytes_outside_declared_uv_attributes':len(different-allowed),
    'positions_normals_nodes_images_preserved_exactly':True,'other_uv0_preserved_exactly':True,
    'mesh_mapping_preserved_exactly':True,'uv2_formulas_verified_exact_float32':True,
    'layout_valid_triangles':layout['uv_non_degenerate_triangle_count'],
    'sha256':{name:hashlib.sha256((NEW/name).read_bytes()).hexdigest() for name in ['room1_baked_uv2_r3.glb','strip_irradiance_denoised.exr','mesh_mapping.json']}}
(Path(__file__).parent/'package_scope_readback.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
