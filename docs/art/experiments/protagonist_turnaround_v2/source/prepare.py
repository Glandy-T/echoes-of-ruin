from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
OLD=ROOT/'docs/art/experiments/protagonist_turnaround_v1'
for n in ['raw','views','editable','source/layers']:(EXP/n).mkdir(parents=True,exist_ok=True)
for name in ['front','side']:shutil.copyfile(OLD/'views'/f'{name}.png',EXP/'views'/f'{name}.png');shutil.copyfile(OLD/'editable'/f'{name}.aseprite',EXP/'editable'/f'{name}.aseprite')
shutil.copyfile(OLD/'views/back.png',HERE/'back_v1.png')
mask=Image.new('L',(192,256),0);d=ImageDraw.Draw(mask)
boxes={'left_hand':[41,125,65,151],'right_hand':[127,125,154,151],'left_ankle_heel':[57,213,92,246],'right_ankle_heel':[101,213,138,246]}
for box in boxes.values():d.rectangle(box,fill=255)
mask.save(HERE/'repair_mask.png')
shutil.copyfile(OLD/'source/pixellab_api.py',HERE/'pixellab_api.py')
prompt=('This is a STRICT BACK VIEW of a woman. The hair and gown already show her back, but the old hands and feet were incorrectly copied from a front view. '
'Repair ONLY the white-mask hands, ankles and feet into anatomically readable REAR views, keeping their attachment points, stance and scale. '
'FEET: we look at the BACK of both bare legs. Show the Achilles tendon continuing into a rounded compact HEEL and posterior ankle. The toes point AWAY from the viewer, forward behind the foot, mostly occluded. '
'Remove the front-facing spread of toes and front-of-foot fan silhouette. No visible toenails, no row of toes toward the camera, no upturned soles, no backward-bent legs. '
'Both heel bottoms remain on the existing ground near y244. Keep the ankle connections under the existing gown; feet can become narrower in projection, do not move the legs. '
'HANDS: same relaxed low A-pose, viewed from behind her body. Show the back/side plane of each hanging hand with restrained knuckle volume and naturally occluded fingers/thumbs. '
'No palm creases or flat open palms presented to the viewer, no waving, no duplicated or reversed thumbs, no extra fingers. Preserve wrists at the existing sleeve openings. '
'Match the existing pale neutral-warm skin and restrained native pixel clusters. Minimal detail, coherent volume; do not add dark outlines or realistic anatomy noise. '
'Keep the COMPLETE back head, hair, white gown, sleeves, hem, body proportions and camera EXACTLY as supplied outside the mask. No face, front neckline or new folds on the back. '
'Keep transparent background. Within masked margins, any pixels not part of the corrected limb must be fully transparent; no shadows or ground marks.192x256 native output, no resizing.')
assert len(prompt)<=2000
(HERE/'prompt_back.txt').write_text(prompt,encoding='utf8')
(HERE/'request.json').write_text(json.dumps({'endpoint':'/inpaint-v3','input':'back_v1.png','mask':'repair_mask.png','description_file':'prompt_back.txt','seed':2026110305,'no_background':True,'crop_to_mask':False},indent=2),encoding='utf8')
paths=['views/front.png','views/side.png','views/back.png','editable/front.aseprite','editable/side.aseprite','editable/back.aseprite']
(HERE/'provenance.json').write_text(json.dumps({'baseline':'protagonist_turnaround_v1','baseline_hashes':{p:hashlib.sha256((OLD/p).read_bytes()).hexdigest() for p in paths},'repair_regions_xy_inclusive':boxes,'scope':'back hands and ankles/heels only; alpha may change within those bounded boxes','third_party_reference_uploads':False,'creative_resize':False},indent=2),encoding='utf8')
(EXP/'.gitignore').write_text('*.log\n*.err\n__pycache__/\n',encoding='utf8')
print('BACK_REPAIR_PREPARED;1 bounded PixelLab request;4 explicit edit regions')
