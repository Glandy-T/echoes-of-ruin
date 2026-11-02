"""Native crop and protected structure registration only. No painted aging."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
raw=Image.open(EXP/'raw/door.png').convert('RGBA');assert raw.size==(256,192)
crop=raw.crop((4,4,116,188));base=Image.open(HERE/'door_clean_structure.png').convert('RGBA');mask=Image.open(HERE/'door_mask.png').convert('L')
assert crop.size==base.size==mask.size==(112,184)
final=Image.composite(crop,base,mask);protected=np.asarray(mask)==0
assert np.array_equal(np.asarray(final)[protected],np.asarray(base)[protected])
layer=np.asarray(crop).copy();layer[:,:,3]=np.asarray(mask);Image.fromarray(layer).save(HERE/'layers/PixelLab_matte_composite_age.png');base.save(HERE/'layers/protected_structure_clean_base.png')
target=ROOT/'assets/art/room1_door_material_r29/door_front.png';final.save(target)
(HERE/'composite_validation.json').write_text(json.dumps({'result':'PASS','request_canvas':[256,192],'native_door_crop':[4,4,116,188],'runtime_size':[112,184],'output_resized':False,'protected_pixels':int(protected.sum()),'changed_pixels':int(np.any(np.asarray(final)!=np.asarray(base),axis=2).sum()),'protected_structure_exact':True,'final_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'manual_art_edits':0},indent=2),encoding='utf8')
print('R29_NATIVE_DOOR_COMPOSITE_PASS')
