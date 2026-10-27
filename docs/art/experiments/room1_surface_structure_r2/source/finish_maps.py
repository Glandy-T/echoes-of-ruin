"""Keep native AI clusters; restore exact existing structure in editable layers."""
from pathlib import Path
from collections import Counter, deque
from PIL import Image, ImageDraw
import numpy as np
import json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parents[3]/'assets/art/room1_surface_structure_r2';OUT.mkdir(parents=True,exist_ok=True)
LAY=ROOT/'source/layers'

def coherent_palette(image,base,steps,min_region=5):
    a=np.asarray(image.convert('RGB'),dtype=float)
    lum=a.mean(2);delta=lum-float(np.median(lum))
    steps=np.array(steps,dtype=float)
    labels=np.argmin(abs(delta[:,:,None]-steps[None,None,:]),axis=2)
    h,w=labels.shape;seen=np.zeros((h,w),bool)
    # Remove only disconnected speckles, not the material contour or large shapes.
    for y in range(h):
        for x in range(w):
            if seen[y,x]:continue
            value=int(labels[y,x]);todo=deque([(x,y)]);seen[y,x]=True;region=[];neighbors=Counter()
            while todo:
                px,py=todo.popleft();region.append((px,py))
                for nx,ny in [(px-1,py),(px+1,py),(px,py-1),(px,py+1)]:
                    if nx<0 or ny<0 or nx>=w or ny>=h:continue
                    nv=int(labels[ny,nx])
                    if nv!=value:neighbors[nv]+=1
                    elif not seen[ny,nx]:seen[ny,nx]=True;todo.append((nx,ny))
            if len(region)<min_region and neighbors:
                replacement=neighbors.most_common(1)[0][0]
                for px,py in region:labels[py,px]=replacement
    result=np.array(base,dtype=float)+steps[labels,None]
    return Image.fromarray(np.clip(result,0,255).astype('uint8'))

def remove_enclosed_floor_islands(image):
    a=np.asarray(image).copy();h,w=a.shape[:2];seen=np.zeros((h,w),bool);removed=0
    for y in range(h):
        for x in range(w):
            if seen[y,x]:continue
            value=tuple(a[y,x]);todo=deque([(x,y)]);seen[y,x]=True;region=[];touches_edge=False
            while todo:
                px,py=todo.popleft();region.append((px,py));touches_edge|=px in [0,w-1] or py in [0,h-1]
                for nx,ny in [(px-1,py),(px+1,py),(px,py-1),(px,py+1)]:
                    if nx<0 or ny<0 or nx>=w or ny>=h or seen[ny,nx]:continue
                    if tuple(a[ny,nx])==value:seen[ny,nx]=True;todo.append((nx,ny))
            if not touches_edge and len(region)>64 and value!=(90,108,115):
                for px,py in region:a[py,px]=[90,108,115]
                removed+=len(region)
    return Image.fromarray(a),removed

raw=Image.open(ROOT/'raw/wall_pro_00.png').convert('RGB');assert raw.size==(256,272)
coating=Image.new('RGB',raw.size,'#D3D6C9')
# Reject the invented upper boxed panel/vertical ends by sampling only the face.
body=coherent_palette(raw.crop((0,78,256,247)),[211,214,201],[-8,-4,0,4,8],8)
# Stretch only the quiet field to the actual face; structural artwork is separate.
coating.paste(body.resize((256,205),Image.Resampling.NEAREST),(0,44))
coating.save(LAY/'wall_coating.png')
structure=Image.open(LAY/'wall_structure_guide.png').convert('RGBA')
s=ImageDraw.Draw(structure)
# Pixel reflections sit on the existing horizontal metal faces only.
for points,c in [([(18,14),(43,14),(43,15),(36,15),(36,16),(18,16)],'#B8C4BA'),
                 ([(106,14),(153,14),(153,15),(142,15),(142,16),(106,16)],'#B5C2B8'),
                 ([(204,14),(237,14),(237,16),(218,16),(218,15),(204,15)],'#B3C0B6'),
                 ([(0,38),(68,38),(68,39),(54,39),(54,40),(0,40)],'#A6B7B2'),
                 ([(134,38),(193,38),(193,39),(178,39),(178,40),(134,40)],'#A3B4AF')]:
    s.polygon(points,fill=c)
