"""Use supported 256px native canvases, retaining one common world pixel grid."""
from pathlib import Path
import json,shutil
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
jobs=json.loads((HERE/'requests.json').read_text())
if not (HERE/'requests_before_floor_resize.json').exists():
    (HERE/'requests_before_floor_resize.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
jobs=[j for j in jobs if j['name'] not in ['floor_1','floor_2'] and not j['name'].startswith('floor_tile_')]
floor=Image.open(ROOT/'assets/art/room1_floor_variants_r15/floor_with_leaks.png').convert('RGBA')
mask=Image.new('L',floor.size,255);d=ImageDraw.Draw(mask)
pods=json.loads((ROOT/'docs/art/experiments/room1_floor_variants_r15/source/pod_footprints.json').read_text())['pods']
for pod in pods:d.polygon([tuple(p) for p in pod['pixel_polygon']],fill=0)
prompt=(HERE/'prompt_floor_1.txt').read_text(encoding='utf-8')
records=[]
for row,ny in enumerate([0,108]):
    for col,nx in enumerate([0,192,384,568]):
        name=f'floor_tile_{row*4+col+1:02d}';x=nx*2;y=ny*2
        guide=floor.crop((x,y,x+512,y+512));full=mask.crop((x,y,x+512,y+512))
        guide.save(HERE/f'guide_full_{name}.png');full.save(HERE/f'mask_full_{name}.png')
        guide.resize((256,256),Image.Resampling.NEAREST).save(HERE/f'guide_{name}.png')
        low=np.asarray(full).reshape(256,2,256,2).min(axis=(1,3));Image.fromarray(low).save(HERE/f'mask_{name}.png')
        (HERE/f'prompt_{name}.txt').write_text(prompt,encoding='utf-8')
        jobs.append({'name':name,'endpoint':'/inpaint-v3','prompt':f'prompt_{name}.txt','guide':f'guide_{name}.png','mask':f'mask_{name}.png','seed':2026103100+row*4+col,'native_size':[256,256],'atlas_size':[512,512]})
        records.append({'name':name,'native_origin':[nx,ny],'row':row,'column':col,'native_size':[256,256]})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
(HERE/'floor_tile_layout.json').write_text(json.dumps({'native_canvas':[824,364],'grid_scale':2,'tiles':records,'reason':'Initial 448x364 edit failed: Tier 2 required; recorded USD usage 0.0. Subsequent requests use already proven 256px native canvases within existing plan. No subscription change.','initial_floor_2':'withdrawn before submission'},indent=2),encoding='utf-8')
print('R22_FLOOR_TILES_PREPARED',len(records),'world-aligned independent edits; active queue',len(jobs))
