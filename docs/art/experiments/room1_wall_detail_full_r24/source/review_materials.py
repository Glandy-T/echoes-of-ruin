"""Native source sheets and a per-half richness screen; this does not paint art."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
R23=ROOT/'docs/art/experiments/room1_wall_detail_r23'
mask=np.asarray(Image.open(R23/'source/mask.png').convert('L'))>0
clean=np.asarray(Image.open(R23/'source/clean_construction.png').convert('RGB')).astype(float)
ceramic=(clean.min(2)>180)&mask
sheet=Image.new('RGB',(1024,576),'#182629');draw=ImageDraw.Draw(sheet);records=[]
selection=json.loads((HERE/'selection.json').read_text()) if (HERE/'selection.json').exists() else {}
for i,key in enumerate('abcdefgh'):
    path=(R23 if key in 'ab' else EXP)/f"raw/{selection.get(key,key)}.png"
    im=Image.open(path).convert('RGB');a=np.asarray(im).astype(float)
    x=(i%4)*256;y=(i//4)*288;draw.text((x+3,y+3),key.upper()+(' / accepted r23' if key in 'ab' else ' / new PixelLab'),fill='white');sheet.paste(im,(x,y+24))
    for half in range(2):
        sl=(slice(None),slice(half*128,(half+1)*128));valid=ceramic[sl]
        # Diagnostic only: darkness relative to the original ceramic guide.
        # No score can stand in for seeing the actual cluster organisation.
        delta=(clean-a).mean(2)[sl];marks=(delta>=12)&valid
        records.append({'id':key+str(half),'ceramic_pixels':int(valid.sum()),'darker_material_pixels':int(marks.sum()),'dark_fraction':round(float(marks.sum()/max(valid.sum(),1)),6),'input_path':path.relative_to(ROOT).as_posix()})
sheet.save(EXP/'evidence/native_variants_review.png')
reference_min=min(r['dark_fraction'] for r in records if r['id'][0] in 'ab')
for r in records:r['below_weakest_approved_diagnostic']=r['dark_fraction']<reference_min
(HERE/'material_density_screen.json').write_text(json.dumps({'purpose':'diagnostic to find weak individual halves, not an artistic approval or a numeric project standard','approved_reference_min':reference_min,'panels':records,'resampling':False,'manual_material_editing':False},indent=2),encoding='utf-8')
print('R24_NATIVE_REVIEW_SHEET',len(records),'half panels; inspect every half visually')
