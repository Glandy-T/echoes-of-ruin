"""Original pixel wall layout for PixelLab text editing, no external art input."""
from pathlib import Path
from PIL import Image, ImageDraw
import json

ROOT=Path(__file__).resolve().parents[1]
P={'base':'#d3d6c9','light':'#e7e7d4','shade':'#c1c8bc',
   'quiet':'#cbd0c2','soft':'#d9dccc','steel':'#b1bab0',
   'steel_dark':'#939f96','joint':'#7f8e85','dust':'#aab2a1',
   'lamp':'#eeeeDF','lamp_edge':'#dce0d1'}
W,H=400,272
im=Image.new('RGB',(W,H),P['base']);d=ImageDraw.Draw(im)
# Native elevation: 5.00 x 3.40m at 80 texels/m. Trial only.
# Restrained stepped value changes describe the coating rather than a grid.
d.polygon([(0,1),(400,1),(400,5),(245,5),(245,4),(112,4),(112,3),(0,3)],fill=P['shade'])
d.line((0,6,W-1,6),fill=P['soft'])
d.polygon([(35,53),(151,53),(151,55),(126,55),(126,57),(57,57),(57,56),(35,56)],fill=P['soft'])
d.polygon([(231,113),(285,113),(285,114),(318,114),(318,116),(276,116),(276,118),(252,118),(252,116),(231,116)],fill=P['quiet'])
d.polygon([(63,204),(77,204),(77,202),(118,202),(118,201),(137,201),(137,204),(111,204),(111,206),(83,206),(83,207),(63,207)],fill=P['quiet'])
# Embedded upper strip: narrow recessed surround, single unbroken diffuser.
d.rectangle((0,23,W-1,31),fill=P['steel_dark'])
d.line((0,23,W-1,23),fill=P['shade'])
d.rectangle((0,25,W-1,28),fill=P['lamp'])
d.line((0,25,W-1,25),fill=P['light'])
d.line((0,29,W-1,29),fill=P['joint'])
d.line((0,31,W-1,31),fill=P['soft'])
# Continuous 0.25m protection band. Light/dark edges imply low relief.
d.line((0,250,W-1,250),fill=P['shade'])
d.line((0,251,W-1,251),fill=P['joint'])
d.line((0,252,W-1,252),fill=P['light'])
d.rectangle((0,253,W-1,268),fill=P['steel'])
d.line((0,254,W-1,254),fill=P['shade'])
d.line((0,265,W-1,265),fill=P['steel_dark'])
d.rectangle((0,269,W-1,271),fill=P['joint'])
# Old contact wear on protection band and dust retained at a sheltered edge.
for x,y,length in [(52,261,9),(203,259,14),(343,264,6)]:
 d.line((x,y,x+length,y),fill=P['shade'])
 d.line((x+2,y+1,x+length-2,y+1),fill=P['steel_dark'])
for x0,x1 in [(103,119),(277,290)]:
 d.line((x0,249,x1,249),fill=P['dust'])
 d.line((x0+3,248,x1-5,248),fill=P['shade'])
(ROOT/'guides').mkdir(parents=True,exist_ok=True)
im.save(ROOT/'guides/wall_layout.png')
prompt=('Refine this ORIGINAL flat wall elevation into a finely authored pixel-art game albedo texture. '
 'Keep the exact layout, flat front-facing view and 400x272 canvas. This is a seamless horizontal '
 '5-meter section of one continuous wall, not a 3D room render. Warm ivory matte mineral/ceramic '
 'composite coating: base #D3D6C9, highlights #E7E7D4, shade #C1C8BC. '
 'Preserve one uninterrupted narrow recessed white light strip at y25-28 and a slim muted-metal '
 'protection band at y252-271. Refine the fine edge light/dark pixels, subtle coating tone variations '
 'and restrained old scuffs on the lower metal. Future sealed long-life facility after 80-90 years: '
 'main wall remains sound, sparse age deposits concentrate beside trims and corners. '
 'Pixel clusters should be deliberately shaped, clean, crisp and richly controlled like high-quality '
 'hand-painted low-poly pixel game surfaces. Keep the broad wall quiet and consistent, with fine '
 'material value changes, not flat color plus sprinkled dots. Very few seams. '
 'NO panel grid, tiles, borders on left/right, vents, pipes, screws, bolts, machines, screens, '
 'letters, numbers, symbols, objects, diagonal lighting, dramatic cast shadows, perspective, '
 'heavy rust, broad peeling, mold, random speckles, or new horizontal bands. '
 'Left and right edges must match for seamless repetition. Opaque image fills the canvas.')
(ROOT/'source/wall_edit_prompt.txt').write_text(prompt,encoding='utf-8')
(ROOT/'source/guide_record.json').write_text(json.dumps({
 'image_size':[W,H],'section_m':[5,3.4],'trial_density_texels_m':80,
 'palette':P,'strip_pixels_y':[25,28],'strip_center_m':3.0625,
 'strip_visible_height_m':.05,'protection_band_height_m':.25,
 'status':'user-confirmed direction; native resolution and exact trim dimensions are review choices',
 'input':'original project pixel guide, no Pixel Canals images/model/textures supplied to AI'
},indent=2),encoding='utf-8')
print('Original wall guide prepared:',im.size)
