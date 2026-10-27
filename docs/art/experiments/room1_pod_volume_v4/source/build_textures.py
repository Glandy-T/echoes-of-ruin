"""Editable pixel-structure/age revision of the existing approved pod basis."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parents[3]
OLD=ROOT/'docs/art/experiments/room1_pixellab_pod_trial_v3/textures'
LAYERS=HERE/'source/texture_layers';OUT=HERE/'textures'
LAYERS.mkdir(parents=True,exist_ok=True);OUT.mkdir(exist_ok=True)
PALETTE=np.array([(221,223,211),(209,211,198),(190,199,194),(168,181,185),(143,161,168),(122,144,152),(91,114,126),(66,88,103),(49,69,83),(34,51,64),(101,158,165),(62,119,132)],dtype=np.int32)
INK=(34,51,64,255);AGE=(102,120,130,235);AGEDARK=(69,91,106,245);EDGE=(141,157,165,235)
glyph={'1':['010','110','010','010','111'],'2':['110','001','010','100','111']}
def label(draw,x,y,word,scale=1):
    for char in word:
        for yy,row in enumerate(glyph[char]):
            for xx,b in enumerate(row):
                if b=='1':draw.rectangle((x+xx*scale,y+yy*scale,x+(xx+1)*scale-1,y+(yy+1)*scale-1),fill=INK)
        x+=4*scale
def canvas(size):return Image.new('RGBA',size,(0,0,0,0))
def save(name,key,image):image.save(LAYERS/(key+'__'+name+'.png'))
records=[]
for key in ['lid','shell_side','shell_end','interior','mattress','glass','display','section']:
    old=Image.open(OLD/(key+'.png')).convert('RGBA') if key!='section' else None
    if key=='glass':
        # The head pane samples only U .111.. .889, V .696.. .858 of this map.
        base=Image.new('RGBA',(128,256),(36,57,67,24))
        reflection=canvas(base.size);r=ImageDraw.Draw(reflection)
        r.polygon([(27,40),(33,40),(56,51),(56,54),(51,54),(27,43)],fill=(146,166,173,88))
        r.polygon([(70,62),(85,68),(85,70),(79,68),(70,65)],fill=(120,145,155,58))
        r.line([(17,78),(21,78),(21,81),(30,81)],fill=(88,112,125,42),width=2)
        # Alpha-compositing is intentional: final alpha is the reflection mask input.
        layers=[('clear_glass_tint',base),('localized_pixel_reflections',reflection)]
    elif key=='section':
        base=Image.new('RGBA',(128,64),(84,107,120,255));d=ImageDraw.Draw(base)
        for y0,y1,col in [(0,6,(39,59,74,255)),(7,9,(127,147,157,255)),(10,26,(101,124,137,255)),(27,45,(76,99,114,255)),(46,54,(48,71,88,255)),(55,63,(65,88,103,255))]:d.rectangle((0,y0,127,y1),fill=col)
        # Actual narrow rim UVs sample rows 34..42, not the whole atlas.
        for y0,y1,col in [(33,34,(129,148,157,255)),(35,36,(103,126,139,255)),(37,39,(76,99,114,255)),(40,42,(47,69,84,255))]:d.rectangle((0,y0,127,y1),fill=col)
        age=canvas(base.size);a=ImageDraw.Draw(age)
        for x,y in [(8,9),(57,10),(91,9)]:a.polygon([(x,y),(x+12,y),(x+12,y+2),(x+5,y+2),(x+5,y+4),(x,y+4)],fill=(67,89,104,255))
        for x in [10,61,100]:a.polygon([(x,34),(x+8,34),(x+8,35),(x+3,35),(x+3,37),(x,37)],fill=(69,91,106,255))
        layers=[('section_material_planes',base),('edge_retained_film',age)]
    else:
        pixels=np.array(old)[:,:,:3].astype(np.int32)
        difference=((pixels[:,:,None,:]-PALETTE[None,None,:,:])**2).sum(axis=3)
        base=Image.fromarray(PALETTE[difference.argmin(axis=2)].astype(np.uint8)).convert('RGBA')
        age=canvas(base.size);a=ImageDraw.Draw(age)
        chips=canvas(base.size);c=ImageDraw.Draw(chips)
        identifiers=canvas(base.size);ident=ImageDraw.Draw(identifiers)
        if key=='lid':
            # Keep existing panel design; remove the repeating UNIT 01 plate text.
            ident.rectangle((47,197,79,210),fill=(190,199,194,255));label(ident,55,198,'12',2)
            for x,y,w in [(24,88,13),(88,88,14),(29,237,18),(75,237,22)]:
                a.polygon([(x,y),(x+w,y),(x+w,y+2),(x+w-5,y+2),(x+w-5,y+4),(x+3,y+4),(x+3,y+2),(x,y+2)],fill=AGE)
            for x,y in [(23,51),(102,66),(28,116),(28,192),(99,221)]:
                a.polygon([(x,y),(x+3,y),(x+3,y+8),(x+1,y+8),(x+1,y+4),(x,y+4)],fill=AGEDARK)
            for x,y in [(29,91),(98,91),(30,233)]:
                c.rectangle((x,y,x+3,y+1),fill=(93,114,127,255));c.line((x,y+2,x+2,y+2),fill=EDGE)
        elif key=='shell_side':
            # Make large material planes calm and readable; no cloudy noise fill.
            d=ImageDraw.Draw(base);d.rectangle((5,6,250,23),fill=(143,161,168,255))
            d.rectangle((5,23,250,25),fill=(91,114,126,255))
            for x,y,w in [(7,26,38),(61,27,28),(144,26,34),(220,27,28),(11,68,42),(121,69,35),(211,68,33)]:
                a.polygon([(x,y),(x+w,y),(x+w,y+2),(x+w-7,y+2),(x+w-7,y+4),(x+6,y+4),(x+6,y+3),(x,y+3)],fill=AGE if y<35 else (76,99,114,255))
            for x,y in [(4,34),(64,36),(192,36),(248,34)]:c.rectangle((x,y,x+2,y+3),fill=AGEDARK);c.line((x,y+4,x+2,y+4),fill=EDGE)
        elif key=='shell_end':
            ident.rectangle((55,35,72,48),fill=(190,199,194,255));label(ident,57,37,'12',2)
            for x,y,w in [(8,25,22),(88,25,28),(9,65,30),(77,66,39)]:
                a.polygon([(x,y),(x+w,y),(x+w,y+2),(x+w-6,y+2),(x+w-6,y+4),(x,y+4)],fill=AGE)
            for x,y in [(5,35),(119,47)]:c.rectangle((x,y,x+2,y+3),fill=AGEDARK)
        elif key=='interior':
            d=ImageDraw.Draw(base)
            d.rectangle((0,0,127,255),fill=(76,99,114,255));d.rectangle((18,15,109,241),fill=(101,124,137,255));d.rectangle((22,20,105,236),fill=(122,144,152,255))
            for x,y,w in [(19,16,22),(76,17,29),(19,235,35),(75,235,28)]:
                a.polygon([(x,y),(x+w,y),(x+w,y+2),(x+w-7,y+2),(x+w-7,y+5),(x,y+5)],fill=(76,99,114,255))
        elif key=='mattress':
            for x,y,w in [(18,25,12),(95,32,11),(19,225,25),(77,224,28)]:
                a.polygon([(x,y),(x+w,y),(x+w,y+2),(x+w-4,y+2),(x+w-4,y+5),(x,y+5)],fill=(106,125,136,150))
        elif key=='display':
            # Placeholder identity and system fields stay as before; no invented data.
            base=old.copy();a.line([(3,2),(3,45),(124,45)],fill=(51,73,87,230),width=2)
        layers=[('v3_design_pixel_planes',base),('seam_and_recess_aging',age),('coating_contact_chips',chips),('sample_id_12_or_placeholder_UI',identifiers)]
    result=canvas(layers[0][1].size)
    for name,image in layers:save(name,key,image);result=Image.alpha_composite(result,image)
    if old is not None:old.save(LAYERS/(key+'__v3_source_HIDDEN.png'))
    result.save(OUT/(key+'.png'))
    records.append({'key':key,'size':list(result.size),'layers':[name for name,_ in layers],'source_v3_hidden':old is not None,'alpha_range':list(result.getchannel('A').getextrema())})
(HERE/'source/texture_manifest.json').write_text(json.dumps({'scope':'Existing pod design retained; clear glass alpha independent of RGB, cool-gray seam/contact aging, sample P12 numbering. No new AI call.','textures':records},indent=2),encoding='utf-8')
print('POD_V4_TEXTURE_LAYERS_READY',len(records))
