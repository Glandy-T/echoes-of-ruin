"""Check real viewport outputs, controls and final room integration metadata."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parents[1]
def im(name):return np.asarray(Image.open(HERE/'evidence'/f'{name}.png').convert('RGB'))
def delta(a,b):
    d=np.abs(im(a).astype(int)-im(b).astype(int))
    return {'changed_pixels':int(np.any(d,axis=2).sum()),'max_channel_difference':int(d.max())}
runtime=json.loads((HERE/'evidence/runtime_readback.json').read_text())
assert runtime['state']=='open' and runtime['old_p12_hidden']
assert runtime['old_p12_collisions_removed']>0
assert not runtime['old_point_light_visible'] and runtime['old_point_light_energy']==0
assert abs(runtime['ambient_energy']-.025)<.000001 and runtime['strip_proxy_count']==0
assert runtime['screen_background_tint']=='526c76' and abs(runtime['screen_background_energy']-.8)<.00001
assert json.loads((HERE.parent/'room1_pod_standard_v8/runtime_check.json').read_text())['pass']
for record in json.loads((HERE/'evidence/capture_record.json').read_text()):
    assert (HERE/'evidence'/record['file']).is_file(),record['file']
files={}
for path in sorted((HERE/'evidence').glob('*.png')):
    assert Image.open(path).size==(1280,720)
    files[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
assert len({files[f'animation_{i:02}.png'] for i in range(11)})==11
controls={k:delta(*v) for k,v in {
    'screen_off_tubes_retained':('new_open','screen_off_tubes_on'),
    'tubes_off_screen_retained':('new_open','screen_on_tubes_off'),
    'independent_controls_restore':('new_open','open_controls_restored'),
    'glass_hidden':('glass_powered','glass_hidden_control'),
    'glass_tubes_off':('glass_powered','glass_tubes_off'),
    'glass_restore':('glass_powered','glass_restored'),
    'real_animation_endpoint':('new_open','real_animation_finished'),
    'screen_live_data':('screen_default_placeholder','screen_data_example'),
    'screen_bluegray_background':('screen_default_placeholder','screen_black_reference'),
    'screen_background_restore':('screen_default_placeholder','screen_background_restored')}.items()}
for key in ['screen_off_tubes_retained','tubes_off_screen_retained','glass_hidden','glass_tubes_off','screen_live_data','screen_bluegray_background']:
    assert controls[key]['changed_pixels']>0,key
for key in ['glass_restore','screen_background_restore']:
    assert controls[key]['changed_pixels']==0,(key,controls[key])
background={k:im(v)[285:310,750:850].mean(axis=(0,1)).round(2).tolist() for k,v in [('black_reference','screen_black_reference'),('bluegray','screen_default_placeholder')]}
assert np.mean(background['bluegray'])>np.mean(background['black_reference'])+10
result={'screenshots':files,'controls':controls,'background_sample_mean_rgb':background,'runtime':runtime,'animation_samples':11,'scope':'Actual Godot 1280x720. Tiny endpoint/global differences may include time-driven P02/P17 screen/bloom; counts retained without claiming exact whole-frame restoration.'}
(HERE/'source/capture_quality.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({'images':len(files),'controls':controls,'background':background},indent=2))
