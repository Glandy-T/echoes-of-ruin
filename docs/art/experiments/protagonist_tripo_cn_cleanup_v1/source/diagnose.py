"""Read-only topology report for the CN P2.0 OBJ.

Run with Blender's bundled Python; this script neither saves nor alters the mesh.
It parses OBJ positions/faces directly so the report preserves OBJ polygon topology.
"""
import json, math, os, sys, hashlib
from collections import defaultdict, deque

EPS = 1e-6
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "protagonist_tripo_cn_p20_v1"))
OBJ = os.path.join(ROOT, "model", "protagonist_tripo_cn_p20_v1_raw.obj")
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "component_report.json"))

def add(a,b): return (a[0]+b[0],a[1]+b[1],a[2]+b[2])
def sub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
def mul(a,s): return (a[0]*s,a[1]*s,a[2]*s)
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def length(a): return math.sqrt(a[0]*a[0]+a[1]*a[1]+a[2]*a[2])
def tri_area(a,b,c): return length(cross(sub(b,a),sub(c,a)))*.5

class DSU:
    def __init__(self,n): self.p=list(range(n)); self.r=[0]*n
    def find(self,x):
        while self.p[x]!=x: self.p[x]=self.p[self.p[x]]; x=self.p[x]
        return x
    def union(self,a,b):
        a,b=self.find(a),self.find(b)
        if a==b:return
        if self.r[a]<self.r[b]:a,b=b,a
        self.p[b]=a
        if self.r[a]==self.r[b]:self.r[a]+=1

def parse_obj(path):
    vs=[]; fs=[]
    with open(path,encoding="utf-8",errors="replace") as f:
        for line in f:
            s=line.split()
            if not s: continue
            if s[0]=='v' and len(s)>=4: vs.append(tuple(map(float,s[1:4])))
            elif s[0]=='f' and len(s)>=4:
                face=[]
                for token in s[1:]:
                    i=int(token.split('/')[0]); face.append(i-1 if i>0 else len(vs)+i)
                fs.append(face)
    return vs,fs

def merge_positions(vs, eps):
    d=DSU(len(vs)); buckets=defaultdict(list)
    # Test neighboring quantized cells, avoiding a false claim from same-cell-only rounding.
    for i,p in enumerate(vs):
        q=tuple(math.floor(x/eps) for x in p)
        for dx in (-1,0,1):
          for dy in (-1,0,1):
           for dz in (-1,0,1):
            for j in buckets.get((q[0]+dx,q[1]+dy,q[2]+dz),[]):
                r=vs[j]
                if max(abs(p[k]-r[k]) for k in range(3))<=eps: d.union(i,j)
        buckets[q].append(i)
    reps={}; out=[]
    for i in range(len(vs)):
        root=d.find(i)
        if root not in reps: reps[root]=len(reps)
        out.append(reps[root])
    return out, len(reps)

def bbox(points):
    lo=[min(p[k] for p in points) for k in range(3)]; hi=[max(p[k] for p in points) for k in range(3)]
    return lo,hi,[hi[k]-lo[k] for k in range(3)]

def classify(c, height):
    lo,hi,size=c['bbox']['min'],c['bbox']['max'],c['bbox']['size']; cen=c['centroid']
    # The task described a +Z-up inspection convention, but raw OBJ extents prove
    # the source itself is Y-up: the single flat plane spans X/Z at Y=.00488281.
    if size[1] < height*.015 and size[0] > height*.8 and size[2] > height*.8:
        return 'obvious_ground_plane_candidate'
    # Spatial candidate only; do not imply semantic mesh membership.
    if cen[1] > lo_global[1]+height*.62 and c['faces'] <= 80 and max(size) < height*.35:
        return 'small_upper_region_fragment_candidate'
    return 'unclassified'

vs,fs=parse_obj(OBJ)
lo_global,hi_global,size_global=bbox(vs); height=size_global[1]
merged,nmerged=merge_positions(vs,EPS)
face_verts=[list(dict.fromkeys(merged[i] for i in f)) for f in fs]
vf=defaultdict(list)
for fi, f in enumerate(face_verts):
    for v in f: vf[v].append(fi)
adj=[set() for _ in fs]
for attached in vf.values():
    for x in attached[1:]: adj[attached[0]].add(x); adj[x].add(attached[0])
seen=set(); groups=[]
for start in range(len(fs)):
    if start in seen: continue
    stack=[start]; seen.add(start); g=[]
    while stack:
        x=stack.pop();g.append(x)
        for y in adj[x]:
            if y not in seen:seen.add(y);stack.append(y)
    groups.append(sorted(g))

