from pathlib import Path
from PIL import Image,ImageChops
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parents[3]
OLD=ROOT/'docs/art/experiments/room1_floor_contact_r8/source/floor_layers';NEW=HERE/'source/floor_layers'
records={}
for file in OLD.glob('*.png'):
    a=np.array(Image.open(file).convert('RGBA'));b=np.array(Image.open(NEW/file.name).convert('RGBA'))
    assert np.array_equal(a[:,:,3],b[:,:,3]),file.name
    records[file.name]={'alpha_exact_r8':True,'rgb_changes':int(np.any(a[:,:,:3]!=b[:,:,:3],axis=2).sum())}
for name in ['floor_coating','floor_perimeter_retention','floor_base_contacts','floor_leak_wicking','floor_leak_dark_film']:
    assert records[name+'.png']['rgb_changes']==0
assert (HERE/'source/pod_footprints.json').read_bytes()==(ROOT/'docs/art/experiments/room1_floor_contact_r8/source/pod_footprints.json').read_bytes()
maps={}
for name in ['floor_aged','floor_with_leaks']:
    path=ROOT/'assets/art/room1_floor_palette_r9'/(name+'.png')
    image=Image.open(path).convert('RGB');a=np.array(image)
    assert image.size==(1648,728)
    assert np.all(a[:,:,0]<=a[:,:,1]) and np.all(a[:,:,1]<=a[:,:,2]),'warm floor pixels remain'
    assert ImageChops.difference(image,Image.open(HERE/'source/readback'/(name+'.png')).convert('RGB')).getbbox() is None
    old=np.array(Image.open(ROOT/'assets/art/room1_floor_contact_r8'/(name+'.png')).convert('RGB'))
    maps[name]={'warm_green_over_blue_pixels_r8':int((old[:,:,1]>old[:,:,2]).sum()),'warm_green_over_blue_pixels_r9':0,'aseprite_reopen_exact':True,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
manifest_path=HERE/'source/floor_manifest.json';manifest=json.loads(manifest_path.read_text())
if 'leak_layers_preserved' in manifest:manifest['leak_layer_hashes']=manifest.pop('leak_layers_preserved')
manifest['leak_masks_preserved_from_r8']=True;manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
checks={'all_layer_alpha_masks_exact_r8':True,'footprints_exact_r8':True,'base_floor_rgb_unchanged':True,'palette_rule':'R <= G <= B for all floor output pixels; neutral/cool blue-gray, no yellow-green highlight ramp','layers':records,'maps':maps}
(HERE/'source/palette_check.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(json.dumps(checks))
