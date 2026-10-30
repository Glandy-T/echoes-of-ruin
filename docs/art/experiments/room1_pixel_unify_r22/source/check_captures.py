"""Validate r22 capture coverage and comparable camera state."""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[5]
EVIDENCE=ROOT/'docs/art/experiments/room1_pixel_unify_r22/evidence'
records=json.loads((EVIDENCE/'capture_record.json').read_text(encoding='utf-8'))
by_name={item['file']:item for item in records}
errors=[]; checks={}
def check(name,passed):
    checks[name]=bool(passed)
    if not passed:errors.append(name)
def same_view(a,b):
    return (a['camera'],a['fov'],a['resolution'],a['p12_pose'])==(b['camera'],b['fov'],b['resolution'],b['p12_pose'])
check('all_pngs_1280x720',all(item['resolution']==[1280,720] for item in records))
check('static_screen_overlays_frozen_for_exact_readback',all(item.get('screen_overlays_frozen') is True for item in records))
for suffix in ['game_front_left_closed','game_front_middle_closed','game_front_right_closed','game_back_left_closed','game_back_middle_closed','game_back_right_closed','whole_room_closed','p12_oblique_closed','corner_rear_left','corner_rear_right','door_header','corner_front_left','corner_front_right','front_wall_lamp','floor_contacts','game_front_left_open','p12_oblique_open']:
    check('same_view_'+suffix,'1_'+suffix+'.png' in by_name and '2_'+suffix+'.png' in by_name and same_view(by_name['1_'+suffix+'.png'],by_name['2_'+suffix+'.png']))
for pod in range(1,21):check('candidate_pod_%02d'%pod,('2_pod_P%02d.png'%pod) in by_name)
for name in ['2_raw_p12_open.png','2_raw_corner_rear_left.png','2_denoised_p12_open.png','2_denoised_corner_rear_left.png','2_base_color_left_wall.png','2_base_color_front_wall.png','2_base_color_floor.png']:
    check('diagnostic_'+name,name in by_name)
base=EVIDENCE/'1_p12_oblique_closed.png'; repeated=EVIDENCE/'1_repeat_p12_oblique_closed.png'; restored=EVIDENCE/'1_restore_p12_closed.png'
restore_readback={}
if base.exists() and repeated.exists() and restored.exists():
    base_pixels=np.array(Image.open(base).convert('RGB'),dtype=np.int16)
    repeat_delta=np.array(Image.open(repeated).convert('RGB'),dtype=np.int16)-base_pixels
    restore_delta=np.array(Image.open(restored).convert('RGB'),dtype=np.int16)-base_pixels
    repeat_mask=np.any(repeat_delta!=0,axis=2);restore_mask=np.any(restore_delta!=0,axis=2)
    def detail(delta,mask):
        y,x=np.where(mask)
        return {'changed_pixels':int(mask.sum()),'bbox':[int(x.min()),int(y.min()),int(x.max()),int(y.max())] if x.size else None,'max_abs_rgb':np.abs(delta).max(axis=(0,1)).astype(int).tolist()}
    restore_readback={'baseline_repeat':detail(repeat_delta,repeat_mask),'restored':detail(restore_delta,restore_mask)}
    # The static screen labels are frozen above.  The remaining few changing
    # pixels are the asynchronous quarter-resolution screen-bloom chain.  Use
    # the immediately repeated A frame as an exact empirical mask: restoration
    # may differ only inside those same pixels and by no greater channel delta.
    # This still rejects the former 164,773-pixel room-surface darkening.
    check('baseline_repeat_only_static_screen_bloom',int(repeat_mask.sum())<=32 and restore_readback['baseline_repeat']['bbox']==[684,449,691,458])
    check('restore_exact_outside_measured_screen_bloom',not np.any(restore_mask & ~repeat_mask))
    check('restore_bloom_delta_within_baseline_repeat',np.all(np.abs(restore_delta).max(axis=(0,1))<=np.abs(repeat_delta).max(axis=(0,1))))
else:
    check('baseline_repeat_only_static_screen_bloom',False)
    check('restore_exact_outside_measured_screen_bloom',False)
    check('restore_bloom_delta_within_baseline_repeat',False)
report={'result':'PASS' if not errors else 'FAIL','errors':errors,'checks':checks,'capture_count':len(records),'restore_readback':restore_readback,'all_image_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(EVIDENCE.glob('*.png'))}}
(Path(__file__).with_name('capture_validation.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('R22_CAPTURE_CHECK',report['result'],'checks=',len(checks),'frames=',len(records),'errors=',errors)
raise SystemExit(0 if not errors else 1)
