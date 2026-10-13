"""Wall v2: material field, wall-specific AI age patches and precise wide light.

No generic speckle noise is generated. AI material/color history is preserved
in palette-corrected native pixels and arranged at wall-specific locations.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
TEX=ROOT/'textures';LAY=ROOT/'source/layers'
TEX.mkdir(exist_ok=True);LAY.mkdir(exist_ok=True)
raw=Image.open(ROOT/'raw/wall_pro_00.png').convert('RGB')
assert raw.size==(400,272)
PALETTE=['#d3d6c9','#e7e7d4','#c1c8bc','#d7d8c9','#d0d3c4','#d9d5c3',
 '#cad0c0','#b5bead','#b9beac','#abb4a2','#9da998','#929f90',
 '#a6b2a9','#d4dcce','#889d93','#627970','#475f59','#afbab0',
 '#b4c0b5','#c8d1c3','#7a8d83','#c6c5b2','#b7b7a2','#a9ac98',
 '#ccdde4','#e5eced','#dce5e8','#b8cbd4','#d2d6c6','#d9dccc']
colors=np.asarray([tuple(bytes.fromhex(c[1:])) for c in PALETTE],dtype=np.int32)
base=np.asarray(colors[0],dtype=np.int32)
pixels=np.asarray(raw,dtype=np.int32).copy()
# AI returned a lighter ivory base. Anchor the wall coating to user #D3D6C9;
# correct coating only, not the metal or blue diffuser.
pixels[47:248]=np.clip(pixels[47:248]+np.array([-14,-10,-8]),0,255)
dist=((pixels[:,:,None,:]-colors[None,None,:,:])**2).sum(axis=3)
corrected=colors[dist.argmin(axis=2)].astype('uint8')
corrected_image=Image.fromarray(corrected)
corrected_image.save(LAY/'ai_palette_corrected.png')

# Build a quiet native material field. Strong old marks are extracted below and
# placed individually, rather than stamping the same damage every few meters.
tile_array=corrected[:,24:376].copy()
strong=np.max(np.abs(tile_array.astype(np.int32)-base),axis=2)>11
material_rows=np.zeros_like(strong);material_rows[47:248]=True
tile_array[strong&material_rows]=base
tile_array[:47]=base;tile_array[248:]=base
tile=Image.fromarray(tile_array)
tile.save(TEX/'wall_material_field.png')

# Original AI shapes, selected as native-resolution transparent patch layers.
ROIS={'chalk':(36,59,160,93),'abraded':(210,128,319,158),
 'small_loss':(306,59,364,104),'warm_age':(38,146,96,190),
 'lower_wear':(68,212,190,244),'fade':(286,192,349,225)}
patches={}
for name,(x0,y0,x1,y1) in ROIS.items():
 data=corrected[y0:y1,x0:x1]
 alpha=(np.max(np.abs(data.astype(np.int32)-base),axis=2)>11).astype('uint8')*255
 rgba=np.concatenate([data,alpha[:,:,None]],axis=2)
 patches[name]=Image.fromarray(rgba)
 (ROOT/'source/age_patches').mkdir(exist_ok=True)
 patches[name].save(ROOT/'source/age_patches'/f'{name}.png')

maps={
 'rear':{'width':1680,'meters':21.,'corners':[16,1663],'phase':0,
 'contacts':[(271,256,30),(610,259,24),(1090,257,34),(1503,258,20)],
 'joints':[520,1155],'door_edges':[784,896],
 'patches':[('chalk',178,70,False),('abraded',588,151,False),
 ('small_loss',1504,68,True),('warm_age',88,178,False),
 ('lower_wear',1256,217,True),('fade',975,177,False)]},
 'front':{'width':1680,'meters':21.,'corners':[16,1663],'phase':101,
 'contacts':[(350,257,25),(895,259,30),(1417,256,24)],
 'joints':[491,1196],'door_edges':[],
 'patches':[('abraded',227,143,True),('small_loss',899,81,False),
 ('lower_wear',1055,213,False),('fade',1464,177,True)]},
 'left':{'width':728,'meters':9.1,'corners':[0,727],'phase':173,
 'contacts':[(169,257,27),(546,259,21)],'joints':[307],'door_edges':[],
 'patches':[('small_loss',85,80,True),('chalk',333,108,True),
 ('lower_wear',562,216,True)]},
 'right':{'width':728,'meters':9.1,'corners':[0,727],'phase':249,
 'contacts':[(230,258,29),(576,256,21)],'joints':[421],'door_edges':[],
 'patches':[('chalk',79,67,False),('abraded',351,140,True),
 ('warm_age',627,188,True)]},
}

def blank(width):return Image.new('RGBA',(width,272),(0,0,0,0))
def line(draw,xy,c):draw.line(xy,fill=c,width=1)
records={}
for key,info in maps.items():
 width=info['width'];phase=info['phase']
 body=Image.new('RGB',(width,272),tuple(base))
 # Ping-pong field repeats meet edge-to-same-edge, avoiding a seam stripe.
 for i,x in enumerate(range(-tile.width,width+tile.width,tile.width)):
  field=tile if i%2==0 else ImageOps.mirror(tile)
  body.paste(field,(x-phase,0))
 material_age=blank(width)
 for name,x,y,mirror in info['patches']:
  patch=ImageOps.mirror(patches[name]) if mirror else patches[name]
  material_age.alpha_composite(patch,(x,y))

 trim=blank(width);d=ImageDraw.Draw(trim)
 # One integrated assembly with a visible upper return, recessed diffuser,
 # lower seal and shallow rolled edge. Narrow surround joins don't cut light.
 d.rectangle((0,0,width-1,2),fill='#c1c8bc')
 line(d,(0,3,width-1,3),'#e7e7d4')
 d.rectangle((0,12,width-1,41),fill='#a6b2a9')
 d.rectangle((0,12,width-1,13),fill='#d4dcce')
 line(d,(0,14,width-1,14),'#889d93')
 d.rectangle((0,15,width-1,17),fill='#475f59')
 d.rectangle((0,36,width-1,38),fill='#475f59')
 line(d,(0,39,width-1,39),'#889d93')
 line(d,(0,40,width-1,40),'#d4dcce')
 d.rectangle((0,42,width-1,43),fill='#b5bead')
 line(d,(0,44,width-1,44),'#c1c8bc')
 for joint in info['joints']:
  d.rectangle((joint,12,joint+1,17),fill='#627970')
  line(d,(joint+2,12,joint+2,16),'#d4dcce')
  d.rectangle((joint,36,joint+1,40),fill='#627970')
  line(d,(joint+2,38,joint+2,40),'#d4dcce')

 line(d,(0,248,width-1,248),'#c1c8bc')
 d.rectangle((0,249,width-1,251),fill='#475f59')
 line(d,(0,252,width-1,252),'#d4dcce')
 d.rectangle((0,253,width-1,266),fill='#a6b2a9')
 line(d,(0,254,width-1,254),'#c1c8bc')
 line(d,(0,256,width-1,256),'#afbab0')
 d.rectangle((0,264,width-1,266),fill='#889d93')
 d.rectangle((0,267,width-1,269),fill='#627970')
 d.rectangle((0,270,width-1,271),fill='#475f59')

 age=blank(width);a=ImageDraw.Draw(age)
 for cx in info['corners']:
  direction=1 if cx<width/2 else -1
  for delta in range(6):
   x=cx+delta*direction
   if 0<=x<width:
    line(a,(x,3,x,248),'#889d93' if delta<2 else '#c1c8bc')
  # Corner shadow/patina and retained deposits become wider near the lower lip.
  for start,span,color in [(238,28,'#c1c8bc'),(242,19,'#b5bead'),(246,12,'#9da998')]:
   end=cx+direction*span
   a.polygon([(cx,start),(cx+direction*6,start),(cx+direction*6,start+2),
    (end,start+2),(end,248),(cx,248)],fill=color)
  x0=cx+direction*7;x1=cx+direction*24
  line(a,(min(x0,x1),267,max(x0,x1),267),'#475f59')
  line(a,(min(x0,x1)+3,266,max(x0,x1)-4,266),'#7a8d83')
 for joint in info['joints']:
  a.polygon([(joint-19,42),(joint+13,42),(joint+13,44),(joint+6,44),
    (joint+6,47),(joint-4,47),(joint-4,45),(joint-19,45)],fill='#9da998')
  line(a,(joint-12,44,joint+5,44),'#abb4a2')
 for x,y,length in info['contacts']:
  line(a,(x,y,x+length,y),'#d4dcce')
  line(a,(x+3,y+1,x+length-4,y+1),'#627970')
  line(a,(x+5,y+2,x+length-2,y+2),'#889d93')
  a.polygon([(x+5,248),(x+20,248),(x+20,247),(x+14,247),
    (x+14,244),(x+8,244),(x+8,246),(x+5,246)],fill='#b5bead')
 for edge in info['door_edges']:
  side=-1 if edge<width/2 else 1
  line(a,(edge+side,80,edge+side,248),'#627970')
  line(a,(edge+side*2,80,edge+side*2,248),'#889d93')
  line(a,(edge+side*3,79,edge+side*3,247),'#d4dcce')
  line(a,(edge+side*4,81,edge+side*4,247),'#c1c8bc')
 if key=='rear':
  line(a,(780,79,900,79),'#627970');line(a,(780,78,900,78),'#d4dcce')

 # Blue-white trial: low saturation, continuous rows18..35, no blackout patches.
 diffuser=blank(width);dd=ImageDraw.Draw(diffuser)
 dd.rectangle((0,18,width-1,35),fill='#ccdde4')
 line(dd,(0,18,width-1,18),'#e5eced')
 line(dd,(0,19,width-1,19),'#dce5e8')
 dd.rectangle((0,32,width-1,35),fill='#b8cbd4')
 emission=Image.new('L',(width,272),0);ed=ImageDraw.Draw(emission)
 ed.rectangle((0,18,width-1,35),fill=255)
 composite=body.convert('RGBA')
 for layer in [material_age,trim,age,diffuser]:composite=Image.alpha_composite(composite,layer)
 composite.convert('RGB').save(TEX/(key+'_albedo.png'))
 emission.save(TEX/(key+'_emission.png'))
 for suffix,layer in [('body',body),('material_age',material_age),('trims',trim),
   ('localized_age',age),('diffuser',diffuser)]:layer.save(LAY/(key+'_'+suffix+'.png'))
 ai_full=Image.new('RGB',(width,272));guide_full=Image.new('RGB',(width,272))
 guide=Image.open(ROOT/'guides/wall_layout.png').convert('RGB')
 for x in range(0,width,400):ai_full.paste(raw,(x,0));guide_full.paste(guide,(x,0))
 ai_full.save(LAY/(key+'_ai_reference.png'));guide_full.save(LAY/(key+'_layout_reference.png'))
 records[key]={'dimensions':[width,272],'horizontal_length_m':info['meters'],
  'world_height_m':3.4,'light_rows_top_origin':[18,35],'protection_band_top_origin':252,
  'true_corner_pixels':info['corners'],'surround_connection_pixels':info['joints'],
  'material_age_patches':info['patches'],
  'aging':'AI native material history arranged individually; true corner and old contact finish'}
(TEX/'manifest.json').write_text(json.dumps({'maps':records,
 'density_texels_per_m':80,'density_status':'wall candidate only, not project standard',
 'palette':PALETTE,'source':'PixelLab Pro v2 material, original integrated trim and local age finish',
 'lamp_center_m':3.0625,'lamp_visible_height_m':.225,'protection_band_height_m':.25,
 'lamp_color_trial':'#CCDDE4 pale gray blue-white; white comparison in Blender',
 'color_status':'soft blue direction suggested by user; exact tint awaits comparison review',
 'no_text':True},indent=2),encoding='utf-8')
Image.open(TEX/'rear_albedo.png').save(ROOT/'evidence_wall_elevation.png')
Image.open(TEX/'right_albedo.png').crop((40,0,440,272)).resize((1200,816),Image.Resampling.NEAREST).save(ROOT/'evidence_wall_material_nearest3x.png')
print('Wall v2 maps completed: wide 22.5cm diffuser, purposeful structure and readable native age patches.')
