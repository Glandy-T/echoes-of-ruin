"""Prepare PixelLab repair of the observed C-versus-new material join, not a painted blend."""
from pathlib import Path
import json
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
accepted=np.asarray(Image.open(HERE/'approved_r25_material_mask.png').convert('L'))>0
edit=np.asarray(Image.open(HERE/'world_edit_mask.png').convert('L'))>0
vertical=np.zeros_like(accepted)
for dy in range(-48,49):
    a=max(0,dy);b=min(728,728+dy);vertical[a:b]|=accepted[a-dy:b-dy]
dilated=np.zeros_like(accepted)
for dx in range(-48,49):
    a=max(0,dx);b=min(1648,1648+dx);dilated[:,a:b]|=vertical[:,a-dx:b-dx]
mask=dilated&edit
guide=Image.open(HERE/'pilot_composite.png').convert('RGBA')
guide.save(HERE/'transition_context.png')
Image.fromarray(np.where(mask,255,0).astype('uint8')).save(HERE/'transition_world_mask.png')
jobs=json.loads((HERE/'requests.json').read_text());jobs=[j for j in jobs if not j['name'].startswith('join_')]
tiles=[]
prompt='''Repair this OWN PROJECT native256 flat FLOOR ALBEDO material join. WHITE is a narrow editable floor region OUTSIDE an already approved material area. BLACK protects that approved area and actual occupied cryopod floor; never render objects there. A straight darker rectangular patch boundary is currently visible: make the surrounding WHITE floor naturally continue its adjacent protected coating and contact details so no rectangular material join is readable. Preserve every black pixel exactly, especially the approved darker slate-blue coating. In WHITE, extend small low-contrast coating variation and fine joined contact clusters around true cryopod edges, and break up the artificial straight tone boundary with coherent subtle material transitions. This is NOT a border, frame, vignette, dark outline, ring of grime or uniform sprayed halo. Keep intact floor between genuine contacts. Same cool desaturated blue-gray palette, native1-3 pixel steps with small/medium clustered fringe details, matched material finish and contrast. No coarse enlargement, giant stains, branching cracks, new leaks, white rims, yellow/brown/green, rusty color, random noise, route, grid, tile seams, text, equipment, perspective, rendered lighting, cast shadows, glow, reflections or blur. Do not alter the layout or footprints. Repair the flat coating continuity, not the scene lighting. All new creative pixels in WHITE are supplied by this edit, not an old layer blend.'''
for index,(x,y) in enumerate([(104,32),(288,32),(104,216),(288,216)],1):
    name=f'join_{index:02d}';box=(x,y,x+256,y+256)
    guide.crop(box).save(HERE/f'guide_{name}.png')
    Image.fromarray(np.where(mask,255,0).astype('uint8')).crop(box).save(HERE/f'mask_{name}.png')
    (HERE/f'prompt_{name}.txt').write_text(prompt,encoding='utf8')
    jobs.append({'name':name,'endpoint':'/inpaint-v3','prompt':f'prompt_{name}.txt','guide':f'guide_{name}.png','mask':f'mask_{name}.png','seed':2026103690+index,'native_size':[256,256]})
    tiles.append({'name':name,'row':(index-1)//2,'column':(index-1)%2,'origin_px':[x,y],'native_size':[256,256]})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf8')
(HERE/'transition_layout.json').write_text(json.dumps({'reason':'Actual pilot showed a rectangular C-versus-new main-tone boundary; use PixelLab outside C, never script recolor or blur','guide':'transition_context.png','approved_C_unchanged':True,'ring_width_px':48,'tiles':tiles,'overlap_px':72,'new_requests':4},indent=2),encoding='utf8')
print('R26_TRANSITION_PREPARED 4 native PixelLab edits, estimate40 generations; approved C protected')
