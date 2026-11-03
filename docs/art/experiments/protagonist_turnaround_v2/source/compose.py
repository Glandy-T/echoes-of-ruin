from pathlib import Path
from PIL import Image
import numpy as np,json
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
base=Image.open(HERE/'back_v1.png').convert('RGBA');raw=Image.open(EXP/'raw/back.png').convert('RGBA');mask=Image.open(HERE/'repair_mask.png').convert('L')
assert raw.size==base.size==mask.size==(192,256)
final=Image.composite(raw,base,mask);final.save(EXP/'views/back.png')
a=np.array(base);b=np.array(final);m=np.array(mask)>0
assert np.array_equal(a[~m],b[~m])
# Store a full-canvas replacement region with exact mask coverage, including
# alpha=0 pixels. Aseprite erases old limbs inside the same boxes before pasting.
layer=np.array(raw);layer[~m]=0;Image.fromarray(layer).save(HERE/'layers/PixelLab_rear_hand_heel_repair.png')
(HERE/'composition.json').write_text(json.dumps({'result':'PASS','outside_mask_exact':True,'native_size':[192,256],'changed_RGBA_pixels':int(np.any(a!=b,axis=2).sum()),'alpha_changed_pixels':int((a[:,:,3]!=b[:,:,3]).sum()),'creative_resizing':False,'manual_art_edits':0},indent=2),encoding='utf8')
print('REAR_HAND_HEEL_COMPOSED;outside4regions exact')
