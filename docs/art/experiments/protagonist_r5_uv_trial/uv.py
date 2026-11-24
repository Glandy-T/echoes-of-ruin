from pathlib import Path
import numpy as np,json,struct
from collections import defaultdict,Counter
root=Path(__file__).resolve().parent
class Model:
    def __init__(self,p):
        b=p.read_bytes(); n=struct.unpack_from('<I',b,12)[0]
        self.j=json.loads(b[20:20+n]); self.raw=bytearray(b[28+n:])
        self.pr=self.j['meshes'][0]['primitives'][0]
    def arr(self,i):
        a=self.j['accessors'][i]; v=self.j['bufferViews'][a['bufferView']]
        dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
        w={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        size=np.dtype(dtype).itemsize
        return np.ndarray((a['count'],w),dtype,buffer=self.raw,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',w*size),size)).copy()
    def attribute(self,name):return self.arr(self.pr['attributes'][name])
    def faces(self):return self.arr(self.pr['indices']).reshape(-1,3)
src=Model(root.parent/'protagonist_walk_r5_hem_fix'/'walk.glb')
ref=Model(root/'tripo_uv.glb')
if __name__=='__main__':
    for m in (src,ref):
        xyz=m.attribute('POSITION');print(m.pr,xyz.min(0),xyz.max(0),len(m.faces()))
from PIL import Image,ImageDraw
def key(v):
    return tuple(v.tolist())
rf=ref.faces()
rp=ref.attribute('POSITION');ru=ref.attribute('TEXCOORD_0')
lookup=defaultdict(list)
for face in rf:
    lookup[tuple(sorted(key(rp[i]) for i in face))].append(face)
faces=src.faces();pos=src.attribute('POSITION')
rowmap={}; old=[]; newuv=[]; indices=[]
for face in faces:
    candidates=lookup[tuple(sorted(key(pos[i]) for i in face))]
    assert len(candidates)==1
    uv_at={key(rp[i]):ru[i] for i in candidates[0]}
    for i in face:
        uv=uv_at[key(pos[i])]
        k=(int(i),key(uv))
        if k not in rowmap:
            rowmap[k]=len(old); old.append(i); newuv.append(uv)
        indices.append(rowmap[k])
newuv=np.array(newuv);indices=np.array(indices,dtype='<u2').reshape(-1,3)
j=src.j
def buffer(blob):
    src.raw.extend(bytes(-len(src.raw)%4))
    start=len(src.raw);src.raw.extend(blob)
    j['bufferViews'].append(dict(buffer=0,byteOffset=start,byteLength=len(blob)))
    return len(j['bufferViews'])-1
def replace(i,a):
    acc=j['accessors'][i]
    acc.update(bufferView=buffer(a.tobytes()),byteOffset=0,count=len(a))
    if 'min' in acc:
        acc.update(min=a.min(0).tolist(),max=a.max(0).tolist())
for name,i in src.pr['attributes'].items():
    replace(i,newuv if name=='TEXCOORD_0' else src.arr(i)[old])
replace(src.pr['indices'],indices.reshape(-1,1))
def write_glb(p):
    j['buffers'][0]['byteLength']=len(src.raw)
    h=json.dumps(j,separators=(',',':')).encode();h+=b' '*(-len(h)%4)
    b=bytes(src.raw)+bytes(-len(src.raw)%4)
    p.write_bytes(struct.pack('<4sIIII',b'glTF',2,28+len(h)+len(b),len(h),0x4e4f534a)+h+struct.pack('<II',len(b),0x004e4942)+b)
# The embedded texture from the old unwrap is meaningless on the new UV.
j['materials']=[dict(name='R5 UV template',pbrMetallicRoughness=dict(metallicFactor=0,roughnessFactor=1))]
write_glb(root/'walk_uv.glb')
def analyze(xyz,uv,faces):
    coords=np.column_stack((xyz.round(6),uv))
    _,ids=np.unique(coords,axis=0,return_inverse=True)
    par=list(range(len(faces)));edge={}
    def rootid(i):
        while par[i]!=i:
            par[i]=par[par[i]];i=par[i]
        return i
    for i,r in enumerate(ids[faces]):
        for a,b in zip(r,np.roll(r,1)):
            k=tuple(sorted((a,b)))
            if k in edge:par[rootid(i)]=rootid(edge[k])
            else:edge[k]=i
    t=uv[faces].astype(float);v=t[:,1]-t[:,0];w=t[:,2]-t[:,0]
    area=abs(v[:,0]*w[:,1]-v[:,1]*w[:,0])/2
    _,g=np.unique([rootid(i) for i in range(len(faces))],return_inverse=True)
    areas=np.bincount(g,weights=area)
    tri=xyz[faces];world_area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
    return dict(islands=len(areas),under4_at256=int(sum(areas*256**2<4)),zero_uv=int(sum(area<1e-12)),uv_range=[float(t.min()),float(t.max())],area_sum=float(area.sum()),density_at128=128*np.sqrt(area.sum()/world_area.sum())/1.4025)
original=Model(root.parent/'protagonist_walk_r5_hem_fix'/'walk.glb')
metrics=dict(original=analyze(pos,original.attribute('TEXCOORD_0'),faces),smart=analyze(pos[old],newuv,indices),triangles=len(indices))
(root/'metrics.json').write_text(json.dumps(metrics,indent=2))
print(metrics)
im=Image.new('RGB',(1024,1024),'#1c2125');draw=ImageDraw.Draw(im)
for tri in newuv[indices]:
    draw.polygon([tuple((v*1023).tolist()) for v in tri],outline='#8bafbc')
im.save(root/'uv_layout.png')
for size in (128,256):
    y,x=np.indices((size,size)); v=np.where(((x//4+y//4)%2)==0,178,102).astype('uint8')
    Image.fromarray(v).convert('RGB').save(root/f'checker{size}.png')
