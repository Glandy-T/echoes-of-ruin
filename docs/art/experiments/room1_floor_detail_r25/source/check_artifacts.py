from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4];PATCH=(168,96,424,352)
checks={}
def check(k,v):checks[k]=bool(v);assert v,k
baseline=json.loads((HERE/'baseline_file_hashes.json').read_text())
for p,sha in baseline.items():check('unchanged '+p,hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha)
base=np.asarray(Image.open(ROOT/'assets/art/room1_pixel_unify_r22/floor_with_leaks.png').convert('RGBA'))
mask=np.asarray(Image.open(HERE/'mask_candidate.png').convert('L'))>0
for item in json.loads((HERE/'packages.json').read_text()):
 key=item['key'];image=np.asarray(Image.open(ROOT/item['output']).convert('RGBA'));readback=np.asarray(Image.open(HERE/f'readback_{key}.png').convert('RGBA'))
 fullmask=np.zeros(base.shape[:2],bool);fullmask[96:352,168:424]=mask
 check(key+' ASE exact',np.array_equal(image,readback));check(key+' unchanged exterior and footprint',np.array_equal(image[~fullmask],base[~fullmask]))
 source=np.asarray(Image.open(HERE/'original_project_r15_detail.png' if key=='reference' else EXP/'raw/candidate.png').convert('RGBA'))
 check(key+' raw exact native pixels',np.array_equal(image[96:352,168:424][mask],source[mask]))
 check(key+' opaque',bool((image[:,:,3]==255).all()));check(key+' output hash',hashlib.sha256((ROOT/item['output']).read_bytes()).hexdigest()==item['sha256'])
 check(key+' distinct sample',bool((image!=base).any()))
result=json.loads((EXP/'result_candidate.json').read_text());check('actual PixelLab completed',result['status']=='completed' and result['native_size']==[256,256])
(HERE/'artifact_validation.json').write_text(json.dumps({'result':'PASS','checks':checks,'immutable_files':len(baseline),'local_patch_px':PATCH,'editable_pixel_count':int(mask.sum()),'editable_masters':2,'new_API_jobs':1,'generations_used':result['usage']['generations'],'resampling':False,'procedural_or_hand_painted_material_art':False},indent=2),encoding='utf8')
print('R25_ARTIFACTS_PASS',len(checks),'checks')
