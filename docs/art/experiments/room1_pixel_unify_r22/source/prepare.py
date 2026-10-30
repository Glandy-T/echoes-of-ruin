"""Original layout guides and conservative masks only; PixelLab creates material art."""
from pathlib import Path
import json, shutil, hashlib
import numpy as np
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent; EXP=HERE.parent; ROOT=HERE.parents[4]
R20=ROOT/'docs/art/experiments/room1_pixel_cluster_r20/source'
WALL=ROOT/'docs/art/experiments/room1_wall_pixellab_r12/source'
POD=ROOT/'docs/art/experiments/room1_pod_pixellab_r16/source'
FLOOR=ROOT/'docs/art/experiments/room1_floor_variants_r15/source'
for n in ['raw','editable','evidence','source/layers']:(EXP/n).mkdir(parents=True,exist_ok=True)
for n in ['pixellab_api.py','jobs.py']:shutil.copyfile(R20/n,HERE/n)
(HERE/'jobs.py').write_text((HERE/'jobs.py').read_text(encoding='utf-8').replace('R20_PIXELLAB_QUEUE_COMPLETE','R22_PIXELLAB_QUEUE_COMPLETE'),encoding='utf-8')
jobs=[]; provenance=[]

def add(name,guide,mask,prompt,seed,source):
    w,h=guide.size; assert w%2==0 and h%2==0
    guide.save(HERE/f'guide_full_{name}.png');mask.save(HERE/f'mask_full_{name}.png')
    guide.resize((w//2,h//2),Image.Resampling.NEAREST).save(HERE/f'guide_{name}.png')
    low=np.asarray(mask).reshape(h//2,2,w//2,2).min(axis=(1,3))
    Image.fromarray(low).save(HERE/f'mask_{name}.png')
    (HERE/f'prompt_{name}.txt').write_text(prompt,encoding='utf-8')
    assert len(prompt)<=2000
    jobs.append(dict(name=name,endpoint='/inpaint-v3',prompt=f'prompt_{name}.txt',guide=f'guide_{name}.png',mask=f'mask_{name}.png',seed=seed,native_size=[w//2,h//2],atlas_size=[w,h]))
    provenance.append(dict(name=name,original_project_sources=source,grid_scale=2,third_party_images=False))

wall_prompt=(R20/'prompt_wall.txt').read_text(encoding='utf-8')
wall_guide=Image.open(R20/'guide_full_wall.png').convert('RGBA')
wall_mask=Image.open(R20/'mask_full_wall.png').convert('L')
themes=[
 'New original distribution: upper-left seam shoulder has short discontinuous contact clusters; lower-right has finer joined residue. Keep uneven empty gaps.',
 'New original distribution: quiet upper center, slightly stronger irregular deposits at lower-left and upper-right existing joint contacts. No new shapes in the center.',
 'New original distribution: a few fine broken upper contact groups, denser small lower-rim deposits on the right bay. Same restrained warm ivory and cool gray.',
 'New original distribution: old joint contact film thinner on one side, several small connected upper-rim notches and uneven bottom deposits. Do not copy another panel.',
 'New original distribution: short scattered but joined seam deposits at upper and lower real junctions, broad centers calm, different left and right aging density.'
]
for i,theme in enumerate(themes):
    # Shorten the historic overly restrictive long prompt without changing its structural locks.
    prompt='Flat albedo pixel-art material on TWO EXISTING flat ceramic wall bays. Preserve exact seams, color zones, ivory ceramic and slate metal. Cohesive stepped clusters about 2-4 native pixels, selected smaller transitions, 4-6 related flat tones. Quiet intact broad centers, subtle material plane differences; medium readable edge aging attached to true joint shoulders, upper contact and lower metal guard. Upper and lower marks share one pixel vocabulary. No floating stains, fine sprayed noise, giant blotches, cushion/vignette shading, new inset frame, border, bevel, cracks, equipment, lettering, yellow, rust or horror. Black mask is exact protected construction and lamp; white is material only. Do not simulate 3D lighting. '+theme
    add(f'wall_{i+1}',wall_guide,wall_mask,prompt,2026103040+i,['r20 clean wall guide and mask'])

guide=Image.open(WALL/'clean_rear.png').convert('RGBA').crop((688,16,944,272))
mask=Image.open(ROOT/'docs/art/experiments/room1_wall_lamp_r13/source/mask_portal.png').convert('L')
lamp=np.asarray(Image.open(ROOT/'docs/art/experiments/room1_wall_lamp_r13/source/rear_lamp_layer.png').convert('RGBA').crop((688,16,944,272)))[:,:,3]
a=np.array(mask);a[lamp>0]=0;a[:,:2]=0;a[:,-2:]=0;mask=Image.fromarray(a)
add('portal',guide,mask,'Flat albedo pixel-art material of the EXISTING wall bay around a personnel door. Exact opening silhouette, seam cores, lower metal band, lamp and ivory/slate zones stay fixed; edit only white mask. Match ceramic wall art: compact joined 2-4 native pixel clusters with fine broken transitions, few related flat tones, calm intact broad faces. Moderate old seal contact deposits along actual door-opening shoulders and upper/lower contacts. No thick outline, dangling horizontal ears, false door frame, new hardware, new divisions, lettering, bright threshold, warm yellow, rust, black holes, large cloudy shading, fine random speckle or perspective. Both upper and lower wear use the same coherent small cluster vocabulary. This is surface material, never a newly designed door.',2026103049,['r12 clean rear wall at existing portal','r13 exact portal mask and lamp alpha'])

for vi,variant in enumerate('bcd'):
    for ri,role in enumerate(['lid','shell_side','shell_end']):
        guide=Image.open(POD/f'clean_{role}.png').convert('RGBA')
        mask=Image.open(POD/f'final_mask_{role}.png').convert('L')
        prompt=(R20/f'prompt_{role}.txt').read_text(encoding='utf-8')
        prompt+=' Material variation '+variant.upper()+': '+['slightly stronger short deposits at upper-left real contacts, quiet broad centers.','irregular small groups near right-end contacts and lower ledges, a little less wear near the middle.','asymmetric small attached seal deposits, balanced short light/dark shoulder steps, main coating intact.'][vi]
        add(f'{variant}_{role}',guide,mask,prompt,2026103050+vi*3+ri,['r16 original clean structural guide and exact final protection mask', 'r20 accepted cluster language'])

# Two overlapping world-space floor edits. Exact occupied footprints are black
# mask, preserving hidden floor pixels. No route/grid or new objects are drawn.
floor=Image.open(ROOT/'assets/art/room1_floor_variants_r15/floor_with_leaks.png').convert('RGBA')
footprints=json.loads((FLOOR/'pod_footprints.json').read_text())['pods']
mask=Image.new('L',floor.size,255); d=ImageDraw.Draw(mask)
for pod in footprints:d.polygon([tuple(p) for p in pod['pixel_polygon']],fill=0)
for i,x in enumerate([0,752]):
    box=(x,0,x+896,728); guide=floor.crop(box); edit=mask.crop(box)
    # Existing PixelLab art is legitimate project input, all editable floor is
    # replaced by a fresh AI output rather than layered with old coarse marks.
    prompt='Edit this original flat top-down FLOOR ALBEDO guide into coherent pixel-art material. Exact occupied cryopod footprints are black protected mask; all new art is continuous flat floor OUTSIDE them. No objects or scene rendering. Reorganize existing wear using connected 2-4 native pixel clusters and several calm blue-gray coating tones, clean stepped boundaries with some smaller transitions. Most floor remains continuous quiet matte mineral composite. Preserve cool desaturated blue-gray #5A6C73 family, restrained contrast; broad material variation is subtle, with more readable uneven contact film tightly attached to actual footprint edges and wall perimeter. Existing small coolant residues stay localized at the same occupied corners, not new scattered pools. No tile joints, grid, route markings, text, perspective, cast light, shiny reflection, large pale patches, long scratches, bright outlines, yellow, green, brown, rust or random peppered noise. The whole image is ONE continuous surface. Preserve the original spatial arrangement, not exact old texture noise. Draw fresh material pixels throughout white mask. Carry material naturally through the canvas edges; never frame the image.'
    add(f'floor_{i+1}',guide,edit,prompt,2026103070+i,['r15 PixelLab floor_with_leaks, same exact world coordinates', 'measured existing pod footprint polygons'])

(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
(HERE/'input_provenance.json').write_text(json.dumps({'jobs':provenance,'third_party_content_submitted':False,'no_procedural_art':True,'wall_original_r20_reused':True,'pod_variant_a_original_r20_reused':True,'floor_crops':[[0,0,896,728],[752,0,1648,728]]},indent=2),encoding='utf-8')
print('R22_PREPARED',len(jobs),'PixelLab jobs; estimate',len(jobs)*10,'generations')
