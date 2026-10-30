"""Reject two observed AI artifacts and ask PixelLab to repair from original inputs."""
from pathlib import Path
import json,shutil
HERE=Path(__file__).resolve().parent
jobs=json.loads((HERE/'requests.json').read_text());names={j['name'] for j in jobs}
selection={}
prompt='''Repair this OWN PROJECT native256 flat FLOOR ALBEDO using its original fine-detail guide. Keep continuous matte cool slate-blue coating, not a rendered scene. The main coating should remain near RGB70,92,102 (#465C66), with modest related lighter blue-gray cluster tones, comparable to a calm maintained-but-aged facility floor. Do NOT darken whole islands into charcoal polygons or paint a stage shadow. Preserve the supplied spatial contacts and any existing localized residue only. BLACK mask is exact occupied floor or approved material; WHITE is editable floor only. Rework WHITE into coherent small/medium attached clusters with fine 1-3 pixel stepped and gradually thinning fringe transitions; broad floor stays intact and subtle. Vary fine contact density naturally, not a stamped repeated round blotch. Canvas edges are NOT walls in this location: material must continue through all four sides with no black side bars, sharp dark planes, rectangular outline, inset rim or texture frame. No black fill or heavy drop shadow next to protected shapes. No large angular dark fields, white outline, yellow/brown/green, rust, moss, random pepper noise, coarse enlarged pixels, new leaks, cracks, long scratches, grid, joints, route, text, equipment, perspective, cast light, glow, shiny reflection, gloss or blur. Match the original low-contrast coating instead of inventing darker lighting. All new material pixels in WHITE are supplied by PixelLab; preserve BLACK.'''
for index,original in enumerate(['floor_11','floor_18','floor_12']):
    name=original+'_fix';selection[original]=name
    if name in names:continue
    for kind in ['guide','mask']:shutil.copyfile(HERE/f'{kind}_{original}.png',HERE/f'{kind}_{name}.png')
    (HERE/f'prompt_{name}.txt').write_text(prompt,encoding='utf8')
    jobs.append({'name':name,'endpoint':'/inpaint-v3','prompt':f'prompt_{name}.txt','guide':f'guide_{name}.png','mask':f'mask_{name}.png','seed':2026103698+index,'native_size':[256,256]})
(HERE/'selection.json').write_text(json.dumps(selection,indent=2),encoding='utf8')
rejected=json.loads((HERE/'rejected_outputs.json').read_text()) if (HERE/'rejected_outputs.json').exists() else {}
rejected.update({'floor_11':'Large dark angular coating fields and a conspicuous join in the empty aisle, unlike approved C.','floor_18':'Artificial dark left/right canvas borders beyond protected pod pixels; not a true wall location.','floor_12':'The final native whole-floor inspection revealed a second large dark field with a rectangular technical-patch read; not a real leak or wall contact.'})
(HERE/'rejected_outputs.json').write_text(json.dumps(rejected,indent=2),encoding='utf8')
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf8')
print('R26_REPAIRS_PREPARED selection for three PixelLab replacements; completed jobs are not submitted again')
