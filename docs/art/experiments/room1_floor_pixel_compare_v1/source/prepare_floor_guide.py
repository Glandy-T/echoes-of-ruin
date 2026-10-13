"""Original seamless material guide: matte continuous floor, no zoning or dirt."""
from pathlib import Path
from PIL import Image, ImageDraw
import json

ROOT=Path(__file__).resolve().parents[1]
W=H=400
P={'base':'#5a6c73','light':'#7d9298','shade':'#415763','deep':'#253943',
 'soft_light':'#607279','soft_shade':'#56686f','midtone':'#5c6e75'}
im=Image.new('RGB',(W,H),P['base']);d=ImageDraw.Draw(im)
# Broad, connected, very shallow pigment/material fields, no isolated stains.
fields=[([(0,53),(58,53),(58,51),(142,51),(142,54),(189,54),(189,58),
 (139,58),(139,61),(71,61),(71,59),(0,59)],P['midtone']),
 ([(209,168),(251,168),(251,165),(313,165),(313,168),(367,168),
 (367,172),(400,172),(400,178),(354,178),(354,176),(284,176),
 (284,180),(236,180),(236,175),(209,175)],P['soft_shade']),
 ([(37,298),(76,298),(76,295),(144,295),(144,297),(189,297),(189,302),
 (174,302),(174,305),(119,305),(119,307),(67,307),(67,304),(37,304)],P['soft_light'])]
for shape,c in fields:d.polygon(shape,fill=c)
# Fine compact mineral/coating texture is represented by connected pixel marks.
for x,y,shape in [(34,103,[(0,0),(4,0),(4,1),(7,1),(7,2),(2,2),(2,1),(0,1)]),
 (115,189,[(0,0),(6,0),(6,1),(10,1),(10,2),(3,2),(3,1),(0,1)]),
 (242,278,[(0,0),(3,0),(3,1),(7,1),(7,2),(0,2)]),
 (323,70,[(0,0),(5,0),(5,1),(8,1),(8,2),(2,2),(2,1),(0,1)]),
 (89,348,[(0,0),(7,0),(7,1),(10,1),(10,2),(3,2),(3,1),(0,1)])]:
 d.polygon([(x+dx,y+dy) for dx,dy in shape],fill=P['soft_shade'])
(ROOT/'guides').mkdir(parents=True,exist_ok=True)
im.save(ROOT/'guides/floor_material_layout.png')
prompt=('Refine this ORIGINAL seamless floor material guide into carefully authored pixel-art '
 'albedo for a low-poly 3D game. Exactly 400x400 opaque image, flat top view of MATERIAL ONLY, '
 'no room, perspective, light source or objects. A continuous sealed matte hard-wearing '
 'composite floor in a precise long-life cryogenic facility. Low-saturation blue-gray, '
 'base #5A6C73, restrained raised tones toward #7D9298, structural shadow family #415763. '
 'The surface is continuous and integrated, not tiles or separate panels. Use connected, '
 'small-scale, restrained pixel clusters and broad extremely shallow material-value changes '
 'to express a dense fine matte finish. Keep most pixels near the blue-gray base. '
 'Texture must be perceptible but calm, clean and usable in a fixed low-angle game camera. '
 'No smooth photo realism, blur, noisy salt-and-pepper dots or haphazard dirt. '
 'NO isolated stain patches, rust, peeling, holes, cracks, footprints, scratches, damage, '
 'debris, puddles, dramatic lighting gradients, panel borders, seams, regular grids, '
 'roads, lanes, arrows, text, symbols, equipment or objects. '
 'Do NOT add aging in this material tile: age will be placed separately at actual room edges '
 'and known contact positions. All four image edges must repeat seamlessly. '
 'Aim for readable hand-painted pixel material organization, not a flat fill with a few dirt spots.')
(ROOT/'source/floor_edit_prompt.txt').write_text(prompt,encoding='utf-8')
(ROOT/'source/guide_record.json').write_text(json.dumps({
 'size':[400,400],'material_section_m':[5,5],'trial_density_texels_per_m':80,
 'palette':P,'surface':'user selected continuous matte hard-wearing floor',
 'comparison':'A uniform color; B same material plus soft existing circulation tone zoning',
 'input':'original authored material guide only; no external Pixel Canals asset',
 'aging':'not in AI tile; limited location-specific room-edge/contact finish later',
 'material_composition':'exact future composite chemistry TBD; visual finish only'
},indent=2),encoding='utf-8')
print('Floor guide prepared',im.size,'prompt chars',len(prompt))
