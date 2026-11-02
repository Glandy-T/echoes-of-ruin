from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,runpy
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
runpy.run_path(str(HERE/'freeze_baseline.py'))
checks={};usage=0
for role,size in {'lid':(96,184),'shell_side':(184,56),'shell_end':(96,56)}.items():
 target=Image.open(ROOT/'assets/art/room1_pod_age_r27'/f'{role}.png').convert('RGBA');readback=Image.open(HERE/f'readback_{role}.png').convert('RGBA')
 checks[role+'_size']=target.size==size
 checks[role+'_aseprite_readback']=np.array_equal(np.asarray(target),np.asarray(readback))
 checks[role+'_opaque']=bool(np.all(np.asarray(target)[:,:,3]==255))
 checks[role+'_editable']=(EXP/'editable'/f'{role}_r27.aseprite').stat().st_size>0
for path in EXP.glob('result_*.json'):
 result=json.loads(path.read_text());checks[path.stem+'_real_job']=result['status']=='completed' and bool(result['background_job_id']);usage+=result['usage']['generations']
checks['four_successful_calls']=len(list(EXP.glob('result_*.json')))==4
checks['usage_40']=usage==40
blend=json.loads((HERE/'blender_readback.json').read_text());checks['blend_scope']=blend['result']=='PASS' and len(blend['changes'])==3 and {c['role'] for c in blend['changes']}=={'lid','shell_side','shell_end'}
checks['blend_dependencies']=not blend['missing'] and not blend['absolute_paths']
assert all(checks.values()),{k:v for k,v in checks.items() if not v}
(HERE/'artifact_validation.json').write_text(json.dumps({'result':'PASS','checks':checks,'usage_generations':usage,'successful_calls':4,'final_selected_outputs':3,'Aseprite_local_paint_edits':0,'note':'Independent local refinement layer retained empty; structure and ID registration only. Existing GI not rebaked.'},indent=2),encoding='utf8')
print('R27_ARTIFACTS_PASS',len(checks),'checks;',usage,'generations')
