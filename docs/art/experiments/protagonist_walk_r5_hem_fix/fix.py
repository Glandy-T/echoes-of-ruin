"""Patch R5 skinning and drop the indexed sole plate, retaining original motion and textures."""
import json
import struct
from pathlib import Path
import numpy as np

here=Path(__file__).resolve().parent
source=here.parent/'protagonist_smart_mesh_walk_r5'/'walk.glb'
data=source.read_bytes()
header_size=struct.unpack_from('<I',data,12)[0]
doc=json.loads(data[20:20+header_size])
binary=bytearray(data[28+header_size:])
primitive=doc['meshes'][0]['primitives'][0]
def array(index):
    acc=doc['accessors'][index]
    view=doc['bufferViews'][acc['bufferView']]
    assert 'byteStride' not in view
    width={'SCALAR':1,'VEC3':3,'VEC4':4}[acc['type']]
    dtype={5126:'<f4',5121:'u1',5123:'<u2'}[acc['componentType']]
    return np.frombuffer(binary,dtype=dtype,count=width*acc['count'],offset=view.get('byteOffset',0)+acc.get('byteOffset',0)).reshape(-1,width)
attrs=primitive['attributes']
pos,joints,weights=[array(attrs[key]) for key in ('POSITION','JOINTS_0','WEIGHTS_0')]
tri=array(primitive['indices']).reshape(-1,3)
names=[doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']]
# UV splits share positions; use those positions to classify the original islands.
points,inverse=np.unique(pos.round(6),axis=0,return_inverse=True)
neighbors=[set() for _ in points]
for a,b,c in inverse[tri]:
    neighbors[a].update((b,c)); neighbors[b].update((a,c)); neighbors[c].update((a,b))
labels=np.full(len(points),-1)
parts=[]
for i in range(len(points)):
    if labels[i]>=0: continue
    idx=len(parts)
    stack=[i]; labels[i]=idx
    while stack:
        for v in neighbors[stack.pop()]:
            if labels[v]<0:
                labels[v]=idx; stack.append(v)
    parts.append(points[labels==idx])
sole,= [i for i,v in enumerate(parts) if np.ptp(v[:,1])<1e-6 and v[:,1].max()<0.01]
dress,= [i for i,v in enumerate(parts) if 0.31<v[:,1].min()<0.33 and v[:,1].max()>0.9]
vid=labels[inverse]
kept=tri[vid[tri[:,0]]!=sole].copy()
removed=len(tri)-len(kept)
tri[:len(kept)]=kept
acc=doc['accessors'][primitive['indices']]
acc.update(count=int(kept.size),min=[int(kept.min())],max=[int(kept.max())])
def smooth(x):
    t=np.clip(x,0,1)
    return t*t*(3-2*t)
left,right,waist=[names.index(n) for n in ('L_ThighTwist01','R_ThighTwist01','Waist')]
def lateral_center(bone):
    return np.average(pos[:,2],weights=np.sum(weights*(joints==bone),axis=1))
direction=np.sign(lateral_center(left)-lateral_center(right))
for i in np.flatnonzero((vid==dress)&(pos[:,1]<0.55)):
    z=pos[i,1]; side=smooth(0.5+direction*pos[i,2]/0.10)
    follow=0.80*(1-smooth((z-0.34)/0.19))
    blend=smooth((z-0.48)/0.07)
    values={left:follow*side*(1-blend),right:follow*(1-side)*(1-blend),waist:(1-follow)*(1-blend)}
    for joint,w in zip(joints[i],weights[i]):
        if 'Hand' not in names[joint] and 'arm' not in names[joint].lower():
            values[int(joint)]=values.get(int(joint),0)+w*blend
    ranked=sorted(values,key=values.get,reverse=True)[:4]
    total=sum(values[j] for j in ranked)
    joints[i]=0; weights[i]=0
    for k,j in enumerate(ranked):
        joints[i,k]=j; weights[i,k]=values[j]/total
header=json.dumps(doc,separators=(',',':')).encode()
header+=b' '*(-len(header)%4)
(here/'walk.glb').write_bytes(struct.pack('<4sIIII',b'glTF',2,28+len(header)+len(binary),len(header),0x4e4f534a)+header+struct.pack('<II',len(binary),0x004e4942)+binary)
print('Removed triangles:',removed,'Triangles:',len(kept))
