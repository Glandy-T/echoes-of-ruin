"""Native PixelLab pixels, geometry masks and alignment only. No grime synthesis."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
W,H=1648,728
LAY=HERE/'layers';LAY.mkdir(parents=True,exist_ok=True)
ASSET=ROOT/'assets/art/room1_floor_pixellab_r14';ASSET.mkdir(parents=True,exist_ok=True)
pods=json.loads((HERE/'pod_footprints.json').read_text())['pods']
raw={n:np.asarray(Image.open(EXP/'raw'/f'{n}.png').convert('RGB'),dtype=float) for n in ['base3','edge','contact_a','contact_c','leak_a']}
# The nearly uniform native base is repeated at 1:1 texel density. A technical
# 16px overlap at tile joins removes only wrap discontinuities, not new marks.
base=raw['base3'].copy()
for axis in [0,1]:
    before=base.copy()
    for i in range(16):
        t=.5*(16-i)/16
        if axis==0:
            base[i]=before[i]*(1-t)+before[255-i]*t
            base[255-i]=before[255-i]*(1-t)+before[i]*t
        else:
            base[:,i]=before[:,i]*(1-t)+before[:,255-i]*t
            base[:,255-i]=before[:,255-i]*(1-t)+before[:,i]*t
yy,xx=np.indices((H,W));floor=base[yy%256,xx%256].copy()
def save(name,arr):
    im=Image.fromarray(np.clip(np.rint(arr),0,255).astype('uint8'),'RGB');im.save(LAY/f'{name}.png');return im
floor=np.asarray(save('01_PixelLab_floor_coating',floor),dtype=float)
layers=[]
def commit_layer(name,before,after,mask):
    # Store the actual replacement pixels and a purely geometric opacity mask.
    rgba=np.zeros((H,W,4),dtype=np.uint8);rgba[:,:,:3]=np.clip(np.rint(after),0,255);rgba[:,:,3]=np.clip(np.rint(mask*255),0,255)
    Image.fromarray(rgba).save(LAY/f'{name}.png');layers.append(name)
    below=Image.fromarray(np.clip(np.rint(before),0,255).astype('uint8'),'RGB').convert('RGBA')
    return np.asarray(Image.alpha_composite(below,Image.fromarray(rgba)).convert('RGB'),dtype=float)
edge=raw['edge'][8:]
edge_delta=edge-np.median(edge[-12:],axis=(0,1))
edge_floor=floor.copy();coverage=np.zeros((H,W));strength=np.zeros((H,W))
for side in ['rear','front','left','right']:
    n=W if side in ['rear','front'] else H
    for d in range(56):
        # Technical transition of source patch boundary, no painted deposits.
        alpha=min(1,(55-d)/10)
        if alpha<=0:continue
        delta=edge_delta[d,(np.arange(n)+{'rear':0,'front':77,'left':151,'right':211}[side])%256]*alpha
        if side=='rear':ys=np.full(n,d);xs=np.arange(n)
        elif side=='front':ys=np.full(n,H-1-d);xs=np.arange(n)
        elif side=='left':ys=np.arange(n);xs=np.full(n,d)
        else:ys=np.arange(n);xs=np.full(n,W-1-d)
        # Wall ends at the current 1.4m personnel door; do not draw a threshold.
        valid=~((xs>=768)&(xs<880)) if side=='rear' else np.ones(n,dtype=bool)
        magnitude=np.max(np.abs(delta),axis=1)
        pick=valid&(magnitude>strength[ys,xs])
        py,px=ys[pick],xs[pick]
        edge_floor[py,px]=floor[py,px]+delta[pick];coverage[py,px]=1;strength[py,px]=magnitude[pick]
floor=commit_layer('02_PixelLab_wall_contact',floor,edge_floor,coverage)
body=np.array(Image.open(HERE/'canonical_footprint.png').convert('L'))>0
contact_floor=floor.copy();contact_mask=np.zeros((H,W));records=[]
def patch_delta(name):
    a=raw[name]
    # Anchoring to preserved clean guide background prevents a rectangular
    # brightness shift if the service returns a different flat background.
    border=np.concatenate([a[:2].reshape(-1,3),a[-2:].reshape(-1,3),a[:,:2].reshape(-1,3),a[:,-2:].reshape(-1,3)])
    return a-np.median(border,axis=0)
def placement(pod,name,radius):
    poly=np.asarray(pod['pixel_polygon'],dtype=int)
    rotated=int(poly[0,1])==int(poly[:,1].min())
    delta=patch_delta(name)
    b=body.copy()
    mirrored=name=='leak_a' and pod['pod'] in ['P06','P13']
    if mirrored:delta=np.fliplr(delta);b=np.fliplr(b)
    if rotated:delta=np.rot90(delta,2);b=np.rot90(b,2)
    by,bx=np.where(b)
    ox=int(poly[:,0].min())-int(bx.min());oy=int(poly[:,1].min())-int(by.min())
    actual=Image.new('L',(256,256));ImageDraw.Draw(actual).polygon([tuple(v-[ox,oy]) for v in poly],fill=255)
    # Exact measured support outline, not a guessed rectangular decal.
    inner=np.asarray(actual)>0
    outer=np.asarray(actual.filter(ImageFilter.MaxFilter(radius*2+1)))>0
    band=(outer&~inner).astype(float)
    # Last 3px only: prevent a clipping boundary at the geometric patch limit.
    safe=np.asarray(actual.filter(ImageFilter.MaxFilter((radius-3)*2+1)))>0
    band[outer&~safe]*=.35
    x0=max(0,ox);y0=max(0,oy);x1=min(W,ox+256);y1=min(H,oy+256)
    sl=(slice(y0-oy,y1-oy),slice(x0-ox,x1-ox));dst=(slice(y0,y1),slice(x0,x1))
    return delta[sl],band[sl],dst,{'pod':pod['pod'],'source':name,'rotation_degrees':180 if rotated else 0,'horizontal_flip':mirrored,'origin_px':[ox,oy],'support_polygon':pod['pixel_polygon']}
for i,pod in enumerate(pods):
    name='contact_a' if i%3==0 or i%3==2 else 'contact_c'
    delta,band,dst,record=placement(pod,name,21)
    contact_floor[dst]=floor[dst]+delta;contact_mask[dst]=np.maximum(contact_mask[dst],band);records.append(record)
floor=commit_layer('03_PixelLab_twenty_pod_contacts',floor,contact_floor,contact_mask)
aged=save('composite_aged',floor);aged.save(ASSET/'floor_aged.png')
leak_floor=floor.copy();leak_mask=np.zeros((H,W));leak_records=[]
for pid,name in [('P03','leak_a'),('P06','leak_a'),('P13','leak_a'),('P18','leak_a')]:
    pod=next(p for p in pods if p['pod']==pid)
    delta,band,dst,record=placement(pod,name,39)
    leak_floor[dst]=floor[dst]+delta;leak_mask[dst]=np.maximum(leak_mask[dst],band);leak_records.append(record)
floor=commit_layer('04_PixelLab_four_coolant_residues',floor,leak_floor,leak_mask)
final=save('composite_with_leaks',floor);final.save(ASSET/'floor_with_leaks.png')
(HERE/'placements.json').write_text(json.dumps({'density_px_per_m':80,'size':[W,H],'mapping':'u=(x-.2)/20.6, v=(z+9.3)/9.1; image top=rear','contacts':records,'leaks':leak_records,'legacy_art_layers_used':[]},indent=2),encoding='utf-8')
(EXP/'editable').mkdir(exist_ok=True)
print('Assembled native AI material, 20 contacts, 4 fixed leak sites; no legacy aging layers.')
