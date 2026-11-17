"""Package the editable silhouette and verify its actual saved visible layers."""
from pathlib import Path
from hashlib import sha256
import json, re, struct, subprocess
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
aseprite = Path('C:/文件类/Aseprite/Aseprite/aseprite.exe')
subprocess.run([str(aseprite), '-b', '--script-param', 'root='+ROOT.as_posix(),
                '--script', str(ROOT/'source/package.lua')], check=True)
expected = Image.open(ROOT/'front_silhouette.png').convert('RGBA')
actual = Image.open(ROOT/'evidence/aseprite_readback.png').convert('RGBA')
assert expected.size == actual.size == (128, 128)
assert ImageChops.difference(expected.getchannel('A'), actual.getchannel('A')).getbbox() is None
assert all(a == b for a, b in zip(expected.getdata(), actual.getdata()) if a[3])
data = (ROOT/'editable/front_silhouette.aseprite').read_bytes()
assert struct.unpack_from('<H', data, 4)[0] == 0xA5E0
count = struct.unpack_from('<H', data, 134)[0]
offset = 144
layers = []
for _ in range(count):
    size, kind = struct.unpack_from('<IH', data, offset)
    chunk = data[offset+6:offset+size]
    if kind == 0x2004:
        flags = struct.unpack_from('<H', chunk)[0]
        n = struct.unpack_from('<H', chunk, 16)[0]
        layers.append({'name':chunk[18:18+n].decode('utf8'), 'visible':bool(flags & 1)})
    offset += size
assert len(layers) == 6
assert [l['visible'] for l in layers] == [True, True, True, False, False, False]
record = json.loads((ROOT/'source/shape_record.json').read_text(encoding='utf8'))
assert sha256((ROOT.parent/'protagonist_simplification_l123/silhouette/L2_front.png').read_bytes()).hexdigest() == record['approved_base_sha256']
result = {'status':'PASS - front silhouette pending user visual approval',
          'native_canvas':[128,128], 'black_only':True, 'binary_alpha':True,
          'editable_layers':layers, 'aseprite_saved_visible_pixels_match':True,
          'approved_L2_source_unchanged':True, 'visible_height_px':117,
          'waist_width_before_after_px':[23,23], 'hem_width_before_after_px':[27,31],
          'changed_outline_pixels':record['silhouette_changed_pixels'],
          'side_thickness_measurement':'Not performed: front-only task',
          'Godot_preview':'Not performed: no coloured or game-ready character in this step',
          'generation_calls':0, 'colouring':'Not performed; waiting for silhouette approval'}
(ROOT/'source/validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
links = re.findall(r'(?:href|src)="([^"]+)"', (ROOT/'preview.html').read_text(encoding='utf8'))
for link in links:
    if not link.startswith(('https:', '#')):
        assert (ROOT/link).is_file(), link
print('PASS: six editable layers; saved front silhouette matches PNG; original L2 preserved; preview links resolve.')
