"""Original flat guides + protected project-owned r24 style context; no reference uploads."""
from pathlib import Path
import json
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
ASSET=ROOT/'assets/art/cryo_stair_material_sample_v1'
ASSET.mkdir(parents=True,exist_ok=True)
wall=Image.open(ROOT/'assets/art/room1_wall_detail_full_r24/wall_left.png').convert('RGB')
wall.crop((0,40,728,272)).save(ASSET/'wall_body.png')
context=wall.crop((174,16,238,272))
common='''Create finished native pixel-art albedo for an indoor emergency fire-stair material in a sealed decades-old cryogenic facility. Output is FLAT texture, never a perspective picture or rendered object. Only repaint the white masked area. The protected 64px strip on the right is our own approved wall texture, solely a pixel-cluster / finish reference; do not copy its panel joints or lamp into the new mineral surface. Use crisp intentional small and medium pixel clusters at native resolution, readable fine aggregate and restrained broader material variation, no smooth airbrushed gradients, no antialiasing or subpixel noise. Main mineral gray #7C8380, lighter #939A91, shadows #5E6B68, cooler dark #455553. Matte dense mineral/ceramic composite, not metallic, not glossy. Decades of dry enclosed storage: material variation and old contact polishing, no yellow/brown rust, no random scattered dirt blobs, no large peeling chunks, no cracks, no brick/tile grid, no road markings, no text, no glow, no cast shadows or baked directional lighting. Do not leave the surface nearly blank; fine patterned mineral pixel clusters should remain visible at native size. Shared material across stair treads and landings, physically continuous. The grain is architectural, smaller and quieter than wood or broken concrete.'''
jobs=[]
for idx,name in enumerate(('mineral_a','mineral_b','tread_edge')):
    guide=Image.new('RGB',(256,256),'#7C8380')
    guide.paste(context,(192,0))
    mask=Image.new('L',(256,256),0)
    if name=='tread_edge':
        ImageDraw.Draw(mask).rectangle((0,0,191,63),fill=255)
        # Straight original structure guide, not authored weathering.
        ImageDraw.Draw(guide).rectangle((0,0,191,3),fill='#939A91')
        extra=' The editable area is a 192x64 pixel straight stair nosing material strip. Top 3-4 rows are a subtly worn mineral front edge, NOT a painted stripe. Remaining rows transition into the SAME mineral material, with fine contact wear. No bright border, warning stripe, black outline or metal trim. Keep the edge variation continuous across width; no isolated chips cut out of the shape.'
        # Final delivery selection: the generated nosing occurred at rows48..63.
        # Guide/mask are unchanged from the actual submitted request.
        crop=[0,48,192,64]
    else:
        ImageDraw.Draw(mask).rectangle((0,0,191,255),fill=255)
        extra=(' Editable material is 192x256 pixels. Produce variant '+('A: fine gray mineral aggregate with localized soft dry contact wear.' if idx==0 else 'B: same palette and grain size as A, different broad aggregate grouping and contact patina, not a new material.')+' Make left and right boundaries blend for repeating use. No edge framing or perimeter dirt, since this is a repeating material field, not one panel.')
        crop=[0,0,192,256]
    guide.save(HERE/f'guide_{name}.png');mask.save(HERE/f'mask_{name}.png')
    (HERE/f'prompt_{name}.txt').write_text(common+extra,encoding='utf-8')
    jobs.append(dict(name=name,endpoint='/inpaint-v3',prompt=f'prompt_{name}.txt',guide=f'guide_{name}.png',mask=f'mask_{name}.png',seed=2026110501+idx,native_size=[256,256],retained_crop=crop))
(HERE/'requests.json').write_text(json.dumps(jobs,indent=2),encoding='utf-8')
print('Prepared 3 original guides, protected owned wall context, and native r24 body crop.')
