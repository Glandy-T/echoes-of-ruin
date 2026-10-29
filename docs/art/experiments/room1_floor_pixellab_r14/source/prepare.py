"""Prepare original flat guides and geometric masks only; no painted aging."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import json, shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
BASE=(90,108,115)
HERE.mkdir(parents=True,exist_ok=True)
shutil.copyfile(ROOT/'docs/art/experiments/room1_floor_palette_r9/source/pod_footprints.json',HERE/'pod_footprints.json')
for name in ['base','edge','contact_a','contact_b','leak_a','leak_b']:
    size=(256,64) if name=='edge' else (256,256)
    im=Image.new('RGB',size,BASE); mask=Image.new('L',size,255)
    if name=='edge':
        ImageDraw.Draw(im).rectangle((0,0,255,7),fill=(37,57,67))
        ImageDraw.Draw(mask).rectangle((0,0,255,7),fill=0)
    elif name!='base':
        # Canonical measured pod support footprint: 84x176 px, 80 px/m.
        body=Image.new('L',size);d=ImageDraw.Draw(body)
        d.polygon([(86,41),(92,40),(164,40),(170,41),(170,216),(86,216)],fill=255)
        im.paste((37,57,67),mask=body)
        radius=21 if name.startswith('contact') else 39
        outer=body.filter(ImageFilter.MaxFilter(radius*2+1))
        import numpy as np
        mask=Image.fromarray(((np.array(outer)>0)&(np.array(body)==0)).astype('uint8')*255)
        body.save(HERE/'canonical_footprint.png')
    im.save(HERE/f'guide_{name}.png');mask.save(HERE/f'mask_{name}.png')
common='''Pixel art game material, orthographic flat top-down texture, native one-pixel edges and small coherent 1-3 pixel clusters, controlled fine detail. Closed advanced cryogenic facility unused for decades. Restrained cool desaturated blue-gray mineral composite flooring, main color #5A6C73, shadows #415763 and #253943, restrained lighter #7D9298. No yellow, brown, warm green, rust, organic mold, text, tiles, joints, stripes, path markings, perspective, outlines, rendered lighting, cast shadows or glossy highlights. The image is a flat albedo texture, not a scene illustration. Preserve the flat guide's scale and palette. '''
prompts={
'base':'''Create a seamless continuous matte wear-resistant floor coating. Very subtle broad cool color variation with fine sparse mineral pigment clusters. Quiet uniform center, no recognizable stains, no scratches or obvious blobs. Keep variation small and low contrast, never make stones or paving. All four edges must continue seamlessly. No large smooth vector-like regions or big hard blocks.''',
'edge':'''The dark strip at TOP is the wall footprint and must remain fixed. Generate fine accumulated cool gray-blue dust along the floor directly touching the top strip, densest within 2-5 pixels of contact, uneven delicate buildup extending 8-24 pixels into the floor with small coherent pixels. Transition naturally to clean floor by the bottom edge. Detailed medium visible age, not enormous jagged patches. No raised skirting, floor seam or second stripe. Left and right edges continue seamlessly.''',
'contact_a':'''The central dark polygon is an OCCUPIED pod base footprint, not a pool. Preserve it exactly. Only texture the floor OUTSIDE it. Create a narrow connected cool dusty contact halo around its perimeter, denser at corners and feet, subtle old pressure/contact accumulation. Fine visible 1-3 pixel deposits within 3-12 pixels of the outline with sparse lighter outer pigment. Do not draw extra mechanical objects. Outer area stays the guide's flat floor blue-gray. No rectangular outer patch boundary.''',
'contact_b':'''The central dark polygon is an OCCUPIED pod base footprint, not a pool. Preserve it exactly. Only texture the floor OUTSIDE it. Another variation of narrow cool dusty contact traces, fine granular buildup attached to edges and corners, asymmetrical small breaks and density variation, restrained visible 1-3 pixel clusters. Keep traces close to footprint, mostly 3-12 pixels wide. Outer area stays the guide's flat floor blue-gray. Do not draw objects or a rectangle around the patch.''',
'leak_a':'''The central dark polygon is an OCCUPIED pod base footprint, preserve it exactly. Generate an old dried coolant seep on the floor OUTSIDE its LOWER RIGHT corner: irregular thin dark cool blue-gray wet-looking remnant and fine desaturated gray-blue dry tide edge, a small spreading connected stain 15-35 pixels wide. Only one localized seep, not a halo around every edge. Crisp small pixel clusters, transparent-looking material discoloration on same floor. No bright puddle, cyan glow, yellow crust or new geometry. Outer boundary blends into flat guide floor.''',
'leak_b':'''The central dark polygon is an OCCUPIED pod base footprint, preserve it exactly. Generate a DIFFERENT old dried coolant seep on the floor OUTSIDE its LEFT long edge near its lower end: irregular elongated connected cool dark gray-blue residue, fine subtle lighter dried edge and sparse fractured mineral pixels, 12-30 pixels wide and 45-70 pixels long. Only one localized seep, not all edges. No cartoon outlines, bright puddle, cyan glow, yellow crust or extra geometry. Outer boundary blends into flat guide floor.'''}
for name,prompt in prompts.items():(HERE/f'prompt_{name}.txt').write_text(common+prompt,encoding='utf-8')
original=ROOT/'docs/art/experiments/room1_wall_lamp_r13/source/job.py'
job=original.read_text(encoding='utf-8').replace('choices=("portal","lamp_a","lamp_b")','choices=("base","edge","contact_a","contact_b","leak_a","leak_b")').replace('kind="portal" if a.variant=="portal" else "lamp"','kind=a.variant').replace('2026102961+["portal","lamp_a","lamp_b"].index(a.variant)','2026102981+["base","edge","contact_a","contact_b","leak_a","leak_b"].index(a.variant)')
(HERE/'job.py').write_text(job,encoding='utf-8')
for name,old in [('base2','base'),('leak_c','leak_b')]:
    for kind in ['guide','mask']:shutil.copyfile(HERE/f'{kind}_{old}.png',HERE/f'{kind}_{name}.png')
(HERE/'prompt_base2.txt').write_text(common+'''Texture the ENTIRE floor, not just sparse specks: create subtle broad irregular swaths of worn mineral composite coating with finely pixelated irregular boundaries and smaller material color clusters within them. Several interlocking soft cloudy fields of blue-gray, visible but low contrast. The broadest fields roughly 40-90 pixels wide, with organic restrained 1-3 pixel edge clustering. Keep all tones between #51656E and #667C84. No isolated dirt spots, scratches, tiles, smooth gradients or raised rock. Do not leave the entire center a single flat color. The material must feel aged as a whole, yet remain one continuous uniform floor. Tile seamlessly on all sides.''',encoding='utf-8')
(HERE/'prompt_leak_c.txt').write_text(common+'''The central dark polygon is an occupied pod base, preserve it. On the floor along its LEFT lower edge, create ONE old dried seep spreading directly from contact, irregular flat discolored coating and granular dark blue-gray residue in a thin elongated 12-28 pixel wide patch. Fine broken edges that blend into floor. Low to medium contrast, visible as old discoloration. Absolutely no black outline, no closed pool shape, no chain of round puddles or snowman silhouette, no cartoon hard black rim, no highlights, no liquid gloss or deep hole. Mostly small irregular material clusters, not dots alone.''',encoding='utf-8')
for kind in ['guide','mask']:shutil.copyfile(HERE/f'{kind}_contact_a.png',HERE/f'{kind}_contact_c.png')
(HERE/'prompt_contact_c.txt').write_text(common+prompts['contact_a']+' Another fine granular variation. No scratches, long lines, hatch marks, cracks, puddles or outlined patches. Only small pixel dust attached to the contact outline.',encoding='utf-8')
job=job.replace('"leak_a","leak_b"','"leak_a","leak_b","contact_c"')
job=job.replace('"leak_b","contact_c"','"leak_b","contact_c","base2","leak_c"')
job=job.replace('"base2","leak_c"','"base2","leak_c","leak_d"')
job=job.replace('sys.path.insert(0,str(ROOT/"docs/art/experiments/pixellab_direct_api_check_v1/source"))','').replace('from pixellab_direct import credential,request','from pixellab_api import credential,request')
(HERE/'job.py').write_text(job,encoding='utf-8')
pods=json.loads((HERE/'pod_footprints.json').read_text())['pods']
for p in pods:
    xs=[v[0] for v in p['pixel_polygon']];ys=[v[1] for v in p['pixel_polygon']]
    print(p['pod'],(min(xs),min(ys),max(xs),max(ys)))
