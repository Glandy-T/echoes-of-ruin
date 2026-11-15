"""Keep base and PixelLab contact-age pixels in editable Aseprite layers."""
import argparse
import json
from pathlib import Path
import subprocess
from PIL import Image, ImageChops

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
ASSETS = ROOT/'assets/art/cryo_handrail_age_v2'
parser = argparse.ArgumentParser()
parser.add_argument('--aseprite', default='C:/文件类/Aseprite/Aseprite/aseprite.exe')
args = parser.parse_args()
placement = json.loads((HERE/'placement_manifest.json').read_text(encoding='utf8'))
output = ASSETS/'editable'
output.mkdir(exist_ok=True)
readbacks = ROOT/'.delivery_uploads/age_v2_aseprite_readbacks'
readbacks.mkdir(parents=True,exist_ok=True)
entries = []
for entry in placement['entries']:
    paths = entry['textures']
    stem = Path(paths['base']).stem.removesuffix('_atlas_base')
    entries.append({**paths, 'output':(output/(stem+'.aseprite')).relative_to(ROOT).as_posix(),
                    'readback':(readbacks/(stem+'.png')).relative_to(ROOT).as_posix()})
literal = '{\n' + ',\n'.join('{'+','.join(key+'='+json.dumps(value,ensure_ascii=False) for key,value in entry.items())+'}' for entry in entries) + '\n}'
lua = '''-- Generated from placement_manifest.json; no painted shapes are generated.
local entries = ENTRIES
local root = app.params.root
for _, entry in ipairs(entries) do
  local sprite = app.open(root .. '/' .. entry.base)
  sprite.layers[1].name = 'Original material - native atlas registration'
  local age = sprite:newLayer()
  age.name = 'PixelLab residue - registered structural regions'
  sprite:newCel(age, 1, Image{fromFile=root .. '/' .. entry.age}, Point(0,0))
  local edit = sprite:newLayer()
  edit.name = 'Aseprite local refinement - empty in v2'
  sprite:newCel(edit, 1, Image(sprite.width,sprite.height,ColorMode.RGB), Point(0,0))
  sprite:saveAs(root .. '/' .. entry.output)
  app.command.SaveFileAs{filename=root .. '/' .. entry.readback}
  sprite:close()
end
'''.replace('ENTRIES',literal)
(HERE/'package_editable.lua').write_text(lua,encoding='utf8')
subprocess.run([args.aseprite,'-b','--script-param','root='+ROOT.as_posix(),
                '--script',str(HERE/'package_editable.lua')],cwd=ROOT,check=True)
checks = []
for entry in entries:
    actual = Image.open(ROOT/entry['readback']).convert('RGBA')
    expected = Image.open(ROOT/entry['composite']).convert('RGBA')
    assert actual.size == expected.size
    diff = ImageChops.difference(actual,expected)
    max_difference = max(high for low,high in diff.getextrema())
    assert max_difference <= 1, (entry['output'],max_difference)
    checks.append({'master':entry['output'],'native_px':list(actual.size),
                   'max_composite_channel_difference':max_difference,
                   'local_refinement':'empty; registration and layering only'})
(HERE/'aseprite_readback.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('ASEPRITE_MASTERS_READBACK',len(checks))
