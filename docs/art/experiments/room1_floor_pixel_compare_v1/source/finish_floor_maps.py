"""Build uniform/zoned floors with identical material, edge and contact detail.

AI-authored generic scratches are removed. Only native matte microtexture is
kept; no random dirt/damage placement is performed. Zoning changes color only.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
TEX=ROOT/'textures';LAY=ROOT/'source/layers'
TEX.mkdir(exist_ok=True);LAY.mkdir(exist_ok=True)
raw=Image.open(ROOT/'raw/floor_pro_00.png').convert('RGB')
assert raw.size==(400,400)
pixels=np.asarray(raw,dtype=np.int32)
values,counts=np.unique(pixels.reshape(-1,3),axis=0,return_counts=True)
anchor=values[counts.argmax()]
# Pro inserted scratches despite prompt exclusions. Replace high-contrast marks
# from local median field; retain only the subtle native material deviations.
replacement=np.asarray(raw.filter(ImageFilter.MedianFilter(31)),dtype=np.int32)
bad=np.max(np.abs(pixels-anchor),axis=2)>6
clean=pixels.copy();clean[bad]=replacement[bad]
base=np.asarray([90,108,115],dtype=np.int32)
deviation=np.clip(clean-anchor,-4,4)
clean=np.clip(base+deviation,0,255)
palette=np.asarray([[86,104,111],[88,106,113],[90,108,115],
 [92,110,117],[94,112,119]],dtype=np.int32)
dist=((clean[:,:,None,:]-palette[None,None,:,:])**2).sum(axis=3)
tile=Image.fromarray(palette[dist.argmin(axis=2)].astype('uint8'))
tile.save(TEX/'common_matte_material.png')

W,H=1680,760;DENSITY=80
common=Image.new('RGB',(W,H),tuple(base))
for row,y in enumerate(range(0,H,400)):
 for col,x in enumerate(range(0,W,400)):
  field=ImageOps.mirror(tile) if col%2 else tile
  field=ImageOps.flip(field) if row%2 else field
  common.paste(field,(x,y))
common.save(LAY/'common_material.png')

layout_path=ROOT.parent/'room1_full_lowpoly_v1/source/engineering_layout.json'
layout=json.loads(layout_path.read_text(encoding='utf-8-sig'))
rects=[layout['circulation'][key]['rect_xy_m'] for key in ['longitudinal_entry_axis','cross_aisle']]
# Pixel centers, world coordinate origin at outer front-left. PNG top is rear.
xx=(np.arange(W,dtype=np.float32)+.5)/DENSITY
yy=(H-np.arange(H,dtype=np.float32)-.5)/DENSITY
X,Y=np.meshgrid(xx,yy)
signed=[]
for r in rects:
 signed.append(np.minimum.reduce([X-r['x_min'],r['x_max']-X,Y-r['y_min'],r['y_max']-Y]))
distance=np.maximum.reduce(signed)
# A soft, 0.30m-wide transition, with 5 stepped pixel values rather than a road
# outline, tile boundary, curb or extra mesh.
weight=np.clip(.5+distance/.30,0,1)
weight=np.round(weight*4)/4
light=np.rint(base+.28*(np.asarray([125,146,152])-base)).astype(np.int32)
dark=np.rint(base+.23*(np.asarray([65,87,99])-base)).astype(np.int32)
delta=(weight[:,:,None]*(light-base)+(1-weight[:,:,None])*(dark-base))
B=Image.fromarray(np.clip(np.rint(np.asarray(common,dtype=np.int32)+delta),0,255).astype('uint8'))
B.save(LAY/'B_tonal_color_finish.png')

edge=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(edge)
def point(x,y):return round(x*DENSITY),round(H-y*DENSITY)
def line(x0,y0,x1,y1,color,width=1):d.line((*point(x0,y0),*point(x1,y1)),fill=color,width=width)
# Actual inner wall feet, with the rear door opening excluded. No arbitrary
# structural seams elsewhere on this continuous floor.
for x0,y0,x1,y1 in [(.2,.2,20.8,.2),(.2,.2,.2,9.3),(20.8,.2,20.8,9.3),
 (.2,9.3,9.8,9.3),(11.2,9.3,20.8,9.3)]:
 line(x0,y0,x1,y1,'#253943',2)
for x0,y0,x1,y1 in [(.23,.23,20.77,.23),(.23,.23,.23,9.27),
 (20.77,.23,20.77,9.27),(.23,9.27,9.8,9.27),(11.2,9.27,20.77,9.27)]:
 line(x0,y0,x1,y1,'#415763')
# A flush threshold material join at the existing doorway, not a step or new door.
line(9.8,9.3,11.2,9.3,'#415763',2)
line(9.8,9.28,11.2,9.28,'#607279')
edge.save(LAY/'common_edge_finish.png')

age=Image.new('RGBA',(W,H),(0,0,0,0));a=ImageDraw.Draw(age)
# Shelter-edge deposits occupy corners of the actual floor/wall intersection.
for x,y,sx,sy in [(.22,.22,1,1),(20.78,.22,-1,1),(.22,9.28,1,-1),(20.78,9.28,-1,-1)]:
 px,py=point(x,y);tx=sx;ty=-sy
 a.polygon([(px,py),(px+tx*13,py),(px+tx*13,py+ty*2),
  (px+tx*8,py+ty*2),(px+tx*8,py+ty*4),(px,py+ty*4)],fill='#415763')
# Two faint old contact scuffs adjacent to existing pod envelopes, not floating
# stain islands. These are review illustrations, not confirmed historical events.
contact_points=[{'pod':'P03','xy_m':[5.84,1.0]}, {'pod':'P14','xy_m':[6.45,7.1]}]
for info in contact_points:
 px,py=point(*info['xy_m'])
 a.line((px,py,px,py+12),fill='#607279')
 a.line((px+1,py+3,px+1,py+10),fill='#4f636c')
age.save(LAY/'common_localized_contact.png')

for label,field in [('A',common),('B',B)]:
 result=field.convert('RGBA')
 for overlay in [edge,age]:result=Image.alpha_composite(result,overlay)
 result.convert('RGB').save(TEX/f'floor_{label}_albedo.png')
# Hidden raw reference is native size in upper-left, not an actual damage tiling.
ref=Image.new('RGBA',(W,H),(0,0,0,0));ref.paste(raw,(0,0))
ref.save(LAY/'AI_RAW_REFERENCE_HIDDEN.png')

(TEX/'manifest.json').write_text(json.dumps({
 'dimensions':[W,H],'outer_floor_m':[21,9.5],'density_texels_m':DENSITY,
 'density_status':'trial only, not a project pixel specification',
 'palette_reference':{'base':'#5A6C73','light':'#7D9298','shade':'#415763','deep':'#253943'},
 'A':'uniform hue, same fine matte material and actual perimeter/contact finish',
 'B':'same material/details; existing circulation receives mild tonal separation',
 'B_nominal_aisle_rgb':light.tolist(),'B_nominal_pod_zone_rgb':dark.tolist(),
 'circulation_rects_m':rects,'transition_width_m':.30,'transition_tone_levels':5,
 'geometry':'unchanged continuous floor; no route mesh or height offset',
 'raw_finish':'discarded AI generic scratches; retained low-contrast native material, organized near source base',
 'localized_contacts':contact_points,'contact_history_status':'illustrative candidate, not confirmed past events',
 'random_dirt_or_damage_placement':False
},indent=2),encoding='utf-8')
for label in ['A','B']:
 im=Image.open(TEX/f'floor_{label}_albedo.png')
 im.resize((840,380),Image.Resampling.NEAREST).save(ROOT/f'evidence_floor_{label}_plan.png')
tile.resize((1200,1200),Image.Resampling.NEAREST).save(ROOT/'evidence_material_nearest3x.png')
print('Floor A/B maps ready; material and edge/contact detail shared, color zoning only.')
