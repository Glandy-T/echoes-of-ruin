"""Full-wall variants at the user-approved r23 density; no material art synthesis."""
from pathlib import Path
import json,shutil,hashlib
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
R23=ROOT/'docs/art/experiments/room1_wall_detail_r23'
WALL=ROOT/'docs/art/experiments/room1_wall_pixellab_r12/source'
LAMP=ROOT/'docs/art/experiments/room1_wall_lamp_r13/source'
for name in ['raw','editable','evidence','source/layers']:(EXP/name).mkdir(parents=True,exist_ok=True)
for name in ['jobs.py','pixellab_api.py']:shutil.copyfile(R23/'source'/name,HERE/name)
(HERE/'jobs.py').write_text((HERE/'jobs.py').read_text(encoding='utf-8').replace('R23_PIXELLAB_QUEUE_COMPLETE','R24_PIXELLAB_QUEUE_COMPLETE'),encoding='utf-8')
jobs=[];provenance=[]
base_prompt=(R23/'source/prompt_a.txt').read_text(encoding='utf-8').split('Variant A:')[0]
themes={
 'c':'New distribution C: connected moderate deposits at both top contacts; slightly denser at the left lower corner and fine joined fragments on the opposite side. Both bays need complete fine transitions.',
 'd':'New distribution D: denser broken clusters at the right upper contact and left-side lower contacts, with a different irregular edge silhouette. Match the same finished density in BOTH bays.',
 'e':'New distribution E: alternating short irregular seam-contact groups, medium deposits at lower-right and upper-left with finer satellite fragments attached to them; never weaken either bay.',
 'f':'New distribution F: more asymmetric little upper-corner groups and old lower-edge contact residue, different shapes on each bay but equally complete fine pixel transitions.',
 'g':'New distribution G: readable upper and lower contact accumulation with short broken branches along existing vertical shoulders; vary location and shape, keep both panels rich like the input.',
 'h':'New distribution H: several differently shaped connected corner deposits and fine discontinuous shoulder transitions, same overall age and completeness; neither bay may become a blank sparse variant.'
}
for i,(key,theme) in enumerate(themes.items()):
    source=R23/'raw'/('a.png' if i%2==0 else 'b.png')
    shutil.copyfile(source,HERE/f'guide_{key}.png');shutil.copyfile(R23/'source/mask.png',HERE/f'mask_{key}.png')
    prompt=base_prompt+theme;assert len(prompt)<=2000
    (HERE/f'prompt_{key}.txt').write_text(prompt,encoding='utf-8')
    jobs.append({'name':key,'endpoint':'/inpaint-v3','prompt':f'prompt_{key}.txt','guide':f'guide_{key}.png','mask':f'mask_{key}.png','seed':2026103440+i,'native_size':[256,256]})
    provenance.append({'name':key,'input':source.relative_to(ROOT).as_posix(),'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'approved_detail_baseline':'r23 A/B accepted by user','resampled':False})

# A single wide wall bay above/beside the opening. The actual opening is mesh;
# do not ask the model to design another door or inset frame in the wall image.
portal=Image.open(ROOT/'assets/art/room1_wall_lamp_r13/wall_rear.png').convert('RGBA').crop((688,16,944,272))
portal.save(HERE/'guide_portal.png')
mask=np.array(Image.open(LAMP/'mask_portal.png').convert('L'))
lamp=np.asarray(Image.open(LAMP/'rear_lamp_layer.png').convert('RGBA').crop((688,16,944,272)))[:,:,3]
mask[lamp>0]=0;mask[:,:2]=0;mask[:,-2:]=0;Image.fromarray(mask).save(HERE/'mask_portal.png')
prompt='''Edit this OWN PROJECT flat albedo material on ONE EXISTING WIDE CERAMIC WALL BAY, preserving its exact original construction. This is wall material, NOT a new door, plaque or object. Preserve ivory ceramic, cool-gray lower guard and the existing light band and outer seam cores. Maintain the input's finished fine pixel DETAIL DENSITY: connected medium old contact deposits, smaller broken clusters, fine 1-3 pixel fringe transitions at actual upper/side/lower construction contacts. Naturally thin into intact broad centers without making the bay blank. Reorganize the material wear into a NEW equally complete distribution; corners and shoulder contacts must retain readable layered information. Surface age must touch the real seam shoulder, no empty separator stripe. Keep exact native 256x256, no pixel enlargement. Absolutely NO second rectangle, inner rim, inset panel, new outline, bevel, groove, rounded internal corners, diagonal corner cuts, glass, screen, hardware or lettering anywhere inside this already-complete wall. Do not add a wall-wide dirt frame, cushion/vignette shading, lighting, gradients, giant patch, uniform pepper noise, random isolated stains, yellow, brown, rust, moss or cracks. This is intact matte ceramic with credible old contact film, not peeling paint. WHITE mask is material only; BLACK is exact protected structure. Fine crisp joined pixel art, same completeness at upper and lower contacts.'''
assert len(prompt)<=2000;(HERE/'prompt_portal.txt').write_text(prompt,encoding='utf-8')
jobs.append({'name':'portal','endpoint':'/inpaint-v3','prompt':'prompt_portal.txt','guide':'guide_portal.png','mask':'mask_portal.png','seed':2026103459,'native_size':[256,256]})
provenance.append({'name':'portal','input':'assets/art/room1_wall_lamp_r13/wall_rear.png crop [688,16,944,272]','approved_detail_baseline':'r23 richness, original project wide-bay geometry','resampled':False})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
baseline=json.loads((R23/'source/baseline_file_hashes.json').read_text())
for path in (ROOT/'assets/art/room1_wall_detail_r23').rglob('*.png'):baseline[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
(HERE/'baseline_file_hashes.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8')
(HERE/'input_provenance.json').write_text(json.dumps({'jobs':provenance,'reused_approved_originals':['r23/raw/a.png','r23/raw/b.png'],'third_party_images_submitted':False,'generation':'PixelLab inpaint-v3 only','scope':'four walls including wide portal bay; preserve existing lamps, geometry, UVs, camera, floor, pods, door and GI'},indent=2),encoding='utf-8')
print('R24_PREPARED',len(jobs),'new native256 jobs; expected70 generations; reuse two approved r23 originals')
