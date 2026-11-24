from pathlib import Path
import io,json,struct,sys
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(p.parent/'protagonist_r5_pixel_skin_v1/source'))
from model import Model
m=Model(p.parent/'protagonist_r5_head_sample_v3/walk_pixel.glb')
j=m.j;b=m.raw
def append(data):
    b.extend(bytes(-len(b)%4))
    j['bufferViews'].append(dict(buffer=0,byteOffset=len(b),byteLength=len(data)))
    b.extend(data)
    return len(j['bufferViews'])-1
regions=np.load(p/'source/triangle_regions.npy')
tris=m.faces()
new=[]
base=np.array(Image.open(p/'source/base.png').convert('RGB'))
skin=np.array(Image.open(p/'skin.png').convert('RGB'))
face=np.any(base!=skin,axis=-1)
j['materials']=[];j['textures']=[];j['images']=[]
for i,name in enumerate(('body','hair','limbs')):
    atlas=np.array(Image.open(p/('source/'+name+'.png')))
    if i==0:atlas[face]=skin[face]
    data=io.BytesIO();Image.fromarray(atlas).save(data,format='PNG')
    j['images'].append(dict(mimeType='image/png',bufferView=append(data.getvalue())))
    j['textures'].append(dict(source=i,sampler=0))
    j['materials'].append(dict(name=name,pbrMetallicRoughness=dict(baseColorTexture=dict(index=i),metallicFactor=0,roughnessFactor=1)))
    indices=tris[regions==i].flatten()
    template=dict(j['accessors'][m.pr['indices']])
    template.update(bufferView=append(indices.tobytes()),byteOffset=0,count=len(indices),min=[int(indices.min())],max=[int(indices.max())])
    j['accessors'].append(template)
    new.append(dict(m.pr,material=i,indices=len(j['accessors'])-1))
j['meshes'][0]['primitives']=new
j['buffers'][0]['byteLength']=len(b)
h=json.dumps(j,separators=(',',':')).encode();h+=b' '*(-len(h)%4);b.extend(bytes(-len(b)%4))
(p/'walk_pixel.glb').write_bytes(struct.pack('<4sIIII',b'glTF',2,len(h)+len(b)+28,len(h),0x4e4f534a)+h+struct.pack('<II',len(b),0x004e4942)+b)
