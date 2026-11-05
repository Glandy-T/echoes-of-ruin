"""Focused response to quiet1 overcorrection; start from original A, not quiet1."""
from pathlib import Path
import json,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
name='mineral_a_middle'
jobs=json.loads((HERE/'requests.json').read_text())
if any(j['name']==name for j in jobs):
    print('Middle revision already prepared; retain job history.');raise SystemExit
guide=Image.open(HERE/'guide_mineral_a.png').convert('RGB')
guide.paste(Image.open(EXP/'raw/mineral_a.png').crop((0,0,192,256)).convert('RGB'),(0,0))
guide.save(HERE/f'guide_{name}.png')
shutil.copy2(HERE/'mask_mineral_a.png',HERE/f'mask_{name}.png')
prompt='''Targeted restrained edit of the EXISTING LEFT192x256 mineral texture, not a replacement design. IMPORTANT: preserve its original fine-grained, clustered mineral texture and visible material richness. The previous revision removed almost all texture and was rejected as an overcorrection. DO NOT make a near-solid gray image. Keep about seventy to eighty percent of the original material richness, small pixel clusters, patina shapes and fine aggregate coverage. ONLY soften the contrast of the larger dark blue-gray islands and the bright flecks by roughly thirty percent, drawing those extreme values toward the SAME existing mid-gray palette. Keep fine sandlike mineral grain distributed across the whole surface; subtle connected pixel clusters and moderate surface variation must be clearly visible at native size. Medium-low contrast, not blank flat paint and not high-contrast camouflage. This is gray matte mineral/ceramic composite used across a fire staircase and landings; not terrazzo or granite pebbles, not chipped paint. Keep the authored cluster scale and mean color. Retain quieter areas between clusters without emptying the texture. No new shapes, dirt borders, seams, tile pattern, stripes, machinery, cracks, text, rust, glow, directional lighting or gradient. Right64px is protected project-owned wall style context only; do not copy its seams. Flat native pixel-art albedo, no antialiasing or blur. Preserve detail; only moderate its contrast.'''
(HERE/f'prompt_{name}.txt').write_text(prompt,encoding='utf-8')
for j in jobs:
    if j.get('output_name',j['name'])=='mineral_a':j['adopted']=False
jobs.append({'name':name,'endpoint':'/inpaint-v3','prompt':f'prompt_{name}.txt','guide':f'guide_{name}.png','mask':f'mask_{name}.png','seed':2026110505,'native_size':[256,256],'retained_crop':[0,0,192,256],'output_name':'mineral_a','adopted':True})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
for role in ('overview','treads','landing'):
    shutil.copy2(EXP/'evidence'/f'material_{role}.png',EXP/'evidence'/f'too_quiet_{role}.png')
print('Prepared middle candidate from original A; quiet1 screenshots retained as rejected comparison.')
