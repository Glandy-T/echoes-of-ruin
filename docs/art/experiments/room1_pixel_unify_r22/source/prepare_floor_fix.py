"""PixelLab repair of rejected white footprint halos; guides only, not final painting."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageFilter
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
raw=Image.open(EXP/'raw/floor_tile_02.png').convert('RGBA');a=np.array(raw)
editable=np.asarray(Image.open(HERE/'mask_floor_tile_02.png').convert('L'))>0
bad=(a[:,:,:3].min(2)>200)&editable
assert bad.any()
area=Image.fromarray(bad.astype('uint8')*255).filter(ImageFilter.MaxFilter(9))
mask=np.asarray(area).copy();mask[~editable]=0
Image.fromarray(mask).save(HERE/'mask_floor_02_fix.png')
guide=np.array(raw);original=np.array(Image.open(HERE/'guide_floor_tile_02.png').convert('RGBA'))
# Restore rejected input pixels to the original project guide, not to final art.
guide[mask>0]=original[mask>0];Image.fromarray(guide).save(HERE/'guide_floor_02_fix.png')
prompt='Flat top-down FLOOR ALBEDO repair, only WHITE edit mask. Replace the unwanted bright footprint halos with matte cool BLUE-GRAY mineral floor and natural old contact film. All repaired pixels must stay in the same muted floor family as the surrounding guide: #4D626B #526771 #566B74 #5A6C73 #5E727B #627780 #687D85 #70858D. No white or pale gray marks, no bright outlines, paint stripes, glowing edges, closed rectangular border, raised rim, deep shadow, object or light. Keep the ground continuous, flat and unlit. Around occupied bases use irregular short low-contrast 2-4 native pixel clusters of neutral cool dust attached to true contact edges, with broken gaps; not a uniformly drawn footprint line. Preserve unrelated material and existing localized seep locations. Use crisp coherent small pixel groups, not smooth gradients or noise spray. Draw actual replacement floor material throughout editable regions; do not retain or reinterpret any white highlight. Black mask is protected original context.'
(HERE/'prompt_floor_02_fix.txt').write_text(prompt,encoding='utf-8')
jobs=json.loads((HERE/'requests.json').read_text())
if not any(j['name']=='floor_02_fix' for j in jobs):jobs.append({'name':'floor_02_fix','endpoint':'/inpaint-v3','prompt':'prompt_floor_02_fix.txt','guide':'guide_floor_02_fix.png','mask':'mask_floor_02_fix.png','seed':2026103199,'native_size':[256,256],'atlas_size':[512,512]})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
rejected=json.loads((HERE/'rejected_outputs.json').read_text());rejected['floor_tile_02']={'reason':'Bright white painted halos outside occupied footprints, inconsistent with matte blue-gray floor','white_editable_native_pixels':int(bad.sum()),'repair_mask_pixels':int((mask>0).sum()),'raw_preserved':'raw/floor_tile_02.png','replacement_request':'floor_02_fix','repair_method':'two real PixelLab outputs combined only inside exact native repair mask','manual_painting_used':False}
(HERE/'rejected_outputs.json').write_text(json.dumps(rejected,indent=2),encoding='utf-8')
print('R22_FLOOR_02_REPAIR_PREPARED',int(bad.sum()),'rejected white native pixels')
