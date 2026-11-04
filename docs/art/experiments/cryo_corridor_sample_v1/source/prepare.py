"""Original structural guides only. PixelLab supplies all material painting."""
from pathlib import Path
import json,shutil,hashlib
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
EXP=HERE.parent
ROOT=HERE.parents[4]
for folder in ['raw','editable','evidence']:(EXP/folder).mkdir(parents=True,exist_ok=True)
for filename in ['pixellab_api.py']:
 shutil.copy2(ROOT/'docs/art/experiments/room1_wall_detail_r23/source'/filename,HERE/filename)
# Two 1.6m bays, 3.2m tall. These lines describe construction, not painted aging.
wall=Image.new('RGB',(256,256),(141,153,152)); d=ImageDraw.Draw(wall)
d.rectangle((0,232,255,255),fill=(68,84,87))
d.rectangle((127,0,128,231),fill=(64,79,82))
d.rectangle((0,22,255,27),fill=(43,61,66))
wall.save(HERE/'guide_wall.png')
floor=Image.new('RGB',(384,192),(76,92,98));floor.save(HERE/'guide_floor.png')
floor.crop((0,0,256,192)).save(HERE/'guide_floor_256.png')
Image.new('L',(256,192),255).save(HERE/'mask_floor_256.png')
for key,size in [('wall',(256,256)),('floor',(384,192))]:
 Image.new('L',size,255).save(HERE/f'mask_{key}.png')
prompts={
'wall':'''Paint this original project flat orthographic wall ALBEDO at native 256x256 resolution. Two 1.6m wide modular wall panels of an abandoned cryogenic facility personnel corridor, understated cool gray ceramic-coated metal, dark charcoal lower kickplate. Keep exact panel split at x127-128, horizontal recessed lighting channel at y22-27, kickplate begins y232. No perspective. Native fine pixel clusters, restrained medium tones, clear irregular contact deposits grouped along the real central seam, lower plate junction and top channel; broken tiny edge flecks gradually thin into intact broad faces. Give BOTH panels substantial but controlled layered material information; subtle uneven surface wear, not empty flat areas or giant stains. Cool desaturated blue-gray, gray-green and neutral gray only. No rusty orange, yellow, moss, cracks, graffiti, text, panels within panels, extra equipment or invented doors. No white glowing borders, baked illumination, gradients, smooth painting, blur or scattered pepper noise. This is a game texture, not a scene illustration. Keep channel dark because the separate 3D lamp provides illumination. Preserve broad simple architecture; detailed native 1-3px edges and coherent clusters. Entire image editable; retain all specified structural positions.''',
'floor':'''Paint this original flat 384x192 ALBEDO guide into a continuous seamless-looking cool dark slate-gray resin personnel-corridor floor for an abandoned cryogenic facility. Top-down orthographic surface only, NO perspective, NO tile grid, NO diagonal grid, NO panel seams, NO frame or border. Fine native pixel-art clusters, subdued low contrast layered material, restrained irregular scuff traces and gentle contact accumulation near top edge where wall meets floor. Main walking strip remains readable, intact and quieter, with a few small broken wear clusters naturally spread through it. More coherent material information than blank flat color, but no uniform speckle or random noise, giant patches, puddles, rust, yellow, brown, moss, cracks or debris. No lighting gradients, shadows, glowing marks, directional arrows, text or equipment. Cool gray-blue with faint desaturated gray-green undertone; broad values close to supplied base. Crisp native 1-3px detail, no enlarged pixels, smooth brushwork or blur. Entire image is editable. This is the full 4.8m by 2.4m unique corridor sample, not a repeating tile.'''
}
jobs=[]
for i,(key,prompt) in enumerate(prompts.items()):
 (HERE/f'prompt_{key}.txt').write_text(prompt,encoding='utf-8')
 jobs.append(dict(name=key,endpoint='/inpaint-v3',prompt=f'prompt_{key}.txt',guide=f'guide_{key}.png',mask=f'mask_{key}.png',seed=2026110401+i))
if not (HERE/'requests.json').exists():
 (HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
if not (HERE/'input_provenance.json').exists():
 (HERE/'input_provenance.json').write_text(json.dumps({'inputs':'Original flat structural guides prepared by prepare.py; no aging painted by script','third_party_images_uploaded':False,'native_density_px_m':80,'wall_bounds_godot':[6.6,9.8,0,3.2,-11.9],'floor_bounds_godot':[6.6,9.8,-11.9,-9.5],'floor_native_resolution':[256,192],'source':'Frozen route_v3 GLB, W032 front z=-11.9, corridor width 2.4m','baseline_commit':'68360d5','lighting':'New sample-only realtime lights; no inherited lightmap reused'},indent=2),encoding='utf-8')
paths=['project.godot','scripts/dev/room1_door_window_r30.gd','assets/art/cryo_building_room1_route_v3/room1_west_route_v3.glb']
paths += [p.relative_to(ROOT).as_posix() for p in (ROOT/'assets/art/room1_door_window_r30').glob('*.png')]
if not (HERE/'baseline_hashes.json').exists():
 (HERE/'baseline_hashes.json').write_text(json.dumps({p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},indent=2))
print('Prepared 2 original guides. No third-party reference input.')
