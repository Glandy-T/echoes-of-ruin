"""Prepare one focused PixelLab revision using owned inputs. No painted texture edits."""
from pathlib import Path
import json,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
name='mineral_a_quiet'
jobs=json.loads((HERE/'requests.json').read_text())
if any(j['name']==name for j in jobs):
    print('Revision already prepared; no changes.');raise SystemExit
guide=Image.open(HERE/'guide_mineral_a.png').convert('RGB')
guide.paste(Image.open(ROOT/'assets/art/cryo_stair_material_sample_v1/mineral_a.png').convert('RGB'),(0,0))
guide.save(HERE/f'guide_{name}.png')
shutil.copy2(HERE/'mask_mineral_a.png',HERE/f'mask_{name}.png')
prompt='''Edit ONLY the masked LEFT 192x256 pixel mineral material. The right64px is protected project-owned wall context. Keep the existing cool-neutral gray average color, native fine pixel size, and matte mineral/ceramic composite identity. The current material is TOO BUSY when repeated over stairs and landings: remove the broad dark blue-gray stain islands and most bright scattered flecks. Reduce visible patina coverage and highlight contrast substantially, by about two thirds. Aim for a calm continuous gray architectural surface, 85-90 percent quiet midtone area, with subtle small connected mineral pixel clusters and very sparse softer contact variation. Mineral grain is fine and low contrast, not terrazzo, granite stones or salt-and-pepper speckling. Small material variation should remain visible up close, but no large dramatic patches, no high-contrast white pixels, no dark islands, no mottled camouflage. Tread shape and step nosing supply the structure in 3D, so this texture should not compete with them. Flat albedo only, no gradients, shading, perspective, cast shadows, highlights, tiles, seams, frame, border dirt, text, machinery, rust or yellow. Keep pixel clusters crisp and deliberate, not blurry. Do not put the wall's panel joints or old paint onto the mineral texture. Keep borders naturally compatible for repeated mapping.'''
(HERE/f'prompt_{name}.txt').write_text(prompt,encoding='utf-8')
jobs[0]['adopted']=False
jobs.append({'name':name,'endpoint':'/inpaint-v3','prompt':f'prompt_{name}.txt','guide':f'guide_{name}.png','mask':f'mask_{name}.png','seed':2026110504,'native_size':[256,256],'retained_crop':[0,0,192,256],'output_name':'mineral_a','adopted':True})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
for role in ('overview','treads','landing'):
    shutil.copy2(EXP/'evidence'/f'material_{role}.png',EXP/'evidence'/f'before_quiet_{role}.png')
print('Prepared one targeted revision; preserved same-camera before images.')
