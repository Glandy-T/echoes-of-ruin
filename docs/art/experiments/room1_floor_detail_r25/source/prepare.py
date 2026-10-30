"""Own floor inputs and exact occupied masks; no material art drawn by this script."""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image,ImageDraw
import numpy as np
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
PATCH=(168,96,424,352)
for name in ['raw','editable','evidence','source/layers']:(EXP/name).mkdir(parents=True,exist_ok=True)
for name in ['jobs.py','pixellab_api.py']:shutil.copyfile(ROOT/'docs/art/experiments/room1_wall_detail_full_r24/source'/name,HERE/name)
(HERE/'jobs.py').write_text((HERE/'jobs.py').read_text().replace('R24_PIXELLAB_QUEUE_COMPLETE','R25_PIXELLAB_QUEUE_COMPLETE'),encoding='utf8')
old=Image.open(ROOT/'assets/art/room1_floor_variants_r15/floor_with_leaks.png').convert('RGBA')
current=Image.open(ROOT/'assets/art/room1_pixel_unify_r22/floor_with_leaks.png').convert('RGBA')
reference=old.crop(PATCH);reference.save(HERE/'original_project_r15_detail.png')
now=current.crop(PATCH);now.save(HERE/'current_r22_crop.png')
full_mask=Image.new('L',old.size,255);d=ImageDraw.Draw(full_mask)
for pod in json.loads((ROOT/'docs/art/experiments/room1_floor_variants_r15/source/pod_footprints.json').read_text())['pods']:
 d.polygon([tuple(p) for p in pod['pixel_polygon']],fill=0)
mask=np.array(full_mask.crop(PATCH));mask[:8]=0;mask[-8:]=0;mask[:,:8]=0;mask[:,-8:]=0
# The guide uses original PixelLab fine detail. Exact current pixels are supplied
# under all protected regions, including the technical 8px join boundary.
guide=np.array(reference);guide[mask==0]=np.asarray(now)[mask==0]
Image.fromarray(guide).save(HERE/'guide_candidate.png');Image.fromarray(mask).save(HERE/'mask_candidate.png')
prompt="""Revise this OWN PROJECT top-down FLOOR ALBEDO into a finished native 256x256 pixel-art material. Preserve the continuous matte desaturated blue-gray floor and supplied fine material detail density. The black shapes are exact existing cryopod footprints, NOT tiles, new panels or things to render. WHITE mask is floor material only; BLACK is protected occupied floor and a current-material join boundary. Match the protected outer join naturally without a square frame. Keep existing old contact film tightly attached to the actual footprint boundaries, with uneven width, gaps, fine corners and secondary residue. Keep the existing localized dry coolant residue near the right-hand occupied corner, do not add other leaks. Retain broad intact coating but enrich it with coherent low-contrast material patches and broken fine transitional clusters; do not flatten it into empty color. Use several related cool slate blue-gray tones, readable compact 1-3 pixel edge steps with varied small and medium connected groups and a finer gradually thinning fringe. Avoid both large rounded chunks and uniform sprayed noise. No coarse pixel enlargement, wide peeling islands, blobs, scratch lines, cracks, moss, yellow, green, brown, rust, bright powder, white rim, repeated stamps, closed outline around footprints, borders, seams, grid, tile joints, route, new objects, text, perspective, rendered lighting, cast shadows, glow, reflections or glossy wet highlights. This is flat material color, not a scene illustration. Maintain the original subtle base color and contrast and current spatial locations; all creative floor pixels in WHITE are newly revised, not an overlaid old grime layer."""
assert len(prompt)<=2000
(HERE/'prompt_candidate.txt').write_text(prompt,encoding='utf8')
job={'name':'candidate','endpoint':'/inpaint-v3','prompt':'prompt_candidate.txt','guide':'guide_candidate.png','mask':'mask_candidate.png','seed':2026103551,'native_size':[256,256]}
(HERE/'requests.json').write_text(json.dumps([job],indent=2),encoding='utf8')
baseline=json.loads((ROOT/'docs/art/experiments/room1_wall_detail_full_r24/source/baseline_file_hashes.json').read_text())
for folder in ['assets/art/room1_wall_detail_full_r24','assets/art/room1_pixel_unify_r22','assets/art/room1_floor_variants_r15']:
 for f in (ROOT/folder).rglob('*.png'):baseline[f.relative_to(ROOT).as_posix()]=hashlib.sha256(f.read_bytes()).hexdigest()
for f in ['scripts/dev/room1_wall_detail_full_r24.gd','scripts/dev/room1_pixel_unify_r22.gd']:
 baseline[f]=hashlib.sha256((ROOT/f).read_bytes()).hexdigest()
(HERE/'baseline_file_hashes.json').write_text(json.dumps(baseline,indent=2),encoding='utf8')
(HERE/'input_provenance.json').write_text(json.dumps({'sources':['assets/art/room1_floor_variants_r15/floor_with_leaks.png','assets/art/room1_pixel_unify_r22/floor_with_leaks.png','docs/art/experiments/room1_floor_variants_r15/source/pod_footprints.json'],'patch_px':PATCH,'world_x_m':[2.3,5.5],'world_z_m':[-8.1,-4.9],'native_size':[256,256],'resampling':False,'technical_guide':'r15 material with exact current r22 protected occupied areas and 8px boundary','creative_production':'PixelLab /v2/inpaint-v3','PixelCanals_content_submitted':False,'scope':'floor PATCH only; r24 walls and other room assets unchanged'},indent=2),encoding='utf8')
print('R25_PREPARED one native 256px PixelLab floor revision, estimate 10 generations')
