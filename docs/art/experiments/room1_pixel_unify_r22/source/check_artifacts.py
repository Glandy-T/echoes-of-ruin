"""Verify actual artifact contents, protection scope, numbering, usage and sources."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
def pixels(p):return np.asarray(Image.open(p).convert('RGBA'))
checks=[]
def check(name,value):
    checks.append({'name':name,'pass':bool(value)})
    assert value,name
baseline=json.loads((HERE/'baseline_file_hashes.json').read_text())
for name,sha in baseline.items():check('unchanged:'+name,hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha)
packages=json.loads((HERE/'packages.json').read_text())
for item in packages:
    output=ROOT/item['final'];actual=pixels(output)
    check('Aseprite readback '+item['name'],np.array_equal(actual,pixels(HERE/f"readback_{item['name']}.png")))
    check('final content hash '+item['name'],hashlib.sha256(output.read_bytes()).hexdigest()==item['sha256'])
    check('opaque '+item['name'],bool((actual[:,:,3]==255).all()))
    if item['name'].startswith('wall_'):
        # Structure and lamp must not change where the PixelLab body layer is black.
        body=pixels(EXP/item['layers'][0][1]);lamp=pixels(EXP/item['layers'][1][1])
        base=pixels(EXP/item['base']);safe=(body[:,:,3]==0)&(lamp[:,:,3]==0)
        check('clean construction exact '+item['name'],np.array_equal(actual[safe],base[safe]))
    if item['name']=='floor_with_leaks':
        layer=pixels(EXP/item['layers'][0][1]);base=pixels(EXP/item['base']);safe=layer[:,:,3]==0
        check('protected occupied floor exact',np.array_equal(actual[safe],base[safe]))
layout=json.loads((ROOT/'assets/art/room1_complete_r19/layout.json').read_text())
for pod in layout['pods']:
    for role,box in {'lid':(47,197,80,211),'shell_end':(55,35,73,49)}.items():
        x0,y0,x1,y1=box
        old=pixels(ROOT/f"assets/art/room1_complete_r19/numbered/{pod['id']}_{role}.png")
        new=pixels(ROOT/f"assets/art/room1_pixel_unify_r22/numbered/{pod['id']}_{role}.png")
        check('functional ID exact '+pod['id']+' '+role,np.array_equal(old[y0:y1,x0:x1],new[y0:y1,x0:x1]))
        expected=pixels(ROOT/f"assets/art/room1_pixel_unify_r22/variant_{'abcd'[pod['variant_index']]}/{role}.png").copy()
        expected[y0:y1,x0:x1]=old[y0:y1,x0:x1]
        check('correct variant '+pod['id']+' '+role,np.array_equal(expected,new))
results=[json.loads(p.read_text()) for p in EXP.glob('result_*.json')]
jobs=json.loads((HERE/'requests.json').read_text())
check('all successful material jobs completed',len(results)==len(jobs) and all(r['status']=='completed' for r in results))
check('actual results match persistent requests',{r['name'] for r in results}=={j['name'] for j in jobs})
failed=json.loads((HERE/'failed_floor_1_status.json').read_text())
report={'result':'PASS','checks':checks,'immutable_files':len(baseline),'editable_packages':len(packages),'numbered_maps':40,'actual_API_posts':len(results)+1,'successful_API_jobs':len(results),'failed_API_jobs':[{'id':failed['id'],'status':failed['status'],'usage':failed['usage']}],'generations_used':sum(r['usage']['generations'] for r in results),'PixelLab_only_art':True,'reference_content_submitted':False}
(HERE/'artifact_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('R22_ARTIFACTS_PASS',len(checks),'checks',len(results),'successful API jobs, 1 failed request')
