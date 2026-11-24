"""Map R5 surface components into flat, editable 128px regions."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parent.parent
prev=p.parent/'protagonist_r5_head_sample_v3'
sys.path.insert(0,str(p.parent/'protagonist_r5_pixel_skin_v1/source'))
from model import Model
m=Model(prev/'walk_pixel.glb')
f=m.faces();pos=m.attribute('POSITION');uv=m.attribute('TEXCOORD_0')
points,ids=np.unique(pos.round(6),axis=0,return_inverse=True)
adj=[set() for _ in points]
for a,b,c in ids[f]:
    adj[a].update((b,c));adj[b].update((c,a));adj[c].update((a,b))
def component(seed):
    seen={seed};todo=[seed]
    while todo:
        more=adj[todo.pop()]-seen;seen.update(more);todo.extend(more)
    return seen
hair=component(ids[pos[:,1].argmax()])
body=None
# The one connected piece reaching from the hem to the head.
for i in np.where((points[:,1]>.317)&(points[:,1]<.33))[0]:
    part=component(i)
    if points[list(part),1].max()>.94:
        body=part;break
assert body and body.isdisjoint(hair)
xyz=pos[f];center=xyz.mean(1)
region=np.full(len(f),2);region[np.isin(ids[f[:,0]],list(hair))]=3
inbody=np.isin(ids[f[:,0]],list(body))
depth,height,lat=center.T

# Work at subtexel resolution for narrow cuff edges and oblique islands.
S=384
labels=np.zeros((3,S,S),np.uint8)
region[inbody & (height<.805)]=1
for idx,(tri,q) in enumerate(zip(uv[f]*S,xyz)):
    lo=np.maximum(0,np.floor(tri.min(0)).astype(int));hi=np.minimum(S,np.ceil(tri.max(0)).astype(int))
    yy,xx=np.mgrid[lo[1]:hi[1],lo[0]:hi[0]]
    weights=(np.stack([xx+.5,yy+.5],-1)-tri[0])@np.linalg.inv((tri[1:]-tri[0]).astype(float))
    use=(weights.min(-1)>=0)&(weights.sum(-1)<=1)
    x,h,z=(q[0]+weights[use]@(q[1:]-q[0])).T
    if inbody[idx]:
        # Shallow oval neckline, low in front and higher at the nape.
        radius=np.sqrt(((x+.011)/.037)**2+(z/.035)**2)
        neck=(h>.764)&((radius<1)|(h>.805))
        collar=(h>.764)&(h<.805)&(radius>=1)&(radius<1.24)
        border=(h<.338)|((abs(z)>.077)&(h>.674)&(h<.698+(abs(z)-.08)*.22))|collar
        values=np.where(neck,2,np.where(border,4,1))
    elif region[idx]==3:
        # A few contiguous locks distinguished by pigment, in model space.
        theta=np.arctan2(z,x+.010)
        stripe=((theta>-.85)&(theta<-.22)&(h>.907))|((theta>.44)&(theta<.76)&(h>.925))
        values=np.where(stripe,5,3)
    else:values=2
    channel=0 if inbody[idx] else (1 if region[idx]==3 else 2)
    labels[channel,yy[use],xx[use]]=values
subsets=labels.copy()
labels=labels.max(0)
votes=np.stack([(labels==k).reshape(128,3,128,3).sum((1,3)) for k in range(1,6)])
native=votes.argmax(0)+1
covered=votes.max(0)>0
# Nearest filled texel gutters only. No old artwork remains on the atlas.
ys,xs=np.where(covered)
for y,x in zip(*np.where(~covered)):
    k=np.argmin((ys-y)**2+(xs-x)**2);native[y,x]=native[ys[k],xs[k]]
palette=np.array([[0,0,0],[231,223,207],[234,193,157],[49,59,58],[190,182,167],[69,78,72]],dtype=np.uint8)
Image.fromarray(palette[native]).save(p/'source/base.png')

# Guard each anatomical region independently so neighboring islands cannot
# leak skin or hair colors into the shirt with nearest filtering.
for i,name in enumerate(('body','hair','limbs')):
    scores=np.stack([(subsets[i]==k).reshape(128,3,128,3).sum((1,3)) for k in range(1,6)])
    region_labels=scores.argmax(0)+1
    mask=scores.max(0)>0
    ys,xs=np.where(mask)
    for y,x in zip(*np.where(~mask)):
        k=np.argmin((ys-y)**2+(xs-x)**2);region_labels[y,x]=region_labels[ys[k],xs[k]]
    Image.fromarray(palette[region_labels]).save(p/('source/'+name+'.png'))
np.save(p/'source/triangle_regions.npy',np.where(inbody,0,np.where(region==3,1,2)))
