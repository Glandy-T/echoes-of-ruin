"""Prepare three new native PixelLab wear distributions from the approved r27 art."""
from pathlib import Path
from PIL import Image
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
R27=ROOT/'docs/art/experiments/room1_pod_age_r27';TARGET=ROOT/'assets/art/room1_pod_age_full_r28'
for folder in ['raw','editable','evidence','source/layers']:(EXP/folder).mkdir(parents=True,exist_ok=True)
TARGET.mkdir(parents=True,exist_ok=True)
for name in ['pixellab_api.py','jobs.py']:
 (HERE/name).write_text((R27/'source'/name).read_text(encoding='utf8').replace('R27_PIXELLAB_QUEUE_COMPLETE','R28_PIXELLAB_QUEUE_COMPLETE'),encoding='utf8')
themes={
 'b':'A DIFFERENT age layout of equivalent strength: more small broken old seal-contact groups toward upper/left real junctions, thinner deposits at lower/right contacts; several shallow mid-face coating changes. Do not repeat the input wear silhouettes.',
 'c':'A DIFFERENT age layout of equivalent strength: irregular material groups toward right/end contacts and some short middle-field wear; upper/left coating remains more intact. Vary group spacing, breakpoints and outlines, not palette or pixel size.',
 'd':'A DIFFERENT age layout of equivalent strength: several separated contact-film groups near both real ends, some shallow center coating mottling and discontinuous lower-underlip age. Keep asymmetry and intact gaps, not a uniform border.'}
details={
 'lid':'Long axis vertical. Preserve the head end cues, ceramic panels, slate shoulders and exact number12 plate. Add no window or inner frame.',
 'shell_side':'Long axis horizontal. Keep the slate shoulder, service recess, pale ceramic field and lower support band. No lettering, new compartments or white recoloring of the blue-gray shoulder.',
 'shell_end':'Short end. Keep exact end face, ceramic/metal regions and number12 plate. No new screen, no closed bright outline or black perimeter.'}
common=('Create a NEW native pixel-art ALBEDO wear variation of this OWN PROJECT approved low-poly cryogenic pod texture. '
 'Match its exact muted ivory ceramic/cool blue-gray metal palette, material character, fine pixel scale and medium readable aging strength. '
 'Preserve all geometry cues and registered structure. Keep connected small/medium stepped clusters with 1-3 pixel broken fringes, and shallow related-tone variations across the main coating. '
 'Old film belongs to real gasket edges, undercuts, corners and maintenance contact areas, with uneven intact gaps. '
 'WHITE mask is fully replaced with NEW wear shapes, not an overlay of previous stains; BLACK protects exact structure/ID. '
 'Do NOT copy the guide stain silhouettes. Do not increase contrast, add giant peeling islands, random pepper noise, thick frames, cracks, holes, rust/yellow/green/brown, extra parts/text, shadows, reflections, glow, perspective or 3D scene drawing. '
 'Do not redraw or move panels and color zones. This is flat UV material, not a picture of a pod. ')
jobs=[];provenance=[]
for vi,(variant,theme) in enumerate(themes.items()):
 for ri,role in enumerate(['lid','shell_side','shell_end']):
  name=f'{variant}_{role}';src=ROOT/'assets/art/room1_pod_age_r27'/f'{role}.png';guide=Image.open(src).convert('RGBA')
  guide.save(HERE/f'guide_{name}.png');shutil.copy2(R27/'source'/f'mask_{role}.png',HERE/f'mask_{name}.png')
  prompt=common+details[role]+theme;assert len(prompt)<=2000
  (HERE/f'prompt_{name}.txt').write_text(prompt,encoding='utf8')
  jobs.append({'name':name,'role':role,'variant':variant,'endpoint':'/inpaint-v3','prompt':f'prompt_{name}.txt','guide':f'guide_{name}.png','mask':f'mask_{name}.png','seed':2026110240+vi*3+ri,'native_size':list(guide.size)})
  provenance.append({'name':name,'source':src.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'native_size':list(guide.size),'input_or_output_resizing':False,'third_party_input':False})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf8')
(HERE/'input_provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf8')
(EXP/'.gitignore').write_text('*.log\n*.log.*\n*.err\n*.blend1\n__pycache__/\nsource/balance_*.json\n',encoding='utf8')
print('R28_PREPARED',len(jobs),'native requests; estimate90 generations; A reuses approvedr27')
