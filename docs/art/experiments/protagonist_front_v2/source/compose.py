from pathlib import Path
from PIL import Image
import numpy as np,json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
base=Image.open(HERE/'input_front_v1.png').convert('RGBA');raw=Image.open(EXP/'raw/front.png').convert('RGBA');mask=Image.open(HERE/'skin_face_mask.png').convert('L')
assert base.size==raw.size==mask.size==(192,256)
a=np.array(raw);a[:,:,3]=np.array(base)[:,:,3];raw=Image.fromarray(a)
final=Image.composite(raw,base,mask);final.save(EXP/'front_design_v2.png')
layer=np.array(raw);layer[:,:,3]=np.array(mask);Image.fromarray(layer).save(HERE/'layers/PixelLab_face_skin_refinement.png')
changed=np.any(np.array(base)!=np.array(final),axis=2);editable=np.array(mask)>0
assert not changed[~editable].any();assert np.array_equal(np.array(base)[:,:,3],np.array(final)[:,:,3])
(HERE/'composition.json').write_text(json.dumps({'result':'PASS','size':[192,256],'changed_pixels':int(changed.sum()),'protected_pixels_exact':True,'alpha_exact':True,'creative_resizing':False,'manual_art_edits':0},indent=2),encoding='utf8')
print('FRONT_V2_COMPOSED',int(changed.sum()),'changed pixels')
