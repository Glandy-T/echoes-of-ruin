"""Validate the focused GPU isolation sequence for the r22 A/B restore fix."""
from pathlib import Path
import hashlib, json

HERE=Path(__file__).resolve().parent
EVIDENCE=HERE.parent/'evidence'/'restore_diagnosis'
records=json.loads((EVIDENCE/'state_record.json').read_text(encoding='utf-8'))
by_name={row['file']:row for row in records}
checks={};errors=[]
def check(name,value):
    checks[name]=bool(value)
    if not value:errors.append(name)
def digest(name):return hashlib.sha256((EVIDENCE/name).read_bytes()).hexdigest()

baseline='00_a_start.png'
for name in ['01_a_repeat.png','03_a_after_material_switch.png','05_a_after_open_close.png','07_a_after_b_open_close.png','08_a_final_repeat.png','09_a_after_room_camera_sweep.png','10_a_after_pod_camera_sweep.png']:
    check('pixel_exact_'+name,digest(name)==digest(baseline))
check('B_closed_differs',digest('02_b_closed.png')!=digest(baseline))
check('B_open_differs',digest('06_b_open.png')!=digest('04_a_open.png'))
for row in records:
    state=row['state'];opened=state['pose']=='open'
    check('pose_state_'+row['file'],state['pod_pose_blend']==(1.0 if opened else 0.0) and state['room_pose_blend']==(1.0 if opened else 0.0))
    check('r19_GI_paths_'+row['file'],state['closed_irradiance'].endswith('/P12_closed.exr') and state['open_irradiance'].endswith('/P12_open.exr') and state['strip_irradiance'].endswith('/room_closed.exr') and state['strip_irradiance_open'].endswith('/room_open.exr'))
report={'result':'PASS' if not errors else 'FAIL','errors':errors,'checks':checks,'frames':len(records),'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(EVIDENCE.glob('*.png'))}}
(HERE/'restore_diagnosis_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('R22_RESTORE_DIAGNOSIS',report['result'],'checks=',len(checks),'frames=',len(records),'errors=',errors)
raise SystemExit(0 if not errors else 1)
