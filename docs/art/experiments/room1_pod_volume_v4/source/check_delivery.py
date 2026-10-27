"""Verify editable exports, embedded GLB textures and screenshot controls."""
from pathlib import Path
import json, struct, io, hashlib
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[3]
KEYS=['lid','shell_side','shell_end','interior','mattress','glass','display','section']
def pixels(path): return Image.open(path).convert('RGBA')
def same(a,b): return a.size==b.size and a.tobytes()==b.tobytes()
def main():
    result={'editable_readback':{},'glb_embedded_textures':{},'screenshots':{}}
    canonical={k:pixels(ROOT/'textures'/f'{k}.png') for k in KEYS}
    for key in KEYS:
        result['editable_readback'][key]={'size':list(canonical[key].size),'exact':same(canonical[key],pixels(ROOT/'source/readback'/f'{key}.png'))}
    for pose in ['closed','open']:
        path=REPO/'assets/art/room1_pod_volume_v4'/f'pod_{pose}_v4.glb'
        raw=path.read_bytes(); n=struct.unpack_from('<I',raw,12)[0]; doc=json.loads(raw[20:20+n]); binary=raw[28+n:]
        rows=[]
        for entry in doc.get('images',[]):
            view=doc['bufferViews'][entry['bufferView']]; start=view.get('byteOffset',0)
            im=Image.open(io.BytesIO(binary[start:start+view['byteLength']])).convert('RGBA')
            matches=[k for k,v in canonical.items() if same(im,v)]
            rows.append({'image':entry.get('name',''),'matches':matches})
        assert set(k for row in rows for k in row['matches'])==set(KEYS),rows
        result['glb_embedded_textures'][pose]=rows
    evidence=ROOT/'evidence'
    for file in sorted(evidence.glob('*.png')):
        im=Image.open(file); assert im.size==(1280,720)
        result['screenshots'][file.stem]={'size':list(im.size),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
    a=pixels(evidence/'new_glass_powered.png'); b=pixels(evidence/'new_glass_restored.png')
    result['glass_restore_exact']=same(a,b)
    result['glass_control_changed']={key:not same(a,pixels(evidence/f'{key}.png')) for key in ['new_glass_removed_control','new_glass_unpowered','new_glass_no_reflection_control']}
    result['glass_texture_alpha_range']=list(canonical['glass'].getchannel('A').getextrema())
    assert all(v['exact'] for v in result['editable_readback'].values())
    assert result['glass_restore_exact'] and all(result['glass_control_changed'].values())
    (ROOT/'source/quality_check.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('DELIVERY_CHECK_PASSED: eight editable readbacks, both GLBs, 1280x720 captures and glass controls')
if __name__=='__main__':main()
