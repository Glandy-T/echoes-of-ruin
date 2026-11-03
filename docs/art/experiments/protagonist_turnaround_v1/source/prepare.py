from pathlib import Path
from PIL import Image
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
for n in ['raw','views','editable']:(EXP/n).mkdir(parents=True,exist_ok=True)
source=ROOT/'docs/art/experiments/protagonist_front_v2/front_design_v2.png'
shutil.copyfile(source,HERE/'approved_front_v2.png');shutil.copyfile(source,EXP/'views/front.png')
shutil.copyfile(ROOT/'docs/art/experiments/protagonist_front_v2/source/pixellab_api.py',HERE/'pixellab_api.py')
common=('Make an orthographic MODELING turnaround of the EXACT SAME young adult woman in the input, rotated as requested. '
'Keep natural adult head/body proportions, silhouette identity, light neutral warm skin, weak/omitted facial features, loose dark long hair and the SAME simple white standardized cryogenic sleep gown. '
'The gown is one continuous loose closed round-neck calf-length garment with simple long sleeves, no collar lapels, belt, buttons, zippers, ornaments or openings. Bare feet as input. '
'Same muted gray fold vocabulary and very light storage aging, no added dirt or damage. This is a rotated design, not a new costume or character. '
'Strict eye-level orthographic view, zero camera elevation, no perspective or three-quarter angle. Same relaxed LOW A-POSE rotated in 3D, no new hand gesture. '
'Match the input scale and alignment:192x256 canvas, head top near y12, soles near y248, shoulder joint near y60, wrists near y139, gown hem near y211. Entire subject visible, centered x96 with margins. '
'Keep coherent native pixel clusters and palette. Transparent background. No cast shadow, labels, grid, props, additional people or alternate views. ')
prompts={
 'side':common+'Output ONLY a strict RIGHT-FACING SIDE PROFILE (90 degree turn). Nose, chest and feet point toward the RIGHT edge. Show one readable side contour with the far limbs occluded naturally; do not turn the head toward the viewer. The low A-pose arms overlap in depth from this view. Keep simple nose/chin volume without eyes, eyebrows, lips or nostrils. Hair is a plain loose mass reaching mid-back behind shoulders; small original front locks remain. Keep the gown roomy around chest/hips without becoming a body-hugging dress. Show real depth of the body and gown, not a thin paper cutout.',
 'back':common+'Output ONLY a strict BACK VIEW (180 degree turn). Show the back of the head, back of neck where visible, both shoulders and back of the gown. Front of face must be completely hidden. Arms still held symmetrically a little away from body and feet matching the front stance. Hair falls as a simple dark loose mid-back mass, covering upper back and ending around y110-120, NOT to the waist or knees. Gown back is plain continuous cloth, no invented opening, ties, fasteners, pockets, accessories or extra fabric panels. Keep back gown hem level and length matching the input.'}
jobs=[]
for i,(name,prompt) in enumerate(prompts.items()):
 assert len(prompt)<=2000
 (HERE/f'prompt_{name}.txt').write_text(prompt,encoding='utf8')
 jobs.append({'name':name,'endpoint':'/edit-image-pro-flash','input':'approved_front_v2.png','prompt':f'prompt_{name}.txt','seed':2026110303+i})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf8')
(HERE/'provenance.json').write_text(json.dumps({'approved_front_source':source.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'approval':'2026-11-03 user accepted v2 as a working basis; further changes after3D expected','source_size':list(Image.open(source).size),'external_reference_uploads':False,'creative_resizing':False,'new_view_count':2,'hair_back_and_gown_back_status':'inferred candidate; not previously visible or confirmed'},indent=2),encoding='utf8')
(EXP/'.gitignore').write_text('*.log\n*.err\n__pycache__/\n',encoding='utf8')
print('TURNAROUND_PREPARED2single-viewedits;frontv2exact')
