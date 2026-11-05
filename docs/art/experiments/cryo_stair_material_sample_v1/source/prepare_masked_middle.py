"""Bounded PixelLab correction: mask only three existing contrast islands, not whole texture."""
from pathlib import Path
import json,shutil
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
name='mineral_a_masked_middle'
jobs=json.loads((HERE/'requests.json').read_text())
if any(j['name']==name for j in jobs):
    print('Targeted request already recorded.');raise SystemExit
shutil.copy2(HERE/'guide_mineral_a_middle.png',HERE/f'guide_{name}.png')
mask=Image.new('L',(256,256),0)
draw=ImageDraw.Draw(mask)
for box in ((18,0,79,140),(0,173,103,244),(125,91,186,170)):
    draw.rectangle(box,fill=255)
mask.save(HERE/f'mask_{name}.png')
prompt='''Edit ONLY the THREE MASKED EXISTING CONTRAST PATCHES on the left mineral material. The rest is intentionally protected to retain the original fine grain and pixel-art richness. These patches are too dark or bright relative to the gray mineral background. Repaint each masked patch with the SAME finely textured matte mineral composite as its surrounding area, but reduce its original patch contrast by approximately one third to one half. Keep visible small native mineral pixel clusters and soft lower-contrast traces of the original patch shape; do not produce flat solid fills. Do not add random isolated speckles or new large dark islands. Blend exactly to the existing surrounding medium-gray palette and native cluster size. This is a restrained gray mineral/ceramic composite, neither polished metal nor chunky granite. Retain some patina rather than erasing age. No shading, illumination, gradients, frames, dirt borders, cracks, tiles, stripes, objects or text. Right64px is protected project-owned wall reference and not the target. Pixel art albedo, crisp native clusters, no blur. Most importantly, do visibly soften these few patches while leaving the unmasked fine grain unchanged.'''
(HERE/f'prompt_{name}.txt').write_text(prompt,encoding='utf-8')
for j in jobs:
    if j.get('output_name',j['name'])=='mineral_a':j['adopted']=False
jobs.append({'name':name,'endpoint':'/inpaint-v3','prompt':f'prompt_{name}.txt','guide':f'guide_{name}.png','mask':f'mask_{name}.png','seed':2026110506,'native_size':[256,256],'retained_crop':[0,0,192,256],'output_name':'mineral_a','adopted':True,'edit_scope':'three existing high-contrast patch bounds; no procedural art'})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
print('Prepared one targeted mask correction from original A; whole-image middle candidate not adopted.')
