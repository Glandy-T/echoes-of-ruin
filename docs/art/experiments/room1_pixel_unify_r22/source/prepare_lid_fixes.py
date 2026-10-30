"""Reject invented inset/window and warm-brown lid shading; ask PixelLab to repaint."""
from pathlib import Path
import json,shutil
HERE=Path(__file__).resolve().parent
jobs=json.loads((HERE/'requests.json').read_text());rejected=json.loads((HERE/'rejected_outputs.json').read_text())
for variant in ['b','d']:
    source=variant+'_lid';name=source+'_fix'
    for stem in ['guide','mask','guide_full','mask_full']:shutil.copyfile(HERE/f'{stem}_{source}.png',HERE/f'{stem}_{name}.png')
    prompt='Flat ALBEDO material of an EXISTING OPAQUE CERAMIC CRYOPOD COVER UV. This texture contains NO GLASS: the actual head glass is a separate model surface and is not pictured here. Every ivory guide region is solid matte ceramic, including the large existing rounded rectangular ID panel. Keep its broad interior the SAME warm-gray ivory #D3D6C9 as the surrounding ceramic. Do not add an inset inner rectangle, smaller frame, window, glass pane, screen, deep recess or new border INSIDE any existing panel. Preserve the original outline, slate blue-gray rails and EXACT existing ID. Black is protected structure; white is material only. Use coherent 2-4 native pixel clusters with a few small broken transitions; 4-6 related flat cool-gray tones. Quiet intact main faces, moderate compact old contact dust at real shoulders, outer seals and existing panel boundaries. No area-wide coarse speckling, random scattered spots, thick peeling bands, warm brown, yellow, rust, hard cast shadows, highlights, gradients, perspective or new hardware. Do not darken the broad center to simulate depth. This is surface material, not an object redesign. '
    prompt+=('A few asymmetric small upper-left and lower-right contact clusters.' if variant=='b' else 'A few asymmetric short upper-right seal deposits and lower-left edge wear, broad centers quiet.')
    (HERE/f'prompt_{name}.txt').write_text(prompt,encoding='utf-8')
    if not any(j['name']==name for j in jobs):
        job=dict(next(j for j in jobs if j['name']==source));job.update(name=name,guide=f'guide_{name}.png',mask=f'mask_{name}.png',prompt=f'prompt_{name}.txt',seed=2026103180+ord(variant));jobs.append(job)
    rejected[source]={'reason':'Invented inner pane/inset rectangle on an opaque ceramic panel; D also added broad warm-brown plane shading. Geometry not changed.','raw_preserved':f'raw/{source}.png','replacement_request':name,'manual_painting_used':False}
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8');(HERE/'rejected_outputs.json').write_text(json.dumps(rejected,indent=2),encoding='utf-8')
print('R22_LID_FIXES_PREPARED 2 actual PixelLab repairs; original raw rejected outputs retained')
