"""Read back geometry/UV0 from both exports; UV2 is intentionally replaced."""
from pathlib import Path
from collections import Counter
import json,struct
import numpy as np

ROOT=Path(__file__).resolve().parents[4]
OLD=ROOT/'assets/art/room1_open_hero_bake_r1/room1_baked_uv2_r3.glb'
NEW=ROOT/'assets/art/room1_open_hero_uv2_r2/room1_baked_uv2_r3.glb'

def decode(path):
 b=path.read_bytes();n,_=struct.unpack_from('<II',b,12);doc=json.loads(b[20:20+n])
 size,_=struct.unpack_from('<II',b,20+n);blob=b[28+n:28+n+size]
 types={5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}
 def read(index):
  ac=doc['accessors'][index];view=doc['bufferViews'][ac['bufferView']]
  dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[ac['type']];dt=np.dtype(types[ac['componentType']])
  return np.ndarray((ac['count'],dim),dtype=dt,buffer=blob,
    offset=view.get('byteOffset',0)+ac.get('byteOffset',0),
    strides=(view.get('byteStride',dim*dt.itemsize),dt.itemsize)).copy()
 result={}
 for node in doc['nodes']:
  if 'mesh' not in node:continue
  triangles=Counter();normal_groups={}
  for primitive in doc['meshes'][node['mesh']]['primitives']:
   data=np.concatenate([read(primitive['attributes'][key]) for key in ['POSITION','NORMAL','TEXCOORD_0']],axis=1)
   indices=(read(primitive['indices']).reshape(-1,3) if 'indices' in primitive else np.arange(len(data)).reshape(-1,3))
   # glTF can duplicate vertices on new UV seams. Compare triangle corners,
   # independent of buffer indices, without discarding the source color UV.
   for tri in indices:
    corners=data[tri].astype(np.float64)
    keys=[tuple(row[[0,1,2,6,7]]) for row in corners]
    order=sorted(range(3),key=lambda i:keys[i])
    signature=tuple(keys[i] for i in order)
    triangles[signature]+=1
    normal_groups.setdefault(signature,[]).append(tuple(corners[order,3:6].reshape(-1)))
  transform={k:node.get(k) for k in ['matrix','translation','rotation','scale']}
  result[node['name']]={'transform':transform,'triangles':triangles,'normals':normal_groups}
 return result

old=decode(OLD);new=decode(NEW)
names=set(old)&set(new)
changed_geometry_uv0=[name for name in names if old[name]['triangles']!=new[name]['triangles']]
normal_differences={}
for name in names:
 if old[name]['triangles']!=new[name]['triangles']:continue
 maximum=0.0
 for key,values in old[name]['normals'].items():
  lhs=np.array(sorted(values));rhs=np.array(sorted(new[name]['normals'][key]))
  maximum=max(maximum,float(np.max(np.abs(lhs-rhs))))
 normal_differences[name]=maximum
changed_normals=[name for name,value in normal_differences.items() if value>1e-6]
changed_transform=[name for name in names if old[name]['transform']!=new[name]['transform']]
report={'old':str(OLD.relative_to(ROOT)),'new':str(NEW.relative_to(ROOT)),
 'old_mesh_nodes':len(old),'new_mesh_nodes':len(new),
 'new_or_missing_nodes':sorted(set(old)^set(new)),
 'changed_position_or_uv0_triangles_exact':changed_geometry_uv0,
 'changed_normals_beyond_1e6':changed_normals,
 'maximum_normal_component_difference':max(normal_differences.values()),
 'changed_node_transforms':changed_transform,
 'precision':'Positions and color UV0 compared exactly per triangle corner. Normals tolerate 1e-6 for Blender reimport normalization; maximum difference reported. UV2 intentionally replaced.'}
(Path(__file__).parent/'export_scope_readback.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
