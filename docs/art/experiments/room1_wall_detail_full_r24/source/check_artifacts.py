from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
checks={}
def check(name,value):checks[name]=bool(value);assert value,name
baseline=json.loads((HERE/'baseline_file_hashes.json').read_text())
for path,sha in baseline.items():check('immutable:'+path,hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha)
for item in json.loads((HERE/'packages.json').read_text()):
    wall=item['wall'];current=ROOT/item['output']
    final=np.asarray(Image.open(current).convert('RGBA'));readback=np.asarray(Image.open(HERE/f'readback_{wall}.png').convert('RGBA'))
    base=np.asarray(Image.open(ROOT/f'assets/art/room1_pixel_unify_r22/wall_{wall}.png').convert('RGBA'))
    layer=np.asarray(Image.open(HERE/f'layers/{wall}/PixelLab_all_new_material.png').convert('RGBA'))
    safe=layer[:,:,3]==0
    check('ASE exact '+wall,np.array_equal(final,readback));check('protected structure exact '+wall,np.array_equal(final[safe],base[safe]));check('opaque '+wall,bool((final[:,:,3]==255).all()))
    check('final hash '+wall,hashlib.sha256(current.read_bytes()).hexdigest()==item['sha256'])
    check('binary replacement mask '+wall,set(np.unique(layer[:,:,3])).issubset({0,255}))
assembly=json.loads((HERE/'assembly.json').read_text())
for wall,item in assembly['wall_placements'].items():
    check('unique half panels '+wall,item['no_repeated_half_panel_on_same_wall']);check('different adjacent pair '+wall,item['adjacent_pairs_different'])
results=[json.loads(p.read_text()) for p in EXP.glob('result_*.json')];jobs=json.loads((HERE/'requests.json').read_text())
check('real completed API jobs',len(results)==len(jobs) and all(r['status']=='completed' for r in results))
report={'result':'PASS','checks':checks,'immutable_files':len(baseline),'editable_masters':4,'new_API_jobs':len(results),'generations_used':sum(r['usage']['generations'] for r in results),'approved_r23_original_pairs_reused':2,'new_material_pair_originals':6,'portal_originals':1,'creative_material_pixels':'PixelLab only'}
(HERE/'artifact_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('R24_ARTIFACTS_PASS',len(checks),'checks',report['generations_used'],'generations')
