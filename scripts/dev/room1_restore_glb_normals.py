"""Restore original per-corner normals; preserve UV2 seams after Blender reimport."""
from pathlib import Path
from collections import defaultdict
import json,struct
import numpy as np


def restore_normals(reference_path, exported_path):
    def decode(path):
        data=Path(path).read_bytes();size,_=struct.unpack_from('<II',data,12)
        doc=json.loads(data[20:20+size]);length,_=struct.unpack_from('<II',data,20+size)
        blob=bytearray(data[28+size:28+size+length])
        def read(index):
            a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
            dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
            width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
            return np.ndarray((a['count'],width),dtype=dtype,buffer=blob,
                offset=v.get('byteOffset',0)+a.get('byteOffset',0),
                strides=(v.get('byteStride',width*dtype.itemsize),dtype.itemsize)).copy()
        return doc,blob,read
    old_doc,_,old_read=decode(reference_path)
    doc,blob,read=decode(exported_path)
    def key_order(pos,uv):
        keys=[tuple((*p,*t)) for p,t in zip(pos,uv)]
        order=sorted(range(3),key=lambda i:keys[i])
        return tuple(keys[i] for i in order),order
    source={}
    for node in old_doc['nodes']:
        if 'mesh' not in node:continue
        groups=defaultdict(list)
        for prim in old_doc['meshes'][node['mesh']]['primitives']:
            attrs={k:old_read(v) for k,v in prim['attributes'].items()}
            indices=old_read(prim['indices']).reshape(-1,3)
            for tri in indices:
                key,order=key_order(attrs['POSITION'][tri],attrs['TEXCOORD_0'][tri])
                groups[key].append(attrs['NORMAL'][tri][order].copy())
        source[node['name']]=groups
    maximum=0.0
    # Snapshot before appending accessors/buffer views, so every read uses original offsets.
    work=[]
    for node in doc['nodes']:
        if 'mesh' not in node:continue
        mesh=doc['meshes'][node['mesh']]
        for prim in mesh['primitives']:
            attrs={k:read(v) for k,v in prim['attributes'].items()}
            indices=read(prim['indices']).reshape(-1,3)
            expanded={k:array[indices].reshape(-1,array.shape[1]).copy() for k,array in attrs.items()}
            groups=source[node['name']]
            for ti,tri in enumerate(indices):
                key,order=key_order(attrs['POSITION'][tri],attrs['TEXCOORD_0'][tri])
                current=attrs['NORMAL'][tri][order]
                candidates=groups[key]
                chosen=min(range(len(candidates)),key=lambda i:float(np.max(np.abs(candidates[i]-current))))
                target=candidates.pop(chosen)
                difference=float(np.max(np.abs(target-current)))
                assert difference<.001,(node['name'],difference)
                maximum=max(maximum,difference)
                for sorted_index,corner in enumerate(order):
                    expanded['NORMAL'][ti*3+corner]=target[sorted_index]
            work.append((prim,expanded))
        assert not any(source[node['name']].values())
    for prim,expanded in work:
        new_attributes={}
        for key,array in expanded.items():
            while len(blob)%4:blob.append(0)
            offset=len(blob);raw=array.tobytes();blob.extend(raw)
            view=len(doc['bufferViews'])
            doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(raw),'target':34962})
            accessor={'bufferView':view,'componentType':5126,'count':len(array),'type':{2:'VEC2',3:'VEC3',4:'VEC4'}[array.shape[1]]}
            assert array.dtype==np.dtype('<f4')
            if key=='POSITION':accessor.update(min=array.min(axis=0).tolist(),max=array.max(axis=0).tolist())
            new_attributes[key]=len(doc['accessors']);doc['accessors'].append(accessor)
        prim['attributes']=new_attributes;prim.pop('indices',None)
    while len(blob)%4:blob.append(0)
    doc['buffers'][0]['byteLength']=len(blob)
    js=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode('utf8')
    js+=b' '*((-len(js))%4)
    output=struct.pack('<III',0x46546c67,2,28+len(js)+len(blob))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(blob),0x004e4942)+blob
    Path(exported_path).write_bytes(output)
    return {'maximum_blender_roundtrip_normal_difference_restored':maximum,
            'method':'Original normal per matching exact position/UV0 triangle corner; expand vertices to retain hard-edge distinctions'}


if __name__=='__main__':
    import sys
    print(json.dumps(restore_normals(sys.argv[1],sys.argv[2]),indent=2))
