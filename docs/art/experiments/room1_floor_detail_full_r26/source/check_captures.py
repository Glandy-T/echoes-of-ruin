from pathlib import Path
from PIL import Image
import json
import numpy as np

HERE=Path(__file__).resolve().parent
EXP=HERE.parent
records=json.loads((EXP/'evidence/capture_record.json').read_text(encoding='utf8'))
checks={}
assert len(records)==78,len(records)
assert len({record['file'] for record in records})==len(records),'duplicate capture record'
for record in records:
    image=Image.open(EXP/'evidence'/record['file'])
    checks[record['file']]={'size':list(image.size),'mode':record['mode'],'diagnostic':record['diagnostic'],'coverage':record['coverage']}
    assert image.size==(1280,720),record['file']
for mode in [1,2]:
    names={r['file'] for r in records if r['mode']==mode}
    for prefix in ['game_front_left','game_front_middle','game_front_right','game_back_left','game_back_middle','game_back_right','corner_front_left','corner_front_right','corner_rear_left','corner_rear_right','floor_topdown_unoccluded']:
        assert f'{mode}_{prefix}.png' in names,prefix
    for pod in [f'P{i:02d}' for i in range(1,21)]:assert f'{mode}_pod_contact_{pod}.png' in names,pod
    for leak in ['P03','P06','P13','P18']:assert f'{mode}_leak_{leak}.png' in names,leak
for extra in ['1_restore_game_floor_patch.png','2_base_color_floor_topdown.png','2_raw_floor_patch.png','2_denoised_floor_patch.png']:
    assert extra in checks,extra
for mode in [1,2]:assert f'{mode}_game_floor_patch_closed.png' in checks
topdown_names=['1_floor_topdown_unoccluded.png','2_floor_topdown_unoccluded.png','2_base_color_floor_topdown.png']
for name in topdown_names:
    record=next(r for r in records if r['file']==name)
    assert np.allclose(record['topdown_position'],[10.5,28.0,-4.75]),(name,record.get('topdown_position'))
    assert np.allclose(record['topdown_target'],[10.5,0.0,-4.74]),(name,record.get('topdown_target'))
    assert record['keep_width'] is True,(name,record.get('keep_width'))
    projected=record['projected_bounds_m']
    required=record['required_floor_bounds_m']
    assert projected[0] <= required[0] and projected[1] >= required[1],(name,projected,required)
    assert projected[2] <= required[2] and projected[3] >= required[3],(name,projected,required)
leak_cameras={
    'P03':([5.858,.02,-.767],[6.658,1.2,-.517]),
    'P06':([11.692,.02,-.769],[10.892,1.2,-.519]),
    'P13':([5.844,.02,-8.674],[6.644,1.2,-8.924]),
    'P18':([15.199,.02,-8.719],[14.399,1.2,-8.969]),
}
for mode in [1,2]:
    for pod,(target,position) in leak_cameras.items():
        record=next(r for r in records if r['file']==f'{mode}_leak_{pod}.png')
        assert np.allclose(record['leak_target'],target),(mode,pod,record.get('leak_target'))
        assert np.allclose(record['leak_camera_position'],position),(mode,pod,record.get('leak_camera_position'))
restored=np.asarray(Image.open(EXP/'evidence'/'1_restore_game_floor_patch.png').convert('RGBA'))
baseline=np.asarray(Image.open(EXP/'evidence'/'1_game_floor_patch_closed.png').convert('RGBA'))
assert np.array_equal(restored,baseline),'A/B/A floor restoration frame differs'
report={'result':'PASS','frames':len(records),'checks':checks,'restore_exact':True,'topdown_camera_verified':True,'leak_cameras_verified':True,'notes':'All normal images retain pods. Only floor_topdown_unoccluded temporarily hides pods and proxies; capture record flags it. Topdown metadata proves the intended camera projection contains the required floor bounds; actual border visibility remains a visual readback gate. Base-color and raw/denoised are diagnostics only.'}
(HERE/'capture_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('R26_CAPTURE_PASS',len(records))
