"""Exact PixelLab pixels plus protected construction/ID. No synthetic aging."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
TARGET=ROOT/'assets/art/room1_pod_age_r27'
records=[]
for job in json.loads((HERE/'requests.json').read_text()):
 role=job.get('role',job['name']);guide=Image.open(HERE/job['guide']).convert('RGBA');raw=Image.open(EXP/'raw'/f"{job['name']}.png").convert('RGBA');mask=Image.open(HERE/job['mask']).convert('L')
 assert raw.size==guide.size==mask.size
 assert set(np.unique(np.asarray(mask))).issubset({0,255})
 new=Image.composite(raw,guide,mask)
 identity=Image.open(HERE/f'identity_{role}.png').convert('RGBA');new=Image.alpha_composite(new,identity)
 base=guide.copy();ai=raw.copy();a=np.asarray(ai).copy();a[:,:,3]=np.asarray(mask);ai=Image.fromarray(a)
 base.save(HERE/'layers'/f'{role}_base.png');ai.save(HERE/'layers'/f'{role}_PixelLab.png');identity.save(HERE/'layers'/f'{role}_identity.png')
 new.save(TARGET/f'{role}.png')
 protected=np.asarray(mask)==0
 assert np.array_equal(np.asarray(new)[protected],np.asarray(guide)[protected])
 records.append({'role':role,'native_size':list(new.size),'creative_output_resized':False,'editable_pixels':int((~protected).sum()),'protected_pixels':int(protected.sum()),'final_sha256':hashlib.sha256((TARGET/f'{role}.png').read_bytes()).hexdigest(),'AI_result':f"raw/{job['name']}.png",'manual_refinements':[]})
(HERE/'composite_validation.json').write_text(json.dumps({'result':'PASS','records':records,'scope':'P12 exterior color maps only; no geometry/UV/light edits'},indent=2),encoding='utf8')
print('R27_COMPOSITE_PASS',len(records),'native maps')
