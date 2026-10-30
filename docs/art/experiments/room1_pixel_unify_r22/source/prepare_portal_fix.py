"""Prepare a new PixelLab wall-only request after rejecting an invented inner frame."""
from pathlib import Path
import json,shutil
HERE=Path(__file__).resolve().parent
for stem in ['guide','mask','guide_full','mask_full']:
    shutil.copyfile(HERE/f'{stem}_portal.png',HERE/f'{stem}_portal_fix.png')
prompt='Flat albedo MATERIAL ONLY on ONE EXISTING WIDE FLAT CERAMIC WALL BAY. This image is not a door, window, plaque, cushion or a new object. The original guide is already the COMPLETE construction. Preserve exact existing outer seams, upper narrow light strip, lower metal guard and warm ivory / cool gray colors. Draw NO inner border, outline, rectangle, inset rim, groove, rounded corner, bevel, extra frame, triangle shading, diagonal corner cut or object silhouette anywhere inside the bay. Main ceramic face stays one broad calm flat ivory field, not a recessed face. Add only several small discontinuous joined pixel clusters of old contact dust ALONG the existing upper joint and lower guard and left/right true seam shoulders, with a few smaller broken pixels attached to those clusters. Same moderate 2-4 native pixel scale and restrained cool-gray aging as ceramic wall samples. Keep center essentially empty and structurally unchanged. No noise spray, giant patches, gradients, lighting, reflections, lettering, hardware, yellow, rust, dirt wall-wide border or perspective. WHITE is editable surface material only; BLACK is exact preserved construction. Never trace a second rectangle or silhouette inside the original bay.'
(HERE/'prompt_portal_fix.txt').write_text(prompt,encoding='utf-8')
jobs=json.loads((HERE/'requests.json').read_text())
if not any(j['name']=='portal_fix' for j in jobs):
    old=next(j for j in jobs if j['name']=='portal');job=dict(old)
    job.update(name='portal_fix',guide='guide_portal_fix.png',mask='mask_portal_fix.png',prompt='prompt_portal_fix.txt',seed=2026103088)
    jobs.append(job);(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
(HERE/'rejected_outputs.json').write_text(json.dumps({'portal':{'reason':'AI invented an inset rectangle/rim on an originally flat wide ceramic bay','raw_preserved':'raw/portal.png','replacement_request':'portal_fix','manual_painting_used':False}},indent=2),encoding='utf-8')
print('R22_PORTAL_FIX_PREPARED; submit only after the initial persistent queue finishes')
