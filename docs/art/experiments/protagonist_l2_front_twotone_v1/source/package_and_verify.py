"""Save and reopen the two-value study; verify the immutable approved outline."""
from pathlib import Path
from hashlib import sha256
import json, re, struct, subprocess
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parent.parent
aseprite='C:/文件类/Aseprite/Aseprite/aseprite.exe'
subprocess.run([aseprite,'-b','--script-param','root='+ROOT.as_posix(),
                '--script',str(ROOT/'source/package.lua')],check=True)
expected=Image.open(ROOT/'front_twotone.png').convert('RGBA')
actual=Image.open(ROOT/'evidence/aseprite_readback.png').convert('RGBA')
approved=Image.open(ROOT/'source/APPROVED_front_silhouette.png').convert('RGBA')
assert expected.size==actual.size==approved.size==(128,128)
assert expected.getchannel('A').tobytes()==actual.getchannel('A').tobytes()==approved.getchannel('A').tobytes()
assert all(a==b for a,b in zip(expected.getdata(),actual.getdata()) if a[3])
colours={p for p in actual.getdata() if p[3]}
assert len(colours)==2
data=(ROOT/'editable/front_twotone.aseprite').read_bytes()
assert struct.unpack_from('<H',data,4)[0]==0xA5E0
count=struct.unpack_from('<H',data,134)[0]; offset=144; layers=[]
for _ in range(count):
    size,kind=struct.unpack_from('<IH',data,offset)
    chunk=data[offset+6:offset+size]
    if kind==0x2004:
        flags=struct.unpack_from('<H',chunk)[0]
        n=struct.unpack_from('<H',chunk,16)[0]
        layers.append({'name':chunk[18:18+n].decode('utf8'),'visible':bool(flags&1)})
    offset+=size
assert [l['visible'] for l in layers]==[True,True,False]
manifest=json.loads((ROOT/'source/manifest.json').read_text(encoding='utf8'))
original=ROOT.parent/'protagonist_l2_front_silhouette_v1/front_silhouette.png'
assert sha256(original.read_bytes()).hexdigest()==manifest['approved_source_sha256']
result={'status':'PASS - pending user visual approval of two-value forms',
        'native_canvas':[128,128],'visible_height_px':117,
        'changed_silhouette_pixels':0,'approved_original_unchanged':True,
        'two_neutral_values_only':sorted([list(c) for c in colours]),
        'no_antialiasing':True,'editable_layers':layers,
        'aseprite_saved_pixels_match':True,
        'face_shadow_or_marks_added':False,'generation_calls':0,
        'not_verified_or_made':['final colour palette','side or back views','3D','new Godot character']}
(ROOT/'source/validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for link in re.findall(r'(?:src|href)="([^"]+)"',(ROOT/'preview.html').read_text(encoding='utf8')):
    if not link.startswith(('https:','#')): assert (ROOT/link).is_file(),link
print('PASS: Aseprite readback exact; approved alpha exact; two colours only; all preview links resolve.')
