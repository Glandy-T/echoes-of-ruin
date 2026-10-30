"""Measured construction guide for all visible portal wall, without leftover sparse strips."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
OLD=ROOT/'docs/art/experiments/room1_wall_pixellab_r11/source'
guide=Image.open(HERE/'guide_portal.png').convert('RGBA')
mask=Image.open(OLD/'mask_portal.png').convert('L')
# Existing world opening: center x10.5, width1.4, height2.4; 80px/m.
# Whole rear UV x=(world_x-.2)*80; y=(3.4-world_y)*80.
# Crop origin688,16 -> opening local x80..192, y64..256.
hole=(80,64,191,255)
ImageDraw.Draw(mask).rectangle(hole,fill=0)
ImageDraw.Draw(guide).rectangle(hole,fill=(37,51,58,255))
lamp=np.asarray(Image.open(ROOT/'docs/art/experiments/room1_wall_lamp_r13/source/rear_lamp_layer.png').convert('RGBA').crop((688,16,944,272)))[:,:,3]>0
a=np.array(mask);a[lamp]=0;a[:,:2]=0;a[:,-2:]=0;mask=Image.fromarray(a)
guide.save(HERE/'guide_portal_opening.png');mask.save(HERE/'mask_portal_opening.png')
prompt='''Flat architectural WALL ALBEDO material around the exact EXISTING opening in this original project guide. The dark cutout is measured missing wall and is protected, not a new object. Keep the exact opening, outer seams, existing lamp and lower guard. Rework ALL editable visible wall material, including the narrow wall shoulders between the outer bay seam and the opening. Match the approved fine pixel-art completeness: compact joined old seal-contact residue, smaller broken clusters, fine 1-3 native pixel fringe transitions along actual upper contacts, outer seams, opening shoulders and lower wall contact. Same restrained moderate age and cool-gray/ivory palette as the existing input, intact broad faces, not more damage. No giant patches, flakes, peeled sheets, stone-like spots, branching cracks or scabs. Keep every contact finished but naturally irregular, with short gaps and gently thinning fine edges. Do not leave plain blank strips beside the opening. Do NOT invent a frame, inner rectangle, rim, bevel, new panel, door leaf, hardware, glass, lettering, glowing edge or construction outside the existing guide. The opening already exists; do not redesign it. No fake 3D shading, lighting, vignette, gradients, perspective, uniform pepper spray, yellow, brown, rust or moss. Crisp native256 pixel material, no scale change. BLACK mask is exact preserved construction/cutout; WHITE is the full material replacement area.'''
assert len(prompt)<=2000;(HERE/'prompt_portal_opening.txt').write_text(prompt,encoding='utf-8')
jobs=json.loads((HERE/'requests.json').read_text())
if not any(j['name']=='portal_opening' for j in jobs):jobs.append({'name':'portal_opening','endpoint':'/inpaint-v3','prompt':'prompt_portal_opening.txt','guide':'guide_portal_opening.png','mask':'mask_portal_opening.png','seed':2026103490,'native_size':[256,256]})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
selection=json.loads((HERE/'selection.json').read_text());selection['portal']='portal_opening';(HERE/'selection.json').write_text(json.dumps(selection,indent=2),encoding='utf-8')
rejected=json.loads((HERE/'rejected_outputs.json').read_text());rejected['portal_fix']={'reason':'Superseded technical scope: inherited r13 mask protected visible strips beside the actual opening and would retain sparse r22 material there. New mask covers all real wall shoulders, with measured opening excluded.','raw_preserved':'raw/portal_fix.png','replacement':'portal_opening','manual_material_editing':False}
(HERE/'rejected_outputs.json').write_text(json.dumps(rejected,indent=2),encoding='utf-8')
(HERE/'portal_mask_scope.json').write_text(json.dumps({'world_opening':{'center_x':10.5,'width':1.4,'height':2.4},'crop':[688,16,944,272],'opening_local_inclusive':hole,'density_px_per_m':80,'geometry_authority':'existing wall header y2.4..3.4 in room1_integrated_door_v3/source/build_portal_wall.py and existing1.4m door, no geometry changes','guide_dark_marker':'construction guide only, excluded from final material by binary mask','old_mask_problem':'side editable strips x1..32 and223..254 missed real wall shoulders x33..79 and192..222'},indent=2),encoding='utf-8')
print('R24_PORTAL_MEASURED_OPENING_PREPARED full visible shoulders, lamp/geometry unchanged')
