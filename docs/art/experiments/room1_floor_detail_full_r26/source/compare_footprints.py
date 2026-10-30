from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np
HERE=Path(__file__).resolve().parent;p=HERE/'current_pod_footprints.json';r=json.loads(p.read_text())
for pod in r['pods']:
 a=Image.new('L',(1648,728));b=a.copy()
 ImageDraw.Draw(a).polygon([tuple(v) for v in pod['old_v3_polygon']],fill=255);ImageDraw.Draw(b).polygon([tuple(v) for v in pod['pixel_polygon']],fill=255)
 aa=np.asarray(a)>0;bb=np.asarray(b)>0
 pod.update({'old_mask_removed_pixels':int((aa&~bb).sum()),'old_mask_missing_pixels':int((bb&~aa).sum()),'new_mask_pixels':int(bb.sum())})
r['old_v3_mask_is_exact']=all(x['old_mask_removed_pixels']==x['old_mask_missing_pixels']==0 for x in r['pods']);p.write_text(json.dumps(r,indent=2),encoding='utf8')
print('R26_MASK_COMPARE',r['old_v3_mask_is_exact'],'all20 actual v8 masks checked')