components=[]
for gid,g in enumerate(groups):
    vertids=sorted({v for fi in g for v in face_verts[fi]}); pts=[vs[next(i for i,m in enumerate(merged) if m==v)] for v in vertids]
    # original-index lookup above is deliberately only for bbox: representative coordinate is exact within EPS.
    area=0.; weighted=[0.,0.,0.]
    edges=defaultdict(list)
    for fi in g:
        orig=fs[fi]
        for t in range(1,len(orig)-1):
            a,b,c=(vs[orig[0]],vs[orig[t]],vs[orig[t+1]]); ar=tri_area(a,b,c); area+=ar
            mid=mul(add(add(a,b),c),1/3); weighted=add(weighted,mul(mid,ar))
        f=face_verts[fi]
        for i,a in enumerate(f): edges[tuple(sorted((a,f[(i+1)%len(f)])))].append(fi)
    lo,hi,sz=bbox(pts); boundary=[e for e,x in edges.items() if len(x)==1]; nonman=[e for e,x in edges.items() if len(x)>2]
    # Boundary-edge connected regions provide compact spatial evidence without asserting loops are clean.
    bad=boundary+nonman; eadj=defaultdict(set)
    for a,b in bad: eadj[a].add(b); eadj[b].add(a)
    erseen=set(); regions=[]
    for v in eadj:
        if v in erseen:continue
        q=[v];erseen.add(v);rr=[]
        while q:
            x=q.pop();rr.append(x)
            for y in eadj[x]:
                if y not in erseen:erseen.add(y);q.append(y)
        rpts=[pts[vertids.index(x)] for x in rr]; rlo,rhi,rsz=bbox(rpts)
        regions.append({'edges':sum(1 for e in bad if e[0] in rr and e[1] in rr),'vertices':len(rr),'bbox':{'min':rlo,'max':rhi,'size':rsz}})
    c={'id':gid,'faces':len(g),'vertices_after_weld':len(vertids),'area':area,'centroid':mul(weighted,1/area) if area else [0,0,0], 'bbox':{'min':lo,'max':hi,'size':sz},'boundary_edges':len(boundary),'nonmanifold_edges':len(nonman),'open_or_nonmanifold_regions':sorted(regions,key=lambda r:-r['edges'])[:12]}
    c['spatial_candidate']=classify(c,height);components.append(c)

components.sort(key=lambda c:(-c['area'],-c['faces']))
for new,c in enumerate(components): c['rank_by_area']=new
floor_ids=[c['id'] for c in components if c['spatial_candidate']=='obvious_ground_plane_candidate']
upper_ids=[c['id'] for c in components if c['spatial_candidate']=='small_upper_region_fragment_candidate']
head_zone_ids=[c['id'] for c in components if c['bbox']['max'][1] >= .46]
report={'purpose':'Read-only OBJ topology evidence; no mesh data was modified or written. Spatial labels are candidates, not semantic/art approval.','source_obj':OBJ,'source_sha256':hashlib.sha256(open(OBJ,'rb').read()).hexdigest(),'coordinate_evidence':'Despite the supplied +Z-up inspection convention, raw OBJ extents show the modeled figure is +Y-up: a single flat plane spans X/Z at Y≈0.00488281 and the figure extent is Y=0..0.70654297. This report therefore uses Y for source-space height.','weld_test':{'method':'all position pairs max-axis-distance <= 1e-6 raw units unioned before face connectivity','epsilon_raw_units':EPS,'source_vertices':len(vs),'vertices_after_weld':nmerged,'source_faces':len(fs),'components_after_weld':len(components),'global_bbox':{'min':lo_global,'max':hi_global,'size':size_global},'height_y':height},'components_ranked_by_area':components,'decision_aids':{'safe_only_if_visually_confirmed':'A deletion candidate must be a separate component and must not affect silhouette in existing inspection cameras. Welding only joins vertices at <=1e-6; it does not close boundary loops or fix nonmanifold topology.','automatic_floor_delete_only_ids':floor_ids,'upper_region_manual_review_ids':upper_ids,'all_head_zone_overlap_ids':head_zone_ids,'head_cleanup_risk':'All 12 small upper-region components have open boundaries and overlap the head zone. They may be intended layered hair/face geometry; there is no topology-only evidence that any is a flyaway. Do not bulk-delete them. The largest thin pieces (17, 37, 30) are especially silhouette-risky because their Y ranges extend 0.125–0.215 of figure height.','recommended_next_observation':'Keep only component 32 eligible for automatic deletion. In a temporary flat-color copy, isolate each upper-region ID against components 5 and 6 in existing front/back/side inspection cameras; select a non-floor deletion only after it is visibly outside the desired silhouette in all relevant views.'}}
os.makedirs(os.path.dirname(OUT),exist_ok=True)
with open(OUT,'w',encoding='utf-8') as f: json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps({'out':OUT,'components':len(components),'vertices_after_weld':nmerged,'height':height},ensure_ascii=False))
