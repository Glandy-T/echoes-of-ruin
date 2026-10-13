"""Finish real PixelLab Pro art into continuous wall-specific pixel maps.

Removes AI-made tile borders, restores approved uninterrupted trims, and places
aging at true room corners/old contact edges. No random noise or fake panel grid.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
TEX=ROOT/'textures';LAY=ROOT/'source/layers'
TEX.mkdir(exist_ok=True);LAY.mkdir(exist_ok=True)
raw=Image.open(ROOT/'raw/wall_pro_00.png').convert('RGB')
assert raw.size==(400,272),'Expected Pro canvas'
PALETTE=['#d3d6c9','#e7e7d4','#c1c8bc','#cbd1c3','#d9dccc','#d0d3c6',
 '#d6d9cc','#d3d7ca','#b9c2b6','#b1bab0','#a2ada4','#8c9a90','#6e8177',
 '#abb19e','#e0e3d2','#f1f1e7','#bfc6b9','#7f8e85']
colors=[tuple(bytes.fromhex(c[1:])) for c in PALETTE]
# Exact nearest color: Pillow's cached palette quantization coarsened these
# close ivory values and introduced visible repeat-boundary color bars.
rgb=np.asarray(raw,dtype=np.int32)
pal=np.asarray(colors,dtype=np.int32)
dist=((rgb[:,:,None,:]-pal[None,None,:,:])**2).sum(axis=3)
corrected=Image.fromarray(pal[dist.argmin(axis=2)].astype('uint8'))
base=colors[0]
tile=corrected.copy();td=ImageDraw.Draw(tile)
# Pro invented borders on both sides. Take quiet neighboring material instead;
# no geometry/UV pixel stretching and no repeating end-frame grime.
tile.paste(corrected.crop((28,0,52,272)),(0,0))
tile.paste(corrected.crop((348,0,372,272)),(376,0))
td.rectangle((0,0,399,7),fill=base)
td.rectangle((0,19,399,36),fill=base)
td.rectangle((0,245,399,271),fill=base)
# Equal border texels make the quiet field repeat without drawn vertical seams.
td.rectangle((0,8,11,244),fill=base)
td.rectangle((388,8,399,244),fill=base)
tile.save(TEX/'wall_material_tile.png')

def blank(width):return Image.new('RGBA',(width,272),(0,0,0,0))
def rect(draw,box,color):draw.rectangle(box,fill=color)
def line(draw,box,color):draw.line(box,fill=color,width=1)

maps={
 'rear':{'width':1680,'meters':21.,'corners':[16,1663],'phase':0,
         'contacts':[(270,261,15),(590,259,9),(1118,262,13),(1502,260,8)],
         'door_edges':[784,896]},
 'front':{'width':1680,'meters':21.,'corners':[16,1663],'phase':109,
         'contacts':[(350,260,11),(924,262,16),(1407,259,10)],'door_edges':[]},
 'left':{'width':728,'meters':9.1,'corners':[0,727],'phase':187,
         'contacts':[(186,260,12),(515,263,9)],'door_edges':[]},
 'right':{'width':728,'meters':9.1,'corners':[0,727],'phase':251,
         'contacts':[(257,259,13),(580,262,10)],'door_edges':[]},
}
records={}
for key,info in maps.items():
 width=info['width'];phase=info['phase']
 body=Image.new('RGB',(width,272),base)
 for x in range(-400,width+400,400):body.paste(tile,(x-phase,0))
 trim=blank(width);d=ImageDraw.Draw(trim)
 # Ceiling return, diffuser recess and metal base protection: intentional trim
 # edges, not arbitrary wall panelling. Keep every world-height row consistent.
 rect(d,(0,0,width-1,1),'#c1c8bc');line(d,(0,2,width-1,2),'#e0e3d2')
 rect(d,(0,23,width-1,30),'#a2ada4')
 line(d,(0,23,width-1,23),'#c1c8bc');line(d,(0,24,width-1,24),'#7f8e85')
 line(d,(0,29,width-1,29),'#6e8177');line(d,(0,30,width-1,30),'#c1c8bc')
 line(d,(0,31,width-1,31),'#e0e3d2')
 line(d,(0,250,width-1,250),'#c1c8bc');line(d,(0,251,width-1,251),'#7f8e85')
 line(d,(0,252,width-1,252),'#e7e7d4')
 rect(d,(0,253,width-1,268),'#b1bab0')
 line(d,(0,254,width-1,254),'#c1c8bc')
 line(d,(0,256,width-1,256),'#b9c2b6')
 line(d,(0,266,width-1,266),'#a2ada4')
 line(d,(0,268,width-1,268),'#8c9a90')
 rect(d,(0,269,width-1,271),'#7f8e85')
 age=blank(width);a=ImageDraw.Draw(age)
 for cx in info['corners']:
  direction=1 if cx<width/2 else -1
  # Vertical corner value falloff is only placed at real architectural corners.
  for delta in range(4):
   xx=cx+direction*delta
   if 0<=xx<width:
    line(a,(xx,3,xx,249),'#b9c2b6' if delta==0 else '#c1c8bc')
  # Sheltered foot-edge deposits, shaped as sparse stepped clusters.
  for delta,span in [(0,27),(1,19),(2,11)]:
   xx=cx+direction*delta
   yy=249-delta
   end=cx+direction*span
   line(a,(min(xx,end),yy,max(xx,end),yy),'#abb19e' if delta==0 else '#c1c8bc')
  # Limited edge loss on the lower protection band, not wide peeling.
  x0=cx+direction*7;x1=cx+direction*15
  line(a,(min(x0,x1),268,max(x0,x1),268),'#6e8177')
  x0=cx+direction*9;x1=cx+direction*12
  line(a,(min(x0,x1),267,max(x0,x1),267),'#8c9a90')
 for x,y,length in info['contacts']:
  line(a,(x,y,x+length,y),'#c1c8bc')
  line(a,(x+2,y+1,x+length-3,y+1),'#8c9a90')
  # Adjacent dull patch suggests old abrasion, not continuing human traffic.
  line(a,(x+4,y+2,x+length-2,y+2),'#a2ada4')
 for edge in info['door_edges']:
  side=-1 if edge<width/2 else 1
  line(a,(edge+side,80,edge+side,250),'#c1c8bc')
  line(a,(edge+side*2,81,edge+side*2,249),'#e0e3d2')
 if key=='rear':
  line(a,(782,79,897,79),'#c1c8bc')
  line(a,(782,78,897,78),'#e0e3d2')
 # Approved intact diffuser is restored LAST so corner/age layers cannot cut it.
 diffuser=blank(width);dd=ImageDraw.Draw(diffuser)
 rect(dd,(0,25,width-1,28),'#f1f1e7')
 line(dd,(0,25,width-1,25),'#e7e7d4')
 line(dd,(0,28,width-1,28),'#e0e3d2')
 emission=Image.new('L',(width,272),0);ed=ImageDraw.Draw(emission)
 rect(ed,(0,25,width-1,28),255)
 composite=body.convert('RGBA')
 for layer in [trim,age,diffuser]:composite=Image.alpha_composite(composite,layer)
 composite.convert('RGB').save(TEX/(key+'_albedo.png'))
 emission.save(TEX/(key+'_emission.png'))
 body.save(LAY/(key+'_body.png'));trim.save(LAY/(key+'_trims.png'))
 age.save(LAY/(key+'_localized_age.png'));diffuser.save(LAY/(key+'_diffuser.png'))
 # Hidden full-canvas guide and unmodified AI material reference for editing.
 ai_full=Image.new('RGBA',(width,272))
 guide_full=Image.new('RGB',(width,272),base)
 guide=Image.open(ROOT/'guides/wall_layout.png').convert('RGB')
 for x in range(0,width,400):
  ai_full.paste(raw,(x,0));guide_full.paste(guide,(x,0))
 ai_full.save(LAY/(key+'_ai_reference.png'));guide_full.save(LAY/(key+'_layout_reference.png'))
 records[key]={'dimensions':[width,272],'horizontal_length_m':info['meters'],
  'world_height_m':3.4,'light_rows_top_origin':[25,28],
  'protection_band_top_origin':252,'true_corner_pixels':info['corners'],
  'aging':'true corner deposits, limited old protection-band contact scuffs, no tiled border wear'}

(TEX/'manifest.json').write_text(json.dumps({'maps':records,
 'density_texels_per_m':80,'density_status':'wall candidate only, not global project standard',
 'palette':PALETTE,'source':'PixelLab Pro wall edit, authored continuous trim and localized age finish',
 'lamp_center_m':3.0625,'lamp_visible_height_m':.05,'protection_band_height_m':.25,
 'ai_finish':'palette organization, removal of fake tile-end borders, restoration of continuous diffuser; no additional generation',
 'no_text':True},indent=2),encoding='utf-8')
preview=Image.open(TEX/'rear_albedo.png')
preview.resize((1680,272),Image.Resampling.NEAREST).save(ROOT/'evidence_wall_elevation.png')
tile_preview=Image.open(TEX/'right_albedo.png').crop((200,0,600,272))
tile_preview.resize((1200,816),Image.Resampling.NEAREST).save(ROOT/'evidence_wall_material_nearest3x.png')
print('Finished four wall-specific albedo / emission maps.')
