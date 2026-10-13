"""Original surface layout guides, authored at native pixel size.
Primary guides go to PixelLab; auxiliary maps are original pixel artwork.
No Pixel Canals images or textures are imported.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
GUIDES = ROOT/'guides'
TEXTURES = ROOT/'textures'
GUIDES.mkdir(parents=True, exist_ok=True)
TEXTURES.mkdir(exist_ok=True)
P = dict(ink='#253943', shadow='#415763', deep='#596e76', steel='#7d9298',
         middle='#9cabad', ivory='#d3d6c9', light='#e7e7d4', edge='#f6edd5',
         teal='#427c84', turquoise='#65a6a6', muted='#c1c8bc', dark='#182b35')

def image(size, color):
    im = Image.new('RGB', size, color)
    return im, ImageDraw.Draw(im)

def panel(d, box, fill, dark=P['shadow'], light=P['edge'], cut=3):
    x0,y0,x1,y1=box
    d.polygon([(x0+cut,y0),(x1-cut,y0),(x1,y0+cut),(x1,y1-cut),
               (x1-cut,y1),(x0+cut,y1),(x0,y1-cut),(x0,y0+cut)],fill=dark)
    d.polygon([(x0+cut,y0+1),(x1-cut,y0+1),(x1-1,y0+cut),(x1-1,y1-cut),
               (x1-cut,y1-1),(x0+cut,y1-1),(x0+1,y1-cut),(x0+1,y0+cut)],fill=fill)
    d.line([(x0+cut,y0+1),(x1-cut,y0+1),(x1-1,y0+cut)], fill=light,width=1)
    d.line([(x0+1,y0+cut),(x0+1,y1-cut)],fill=light,width=1)

def barcode(d,x,y,height=6):
    for i,w in [(0,1),(3,2),(7,1),(10,1),(13,3),(18,1),(21,2),(25,1)]:
        d.rectangle((x+i,y,x+i+w-1,y+height), fill=P['shadow'])

im,d=image((128,256),P['steel'])
# Aligned shoulder and roof bands match the existing chamfer profile.
for x0,x1,c in [(7,15,P['shadow']),(16,22,P['deep']),(23,32,P['middle']),
                (33,94,P['ivory']),(95,104,P['middle']),(105,111,P['deep']),
                (112,120,P['shadow'])]:
    d.rectangle((x0,0,x1,255),fill=c)
for x in [23,33,95,105]: d.line((x,0,x,255),fill=P['light'])
# One central access skin; clear spacing instead of a grid of plates.
panel(d,(37,89,90,222),P['ivory'])
d.rectangle((41,94,86,97),fill=P['light'])
d.rectangle((40,217,86,219),fill=P['middle'])
# Existing head end and foot joint receive edge treatment.
for y in [18,83,232]:
    d.line((24,y,103,y),fill=P['shadow'])
    d.line((25,y+1,102,y+1),fill=P['light'])
for x,y in [(38,91),(87,91),(38,219),(87,219)]:
    d.rectangle((x,y,x+1,y+1),fill=P['deep'])
panel(d,(44,194,83,212),P['muted'],light=P['light'],cut=1)
barcode(d,49,199)
d.line((36,122,37,127),fill=P['edge'])
d.line((90,178,90,184),fill=P['deep'])
im.save(GUIDES/'lid_layout.png')

im,d=image((256,80),P['ivory'])
# z=.0..71875, top->bottom. Functional hierarchy follows actual basin/skirt.
d.rectangle((0,0,255,31),fill=P['middle'])
d.rectangle((0,32,255,38),fill=P['light'])
d.rectangle((0,39,255,44),fill=P['ink'])
d.line((0,44,255,44),fill=P['steel'])
d.rectangle((0,45,255,65),fill=P['ivory'])
d.line((0,46,255,46),fill=P['edge'])
d.rectangle((0,66,255,79),fill=P['shadow'])
d.line((0,66,255,66),fill=P['steel'])
# One short inspection patch; two physical end joints, not repeated panelling.
panel(d,(25,48,81,62),P['muted'],light=P['light'],cut=2)
barcode(d,31,52,height=4)
d.rectangle((66,52,75,56),fill=P['steel'])
for x in [12,241]:
    d.line((x,10,x,66),fill=P['deep'])
    d.line((x+1,10,x+1,64),fill=P['light'])
for x,y in [(14,52),(237,53),(94,66),(175,66)]:
    d.line((x,y,x+4,y),fill=P['edge'])
    d.point((x+5,y+1),fill=P['deep'])
# Installation label area to be finished in Aseprite after AI refinement.
panel(d,(185,49,225,61),P['middle'],light=P['light'],cut=1)
im.save(GUIDES/'shell_side_layout.png')

im,d=image((128,80),P['ivory'])
d.rectangle((0,0,127,24),fill=P['middle'])
d.line((0,24,127,24),fill=P['light'])
d.rectangle((0,56,127,79),fill=P['shadow'])
d.line((0,56,127,56),fill=P['steel'])
panel(d,(18,28,109,52),P['ivory'])
d.line((22,49,105,49),fill=P['middle'])
d.line((15,31,15,47),fill=P['light'])
d.line((112,31,112,48),fill=P['deep'])
for x in [19,106]:
    d.rectangle((x,32,x+1,33),fill=P['deep'])
    d.rectangle((x,46,x+1,47),fill=P['deep'])
im.save(GUIDES/'shell_end_layout.png')

# Auxiliary original maps: no AI precision typography or glass redesign.
im,d=image((128,256),P['shadow'])
d.rectangle((18,0,109,255),fill=P['deep'])
d.rectangle((24,0,103,255),fill=P['steel'])
for x in [21,106]: d.line((x,0,x,255),fill=P['ink'])
for x in [25,102]: d.line((x,0,x,255),fill=P['middle'])
for y in [30,224]:
    d.line((24,y,103,y),fill=P['ink'])
    d.line((25,y+1,102,y+1),fill=P['middle'])
im.save(TEXTURES/'interior.png')

im,d=image((128,256),P['deep'])
panel(d,(14,16,113,239),P['middle'],light=P['muted'],cut=10)
for x in [22,105]: d.line((x,28,x,228),fill=P['steel'])
# Woven liner, deliberate three-tone stitched folds only at margins.
for y in range(38,229,26):
    d.line((23,y,104,y),fill=P['steel'])
    d.line((24,y+1,103,y+1),fill=P['muted'])
    d.line((24,y+2,28,y+2),fill=P['ivory'])
im.save(TEXTURES/'mattress.png')

im,d=image((128,256),P['dark'])
d.rectangle((24,26,104,86),fill=P['shadow'])
d.rectangle((27,28,101,82),fill='#34545f')
d.rectangle((29,30,99,34),fill='#466b73')
d.line((29,80,99,80),fill=P['ink'],width=2)
# Stepped painted reflection in head pane UV region; no physical glass change.
for j in range(15):
    x=31+j*2;y=39+j
    d.rectangle((x,y,x+5,y+2),fill=P['steel'])
    if j<8: d.rectangle((x,y,x+3,y),fill=P['muted'])
d.rectangle((85,34,88,70),fill=P['deep'])
d.line((86,35,86,67),fill=P['steel'])
im.save(TEXTURES/'glass.png')

im,d=image((128,48),P['dark'])
d.rectangle((2,2,125,45),outline=P['steel'])
d.rectangle((5,5,122,14),fill=P['shadow'])
font=ImageFont.load_default(size=8)
d.text((8,4),'UNIT 01',fill=P['edge'],font=font)
d.line((7,17,119,17),fill=P['deep'])
for y,l in [(22,60),(29,82),(36,43)]:
    d.rectangle((9,y,91,y+3),fill=P['shadow'])
    d.rectangle((9,y,9+l,y+3),fill=P['teal'])
    d.line((9,y,9+l,y),fill=P['turquoise'])
    d.rectangle((102,y,115,y+3),fill=P['steel'])
im.save(TEXTURES/'display.png')
print('Prepared three PixelLab guides and four original auxiliary maps.')
