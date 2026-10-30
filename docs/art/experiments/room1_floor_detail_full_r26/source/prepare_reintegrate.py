"""An owned colour/geometry guide only; final C-area pixels come from PixelLab."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
R25=ROOT/'docs/art/experiments/room1_floor_detail_r25/source'
patch=(168,96,424,352)
guide=np.array(Image.open(HERE/'transition_context.png').convert('RGBA').crop(patch))
mask=np.asarray(Image.open(R25/'mask_candidate.png').convert('L'))>0
reference=np.array(Image.open(R25/'original_project_r15_detail.png').convert('RGBA'))
# Calibrate only the owned INPUT guide's coating reference to the surrounding
# new material. This is not a final-material recolour or a painted transition.
# The original spatial clusters remain guide information for PixelLab to revise.
reference[:,:,:3]=np.clip(reference[:,:,:3].astype(int)+np.array([7,6,5]),0,255).astype('uint8')
guide[mask]=reference[mask]
Image.fromarray(guide).save(HERE/'guide_c_reintegrate.png')
Image.fromarray(np.where(mask,255,0).astype('uint8')).save(HERE/'mask_c_reintegrate.png')
prompt='''Reintegrate this OWN PROJECT flat FLOOR ALBEDO patch into the protected surrounding material. Produce native256 pixel art. WHITE is the old sample's material area; BLACK is actual occupied cryopod floor and exact surrounding new floor. Keep footprints, existing residue locations and outer context fixed. Revise WHITE to the SAME coating base and contrast as adjacent protected floor: main matte blue-gray RGB77,98,107 (#4D626B) with modest nearby lighter/darker cluster tones. Do not darken WHITE into a rectangle or shaded inset. Its former patch boundary must disappear into one continuous floor, not become a dark square, rim, frame, glow or uniform grime ring. Preserve the approved fine material-completion level: coherent small/medium attached contact groups, fine1-3 pixel stepped fringes and gradually thinning transitions; keep intact coating between real contacts. Vary cluster arrangement naturally, no blank colour slab and no coarse enlarged pixels. Maintain only the supplied localized existing dry residue near the right occupied corner, not new leaks. Do not create shadows/lighting. No giant angular or rounded dark islands, bright powder, white outline, yellow/green/brown, rust/moss, random noise, cracks, long scratches, seams, tile joints, route/grid, text, equipment, perspective, reflections, gloss or blur. This is continuous flat material colour; do not retain the old sample as another texture layer. Every creative WHITE pixel must be revised by this PixelLab edit, matching the protected new floor at the join.'''
assert len(prompt)<=2000
(HERE/'prompt_c_reintegrate.txt').write_text(prompt,encoding='utf8')
jobs=json.loads((HERE/'requests.json').read_text());jobs=[j for j in jobs if j['name']!='c_reintegrate']
jobs.append({'name':'c_reintegrate','endpoint':'/inpaint-v3','prompt':'prompt_c_reintegrate.txt','guide':'guide_c_reintegrate.png','mask':'mask_c_reintegrate.png','seed':2026103705,'native_size':[256,256]})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf8')
rejected=json.loads((HERE/'rejected_outputs.json').read_text())
for i in range(1,5):rejected[f'join_{i:02d}']='The fixed original C material still read as a rectangular dark patch after perimeter repair. Not used in final.'
(HERE/'rejected_outputs.json').write_text(json.dumps(rejected,indent=2),encoding='utf8')
(HERE/'final_strategy.json').write_text(json.dumps({'C_is_style_and_completion_reference':'User approved the C direction, not an additional per-pixel freeze imposed by the producer.','old_C_sample_retained_in_r25':True,'old_C_pixels_reused_in_final':False,'C_world_patch_px':patch,'new_C_area_source':'c_reintegrate','rejected_perimeter_attempts':[f'join_{i:02d}' for i in range(1,5)],'input_guide_only_colour_reference_offset':[7,6,5],'final_script_recolour':False,'final_script_painted_material':False},indent=2),encoding='utf8')
print('R26_REINTEGRATE_PREPARED one native256 PixelLab request; old C kept as reference, not frozen final pixels')
