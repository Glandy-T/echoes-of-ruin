from mapping import old, p; from model import Model,Path,np,json,struct
from PIL import Image
p=Path(__file__).resolve().parent.parent
im=Image.open(p/'skin.png').convert('RGB')
assert im.size==(128,128)
im.save(p/'skin.png')
m=Model(p.parent/'protagonist_r5_uv_trial/walk_uv.glb')
a=m.j['accessors'][m.pr['attributes']['TEXCOORD_0']]
view=m.j['bufferViews'][a['bufferView']]
uv=np.load(p/'source/face_uv.npy')
assert uv.nbytes==view['byteLength']
off=view.get('byteOffset',0)
m.raw[off:off+uv.nbytes]=uv.tobytes()
a.update(min=uv.min(0).tolist(),max=uv.max(0).tolist())
j=m.j;b=m.raw;b.extend(bytes(-len(b)%4));png=(p/'skin.png').read_bytes()
j['bufferViews'].append(dict(buffer=0,byteOffset=len(b),byteLength=len(png)))
b.extend(png);j['buffers'][0]['byteLength']=len(b)
j['images']=[dict(mimeType='image/png',bufferView=len(j['bufferViews'])-1)]
j['samplers']=[dict(magFilter=9728,minFilter=9728,wrapS=33071,wrapT=33071)]
j['textures']=[dict(source=0,sampler=0)]
j['materials'][0]['pbrMetallicRoughness']['baseColorTexture']=dict(index=0)
h=json.dumps(j,separators=(',',':')).encode();h+=b' '*(-len(h)%4);b.extend(bytes(-len(b)%4))
(p/'walk_pixel.glb').write_bytes(struct.pack('<4sIIII',b'glTF',2,len(h)+len(b)+28,len(h),0x4e4f534a)+h+struct.pack('<II',len(b),0x004e4942)+b)


