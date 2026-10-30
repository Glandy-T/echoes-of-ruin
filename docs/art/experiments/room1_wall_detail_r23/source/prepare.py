"""Owned project inputs; PixelLab revises all editable material at native resolution."""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
R22=ROOT/'docs/art/experiments/room1_pixel_unify_r22/source'
WALL=ROOT/'docs/art/experiments/room1_wall_pixellab_r12/source'
LAMP=ROOT/'docs/art/experiments/room1_wall_lamp_r13/source'
PATCH=(944,16,1200,272)
for n in ['raw','editable','evidence','source/layers']:(EXP/n).mkdir(parents=True,exist_ok=True)
for name in ['jobs.py','pixellab_api.py']:shutil.copyfile(R22/name,HERE/name)
(HERE/'jobs.py').write_text((HERE/'jobs.py').read_text(encoding='utf-8').replace('R22_PIXELLAB_QUEUE_COMPLETE','R23_PIXELLAB_QUEUE_COMPLETE'),encoding='utf-8')
reference=Image.open(ROOT/'assets/art/room1_wall_lamp_r13/wall_rear.png').convert('RGBA').crop(PATCH)
reference.save(HERE/'original_project_detail_reference.png')
clean=Image.open(WALL/'clean_rear.png').convert('RGBA').crop(PATCH);clean.save(HERE/'clean_construction.png')
current=Image.open(ROOT/'assets/art/room1_pixel_unify_r22/wall_rear.png').convert('RGBA').crop(PATCH);current.save(HERE/'rejected_sparse_r22.png')
mask=np.array(Image.open(WALL/'mask.png').convert('L'))
lamp=Image.open(LAMP/'rear_lamp_layer.png').convert('RGBA').crop(PATCH);lamp.save(HERE/'retained_lamp_RGBA.png')
mask[np.asarray(lamp)[:,:,3]>0]=0;mask[:,:2]=0;mask[:,-2:]=0
Image.fromarray(mask).save(HERE/'mask.png')
common='''Edit this OWN PROJECT wall albedo into a NEW, equally finished pixel-art material variant. Keep exact existing two flat wall bays, seams, lamp, lower guard, ivory ceramic and cool-gray metal. Preserve the input's readable material DETAIL DENSITY and layered edge transitions; do not simplify it into a blank wall. Keep the same native 256x256 canvas, NO coarse pixel enlargement. Each real upper corner, vertical joint shoulder and lower contact needs an irregular connected group of age, with medium-sized deposits, smaller broken clusters and fine 1-3 pixel fringe transitions that gradually thin into the intact broad face. Give the real seam shoulders and lamp-slot/base contacts sufficient nearby material information, not just a black core and a few isolated dots. Broad centers remain intact, with very subtle material tone variation; no giant stains or face-wide shading. Make a coherent NEW distribution comparable in completeness to the supplied original, not a copy or a weaker sparse version. Surface age attaches directly to real construction contacts with natural gaps, never an empty stripe between the seam and deposit. No new inner frame, inset rim, bevel, glass, hardware, text, perspective, rendered lighting, gradients, random pepper noise, uniform spray, cracks, peeling wall-wide band, white outline, yellow, brown, rust or moss. BLACK mask is protected construction, WHITE is material replacement. Crisp native pixel clusters and fine fragmented boundaries; no blurry airbrush. '''
jobs=[]
for i,key in enumerate(['a','b']):
    reference.save(HERE/f'guide_{key}.png')
    prompt=common+['Variant A: medium uneven deposits at the upper-left and lower-right contacts, and finer joined clusters at the opposite contacts; keep BOTH bays comparably finished.','Variant B: shift the denser contact groups to upper-right and lower-left, with differently broken edges and gentle asymmetry; keep the SAME overall richness and restrained contrast as A.'][i]
    assert len(prompt)<=2000
    (HERE/f'prompt_{key}.txt').write_text(prompt,encoding='utf-8')
    jobs.append({'name':key,'endpoint':'/inpaint-v3','prompt':f'prompt_{key}.txt','guide':f'guide_{key}.png','mask':'mask.png','seed':2026103340+i,'native_size':[256,256]})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
baseline=json.loads((R22/'baseline_file_hashes.json').read_text())
for path in (ROOT/'assets/art/room1_pixel_unify_r22').rglob('*.png'):
    baseline[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
for name in ['scripts/dev/room1_pixel_unify_r22.gd','scripts/dev/capture_room1_pixel_unify_r22.gd']:
    baseline[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
(HERE/'baseline_file_hashes.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8')
(HERE/'input_provenance.json').write_text(json.dumps({'original_project_input':'assets/art/room1_wall_lamp_r13/wall_rear.png','original_pixel_art_source':'PixelLab r11/r12 material and r13 lamp','patch':PATCH,'world_sample':'rear wall x=12.0..15.2m; z=-9.3m','native_size':[256,256],'resampling':False,'retained_construction':'r12 clean rear wall + exact r13 lamp; no old aging under the editable replacement','third_party_content_submitted':False,'Pixel_Canals':'human technical reference only, NoAI content not submitted','scope':'two wall bays only; all other r22 materials, shaders, GI, models, layout untouched'},indent=2),encoding='utf-8')
print('R23_PREPARED 2 native 256px PixelLab revisions; estimated 20 generations')
