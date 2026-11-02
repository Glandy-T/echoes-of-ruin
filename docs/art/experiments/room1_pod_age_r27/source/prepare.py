"""Prepare owned structural guides at near-80px/m. No material art is painted here."""
from pathlib import Path
from PIL import Image
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
OLD=ROOT/'docs/art/experiments/room1_pod_pixellab_r16/source'
for name in ['raw','editable','evidence','source/layers']:(EXP/name).mkdir(parents=True,exist_ok=True)
TARGET=ROOT/'assets/art/room1_pod_age_r27';TARGET.mkdir(parents=True,exist_ok=True)
for name in ['pixellab_api.py','jobs.py']:
 text=(ROOT/'docs/art/experiments/room1_floor_detail_full_r26/source'/name).read_text(encoding='utf8').replace('R26_PIXELLAB_QUEUE_COMPLETE','R27_PIXELLAB_QUEUE_COMPLETE')
 (HERE/name).write_text(text,encoding='utf8')
sizes={'lid':(96,184),'shell_side':(184,56),'shell_end':(96,56)}
common=('Edit this OWN PROJECT flat UV ALBEDO into finished fine native pixel art for a low-poly cryogenic preservation pod. '
 'Keep EXACT existing panel outlines, seals, tiny service recesses and color zones: pale gray ivory ceramic composite and cooler blue-gray metal. '
 'Age must be CLEARLY READABLE at normal game distance after decades without maintenance, medium contrast, not almost-clean. '
 'Draw layered connected cool-gray residue and old coating wear with small/medium stepped pixel clusters and 1-3 pixel broken fringes. '
 'Surface history across the broad coating: shallow irregular related-tone patches and sparse small worn clusters, not only a dirty bottom edge. '
 'Put stronger old film at actual gasket contacts, undercuts, corners and service touch edges; retain intact coating between groups. '
 'No fine sprayed noise, giant peeling islands, thick dark frames, rust orange, yellow, green, blood, moss, cracks, holes, shiny PBR, cast light, gradients, shadows, perspective, new parts, new text or windows. '
 'This is a flat texture map, NOT a picture of a pod. Match the supplied subdued palette. Do not make blue-gray metal white. '
 'Black mask is precise protected structure/ID; WHITE is replaced with fresh material, not overlaid old grime. ')
details={
 'lid':'Cover UV, long axis vertical. Preserve the head end geometry cues and number 12 near the foot. Readable asymmetric age at shoulder/seal edges, some shallow material patches through the upper and middle main ceramic planes. No added square window, black inset, inner frame or large continuous border.',
 'shell_side':'Long casing UV, long axis horizontal. Keep the slate top shoulder, narrow existing recessed service strip, ceramic side field and lower support band. Age the upper ledge AND ceramic face and lower undercut with different groups. No lettering or repeated UNIT labels. Do not invent a new central compartment.',
 'shell_end':'Short end UV. Preserve the exact existing face and number 12. Small grouped coating changes in the upper and middle face, contact film under actual lip and at real corners, uneven lower deposits. No added screen, no black perimeter and no bright closed frame.'}
jobs=[];inputs=[]
for i,(role,size) in enumerate(sizes.items()):
 src=OLD/f'clean_{role}.png';guide=Image.open(src).convert('RGBA').resize(size,Image.Resampling.NEAREST)
 mask=Image.open(OLD/f'mask_{role}.png').convert('L').resize(size,Image.Resampling.NEAREST)
 guide.save(HERE/f'guide_{role}.png');mask.save(HERE/f'mask_{role}.png')
 identity=Image.open(OLD/f'identity_{role}.png').convert('RGBA').resize(size,Image.Resampling.NEAREST) if role!='shell_side' else Image.new('RGBA',size)
 identity.save(HERE/f'identity_{role}.png')
 prompt=common+details[role];assert len(prompt)<=2000
 (HERE/f'prompt_{role}.txt').write_text(prompt,encoding='utf8')
 jobs.append({'name':'lid_native_fix' if role=='lid' else role,'role':role,'endpoint':'/inpaint-v3','prompt':f'prompt_{role}.txt','guide':f'guide_{role}.png','mask':f'mask_{role}.png','seed':2026110210+i,'native_size':list(size)})
 inputs.append({'role':role,'source':src.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'native_size':list(size),'guide_only_nearest_registration':True,'creative_output_resizing':False,'third_party_input':False})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf8')
(HERE/'input_provenance.json').write_text(json.dumps(inputs,indent=2),encoding='utf8')
(EXP/'.gitignore').write_text('*.log\n*.log.*\n*.err\n*.blend1\n__pycache__/\nsource/balance_*.json\n',encoding='utf8')
print('R27_PREPARED',len(jobs),'native requests; estimate 30 generations; no paid calls made by prepare')
