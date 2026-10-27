"""Palette alignment and native pixel cleanup of the two saved PixelLab edits."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np
import json
from collections import deque,Counter

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT.parents[3]/'assets/art/room1_surface_sample_r1'
LAY=ROOT/'source/layers';LAY.mkdir(exist_ok=True)

def align(im,base,low,high):
 a=np.asarray(im.convert('RGB'),dtype=float)
 lum=a.mean(axis=2);center=float(np.median(lum))
 delta=np.clip((lum-center),low,high)
 delta=np.round(delta/3)*3
 result=np.array(base,dtype=float)+delta[:,:,None]
 return Image.fromarray(np.clip(result,0,255).astype('uint8'))

def remove_small_islands(im,limit):
 a=np.asarray(im).copy();h,w=a.shape[:2]
 for iteration in range(2):
  seen=np.zeros((h,w),bool)
  for y in range(h):
   for x in range(w):
    if seen[y,x]:continue
    color=tuple(a[y,x]);seen[y,x]=True;queue=deque([(x,y)]);region=[];border=Counter()
    while queue:
     px,py=queue.popleft();region.append((px,py))
     for nx,ny in [(px-1,py),(px+1,py),(px,py-1),(px,py+1)]:
      if not(0<=nx<w and 0<=ny<h):continue
      neighbor=tuple(a[ny,nx])
      if neighbor!=color:border[neighbor]+=1
      elif not seen[ny,nx]:seen[ny,nx]=True;queue.append((nx,ny))
    if len(region)<=limit and border:
     replacement=border.most_common(1)[0][0]
     for px,py in region:a[py,px]=replacement
 return Image.fromarray(a)

floor_raw=Image.open(ROOT/'raw/floor_pro_00.png').convert('RGB')
floor=remove_small_islands(align(floor_raw,[90,108,115],-12,12),6)
floor.save(LAY/'floor_coherent_material.png')
floor.save(ASSETS/'floor_sample.png')

wall_raw=Image.open(ROOT/'raw/wall_pro_00.png').convert('RGB')
wall=Image.new('RGB',(128,136),'#d3d6c9')
# Local native-pixel mode cleanup removes isolated speckles, not broad plateaus.
body=wall_raw.crop((0,24,128,124)).filter(ImageFilter.ModeFilter(3))
body=remove_small_islands(align(body,[211,214,201],-12,12),18)
wall.paste(body,(0,24))
wall.save(LAY/'wall_material_cleaned.png')

# Sampling covers world y=3.2..6.4m on the existing left wall. Its source UV
# starts at room y=.2m: source texture x=(world_y-.2)*80, hence 240..496.
old=ROOT.parent/'room1_material_revision_v1/source/layers'
trim=Image.open(old/'left_trims.png').crop((240,0,496,272)).resize((128,136),Image.Resampling.NEAREST)
diffuser=Image.open(old/'left_diffuser.png').crop((240,0,496,272)).resize((128,136),Image.Resampling.NEAREST)
deposit=Image.new('RGBA',(128,136),(0,0,0,0));d=ImageDraw.Draw(deposit)
# Coating foot only: shallow connected deposits in a retained joint, no mid-wall dirt.
d.polygon([(0,122),(15,122),(15,121),(23,121),(23,123),(47,123),(47,124),(0,124)],fill=(175,186,169,70))
d.polygon([(128,123),(112,123),(112,121),(104,121),(104,122),(95,122),(95,124),(128,124)],fill=(175,186,169,60))
# One broad faint old metal contact finish; not a new scratch or fabricated event.
d.rectangle((37,129,57,130),fill=(138,157,146,42))
d.rectangle((42,130,63,131),fill=(138,157,146,30))
for name,layer in [('wall_structure',trim),('wall_edge_finish',deposit),('wall_diffuser',diffuser)]:layer.save(LAY/(name+'.png'))
result=wall.convert('RGBA')
for layer in [trim,deposit,diffuser]:result=Image.alpha_composite(result,layer)
result.convert('RGB').save(ASSETS/'wall_sample.png')
for key in ['floor','wall']:
 im=Image.open(ASSETS/(key+'_sample.png'))
 im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST).save(ROOT/'evidence'/(key+'_native_4x.png'))
(ROOT/'source/finish_manifest.json').write_text(json.dumps({
 'source':'saved PixelLab edits of original project guides only',
 'floor':'coherent native shape retained; palette centered #5A6C73, channel range +/-12',
 'wall':'native 3x3 mode plus small-island cleanup; broad connected shape kept, centered #D3D6C9 +/-12',
 'wall_structure':'exact original project trims/diffuser crop x240..496; no new wall seam',
 'new_contact_history':'faint illustrative band finish, not a confirmed past event',
 'sample_wall_godot_world_yz':{'z':[-6.4,-3.2],'height':[0,3.4],'plane_x':.2},
 'sample_floor_godot_xz':{'x':[.2,3.4],'z':[-6.4,-3.2]},
 'native_texels_m':40,'density_scope':'single trial only; no project-wide density or render-resolution change',
 'new_generation_usage':{'floor':10,'wall':10,'total':20},
 'wall2_old_age_patch_used':False,'reference_images_submitted':False
},indent=2),encoding='utf-8')
print('Native floor/wall candidate maps and separate editable layers saved.')
