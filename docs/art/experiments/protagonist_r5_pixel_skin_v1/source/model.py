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

