"""Connected pixel deposits on real perimeter and twenty measured pod bases."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,shutil,hashlib
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parents[3]
LAYERS=HERE/'source/floor_layers';LAYERS.mkdir(parents=True,exist_ok=True)
OLD=ROOT/'docs/art/experiments/room1_surface_full_r5/source/floor_layers'
W,H,D=1648,728,80
for name in ['floor_coating','floor_perimeter_retention','floor_base_contacts','floor_leak_wicking','floor_leak_dark_film','floor_leak_dried_tide']:shutil.copyfile(OLD/(name+'.png'),LAYERS/(name+'.png'))
yy,xx=np.indices((H,W),dtype=float)
# Connected stepped edges, not independent speckles or a new floor tile pattern.
def profile(n,phase,depth):
    rng=np.random.default_rng(20261027+round(phase*100))
    stops=[0]
    while stops[-1]<n:stops.append(stops[-1]+int(rng.integers(14,43)))
    levels=depth+rng.integers(-9,10,len(stops))
    coarse=np.interp(np.arange(n),stops,levels)
    chips=np.repeat(rng.integers(-2,3,(n+1)//2),2)[:n]
    return np.maximum(8,np.round((coarse+chips)/2)*2)
depths=[profile(W,.4,23),profile(W,2.2,26),profile(H,4.1,21),profile(H,5.3,24)]
near=[yy,H-1-yy,xx,W-1-xx]
amount=np.zeros((H,W),dtype=float)
for i,(dist,widths) in enumerate(zip(near,depths)):
    width=widths[None,:] if i<2 else widths[:,None]
    band=np.clip(1-dist/width,0,1)
    if i==0:
        # Actual rear wall stops at the single personnel door opening.
        left=(9.8-.2)*D;right=(11.2-.2)*D
        jamb=np.clip(np.maximum(left-xx,xx-right)/5,0,1)
        band*=jamb
    amount=np.maximum(amount,band)
wall=np.zeros((H,W,4),dtype=np.uint8)
# Broad outer dust, denser stepped shoulders, narrow dark true wall contact.
for low,color,alpha in [(0.03,(130,151,140),155),(.30,(158,171,155),180),(.59,(103,129,125),195),(.85,(50,77,86),215)]:
    mask=amount>low;wall[mask,:3]=color;wall[mask,3]=alpha
Image.fromarray(wall).save(LAYERS/'wall_floor_connected_deposit.png')
pods=json.loads((HERE/'source/pod_footprints.json').read_text())['pods']
contact=Image.new('RGBA',(W,H));corners=Image.new('RGBA',(W,H));accents=Image.new('RGBA',(W,H))
records=[]
for idx,pod in enumerate(pods):
    poly=np.array(pod['pixel_polygon'],dtype=float)
    x0=max(0,int(poly[:,0].min())-25);x1=min(W,int(poly[:,0].max())+26)
    y0=max(0,int(poly[:,1].min())-25);y1=min(H,int(poly[:,1].max())+26)
    y,x=np.indices((y1-y0,x1-x0),dtype=float);x+=x0;y+=y0
    point=np.stack([x,y],axis=2);dist=np.full(x.shape,1e6);arc=np.zeros(x.shape);travel=0
    for j in range(len(poly)):
        a=poly[j];b=poly[(j+1)%len(poly)];v=b-a;length=float(np.linalg.norm(v))
        if length<.01:continue
        t=np.clip(np.sum((point-a)*v,axis=2)/length**2,0,1)
        d=np.sqrt(np.sum((point-(a+t[:,:,None]*v))**2,axis=2));pick=d<dist
        arc[pick]=travel+t[pick]*length;dist=np.minimum(dist,d);travel+=length
    mask=Image.new('L',(x1-x0,y1-y0));ImageDraw.Draw(mask).polygon([tuple(p-[x0,y0]) for p in poly],fill=255)
    inside=np.asarray(mask)>0
    phase=idx*1.37
    pattern=np.random.default_rng(20261027+idx*73)
    stops=np.linspace(0,max(travel,1),14)
    width=np.clip(np.round(np.interp(arc,stops,pattern.integers(2,11,14))),2,10)
    strength=np.interp(arc,stops,pattern.uniform(.0,1.0,14))
    active=(~inside)&(dist<=width)&(strength>.38)
    rim=np.zeros((*x.shape,4),dtype=np.uint8)
    rim[active,:3]=(132,151,140);rim[active,3]=175
    mid=active&(dist<width*.55);rim[mid,:3]=(104,131,127);rim[mid,3]=195
    core=dist<=1.6;rim[core,:3]=(49,74,84);rim[core,3]=215
    contact.alpha_composite(Image.fromarray(rim),(x0,y0))
    # Broad clusters attach at measured outline corners. No gap between mark/base.
    corner_cover=np.zeros(x.shape,dtype=bool)
    for j,vertex in enumerate(poly):
        v1=vertex-poly[j-1];v2=poly[(j+1)%len(poly)]-vertex
        turn=np.arccos(np.clip(np.dot(v1,v2)/max(np.linalg.norm(v1)*np.linalg.norm(v2),.001),-1,1))
        if turn<.6:continue
        # Asymmetric angular corner lobes, no identical circular halos.
        ax=float(pattern.integers(12,29));ay=float(pattern.integers(11,27))
        form=np.abs((x-vertex[0])/ax)**1.4+np.abs((y-vertex[1])/ay)**1.4
        corner_cover|=form<1+np.round(.11*np.sin((x+y)*.37+phase),1)
    corner_width=np.round(12+3*np.sin(arc*.071+phase)+2*np.cos(arc*.19-phase))
    attached=(~inside)&(dist<=corner_width)&corner_cover
    corner=np.zeros_like(rim);corner[attached,:3]=(155,168,151);corner[attached,3]=185
    dense=attached&(dist<corner_width*.55);corner[dense,:3]=(112,139,132);corner[dense,3]=195
    # Keep the contact core dark; deposits join its adjacent pixel, no clean moat.
    corner[core,3]=0
    corners.alpha_composite(Image.fromarray(corner),(x0,y0))
    # Sparse *connected* light mineral ledges along the corner cluster, not dots.
    ledge=attached&(dist<corner_width*.9)&(dist>corner_width*.65)&(np.sin(arc*.17+phase)>.1)
    accent=np.zeros_like(rim);accent[ledge,:3]=(174,184,163);accent[ledge,3]=160
    accents.alpha_composite(Image.fromarray(accent),(x0,y0))
    records.append({'pod':pod['pod'],'outline_pixels':pod['pixel_polygon'],'contact_outer_width_px':[2,10],'corner_outer_width_px':[7,17],'bounds':[x0,y0,x1,y1]})
for name,image in [('pod_connected_contact',contact),('pod_corner_accumulation',corners),('pod_corner_mineral_ledges',accents)]:image.save(LAYERS/(name+'.png'))
order=['floor_coating','floor_perimeter_retention','floor_base_contacts','wall_floor_connected_deposit','pod_connected_contact','pod_corner_accumulation','pod_corner_mineral_ledges','floor_leak_wicking','floor_leak_dark_film','floor_leak_dried_tide']
output=Image.new('RGBA',(W,H))
for name in order:output=Image.alpha_composite(output,Image.open(LAYERS/(name+'.png')).convert('RGBA'))
output.convert('RGB').save(HERE/'evidence/floor_preview_native.png')
manifest={'size':[W,H],'density_trial':80,'map_uv':'u=(GodotX-.2)/20.6, v=(GodotZ+9.3)/9.1; image top=rear','pod_contact_count':20,'perimeter_count':4,'base_layers_copied_exactly':[str(n) for n in ['floor_coating','floor_perimeter_retention','floor_base_contacts']],'leak_layers_preserved':{n:hashlib.sha256((LAYERS/(n+'.png')).read_bytes()).hexdigest() for n in ['floor_leak_wicking','floor_leak_dark_film','floor_leak_dried_tide']},'new_layers':order[3:7],'pods':records,'door_opening_wall_deposit_break_x_m':[9.8,11.2],'no_tile_route_or_geometry':True}
(HERE/'source/floor_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('FLOOR_R8_SOURCE_COMPLETE',len(records))
