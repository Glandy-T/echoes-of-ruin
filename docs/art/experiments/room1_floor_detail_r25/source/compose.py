from pathlib import Path
import json,hashlib
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4];PATCH=(168,96,424,352)
OUT=ROOT/'assets/art/room1_floor_detail_r25';OUT.mkdir(parents=True,exist_ok=True)
base=Image.open(ROOT/'assets/art/room1_pixel_unify_r22/floor_with_leaks.png').convert('RGBA')
mask=np.asarray(Image.open(HERE/'mask_candidate.png').convert('L'))>0
packages=[]
for key,src in [('reference',HERE/'original_project_r15_detail.png'),('candidate',EXP/'raw/candidate.png')]:
 raw=Image.open(src).convert('RGBA');assert raw.size==(256,256)
 layer=np.array(raw);layer[:,:,3]=np.where(mask,255,0)
 full=Image.new('RGBA',base.size);full.paste(Image.fromarray(layer),PATCH[:2])
 final=Image.alpha_composite(base,full)
 folder=HERE/'layers'/key;folder.mkdir(parents=True,exist_ok=True)
 base.save(folder/'base_r22.png');full.save(folder/'material_replacement.png')
 final.save(OUT/f'floor_{key}.png')
 local=final.crop(PATCH);local.save(HERE/f'final_patch_{key}.png')
 packages.append({'key':key,'output':(OUT/f'floor_{key}.png').relative_to(ROOT).as_posix(),'sha256':hashlib.sha256((OUT/f'floor_{key}.png').read_bytes()).hexdigest(),'native_patch':PATCH,'resampling':False,'mask':'mask_candidate.png','replace':'binary 0/255, no old age layer under edited pixels'})
(HERE/'packages.json').write_text(json.dumps(packages,indent=2),encoding='utf8')
(OUT/'.gitignore').write_text('*.import\n',encoding='utf8')
(EXP/'.gitignore').write_text('*.log\n*.blend1\n__pycache__/\nsource/balance_*.json\n',encoding='utf8')
print('R25_COMPOSED local reference and PixelLab candidate; all exterior current exact')
