"""Verify native texel density from delivered GLB geometry and actual PNG sizes."""
from collections import defaultdict
import json
from math import dist
from pathlib import Path
from statistics import median
from struct import unpack_from
from PIL import Image

base=Path(__file__).resolve().parent.parent
root=base.parents[3]
art=root/'assets/art/cryo_building_review_v1'
sizes={p.stem:Image.open(p).size for p in (art/'textures').glob('*.png')}
sizes.update({'M06':sizes['M06-01'],'M06-BASE':sizes['M06-02']})

def read_model(path):
    data=path.read_bytes()
    assert data[:4]==b'glTF'
    length=unpack_from('<I',data,12)[0]
    info=json.loads(data[20:20+length])
    buf=data[28+length:]
    def values(i):
        a=info['accessors'][i]
        v=info['bufferViews'][a['bufferView']]
        code={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']]
        n={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
        size={'f':4,'I':4,'H':2,'B':1}[code]*n
        off=a.get('byteOffset',0)+v.get('byteOffset',0)
        stride=v.get('byteStride',size)
        return [unpack_from('<'+code*n,buf,off+k*stride) for k in range(a['count'])]
    results=defaultdict(list)
    skipped=defaultdict(int)
    for node in info['nodes']:
        if 'mesh' not in node:
            continue
        scale=node.get('scale',[1,1,1])
        for p in info['meshes'][node['mesh']]['primitives']:
            attr=p['attributes']
            mat=info['materials'][p['material']]['name']
            size=sizes[mat]
            xyz=[tuple(a*b for a,b in zip(pt,scale)) for pt in values(attr['POSITION'])]
            uv=[tuple(a*b for a,b in zip(pt,size)) for pt in values(attr['TEXCOORD_0'])]
            ids=[a[0] for a in values(p['indices'])]
            edges=set()
            for i in range(0,len(ids),3):
                a,b,c=ids[i:i+3]
                edges.update(tuple(sorted(e)) for e in ((a,b),(b,c),(c,a)))
            for i,j in edges:
                metres=dist(xyz[i],xyz[j])
                if metres<.025:
                    skipped[mat]+=1
                    continue
                results[mat].append(dist(uv[i],uv[j])/metres)
    records={}
    for name,ds in sorted(results.items()):
        records[name]={
            'size_px':sizes[name],'edge_samples':len(ds),
            'median_texels_per_m':round(median(ds),2),
            'within_1pct_percent':round(100*sum(79.2<=x<=80.8 for x in ds)/len(ds),2),
            'min':round(min(ds),2),'max':round(max(ds),2),
            'edges_under_25mm_excluded':skipped[name],
        }
    return records

report={p.stem:read_model(p) for p in sorted((art/'models').glob('*.glb'))}
primary={'M01','M02','M03','M05-L','M05-D','M06-01','M06-02','M06-03','M06-BASE','M06-J','M06-R','M07'}
for model, mats in report.items():
    for name, m in mats.items():
        if name in primary or name.startswith('FACE_'):
            assert abs(m['median_texels_per_m']-80)<.1,(model,name,m)
data={'target_texels_per_m':80,'method':'GLB UV0 edge length in native PNG pixels divided by local geometric length in metres, checking major faces by material, excluding edges under 25 mm. Not pixels on screen. Curved grips, 15-degree diffuser sections, and projected bevel edges can have local deviations.', 'models':report}
(base/'evidence/uv0_density.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
print(f'UV0 checked for {len(report)} GLBs')
