from pathlib import Path
from PIL import Image
import json,hashlib,numpy as np,runpy
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4];TARGET=ROOT/'assets/art/room1_pod_age_full_r28'
runpy.run_path(str(HERE/'freeze_baseline.py'))
layout=json.loads((TARGET/'layout_variants.json').read_text());checks={};stats=[];sizes={'lid':(96,184),'shell_side':(184,56),'shell_end':(96,56)}
for role,size in sizes.items():
 hashes=[];arrays=[];mask=np.asarray(Image.open(ROOT/'docs/art/experiments/room1_pod_age_r27/source'/f'mask_{role}.png'))>0
 letters='abc' if role=='shell_end' else 'abcd'
 for v in letters:
  p=TARGET/f'variant_{v}'/f'{role}.png';a=np.asarray(Image.open(p).convert('RGBA'));arrays.append(a);hashes.append(hashlib.sha256(p.read_bytes()).hexdigest())
  checks[f'{v}_{role}_native']=Image.open(p).size==size
  checks[f'{v}_{role}_aseprite_readback']=np.array_equal(a,np.asarray(Image.open(HERE/f'readback_{v}_{role}.png').convert('RGBA')))
  checks[f'{v}_{role}_opaque']=bool(np.all(a[:,:,3]==255))
 checks[role+'_distinct_materials']=len(set(hashes))==len(letters)
 checks[role+'_A_exact_r27']=(TARGET/'variant_a'/f'{role}.png').read_bytes()==(ROOT/'assets/art/room1_pod_age_r27'/f'{role}.png').read_bytes()
 stats.append({'role':role,'fraction_changed_from_A_on_material_mask':{v:float(np.any(arrays[i]!=arrays[0],axis=2)[mask].mean()) for i,v in enumerate(letters) if v!='a'}})
checks['20_unique_combinations']=len({(p['lid_variant'],p['side_variant'],p['end_variant']) for p in layout['pods']})==20
checks['numbers_01_to_20']=[p['number'] for p in layout['pods']]==list(range(1,21))
for p in layout['pods']:
 for role,key in [('lid','lid_variant'),('shell_end','end_variant')]:
  image=np.asarray(Image.open(ROOT/p['maps'][role].removeprefix('res://')).convert('RGBA'));base=np.asarray(Image.open(TARGET/f"variant_{p[key]}"/f'{role}.png').convert('RGBA'));alpha=np.asarray(Image.open(HERE/'number_layers'/f"{p['id']}_{role}.png"))[:,:,3]
  checks[f"{p['id']}_{role}_outside_number_unchanged"]=np.array_equal(image[alpha==0],base[alpha==0])
  if p['id']=='P12':checks[role+'_P12_exact']=np.array_equal(image,np.asarray(Image.open(ROOT/'assets/art/room1_pod_age_r27'/f'{role}.png').convert('RGBA')))
usage=0;results=list(EXP.glob('result_*.json'))
for p in results:
 d=json.loads(p.read_text());checks[p.stem+'_actual_job']=d['status']=='completed' and bool(d['background_job_id']);usage+=d['usage']['generations']
checks['10_successful_calls']=len(results)==10;checks['100_generations']=usage==100
assert all(checks.values()),{k:v for k,v in checks.items() if not v}
(HERE/'artifact_validation.json').write_text(json.dumps({'result':'PASS','checks':checks,'variation_statistics':stats,'new_calls':len(results),'new_generations':usage,'independent_maps_per_role':{'lid':4,'shell_side':4,'shell_end':3},'reused_original_A_maps':3,'unique_pod_combinations':20,'numbered_exports':40,'local_paint_edits':0},indent=2),encoding='utf8')
print('R28_ARTIFACTS_PASS',len(checks),'checks;',usage,'generations')
