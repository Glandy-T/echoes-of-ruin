"""Verify GLB color maps are the unchanged v4 pixels and new UV2 exists."""
from pathlib import Path
import struct,json,io,hashlib
from PIL import Image
HERE=Path(__file__).resolve().parents[1];REPO=HERE.parents[3]
V4=REPO/'docs/art/experiments/room1_pod_volume_v4/textures'
def image(data):return Image.open(io.BytesIO(data)).convert('RGBA')
original={p.stem:Image.open(p).convert('RGBA') for p in V4.glob('*.png')}
rows=[]
for pose in ['closed','open']:
    path=REPO/'assets/art/room1_pod_room_v5'/f'pod_{pose}_v5.glb'
    raw=path.read_bytes();length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);binary=raw[28+length:]
    matches=[]
    for entry in doc['images']:
        view=doc['bufferViews'][entry['bufferView']];start=view.get('byteOffset',0);im=image(binary[start:start+view['byteLength']])
        found=[k for k,v in original.items() if im.size==v.size and im.tobytes()==v.tobytes()]
        assert len(found)==1,(entry,found);matches+=found
    assert set(matches)==set(original)
    primitives=[p for mesh in doc['meshes'] for p in mesh['primitives']]
    assert all('TEXCOORD_0' in p['attributes'] and 'TEXCOORD_1' in p['attributes'] for p in primitives)
    rows.append({'pose':pose,'glb_sha256':hashlib.sha256(raw).hexdigest(),'unchanged_v4_maps':matches,'primitives_with_uv0_uv2':len(primitives)})
(HERE/'source/assets_quality.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
print('ASSET_CHECK_PASS: both GLBs retain all eight v4 maps and UV0+UV2')
