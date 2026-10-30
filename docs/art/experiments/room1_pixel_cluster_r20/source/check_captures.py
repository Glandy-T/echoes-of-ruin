"""Read back real screenshots and require identical camera settings per comparison."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;E=EXP/'evidence'
records=json.loads((E/'capture_record.json').read_text());index={r['file']:r for r in records}
checks={};differences={}
for view in ['gameplay_distance','left_distance','p12','left_bay']:
    for pose in ['closed','open']:
        suffix=f'{view}_{pose}.png';rows=[index[f'{mode}_{suffix}'] for mode in [1,2,3]]
        for field in ['camera','fov','resolution','p12_pose']:
            checks[f'{suffix}_{field}_identical']=all(r[field]==rows[0][field] for r in rows)
        images=[np.array(Image.open(E/r['file']).convert('RGB')) for r in rows]
        checks[f'{suffix}_1280x720']=images[0].shape[:2]==(720,1280)
        for a,b,label in [(0,1,'A_B'),(1,2,'B_C')]:
            count=int(np.any(images[a]!=images[b],axis=2).sum())
            differences[f'{suffix}_{label}']=count
            checks[f'{suffix}_{label}_actually_differs']=count>0
restored=np.array(Image.open(E/'1_restore_p12_closed.png').convert('RGBA'))
original=np.array(Image.open(E/'1_p12_closed.png').convert('RGBA'))
checks['A_restored_pixel_exact']=bool(np.array_equal(restored,original))
for mode in [1,2,3]:
    checks[f'{mode}_technical_near_not_game_follow']=index[f'{mode}_p12_closed.png']['camera']!=index[f'{mode}_gameplay_distance_closed.png']['camera']
failures=[key for key,value in checks.items() if not value]
report={'result':'PASS' if not failures else 'FAIL','checks':checks,'failures':failures,'comparison_changed_pixels':differences,'screenshots':len(records),'capture_sha256':{r['file']:hashlib.sha256((E/r['file']).read_bytes()).hexdigest() for r in records}}
(HERE/'visual_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert not failures,failures
print('R20_CAPTURE_VALIDATION_PASS',len(checks),'checks,',len(records),'screenshots')
