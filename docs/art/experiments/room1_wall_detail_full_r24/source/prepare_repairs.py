"""Reject oversized peeling/crack-like AI marks and request native PixelLab replacements."""
from pathlib import Path
import json,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
R23=ROOT/'docs/art/experiments/room1_wall_detail_r23'
jobs=json.loads((HERE/'requests.json').read_text());rejected={}
common='''Flat wall ALBEDO edit matching the supplied OWN PROJECT approved material. Preserve exact flat ceramic bays, outer seams, lamp and lower guard. Maintain the SAME moderate amount and physical extent of fine edge residue as the guide; do not make it dirtier or more damaged. Every existing upper corner, seam shoulder and lower contact still needs finished layered detail, with compact connected groups and fine 1-3 native pixel fringes, naturally thinning into intact ivory ceramic. Make a new arrangement of SMALL broken contact deposits, not new kinds of damage. No broad peeled sheets, chunks, flakes, stone-like spots, heavy scabs, large islands, branch/crack lines or wide spreading gray silhouettes. Keep all main ceramic intact. Do not draw only a few dots or blank out one bay. Do not add an inner rim, frame, outline, bevel, groove, compartment, hardware or lettering. No lighting, gradients, perspective, uniform pepper spray, yellow, brown, rust, moss or glass. Use the existing warm-gray ivory / cool-neutral gray palette, crisp fine native pixel detail at 256x256. BLACK is protected construction; WHITE is editable material. Keep the quiet broad face with complete fine-to-medium shoulder transitions, same density as the guide, not giant deposits.'''
for i,key in enumerate(['g','h','portal']):
    name=key+'_fix'
    source=(R23/'raw'/('a.png' if key=='g' else 'b.png')) if key!='portal' else HERE/'guide_portal.png'
    shutil.copyfile(source,HERE/f'guide_{name}.png');shutil.copyfile(HERE/f'mask_{key}.png',HERE/f'mask_{name}.png')
    extra=' Different fine distribution at the upper-left and lower-right contacts, with modest complete detail at the opposite contacts.' if key=='g' else ' Different fine distribution at upper-right and lower-left, same moderate finished richness.'
    if key=='portal':extra=' This is ONE WIDE existing ceramic WALL bay, not a new door. Absolutely no second rectangle or silhouette inside the bay. Keep fine irregular contact film on the true outer construction contacts; do not form a wall-wide thick dirty border.'
    prompt=common+extra;assert len(prompt)<=2000
    (HERE/f'prompt_{name}.txt').write_text(prompt,encoding='utf-8')
    if not any(j['name']==name for j in jobs):jobs.append({'name':name,'endpoint':'/inpaint-v3','prompt':f'prompt_{name}.txt','guide':f'guide_{name}.png','mask':f'mask_{name}.png','seed':2026103470+i,'native_size':[256,256]})
    rejected[key]={'reason':'Oversized peeling/chunk-like deposits and/or branch-like lines exceed the approved r23 fine contact-film character; richness must not be obtained by larger damage','raw_preserved':f'raw/{key}.png','replacement':name,'manual_material_editing':False}
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
(HERE/'rejected_outputs.json').write_text(json.dumps(rejected,indent=2),encoding='utf-8')
(HERE/'selection.json').write_text(json.dumps({'g':'g_fix','h':'h_fix','portal':'portal_fix'},indent=2),encoding='utf-8')
print('R24_REPAIRS_PREPARED 3 PixelLab redraws from approved project guides; no manual repaint')
