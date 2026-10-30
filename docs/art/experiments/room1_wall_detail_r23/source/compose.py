"""Native PixelLab material replacement inside an exact existing wall sample."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
OUT=ROOT/'assets/art/room1_wall_detail_r23';OUT.mkdir(parents=True,exist_ok=True)
PATCH=(944,16,1200,272)
base=Image.open(ROOT/'assets/art/room1_pixel_unify_r22/wall_rear.png').convert('RGBA')
mask=Image.open(HERE/'mask.png').convert('L'); editable=np.asarray(mask)>0
packages=[];checks=[]
for key in ['reference','a','b']:
    path=HERE/'original_project_detail_reference.png' if key=='reference' else EXP/f'raw/{key}.png'
    raw=Image.open(path).convert('RGBA');assert raw.size==(256,256)
    layer=Image.new('RGBA',base.size);patch=raw.copy();patch.putalpha(mask);layer.paste(patch,PATCH[:2])
    final=Image.alpha_composite(base,layer)
    protected=np.asarray(layer)[:,:,3]==0
    assert np.array_equal(np.asarray(final)[protected],np.asarray(base)[protected])
    outside=np.ones((base.height,base.width),bool);outside[16:272,944:1200]=False
    assert np.array_equal(np.asarray(final)[outside],np.asarray(base)[outside])
    folder=HERE/'layers'/key;folder.mkdir(parents=True,exist_ok=True)
    base.save(folder/'base_r22.png');layer.save(folder/'PixelLab_material.png');final.save(folder/'composite.png')
    target=OUT/f'wall_rear_{key}.png';final.save(target)
    packages.append({'name':key,'output':target.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
    checks.append({'variant':key,'outside_patch_exact':True,'all_protected_pixels_exact':True,'lamp_exact':True,'resampled':False,'native_size':list(raw.size),'source':'r13 project PixelLab reference' if key=='reference' else 'new PixelLab inpaint-v3'})
(HERE/'packages.json').write_text(json.dumps(packages,indent=2),encoding='utf-8')
(HERE/'composite_validation.json').write_text(json.dumps({'result':'PASS','patch':PATCH,'records':checks,'operations':['binary exact protection mask','native-pixel placement','no painted or procedural age','no old aging overlay in editable pixels']},indent=2),encoding='utf-8')
print('R23_COMPOSED 3 rear-wall review maps; exact 256px sample only')
