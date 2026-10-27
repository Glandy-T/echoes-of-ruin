"""Read GLBs independently: source pixels, actual UV0, shared UV2 and poses."""
from pathlib import Path
import json,struct,io,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parents[1];REPO=HERE.parents[3]
OUT=REPO/'assets/art/cryopod_standard_v8'
CANON={p.stem:Image.open(p).convert('RGBA') for p in (REPO/'docs/art/experiments/room1_pod_volume_v4/textures').glob('*.png')}
class GLB:
    def __init__(self,path):
        raw=path.read_bytes();length=struct.unpack_from('<I',raw,12)[0];self.j=json.loads(raw[20:20+length]);self.bin=raw[28+length:];self.world={}
        def visit(i,parent):
            n=self.j['nodes'][i]
            if 'matrix' in n:m=np.array(n['matrix']).reshape(4,4).T
            else:
                x,y,z,w=n.get('rotation',[0,0,0,1]);r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
                m=np.eye(4);m[:3,:3]=r@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
            self.world[i]=parent@m
            for c in n.get('children',[]):visit(c,self.world[i])
        for i in self.j['scenes'][self.j.get('scene',0)]['nodes']:visit(i,np.eye(4))
    def accessor(self,i):
        a=self.j['accessors'][i];v=self.j['bufferViews'][a['bufferView']]
        dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        return np.ndarray((a['count'],width),dtype=dt,buffer=self.bin,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*dt.itemsize),dt.itemsize)).copy()
    def primitives(self):
        for ni,n in enumerate(self.j['nodes']):
            if 'mesh' not in n:continue
            for p in self.j['meshes'][n['mesh']]['primitives']:
                key=self.j['materials'][p['material']]['name'].split('POD_V')[-1].split('_',1)[1]
                yield n['name'],self.world[ni],key,p
def color_pairs(g):
    result={}
    for name,matrix,key,p in g.primitives():
        if key not in CANON:continue
        pos=g.accessor(p['attributes']['POSITION']);uv=g.accessor(p['attributes']['TEXCOORD_0'])
        world=(matrix@np.column_stack([pos,np.ones(len(pos))]).T).T[:,:3]
        pairs=np.column_stack([np.round(world,4),np.round(uv,6)])
        result.setdefault(key,set()).update(tuple(float(x) for x in row) for row in pairs)
    return result
def uv_records(g):
    rows={}
    for name,matrix,key,p in g.primitives():
        assert set(p['attributes']).issuperset({'TEXCOORD_0','TEXCOORD_1'})
        material=g.j['materials'][p['material']]
        texture=material.get('pbrMetallicRoughness',{}).get('baseColorTexture')
        if texture:assert texture.get('texCoord',0)==0,(name,key,texture)
        uv=g.accessor(p['attributes']['TEXCOORD_1'])
        rows[name]=sorted(set(tuple(float(v) for v in np.round(r,7)) for r in uv))
    return rows
def main():
    variants={k:GLB(OUT/f'cryopod_standard_v8{suffix}.glb') for k,suffix in [('animated',''),('closed','_closed'),('open','_open')]}
    uv={k:uv_records(v) for k,v in variants.items()};assert uv['animated']==uv['closed']==uv['open']
    images=[]
    for entry in variants['animated'].j['images']:
        view=variants['animated'].j['bufferViews'][entry['bufferView']];start=view.get('byteOffset',0)
        im=Image.open(io.BytesIO(variants['animated'].bin[start:start+view['byteLength']])).convert('RGBA')
        match=[k for k,v in CANON.items() if im.size==v.size and im.tobytes()==v.tobytes()]
        assert len(match)==1,(entry,match);images+=match
    assert set(images)==set(CANON)
    comparisons={}
    for pose in ['closed','open']:
        old=GLB(REPO/f'assets/art/room1_pod_volume_v4/pod_{pose}_v4.glb')
        a,b=color_pairs(old),color_pairs(variants[pose]);rows={}
        for key in CANON:
            extra=b[key]-a[key];rows[key]={'old_unique_corners':len(a[key]),'new_unique_corners':len(b[key]),'new_unmatched_corners':len(extra)}
            assert not extra,(pose,key,list(extra)[:4])
        comparisons[pose]=rows
    names=[a.get('name') for a in variants['animated'].j.get('animations',[])];assert 'LidOpen' in names,names
    result={'v4_color_pixels_unchanged':images,'color_uv_world_corner_comparison':comparisons,'shared_uv2_identical_across_all_three_glbs':True,'mesh_names':list(uv['animated']),'actual_animation_names':names,'glb_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.glb')}}
    (HERE/'source/glb_assets_readback.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print('V8_GLB_READBACK_PASS: source pixels/UV0+poses unchanged, one shared UV2, true animation')
if __name__=='__main__':main()
