"""4x material-grid guides. PixelLab, not this script, creates every art mark."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
OLD=ROOT/'docs/art/experiments/room1_pixel_cluster_r20/source'
for name in ['raw','editable','evidence','source/layers']:(EXP/name).mkdir(parents=True,exist_ok=True)
for name in ['jobs.py','pixellab_api.py']:
    text=(OLD/name).read_text(encoding='utf-8')
    (HERE/name).write_text(text.replace('R20_PIXELLAB_QUEUE_COMPLETE','R21_PIXELLAB_QUEUE_COMPLETE'),encoding='utf-8')
common='''Create BOLD, GRAPHIC pixel-art albedo on this EXACT original industrial UV guide. This is a deliberately very coarse native pixel grid for a low-poly game. Clearly readable 1-3 native-pixel clusters, strong stepped contours and 3-4 distinct FLAT light/mid/dark colors per material; make color groups read at small gameplay size. NO fine speckle, dithering, smooth grain, airbrushing or soft gradients. Broad surfaces need organized connected tone shapes, NOT a blank single color with a few dots. Preserve warm gray ivory matte ceramic and cool blue-slate supports; stronger cool-gray contrast, never yellow or brown. Place stepped contact wear at real existing edge joints, corners and recesses; join nearby marks into deliberate groups. Structure is already supplied: preserve its exact positions and only edit WHITE pixels. No perspective, cast shadows, fake 3D rendering, extra panels, new grooves, inner frames, outline rings, rounded pillow shading, cracks, holes, new equipment, lettering, orange rust, green moss, huge polygon stains or random floating blobs. '''
extras={
 'wall':'''Two EXISTING FLAT ceramic wall bays. Use a compact upper edge cluster and an uneven lower/side-joint cluster, with broader flat pale-gray material tone breaks attached to them, readable stair-step boundaries. Keep the middle less busy but do not leave the entire face featureless. All marks must belong to those existing edge zones; NO invented inset border, dark rectangular outline, rounded highlight or face-wide vignette. Lamp and seam cores stay protected.''',
 'lid':'''Cryopod cover. Preserve every window/frame/number location. Draw clearly grouped flat light and dark accents following EXISTING shoulder/bevel bands, compact coarse notches at gasket corners, and two or three broad shallow face-tone groups. These are pixel-painted material planes, not new surface cutouts. No new outlined inset panel or all-over micro scratches.''',
 'shell_side':'''Cryopod long casing. Preserve the existing top support band, recess, vents and bottom band. Simplify fine texture into chunky readable light/mid/dark bands on existing shoulders and a few joined contact-wear groups. A graphic flat material, no shiny gradients, no tiny noise, no new vents or lettering.''',
 'shell_end':'''Cryopod short end. Keep the ID plate exact. Broad angular light/mid/dark blocks follow the EXISTING top rim and supporting foot corners; coarse attached wear groups break those edges. No rounded cushion, new frame, screen or large detached chips.'''
}
jobs=[];provenance=[]
for index,key in enumerate(['wall','lid','shell_side','shell_end']):
    guide=Image.open(OLD/f'guide_full_{key}.png').convert('RGBA')
    mask=Image.open(OLD/f'mask_full_{key}.png').convert('L')
    baseline=Image.open(OLD/f'baseline_{key}.png').convert('RGBA')
    guide.save(HERE/f'guide_full_{key}.png');mask.save(HERE/f'mask_full_{key}.png');baseline.save(HERE/f'baseline_{key}.png')
    w,h=guide.size;assert w%4==0 and h%4==0
    nw,nh=w//4,h//4;cw,ch=max(32,nw),max(32,nh);x,y=(cw-nw)//2,(ch-nh)//2
    small=guide.resize((nw,nh),Image.Resampling.NEAREST)
    lowmask=Image.fromarray(np.array(mask).reshape(nh,4,nw,4).min(axis=(1,3)))
    canvas=Image.new('RGBA',(cw,ch),small.getpixel((0,0)));canvas.paste(small,(x,y))
    safe_mask=Image.new('L',(cw,ch));safe_mask.paste(lowmask,(x,y))
    canvas.save(HERE/f'guide_{key}.png');safe_mask.save(HERE/f'mask_{key}.png')
    prompt=common+extras[key];assert len(prompt)<=2000
    (HERE/f'prompt_{key}.txt').write_text(prompt,encoding='utf-8')
    jobs.append({'name':key,'endpoint':'/inpaint-v3','prompt':f'prompt_{key}.txt','guide':f'guide_{key}.png','mask':f'mask_{key}.png','seed':2026103041+index,'native_size':[cw,ch],'content_box':[x,y,x+nw,y+nh],'atlas_size':[w,h]})
    provenance.append({'role':key,'source':str((OLD/f'guide_full_{key}.png').relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256((OLD/f'guide_full_{key}.png').read_bytes()).hexdigest(),'scale':4,'canvas_padding_black_masked':cw!=nw or ch!=nh,'mask':'4x4 minimum; no partially protected block is editable','old_aging_submitted':False})
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
(HERE/'input_provenance.json').write_text(json.dumps({'inputs':provenance,'third_party_images_submitted':False,'art_synthesis_by_scripts':False},indent=2),encoding='utf-8')
baseline=json.loads((OLD/'baseline_file_hashes.json').read_text())
locked=[str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'assets/art/room1_pixel_cluster_r20').glob('*.png')]
locked+=['scripts/dev/room1_pixel_cluster_r20.gd','scripts/dev/room1_pixel_cluster_wall_r20.gdshader','scripts/dev/room1_pixel_cluster_pod_r20.gdshader']
baseline.update({p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in locked})
(HERE/'baseline_file_hashes.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8')
print('R21_PREPARED 4 PixelLab jobs; 4x material grid, protected 32px minimum canvases')
