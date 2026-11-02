"""Read GLB vertex/UV triangle Jacobians; never change geometry or UVs."""
from pathlib import Path
import json,struct,numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
p=ROOT/'assets/art/cryopod_standard_v8/cryopod_standard_v8.glb';data=p.read_bytes();offset=12;binary=None;g=None
while offset<len(data):
 length,kind=struct.unpack_from('<II',data,offset);chunk=data[offset+8:offset+8+length];offset+=8+length
 if kind==0x4e4f534a:g=json.loads(chunk)
 if kind==0x004e4942:binary=chunk
def accessor(index):
 a=g['accessors'][index];v=g['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
 start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',np.dtype(dt).itemsize*n)
 return np.ndarray((a['count'],n),dtype=dt,buffer=binary,offset=start,strides=(stride,np.dtype(dt).itemsize)).copy()
roles={'POD_V8_lid':'lid','POD_V8_shell_side':'shell_side','POD_V8_shell_end':'shell_end'};report=[]
for mesh in g['meshes']:
 for prim in mesh['primitives']:
  name=g['materials'][prim['material']]['name'];role=roles.get(name)
  if role is None:continue
  pos=accessor(prim['attributes']['POSITION']);uv=accessor(prim['attributes']['TEXCOORD_0']);ix=accessor(prim['indices']).flatten().reshape(-1,3)
  size=Image.open(ROOT/'assets/art/room1_pod_age_r27'/f'{role}.png').size;measure=[];areas=[];largest=[]
  for tri in ix:
   xyz=pos[tri];tex=uv[tri]*np.array(size)
   world=np.column_stack((xyz[1]-xyz[0],xyz[2]-xyz[0]));area=np.linalg.norm(np.cross(world[:,0],world[:,1]))/2
   if area<1e-10:continue
   texedges=np.column_stack((tex[1]-tex[0],tex[2]-tex[0]))
   if abs(np.linalg.det(texedges))<1e-8:continue
   sigma=np.linalg.svd(texedges@np.linalg.pinv(world),compute_uv=False)
   measure.append(sigma[:2]);areas.append(float(area));largest.append({'triangle_area_m2':float(area),'density':sigma[:2].tolist()})
  d=np.array(measure);w=np.array(areas)
  report.append({'role':role,'mesh':mesh['name'],'material':name,'native_size':list(size),'triangles':len(d),'surface_m2':sum(areas),'largest_triangle_samples':sorted(largest,key=lambda x:x['triangle_area_m2'],reverse=True)[:4],'principal_density_weighted_mean':np.average(d,axis=0,weights=w).tolist(),'principal_density_median':np.median(d,axis=0).tolist(),'principal_density_p10_p90':np.percentile(d,[10,90],axis=0).tolist(),'note':'Principal values include small bevels and packed strips; lower extremes are not a main-face target. GLB model has unit scale; rotations do not affect this metric.'})
assert {x['role'] for x in report}==set(roles.values()),[(m['name']) for m in g['materials']]
(HERE/'density_measurement.json').write_text(json.dumps({'creative_output_scale':1,'geometry_or_UV_changed':False,'measurements':report},indent=2),encoding='utf8')
print('R27_DENSITY_READBACK',json.dumps(report))
