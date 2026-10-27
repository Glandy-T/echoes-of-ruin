"""One continuous aged floor with fixed pod-anchored old leak differences."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,random,re,json,math,hashlib
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT.parents[3]
for folder in ['source/floor_layers','editable','evidence','survey']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
OUT=PROJECT/'assets/art/room1_surface_full_r5';OUT.mkdir(parents=True,exist_ok=True)
W,H,D=1648,728,80
SEED=20261027
scene=(PROJECT/'scenes/dev/room1_pod_exit_animation_r3.tscn').read_text(encoding='utf-8')
pods={}
for match in re.finditer(r'\[node name="(P\d+)"[^\n]*\ntransform = Transform3D\(([^\n]+)\)',scene):
    vals=list(map(float,match.group(2).split(',')));pods[match.group(1)]={'x':vals[-3],'y':vals[-2],'z':vals[-1]}
assert len(pods)==20
selection=random.Random(SEED)
groups=[['P01','P03','P04','P05'],['P06','P07','P08','P09','P10'],['P11','P13','P14','P15'],['P16','P18','P19','P20']]
selected=[selection.choice(group) for group in groups]
assert selected==['P03','P06','P13','P18']
rng=np.random.default_rng(SEED)

def field(width,height,shape):
    a=rng.normal(0,1,shape).astype('float32')
    im=Image.fromarray(a).resize((width,height),Image.Resampling.BILINEAR)
    a=np.asarray(im).copy();return a/max(float(a.std()),.001)
coarse=field(W,H,(9,20));medium=field(W,H,(39,87));grain=field(W,H,(146,330))
# Low-contrast material variation is continuous across the entire room; no tiles.
values=np.clip(np.round((coarse*1.5+medium*1.0+grain*.6)/2)*2,-6,8)
base_color=np.array([90,108,115],dtype=float)
rgb=np.clip(base_color+values[:,:,None],0,255).astype('uint8')
coating=Image.fromarray(rgb).convert('RGBA')
coating.save(ROOT/'source/floor_layers/floor_coating.png')

yy,xx=np.indices((H,W))
# Retention follows the real room perimeter. Unequal depth avoids a drawn frame.
north_depth=23+8*np.sin(np.arange(W)*.018)+4*np.sin(np.arange(W)*.049)
south_depth=26+7*np.sin(np.arange(W)*.013+1.2)+5*np.cos(np.arange(W)*.057)
west_depth=22+7*np.sin(np.arange(H)*.023+.4)
east_depth=25+8*np.cos(np.arange(H)*.018+1.1)
edge=np.maximum.reduce([np.clip(1-yy/north_depth[None,:],0,1),np.clip(1-(H-1-yy)/south_depth[None,:],0,1),
 np.clip(1-xx/west_depth[:,None],0,1),np.clip(1-(W-1-xx)/east_depth[:,None],0,1)])
edge_alpha=(np.round(edge*7)/7*142).astype('uint8')
perimeter=Image.new('RGBA',(W,H),(53,76,85,0));perimeter.putalpha(Image.fromarray(edge_alpha))
perimeter.save(ROOT/'source/floor_layers/floor_perimeter_retention.png')
contact=Image.new('RGBA',(W,H),(0,0,0,0));draw=ImageDraw.Draw(contact)
for i,(name,pod) in enumerate(pods.items()):
    cx=round((pod['x']-.2)*D);cy=round((pod['z']+9.3)*D)
    # Small contact/maintenance-age lobes attach to existing base edges, not a grid.
    for side in [-1,1]:
        sx=cx+side*round(.51*D);sy=cy+(-1 if i%2 else 1)*round(.67*D)
        draw.ellipse((sx-8,sy-22,sx+8,sy+22),fill=(116,133,135,32))
contact.save(ROOT/'source/floor_layers/floor_base_contacts.png')
aged=Image.alpha_composite(Image.alpha_composite(coating,perimeter),contact)
aged.convert('RGB').save(OUT/'floor_aged.png')

leak_halo=Image.new('RGBA',(W,H),(0,0,0,0))
leak_body=Image.new('RGBA',(W,H),(0,0,0,0))
leak_tide=Image.new('RGBA',(W,H),(0,0,0,0))
leak_records=[]
for index,name in enumerate(selected):
    pod=pods[name];cx=(pod['x']-.2)*D;cy=(pod['z']+9.3)*D
    direction=-1 if pod['z']>-4 else 1 # old liquid spreads a little toward the aisle
    side=[1,-1,1,-1][index]
    left=round(cx-118);top=round(cy-152);lw,lh=236,304
    mask=Image.new('L',(lw,lh),0);md=ImageDraw.Draw(mask)
    phase=[.35,1.45,2.6,3.8][index]
    rx=[.82,.90,.86,.80][index]*D;rz=[1.36,1.31,1.40,1.34][index]*D
    centerx=cx-left+side*4;centery=cy-top+direction*8
    points=[]
    for k in range(88):
        theta=2*math.pi*k/88
        radius=1+.105*math.sin(3*theta+phase)+.065*math.cos(5*theta-phase)+.035*math.sin(9*theta+phase)
        points.append((round(centerx+rx*radius*math.cos(theta)),round(centery+rz*radius*math.sin(theta))))
    md.polygon(points,fill=255)
    # A joined low-side lobe makes each footprint an uneven spill, not a pod outline.
    lx=centerx+side*.63*D;ly=centery+direction*.72*D
    md.ellipse((lx-.38*D,ly-.48*D,lx+.38*D,ly+.48*D),fill=255)
    expanded=mask.filter(ImageFilter.MaxFilter(11));eroded=mask.filter(ImageFilter.MinFilter(11))
    m=np.asarray(mask,dtype=float)/255;e=np.asarray(expanded,dtype=float)/255;inner=np.asarray(eroded,dtype=float)/255
    texture=field(lw,lh,(29,23))
    halo_alpha=np.clip((e-m)*68,0,255).astype('uint8')
    body_alpha=np.clip(m*(163+np.clip(texture,-1,1)*22),0,255).astype('uint8')
    rim=np.maximum(0,m-inner)
    # Coherent broken mineral crust follows the spill perimeter, no floating dots.
    crust=np.clip((texture+.15)*.55,0,1)
    # A broken tide line, not a bright closed selection ring around each pod.
    edge_alpha=np.clip(rim*(30+crust*215),0,255).astype('uint8')
    halo=Image.new('RGBA',(lw,lh),(67,92,99,0));halo.putalpha(Image.fromarray(halo_alpha))
    body=Image.new('RGBA',(lw,lh),(43+index*2,67+index,78+index,0));body.putalpha(Image.fromarray(body_alpha))
    tide_array=np.empty((lh,lw,4),dtype='uint8')
    bright=(texture>1.1)&(rim>.0)
    tide_array[:,:,:3]=np.array([108,135,135],dtype='uint8')
    tide_array[bright,:3]=[159,175,160]
    tide_array[:,:,3]=edge_alpha
    tide=Image.fromarray(tide_array)
    for layer,piece in [(leak_halo,halo),(leak_body,body),(leak_tide,tide)]:layer.alpha_composite(piece,(left,top))
    visible=np.asarray(expanded)>0
    ys,xs=np.where(visible)
    leak_records.append({'pod':name,'world_center':[pod['x'],0,pod['z']],
      'world_floor_uv':[(pod['x']-.2)/20.6,(pod['z']+9.3)/9.1],
      'pixel_center':[cx,cy],'pixel_bounds':[int(left+xs.min()),int(top+ys.min()),int(left+xs.max()),int(top+ys.max())],
      'flow_side':side,'toward_aisle':direction,'variant':index,
      'meaning':'Static old leak residue/crust around this pod base; fluid composition and gameplay significance not established.'})
for name,layer in [('floor_leak_wicking',leak_halo),('floor_leak_dark_film',leak_body),('floor_leak_dried_tide',leak_tide)]:
    layer.save(ROOT/'source/floor_layers'/f'{name}.png')
final=aged
for layer in [leak_halo,leak_body,leak_tide]:final=Image.alpha_composite(final,layer)
final.convert('RGB').save(OUT/'floor_with_leaks.png')
plan=final.convert('RGB').copy();d=ImageDraw.Draw(plan)
for name,pod in pods.items():
    x=(pod['x']-.2)*D;y=(pod['z']+9.3)*D
    d.rectangle((x-.525*D,y-1.15*D,x+.525*D,y+1.15*D),outline='#D3D6C9',width=2)
    d.text((x-11,y-4),name,fill='#E7E7D4')
for row in leak_records:
    x,y=row['pixel_center'];d.text((x-23,y+1.23*D),row['pod']+' LEAK',fill='#CCDFC6')
plan.save(ROOT/'evidence/floor_leak_placement_plan.png')
aged.convert('RGB').save(ROOT/'evidence/floor_aged_native.png')
final.convert('RGB').save(ROOT/'evidence/floor_leaks_native.png')
(ROOT/'source/floor_manifest.json').write_text(json.dumps({
 'authority':'User accepted wall aging and requested a seamless fully aged floor, plus conspicuous leak traces around several random pods.',
 'authorship':'Project-authored continuous coating fields, real-perimeter/base contact and pod-anchored residue masks. No third-party images or AI calls.',
 'size':[W,H],'density_trial_texels_m':D,'world_mapping':{'x':[.2,20.8],'z':[-9.3,-.2],'u':'(x-.2)/20.6','v':'(z+9.3)/9.1','image_top':'rear wall'},
 'pod_layout_source':'scenes/dev/room1_pod_exit_animation_r3.tscn','pod_count':20,'selection_seed':SEED,
 'selection_rule':'One pod in each of four row/side groups; excludes hero P12 and special red-screen P02/P17 to avoid asserting a causal story.',
 'selected_pods':selected,'leaks':leak_records,
 'floor_seams_routes_new_geometry':False,'liquid_simulation':False,'new_generation_usage':0,
 'pod_plan_bounds':'1.05x2.3m nominal footprint; runtime r5 readback measures approximately 1.05x2.294m on all four closed leak pods, consistent with placement.',
 'original_floor_reference_sha256':hashlib.sha256((PROJECT/'assets/art/room1_surface_structure_r2/floor_sample.png').read_bytes()).hexdigest()
},indent=2),encoding='utf-8')
print(json.dumps({'size':[W,H],'selected_pods':selected,'leaks':leak_records}))
