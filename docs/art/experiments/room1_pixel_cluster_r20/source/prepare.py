"""Project-owned structural guides, conservative masks and a 2x material grid.

No dirt or material art is synthesized here: PixelLab creates every new mark.
"""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent; EXP=HERE.parent; ROOT=HERE.parents[4]
POD=ROOT/'docs/art/experiments/room1_pod_pixellab_r16/source'
WALL=ROOT/'docs/art/experiments/room1_wall_pixellab_r12/source'
for name in ['source/layers','raw','editable','evidence']:(EXP/name).mkdir(parents=True,exist_ok=True)
shutil.copyfile(POD/'pixellab_api.py',HERE/'pixellab_api.py')
common='''Edit this flat original UV material guide into deliberate chunky pixel art for a low-poly 3D game. Keep exact panel outlines, existing color zones, recesses and functional features. Use cohesive stepped pixel CLUSTERS, crisp hard edges, about 4-6 flat tones per material, readable short light/dark edge bands. Material marks should form connected shapes 2-4 native pixels across with selected smaller transitions, not an even spray of tiny dots. Reduce fine texture noise. Preserve warm gray ivory matte ceramic and cool slate-gray supports. Age belongs to existing seams, seal contact and lower undercuts in a sealed indoor cryogenic facility. Moderate age, intact material, quiet broad centers. No new seams, extra parts, perspective, cast-light gradients, smooth airbrushing, dithering, checkerboard, giant polygon stains, rectangular dirt blocks, rust, yellow, moss, gore, cracks or new lettering. Redesign only the WHITE mask; BLACK is exact protected construction. '''
jobs=[]; provenance=[]
for index,key in enumerate(['wall','lid','shell_side','shell_end']):
    if key=='wall':
        guide_path=WALL/'clean_left.png'; guide=Image.open(guide_path).convert('RGBA').crop((432,16,688,272))
        mask=Image.open(WALL/'mask.png').convert('L')
        a=np.array(mask)
        lamp=np.asarray(Image.open(ROOT/'docs/art/experiments/room1_wall_lamp_r13/source/left_lamp_layer.png').convert('RGBA').crop((432,16,688,272)))[:,:,3]
        a[lamp>0]=0;a[:,:2]=0;a[:,-2:]=0
        mask=Image.fromarray(a)
        baseline=Image.open(ROOT/'assets/art/room1_wall_lamp_r13/wall_left.png').convert('RGBA').crop((432,16,688,272))
        extra='Two existing ceramic wall bays, without changing divisions. Use the SAME coherent coarse stepped cluster language at upper and lower joints; no fine speckled top band. Keep centers calm. Attach contact residue to real seam shoulders and lower base; no detached stains, floating gray islands, pale blotches or large polygon chips in panel centers. Selected short light/dark steps describe existing edge thickness, not new grooves or hardware. No dark wall-wide frame.'
    else:
        guide_path=POD/f'clean_{key}.png';guide=Image.open(guide_path).convert('RGBA')
        mask=Image.open(POD/f'final_mask_{key}.png').convert('L')
        baseline=Image.open(ROOT/f'assets/art/room1_pod_pixellab_r16/variant_a/{key}.png').convert('RGBA')
        extra={'lid':'Cryopod cover: preserve the observation window, all frame bands and ID. Organize edge wear into sparse joined notches and compact seal residue clusters; readable 2-3 tone face transitions, no broad peeling patches.',
               'shell_side':'Cryopod long side: preserve every narrow horizontal recess, blue-gray ledge and base. Use a few strong short stepped corner/contact groups and simple flat face tones. No lettering or new hardware.',
               'shell_end':'Cryopod short end: preserve the ID and slate-blue support band. Coherent corner residue and stepped rim highlights, not a thick black outline; no screen or extra compartments.'}[key]
    guide.save(HERE/f'guide_full_{key}.png');mask.save(HERE/f'mask_full_{key}.png');baseline.save(HERE/f'baseline_{key}.png')
    w,h=guide.size;assert w%2==0 and h%2==0
    guide.resize((w//2,h//2),Image.Resampling.NEAREST).save(HERE/f'guide_{key}.png')
    # A half-size pixel is editable only when all four corresponding full pixels are editable.
    low=np.array(mask).reshape(h//2,2,w//2,2).min(axis=(1,3))
    Image.fromarray(low).save(HERE/f'mask_{key}.png')
    prompt=common+extra
    if key=='wall':
        prompt='''Flat albedo pixel-art MATERIAL on TWO EXISTING FLAT wall bays in this original UV guide. Preserve exact existing seams, material boundaries, ivory ceramic and slate metal colors. These are flat continuous architectural wall surfaces, NOT raised panels or cushions. Keep broad ceramic centers essentially ONE FLAT IVORY TONE. No face-wide shading, no vignette, no cloudy gradients, no large shaded silhouette. Draw only moderate irregular contact dust along existing vertical joint shoulders and near the existing upper/lower material edges. Use coherent stepped small clusters, about 2-4 native pixels, with short clean gaps; quieter centers and slightly irregular density. Upper and lower deposits use the same coarse pixel vocabulary. No isolated stains, fine single-pixel spray, uniform mottled noise, yellow, rust or damage. Do NOT add any inner frame, inset rim, extra border, extra bevel, rounded corners, contour ring, groove, light direction, 3D shading or new construction. Never trace a new dark outline inside the bays. Existing dark cores and lamp are BLACK protected pixels. WHITE is material surface only; match the flat guide rather than illustrating a new object. Pixel art with crisp connected marks, not an airbrushed or rendered wall.'''
    (HERE/f'prompt_{key}.txt').write_text(prompt,encoding='utf-8')
    jobs.append({'name':key,'endpoint':'/inpaint-v3','prompt':f'prompt_{key}.txt','guide':f'guide_{key}.png','mask':f'mask_{key}.png','seed':2026103122 if key=='wall' else 2026103020+index,'native_size':[w//2,h//2],'atlas_size':[w,h]})
    provenance.append({'role':key,'source':str(guide_path.relative_to(ROOT)).replace('\\','/'),'source_sha256':hashlib.sha256(guide_path.read_bytes()).hexdigest(),'source_has_legacy_aging':False,'native_grid_scale':2,'mask_method':'2x2 conservative minimum; exact full-size mask restored after nearest enlargement','wall_crop':[432,16,688,272] if key=='wall' else None})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
(HERE/'input_provenance.json').write_text(json.dumps({'inputs':provenance,'third_party_images_submitted':False,'unchanged':['models','UV','layout','camera','resolution','source lightmaps','formal entry','all other nineteen pods']},indent=2),encoding='utf-8')
print('R20_PREPARED 4 bounded PixelLab jobs, project-owned inputs only')
