"""Check actual Room 1 capture dimensions, independent controls and bindings."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parents[1]
def im(name):return np.asarray(Image.open(HERE/'evidence'/f'{name}.png').convert('RGB'))
def diff(a,b):
    delta=np.abs(im(a).astype('int16')-im(b).astype('int16'))
    return {'changed_pixels':int(np.any(delta,axis=2).sum()),'max_channel_difference':int(delta.max())}
def main():
    evidence=HERE/'evidence'; records=json.loads((evidence/'capture_record.json').read_text())
    runtime=json.loads((evidence/'runtime_readback.json').read_text())
    assert runtime['strip_proxy_light_count']==0
    assert abs(runtime['ambient_energy']-.025)<.00001
    assert runtime['pixel_size']==[1280,720]
    assert all(m['expected']==m['bound'] for m in runtime['pod_maps'])
    files={}
    for path in sorted(evidence.glob('*.png')):
        assert Image.open(path).size==(1280,720)
        files[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    rows={r['file']:r for r in records}
    base=rows['glass_powered.png']
    for key,changed in [('glass_hidden_control.png','glass'),('glass_unpowered.png','window_power'),('glass_no_reflection_control.png','reflection')]:
        for control in ['new_pod','open','glass','reflection','window_power','local_light','strip','base_color','camera','fov']:
            if control!=changed:assert rows[key][control]==base[control],(key,control)
    checks={
       'glass_hidden':diff('glass_powered','glass_hidden_control'),
       'glass_inner_light_off':diff('glass_powered','glass_unpowered'),
       'glass_reflection_off':diff('glass_powered','glass_no_reflection_control'),
       'glass_restore':diff('glass_powered','glass_restored'),
       'closed_base_color_restore':diff('new_side_closed','new_side_closed_restored'),
       'open_base_color_restore':diff('new_side_open','new_side_open_restored'),
       'strip_light_off':diff('new_close_open','strip_off_control'),
       'strip_light_restore':diff('new_close_open','strip_restored'),
       'original_room_baseline':diff('original_r9_baseline','old_game_open'),
       'old_pod_restore':diff('old_game_open','old_game_restored')}
    assert all(checks[k]['changed_pixels']>0 for k in ['glass_hidden','glass_inner_light_off','glass_reflection_off','strip_light_off'])
    (HERE/'source/capture_quality.json').write_text(json.dumps({'files':files,'controls':checks,'runtime':runtime,'scope':str(len(files))+' actual Godot screenshots; original room comparison may include TIME-driven P02/P17 red-screen changes, reported without claiming bit-exact restoration.'},indent=2),encoding='utf8')
    print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
