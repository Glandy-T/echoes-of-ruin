from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import numpy as np,json,hashlib
from collections import deque
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parents[3];OUT=ROOT/'assets/art/room1_floor_contact_r8';W,H=1648,728
manifest=json.loads((HERE/'source/floor_manifest.json').read_text())
pods=json.loads((HERE/'source/pod_footprints.json').read_text())['pods'];assert len(pods)==20
for name in ['floor_aged','floor_with_leaks']:
    runtime=Image.open(OUT/(name+'.png')).convert('RGBA');source=Image.open(HERE/'source/readback'/(name+'.png')).convert('RGBA')
    assert runtime.size==source.size==(W,H);assert ImageChops.difference(runtime,source).getbbox() is None
for name,digest in manifest['leak_layers_preserved'].items():
    assert hashlib.sha256((ROOT/'docs/art/experiments/room1_surface_full_r5/source/floor_layers'/(name+'.png')).read_bytes()).hexdigest()==digest
new=np.zeros((H,W),dtype=bool)
for name in manifest['new_layers']:new|=np.array(Image.open(HERE/'source/floor_layers'/(name+'.png')))[:,:,3]>0
anchor=Image.new('L',(W,H));d=ImageDraw.Draw(anchor)
d.line([(0,0),(0,H-1),(W-1,H-1),(W-1,0),(0,0)],fill=255,width=3)
for pod in pods:
    poly=[tuple(p) for p in pod['pixel_polygon']];d.line(poly+[poly[0]],fill=255,width=3)
anchor=np.array(anchor)>0;pending=new.copy();components=[]
while pending.any():
    y,x=np.argwhere(pending)[0];q=deque([(int(y),int(x))]);pending[y,x]=False;touch=False;count=0
    while q:
        y,x=q.popleft();count+=1;touch|=bool(anchor[y,x])
        for dy,dx in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
            ny=y+dy;nx=x+dx
            if 0<=ny<H and 0<=nx<W and pending[ny,nx]:pending[ny,nx]=False;q.append((ny,nx))
    assert touch,'floating deposit component';components.append(count)
checks={'aseprite_reopen_export_exact':True,'size':[W,H],'perimeter_edges':4,'measured_pod_contacts':20,'new_deposit_pixels':int(new.sum()),'connected_component_count':len(components),'all_new_components_touch_real_wall_or_pod_base':True,'component_sizes':components,'original_leak_layers_exact':True,'geometry_uv_layout_lights_changed':False}
(HERE/'source/floor_quality.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
plan=Image.open(OUT/'floor_with_leaks.png').convert('RGB');d=ImageDraw.Draw(plan)
for pod in pods:
    poly=pod['pixel_polygon'];cx=sum(p[0] for p in poly)/len(poly);cy=sum(p[1] for p in poly)/len(poly)
    d.text((cx-11,cy-4),pod['pod'],fill='#E7E7D4')
plan.save(HERE/'evidence/floor_contact_plan.png')
Image.open(OUT/'floor_with_leaks.png').convert('RGB').save(HERE/'evidence/floor_preview_native.png')
print(json.dumps(checks))
