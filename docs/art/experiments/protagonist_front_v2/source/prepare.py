from pathlib import Path
from PIL import Image
import numpy as np,json,shutil,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
for n in ['raw','editable','source/layers']:(EXP/n).mkdir(parents=True,exist_ok=True)
old=ROOT/'docs/art/experiments/protagonist_front_v1/raw/front.png'
im=Image.open(old).convert('RGBA');a=np.array(im);rgb=a[:,:,:3].astype(int)
skin=(a[:,:,3]>128)&(rgb[:,:,0]>rgb[:,:,1]+10)&(rgb[:,:,1]>rgb[:,:,2]+5)&(rgb[:,:,0]>65)
mask=skin.copy()
# Fill only internal facial holes (old eyebrows, eyes, mouth) within the original
# skin span. This is a technical edit/protection mask, not replacement drawing.
for y in range(19,45):
 xs=np.where(skin[y,70:123])[0]+70
 if len(xs)>1:mask[y,xs.min():xs.max()+1]=True
im.save(HERE/'input_front_v1.png');Image.fromarray((mask*255).astype('uint8')).save(HERE/'skin_face_mask.png')
for name in ['pixellab_api.py','jobs.py']:
 shutil.copyfile(ROOT/'docs/art/experiments/room1_door_material_r29/source'/name,HERE/name)
prompt=('Modify ONLY the white mask: the exposed face, neck, hands and bare feet of this SAME woman. '
'Preserve exact head shape, hair silhouette, anatomy, pose, opaque skin boundary, white sleep gown and every unmasked pixel. '
'LIGHTER skin, neutral softly warm fair complexion with pale beige base and muted rosy-gray shadows. All exposed skin areas must match, not orange, bronze, brown or chalk white. '
'The face should have intentionally MINIMAL facial information for a stylized low-poly character: peaceful neutral, relaxed, no specific emotion. '
'Remove the existing severe eyebrows, dark eyeliner, detailed eyes, dark eye sockets, sharp cheek lines, dark mouth corners and frown. '
'Do NOT replace them with smiling cartoon eyes. Omit individually drawn eyebrows, eye dots, eyelashes, lips, teeth and nostrils. '
'Use only a few coherent related skin-color planes to suggest forehead, very subtle nose volume, cheek and chin. The direction of the head must remain readable without a detailed portrait. '
'No blur filter: keep clean native pixel clusters and simple soft contrast through discrete colors. Preserve natural human volume, not a mask, skull, doll or metal face. '
'Hands and feet also become lighter with restrained shadows, maintaining their original design and silhouette. '
'Same front orthographic view, same young adult, same dimensions, same transparent background. Do not redesign hair, outfit, sleeves, folds, gown aging, framing or proportions. No new accessories or text.')
assert len(prompt)<=2000
(HERE/'prompt_front.txt').write_text(prompt,encoding='utf8')
(HERE/'requests.json').write_text(json.dumps([{'name':'front','endpoint':'/inpaint-v3','prompt':'prompt_front.txt','guide':'input_front_v1.png','mask':'skin_face_mask.png','seed':2026110302}],indent=2),encoding='utf8')
(HERE/'provenance.json').write_text(json.dumps({'input':old.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'mask_pixels':int(mask.sum()),'external_reference_upload':False,'creative_resize':False,'scope':'skin and inner facial detail only'},indent=2),encoding='utf8')
(EXP/'.gitignore').write_text('*.log\n*.err\n__pycache__/\n',encoding='utf8')
print('FRONT_V2_PREPARED',int(mask.sum()),'editable pixels;1 bounded request')
