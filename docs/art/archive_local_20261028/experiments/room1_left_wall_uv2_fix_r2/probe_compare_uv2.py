import json,struct
from pathlib import Path
from collections import Counter
import numpy as np
HERE=Path(__file__).resolve().parent
source=json.loads((HERE/'probe_source_uv2.json').read_text())
b=(HERE.parents[3]/'assets/art/room1_open_hero_uv2_r2/room1_baked_uv2_r3.glb').read_bytes()
n,_=struct.unpack_from('<II',b,12);doc=json.loads(b[20:20+n]);size,_=struct.unpack_from('<II',b,20+n);blob=b[28+n:28+n+size]
def read(idx):
 a=doc['accessors'][idx];v=doc['bufferViews'][a['bufferView']];dt=np.dtype({5126:'<f4',5123:'<u2',5125:'<u4'}[a['componentType']]);dim={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
 return np.ndarray((a['count'],dim),dtype=dt,buffer=blob,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dim*dt.itemsize),dt.itemsize)).copy()
def sig(rows):return Counter(tuple(sorted(tuple(v) for v in np.round(np.asarray(row,dtype=np.float64),5).tolist())) for row in rows)
changed=[]
for node in doc['nodes']:
 if node['name'] not in source:continue
 rows=[]
 for p in doc['meshes'][node['mesh']]['primitives']:
  data=np.concatenate([read(p['attributes'][k]) for k in ['POSITION','TEXCOORD_0','TEXCOORD_1']],axis=1)
  rows.extend(data[read(p['indices']).reshape(-1,3)])
 if sig(rows)!=sig(source[node['name']]['triangles']):changed.append(node['name'])
print('Source-vs-GLB UV2 triangle differences:',len(changed),changed[:12])
print('Layers',source['Bake_Shell_Wall_left']['layers'])
node=next(x for x in doc['nodes'] if x['name']=='Bake_Shell_Wall_left')
p=doc['meshes'][node['mesh']]['primitives'][0]
data=np.concatenate([read(p['attributes'][k]) for k in ['POSITION','TEXCOORD_0','TEXCOORD_1']],axis=1)
print('GLB first',data[read(p['indices']).reshape(-1,3)[:2]].tolist())
print('Source first',source[node['name']]['triangles'][:2])

