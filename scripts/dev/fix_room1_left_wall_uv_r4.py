"""Repair only the baked left wall color UVs; keep geometry and UV2 exact."""
import json
import struct
from pathlib import Path

root = Path(__file__).resolve().parents[2]
folder = root / 'assets/art/room1_continuous_bake_r3'
source = folder / 'room1_baked_uv2_r3.glb'
target = folder / 'room1_baked_uv2_r4_uv_fixed.glb'
raw = source.read_bytes()
json_length = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + json_length])
offset = 20 + json_length
binary_length = struct.unpack_from('<I', raw, offset)[0]
binary = bytearray(raw[offset + 8:offset + 8 + binary_length])
before_binary = bytes(binary)
changed = 0
for node in doc['nodes']:
    if node.get('name') != 'Bake_Shell_Wall_left':
        continue
    for primitive in doc['meshes'][node['mesh']]['primitives']:
        accessor = doc['accessors'][primitive['attributes']['TEXCOORD_0']]
        view = doc['bufferViews'][accessor['bufferView']]
        start = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
        stride = view.get('byteStride', 8)
        values = [struct.unpack_from('<2f', binary, start + i * stride) for i in range(accessor['count'])]
        if min(v for u, v in values) < 0.99 or max(v for u, v in values) > 2.001:
            continue
        assert accessor['componentType'] == 5126 and accessor['type'] == 'VEC2'
        for index, (u, v) in enumerate(values):
            struct.pack_into('<f', binary, start + index * stride + 4, v - 1.0)
            changed += 1
        if 'min' in accessor:
            accessor['min'][1] -= 1.0
            accessor['max'][1] -= 1.0
        # All static lightmap coordinates remain bit-identical.
        uv2 = doc['accessors'][primitive['attributes']['TEXCOORD_1']]
        uv2_view = doc['bufferViews'][uv2['bufferView']]
        uv2_start = uv2_view.get('byteOffset', 0) + uv2.get('byteOffset', 0)
        uv2_stride = uv2_view.get('byteStride', 8)
        for index in range(uv2['count']):
            begin = uv2_start + index * uv2_stride
            assert binary[begin:begin + 8] == before_binary[begin:begin + 8]
assert changed > 0
encoded = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
encoded += b' ' * ((-len(encoded)) % 4)
length = 12 + 8 + len(encoded) + 8 + len(binary)
target.write_bytes(struct.pack('<III', 0x46546C67, 2, length) + struct.pack('<II', len(encoded), 0x4E4F534A) + encoded + struct.pack('<II', len(binary), 0x004E4942) + binary)
(folder / 'left_wall_uv_fix_r4.json').write_text(json.dumps({'changed_uv_vertices': changed, 'left_wall_v_before': [1.0, 2.0], 'left_wall_v_after': [0.0, 1.0], 'uv2_bit_identical': True, 'geometry_unchanged': True, 'textures_unchanged': True, 'scope': 'Bake conversion V sign error fixed; solid material surface untouched; old asset preserved.'}, indent=2), encoding='utf-8')
print('LEFT_WALL_UV_FIXED', changed, target)
