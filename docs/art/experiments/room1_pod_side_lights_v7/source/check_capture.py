"""Validate actual distributed-light captures and preserved room settings."""
from pathlib import Path
import json,hashlib
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parents[1];REPO=HERE.parents[3]
def im(path):return np.asarray(Image.open(path).convert('RGB'))
def delta(a,b):
    d=np.abs(im(HERE/'evidence'/f'{a}.png').astype(int)-im(HERE/'evidence'/f'{b}.png').astype(int))
    return {'changed_pixels':int(np.any(d,axis=2).sum()),'max_channel_difference':int(d.max())}
runtime=json.loads((HERE/'evidence/runtime_readback.json').read_text())
assert runtime['chamber_proxies']['P12']=={'energy':0,'visible':False}
assert all(abs(runtime['chamber_proxies'][k]['energy']-.16)<.00001 for k in ['P02','P17'])
assert abs(runtime['ambient_energy']-.025)<.00001 and runtime['strip_proxy_count']==0
tubes=[r for r in runtime['fixtures'] if r['name'] in ['InnerTube_left','InnerTube_right']]
assert len(tubes)==4
assert all(abs(abs(t['position'][0])-.447)<.00001 and abs(t['position'][1]-.31)<.00001 and abs(t['size'][2]-1.7)<.00001 for t in tubes)
assert runtime['glass_shader']=='res://scripts/dev/room1_pod_volume_glass_v4.gdshader'
files={}
for file in sorted((HERE/'evidence').glob('*.png')):
    assert Image.open(file).size==(1280,720)
    files[file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
checks={k:delta(*v) for k,v in {
    'tube_off':('bed_and_side_tubes','bed_tubes_off_control'),
    'tube_restore':('bed_and_side_tubes','bed_tubes_restored'),
    'glass_hidden':('glass_powered','glass_hidden_control'),
    'inner_light_off':('glass_powered','glass_unpowered'),
    'reflection_off':('glass_powered','glass_no_reflection_control'),
    'glass_restore':('glass_powered','glass_restored')}.items()}
assert all(checks[k]['changed_pixels']>0 for k in ['tube_off','glass_hidden','inner_light_off','reflection_off'])
assert checks['glass_restore']['changed_pixels']==0
crop=[440,370,560,410]
bed={}
for key,path in [('v5_point',REPO/'docs/art/experiments/room1_pod_room_v5/evidence/new_close_open.png'),('v7_tubes',HERE/'evidence/new_open.png')]:
    a=im(path)[crop[1]:crop[3],crop[0]:crop[2]]
    bed[key]={'mean_rgb':a.mean(axis=(0,1)).round(2).tolist(),'max_rgb':a.max(axis=(0,1)).tolist(),'blue_white_pixels':int(((a[:,:,0]>=190)&(a[:,:,1]>=235)&(a[:,:,2]>=235)).sum())}
assert bed['v7_tubes']['blue_white_pixels']==0
result={'screenshots':files,'controls':checks,'runtime':runtime,'bed_comparison':{'same_camera_crop_xyxy':crop,'samples':bed},'limitations':'Tube restore may include tiny TIME-driven red-screen/bloom differences; exact counts reported. Body/UV2/HDR reused unchanged from v5; side-light transport is local line integration, not a new room GI bake.'}
(HERE/'source/quality_check.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({'controls':checks,'bed':bed},indent=2))
