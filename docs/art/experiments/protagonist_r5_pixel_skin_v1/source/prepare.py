from model import Model,Path,np
from PIL import Image
import io
p=Path(__file__).resolve().parent
root=p.parent.parent
original=Model(root/'protagonist_walk_r5_hem_fix/walk.glb')
new=Model(root/'protagonist_r5_uv_trial/walk_uv.glb')
tex=original.j['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']
v=original.j['bufferViews'][original.j['images'][original.j['textures'][tex]['source']]['bufferView']]
tex=np.array(Image.open(io.BytesIO(original.raw[v['byteOffset']:v['byteOffset']+v['byteLength']])).convert('RGB'))
f0=original.faces();f1=new.faces()
assert np.array_equal(original.attribute('POSITION')[f0],new.attribute('POSITION')[f1])
u0=original.attribute('TEXCOORD_0')[f0];u1=new.attribute('TEXCOORD_0')[f1]
N=512
atlas=np.full((N,N,3),120,np.uint8);mask=np.zeros((N,N),np.uint8)
for dst,src in zip(u1*N,u0):
    lo=np.maximum(0,np.floor(dst.min(0)).astype(int)); hi=np.minimum(N,np.ceil(dst.max(0)).astype(int))
    y,x=np.mgrid[lo[1]:hi[1],lo[0]:hi[0]];delta=np.stack((x+.5,y+.5),-1)-dst[0]
    w=delta@np.linalg.inv((dst[1:]-dst[0]).astype(float))
    inside=(w.min(-1)>=0)&(w.sum(-1)<=1)
    uv=np.clip(src[0]+w[inside]@(src[1:]-src[0]),0,.999999)
    atlas[y[inside],x[inside]]=tex[(uv[:,1]*tex.shape[0]).astype(int),(uv[:,0]*tex.shape[1]).astype(int)]
    mask[y[inside],x[inside]]=255
rgba=Image.fromarray(atlas).convert('RGBA');rgba.putalpha(Image.fromarray(mask))
rgba=rgba.resize((128,128),Image.Resampling.BOX)
background=Image.new('RGB',rgba.size,(86,91,90));background.paste(rgba,mask=rgba.getchannel('A'))
background.save(p/'guide.png')
rgba.getchannel('A').point(lambda x:255 if x>95 else 0).save(p/'coverage.png')