structure.save(LAY/'wall_structure.png')
edge=Image.open(LAY/'wall_contact_guide.png').convert('RGBA');e=ImageDraw.Draw(edge)
# Shallow deposition clings to the true wall foot, not to floating patches.
e.polygon([(0,248),(0,244),(9,244),(9,241),(20,241),(20,243),(32,243),(32,245),(51,245),(51,247),(66,247),(66,248)],fill='#C1C8BC')
e.polygon([(156,248),(156,247),(168,247),(168,244),(179,244),(179,242),(192,242),(192,243),(208,243),(208,245),(233,245),(233,247),(256,247),(256,248)],fill='#C3CABE')
e.polygon([(7,248),(7,246),(20,246),(20,245),(30,245),(30,247),(44,247),(44,248)],fill='#B8C2B5')
# Short continuous highlights and broad old contact on the lower metal face.
for box,c in [((12,257,43,257),'#91A39B'),((47,258,69,258),'#93A49C'),
              ((116,257,146,258),'#94A59E'),((187,258,228,258),'#8C9F97'),
              ((100,264,123,265),'#728985'),((150,263,173,264),'#708783')]:e.rectangle(box,fill=c)
edge.save(LAY/'wall_edge_finish.png')
result=coating.convert('RGBA')
for layer in [structure,edge]:result=Image.alpha_composite(result,layer)
# Match the inherited wall exactly at both trial ends, including its trim rows.
# This handoff is a prototype boundary, not a newly invented construction joint.
old=Image.open(ROOT.parent/'room1_material_revision_v1/textures/left_albedo.png').convert('RGB')
old=old.crop((240,0,496,272));assert old.size==result.size
transition=old.convert('RGBA')
alpha=Image.new('L',old.size,0)
for x in range(256):
    distance=min(x,255-x)
    opacity=round((1-min(1,max(0,(distance-8)/40)))*8)/8
    ImageDraw.Draw(alpha).line((x,0,x,271),fill=round(opacity*255))
transition.putalpha(alpha);transition.save(LAY/'wall_trial_end_match.png')
result=Image.alpha_composite(result,transition)
result.convert('RGB').save(OUT/'wall_sample.png')

floor_raw=Image.open(ROOT/'raw/floor_pro_00.png').convert('RGB');assert floor_raw.size==(256,256)
floor=coherent_palette(floor_raw,[90,108,115],[-5,-3,-1,0,2,4,6],4)
floor,removed_floor_pixels=remove_enclosed_floor_islands(floor)
floor.save(LAY/'floor_material.png')
contact=Image.new('RGBA',floor.size,(0,0,0,0));c=ImageDraw.Draw(contact)
# x=0 is the actual left room wall; do not frame any other sample edge.
c.rectangle((0,0,1,255),fill=(48,70,79,100))
c.rectangle((2,0,3,255),fill=(57,79,87,70))
c.rectangle((4,0,6,255),fill=(65,87,95,35))
contact.save(LAY/'floor_wall_contact.png')
Image.alpha_composite(floor.convert('RGBA'),contact).convert('RGB').save(OUT/'floor_sample.png')
for key in ['wall','floor']:
    im=Image.open(OUT/f'{key}_sample.png')
    im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).save(ROOT/'evidence'/f'{key}_native_3x.png')
(ROOT/'source/finish_manifest.json').write_text(json.dumps({
 'wall':'Native AI quiet field palette-organized separately from exact project-authored lamp/protection returns. AI invented vertical ends and boxed panel rejected.',
 'floor':'Native AI connected clusters, restrained blue-gray palette; disconnected large colour islands removed. Edge overlay only at actual wall.',
 'physical_sample_m':{'wall':[3.2,3.4],'floor':[3.2,3.2]},'density_candidate_texels_m':80,
 'wall_main_steps':[-8,-4,0,4,8],'floor_steps':[-5,-3,-1,0,2,4,6],
 'floor_enclosed_pixels_reset_to_base':removed_floor_pixels,
 'wall_end_match':'8px exact inherited albedo, then40px eight-step transition per side; central160px fully new art.',
 'source_reference_images_submitted':False,'geometry_or_light_changes':False,
 'actual_generation_usage':{'wall':15,'floor':10,'total':25},
 'known_limit':'Existing r4 irradiation retained for fixed-light comparison; new colour bounce not rebaked.'
},indent=2),encoding='utf-8')
print('Structure layers and native texture candidates saved.')
