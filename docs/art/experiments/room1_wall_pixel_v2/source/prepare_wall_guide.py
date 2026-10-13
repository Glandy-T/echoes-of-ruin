"""Original wall v2 design: wide continuous diffuser and legible aging.
No external reference images are supplied to AI.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import json

ROOT=Path(__file__).resolve().parents[1]
W,H=400,272
P={'base':'#d3d6c9','light':'#e7e7d4','shade':'#c1c8bc',
 'warm':'#d9d5c3','coat':'#cad0c0','worn':'#b5bead','deposit':'#9da998',
 'metal':'#a6b2a9','metal_light':'#d4dcce','metal_mid':'#889d93',
 'metal_dark':'#627970','gasket':'#475f59','lamp':'#d5e4e5','white':'#edf3ef'}
im=Image.new('RGB',(W,H),P['base']);d=ImageDraw.Draw(im)
# Controlled material fields: broad stepped value regions, sparse worn islands.
d.polygon([(0,45),(400,45),(400,49),(347,49),(347,50),(259,50),(259,52),
 (173,52),(173,50),(88,50),(88,49),(0,49)],fill=P['shade'])
d.polygon([(0,2),(400,2),(400,6),(306,6),(306,7),(199,7),(199,8),
 (104,8),(104,6),(0,6)],fill=P['coat'])
d.polygon([(53,81),(79,81),(79,78),(139,78),(139,79),(157,79),(157,82),
 (151,82),(151,84),(125,84),(125,86),(77,86),(77,85),(53,85)],fill=P['light'])
d.polygon([(222,139),(245,139),(245,135),(289,135),(289,138),(311,138),
 (311,144),(297,144),(297,147),(257,147),(257,146),(233,146),(233,144),(222,144)],fill=P['coat'])
d.polygon([(62,224),(94,224),(94,220),(133,220),(133,217),(157,217),
 (157,218),(190,218),(190,222),(177,222),(177,228),(141,228),
 (141,230),(94,230),(94,229),(62,229)],fill=P['shade'])
d.polygon([(292,206),(306,206),(306,203),(322,203),(322,201),(332,201),
 (332,204),(345,204),(345,208),(334,208),(334,211),(308,211),(308,209),(292,209)],fill=P['warm'])
# Integrated lighting cross-section, not an extra machine on the wall.
# Diffuser rows18..35 are 18 texels = .225m, centered at the same height as v1.
d.rectangle((0,12,399,41),fill=P['metal'])
d.rectangle((0,12,399,13),fill=P['metal_light'])
d.line((0,14,399,14),fill=P['metal_mid'])
d.rectangle((0,15,399,17),fill=P['gasket'])
d.rectangle((0,18,399,35),fill=P['lamp'])
d.line((0,18,399,18),fill=P['white'])
d.line((0,19,399,19),fill='#e1eae7')
d.rectangle((0,32,399,35),fill='#bdcdd0')
d.rectangle((0,36,399,38),fill=P['gasket'])
d.line((0,39,399,39),fill=P['metal_mid'])
d.line((0,40,399,40),fill=P['metal_light'])
d.rectangle((0,42,399,44),fill=P['shade'])
# Subtle service-section joins exist in the recess surround; diffuser continuous.
for x in [92,306]:
 d.rectangle((x,12,x+1,17),fill=P['metal_dark'])
 d.line((x+2,12,x+2,16),fill=P['metal_light'])
 d.rectangle((x,36,x+1,40),fill=P['metal_dark'])
 d.line((x+2,38,x+2,40),fill=P['metal_light'])
 # Gasket aging at a sheltered transition, not random body speckles.
 d.polygon([(x-12,42),(x+9,42),(x+9,43),(x+3,43),(x+3,45),
 (x-4,45),(x-4,44),(x-12,44)],fill=P['deposit'])
# Long-life lower protection band with readable rolled lip and a dark base seal.
d.line((0,248,399,248),fill=P['shade'])
d.rectangle((0,249,399,251),fill=P['gasket'])
d.line((0,252,399,252),fill=P['metal_light'])
d.rectangle((0,253,399,266),fill=P['metal'])
d.line((0,254,399,254),fill=P['shade'])
d.rectangle((0,264,399,266),fill=P['metal_mid'])
d.rectangle((0,267,399,269),fill=P['metal_dark'])
d.rectangle((0,270,399,271),fill=P['gasket'])
# Meaningful old wear from contact on the band and deposits along its upper lip.
for x,y,length in [(53,257,20),(206,260,27),(345,259,15)]:
 d.line((x,y,x+length,y),fill=P['metal_light'])
 d.line((x+3,y+1,x+length-4,y+1),fill=P['metal_dark'])
 d.line((x+5,y+2,x+length-2,y+2),fill=P['metal_mid'])
for x in [108,279]:
 d.polygon([(x-18,248),(x+23,248),(x+23,246),(x+17,246),
 (x+17,245),(x+7,245),(x+7,242),(x-4,242),(x-4,243),
 (x-13,243),(x-13,245),(x-18,245)],fill=P['worn'])
 d.line((x-13,247,x+14,247),fill=P['deposit'])
(ROOT/'guides').mkdir(parents=True,exist_ok=True)
im.save(ROOT/'guides/wall_layout.png')
prompt=('Refine this original flat game wall texture into expertly controlled hand-painted pixel art, '
 'same 400x272 layout. Opaque front elevation, no perspective or 3D render. '
 'Warm ivory mineral/ceramic composite wall, #D3D6C9 base, #E7E7D4 light, #C1C8BC shade. '
 'Create READABLE medium-scale material color fields and carefully shaped worn pixel clusters. '
 'Long-life future automated cryogenic facility, 80-90 years old: sound main structure, aging '
 'in mineral facing tone, edge deposits, old abrasion, dull oxidized metal and overdue seals. '
 'Art direction is precise integrated technology with tangible time history. Preserve the wide '
 'continuous very pale gray cyan-white diffuser (#D5E4E5, low saturation) exactly at rows18-35; '
 'it is a 22.5cm embedded band, soft low brightness, not vivid blue or neon. Keep its light '
 'face unbroken to both image edges. Refine its layered metal housing, dark recess, edge return '
 'and tiny surround-only service joins. Lower 25cm metal protection band has layered lip, seal '
 'and coherent old contact scuffs. Keep material differences and age clearly visible at game-camera '
 'scale. Use stepped pixel clusters and restrained value ramps, not smooth photographic shading, '
 'blur or isolated random dots. Increase readable surface history compared with a flat blank wall; '
 'avoid chaotic grunge. Keep the main wall continuous, with only a few purposeful connections '
 'at lighting and protection structure. Left/right field should repeat seamlessly. '
 'NO end-frame borders, regular wall panel grid, vents, pipes, bolts, screens, symbols, text, '
 'objects, heavy rust, mold, wide peeling, exposed machines, or broken light sections.')
(ROOT/'source/wall_edit_prompt.txt').write_text(prompt,encoding='utf-8')
(ROOT/'source/guide_record.json').write_text(json.dumps({
 'image_size':[W,H],'section_m':[5,3.4],'trial_density_texels_m':80,
 'palette':P,'strip_pixels_y':[18,35],'strip_center_m':3.0625,
 'strip_visible_height_m':.225,'protection_band_height_m':.25,
 'status':'user chose 20-25cm continuous diffuser and suggested softly blue light; pale gray cyan-white trial, exact color not yet approved',
 'v1_feedback':'light too thin, technology and history insufficient; strengthen structured material details and localized age',
 'input':'original authored guide only; no Pixel Canals image/model/texture supplied to AI'
},indent=2),encoding='utf-8')
print('Wall v2 guide prepared:',im.size,'prompt chars:',len(prompt))
