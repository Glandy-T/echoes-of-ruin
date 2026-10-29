from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
data={};groups={}
for group in ['base','contact','leak']:
    files=sorted((EXP/'raw').glob(group+'_*.png'));groups[group]=files
    if not files:continue
    ref=np.asarray(Image.open(files[0]).convert('RGB'),dtype=float)
    for p in files:
        a=np.asarray(Image.open(p).convert('RGB'),dtype=float)
        corr=float(np.corrcoef(ref.mean(2).ravel(),a.mean(2).ravel())[0,1])
        item={'equal_to_first_fraction':float(np.mean(np.all(ref==a,axis=2))),'correlation_to_first':corr,'colors':len(np.unique(a.reshape(-1,3),axis=0))}
        if group in ['contact','leak']:
            occupied=np.asarray(Image.open(HERE/'canonical_footprint.png').convert('L'))>0
            foreground=(np.any(ref!=ref[0,0],axis=2)|np.any(a!=a[0,0],axis=2))&~occupied
            item['deposit_union_pixels']=int(foreground.sum())
            item['equal_fraction_on_deposit_union']=float(np.mean(np.all(ref[foreground]==a[foreground],axis=1))) if foreground.any() else 1.0
        data[p.stem]=item
    rows=(len(files)+3)//4;out=Image.new('RGB',(1024,rows*280),(20,27,29));draw=ImageDraw.Draw(out)
    for i,p in enumerate(files):
        x=(i%4)*256;y=(i//4)*280
        out.paste(Image.open(p).convert('RGB'),(x,y));draw.text((x+6,y+260),p.stem,fill=(215,230,224))
    out.save(EXP/'evidence'/f'raw_{group}_candidates.png')
(HERE/'source_similarity.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print(json.dumps(data))
