"""Repair only front inner-face UV0; keep the complete GLB otherwise intact."""
import json
import struct
from pathlib import Path


def fix_front_uv0(source, destination):
    data = bytearray(Path(source).read_bytes())
    size, _ = struct.unpack_from('<II', data, 12)
    doc = json.loads(data[20:20+size])
    binary_start = 28 + size
    node = next(n for n in doc['nodes'] if n['name'] == 'Bake_Shell_Wall_front')
    changed = 0
    before = []
    after = []
    for primitive in doc['meshes'][node['mesh']]['primitives']:
        if 'MATERIAL_REVISION' not in doc['materials'][primitive['material']]['name']:
            continue
        accessor = doc['accessors'][primitive['attributes']['TEXCOORD_0']]
        view = doc['bufferViews'][accessor['bufferView']]
        assert accessor['componentType'] == 5126 and accessor['type'] == 'VEC2'
        offset = binary_start + view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        stride = view.get('byteStride', 8)
        for i in range(accessor['count']):
            u, v = struct.unpack_from('<ff', data, offset+i*stride)
            assert -.501 <= u <= .501 and .499 <= v <= 1.501
            before.append([u,v])
            struct.pack_into('<ff', data, offset+i*stride, u+.5, v-.5)
            after.append([u+.5,v-.5])
            changed += 1
    assert changed == 6, changed
    Path(destination).write_bytes(data)
    return {'changed_uv0_corners':changed,'surface':'Bake_Shell_Wall_front / MATERIAL_REVISION inner face',
            'offset_gltf':[.5,-.5],'before':before,'after':after,
            'scope':'Only these TEXCOORD_0 float32 bytes modified; positions/normals/UV2/nodes/images unchanged'}


def repair_wall_package(source, destination):
    record = fix_front_uv0(source, destination)
    data = bytearray(Path(destination).read_bytes())
    size, _ = struct.unpack_from('<II', data, 12)
    doc = json.loads(data[20:20+size])
    binary_start = 28+size
    def accessor(index):
        a = doc['accessors'][index]
        view = doc['bufferViews'][a['bufferView']]
        assert a['componentType'] == 5126
        width = {'VEC2':2,'VEC3':3}[a['type']]
        return a['count'], binary_start+view.get('byteOffset',0)+a.get('byteOffset',0), view.get('byteStride',width*4)
    seen = set()
    changed_uv2 = 0
    rear_corners = 0
    rear_names = {'Bake_Shell_Wall_rear_left','Bake_Shell_Wall_rear_right','Bake_Shell_Wall_rear_door_header'}
    for node in doc['nodes']:
        if 'mesh' not in node:
            continue
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            attrs = primitive['attributes']
            if 'TEXCOORD_1' not in attrs:
                continue
            count, offset, stride = accessor(attrs['TEXCOORD_1'])
            if attrs['TEXCOORD_1'] not in seen:
                for index in range(count):
                    u,v = struct.unpack_from('<ff',data,offset+index*stride)
                    struct.pack_into('<ff',data,offset+index*stride,.005+.875*u,.005+.875*v)
                changed_uv2 += count
                seen.add(attrs['TEXCOORD_1'])
            if node['name'] not in rear_names or 'MATERIAL_REVISION' not in doc['materials'][primitive['material']]['name']:
                continue
            assert not node.get('rotation') and not node.get('matrix') and not node.get('scale')
            _,position_offset,position_stride = accessor(attrs['POSITION'])
            translation = node['translation']
            for index in range(count):
                x,y,_ = struct.unpack_from('<fff',data,position_offset+index*position_stride)
                x = round(x+translation[0],5)
                y = round(y+translation[1],5)
                struct.pack_into('<ff',data,offset+index*stride,.02+x/21.0*.61,.89+(1-y/3.4)*.09876)
                rear_corners += 1
    assert rear_corners == 18, rear_corners
    Path(destination).write_bytes(data)
    record.update({'changed_uv2_corners':changed_uv2,'rear_inner_corners_unified':rear_corners,
        'other_uv2_affine_gltf':{'scale':.875,'offset':[.005,.005]},
        'rear_continuous_chart_gltf':[.02,.89,.63,.98876],
        'scope':'Only front inner UV0 and UV2 attributes modified; positions/normals/nodes/images unchanged. Re-bake required.'})
    return record
