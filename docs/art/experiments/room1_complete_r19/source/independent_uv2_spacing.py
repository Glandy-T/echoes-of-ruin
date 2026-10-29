"""Read-only UV2 island-spacing measurement for Room 1 r19.

Run under Blender on the saved r19 blend.  Islands are connected components of
triangles sharing an identical UV2 edge; their outer boundary segments are then
measured against all other islands.  This measures chart geometry, not whether
the baked EXR has good-looking dilation.
"""
import json, math, re
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent
OUT=HERE/'independent_uv2_spacing.json'
EPS=1.0e-9

def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def dot(a,b): return a[0]*b[0]+a[1]*b[1]
def sub(a,b): return (a[0]-b[0],a[1]-b[1])
def dist2(a,b):
    d=sub(a,b); return dot(d,d)
def point_segment2(p,a,b):
    d=sub(b,a); n=dot(d,d)
    if n<=EPS: return dist2(p,a)
    t=max(0.0,min(1.0,dot(sub(p,a),d)/n)); q=(a[0]+t*d[0],a[1]+t*d[1]); return dist2(p,q)
def on_segment(a,b,p): return min(a[0],b[0])-EPS<=p[0]<=max(a[0],b[0])+EPS and min(a[1],b[1])-EPS<=p[1]<=max(a[1],b[1])+EPS
def segments_intersect(a,b,c,d):
    x1,x2,x3,x4=cross(a,b,c),cross(a,b,d),cross(c,d,a),cross(c,d,b)
    if ((x1>EPS and x2<-EPS) or (x1<-EPS and x2>EPS)) and ((x3>EPS and x4<-EPS) or (x3<-EPS and x4>EPS)): return True
    return (abs(x1)<=EPS and on_segment(a,b,c)) or (abs(x2)<=EPS and on_segment(a,b,d)) or (abs(x3)<=EPS and on_segment(c,d,a)) or (abs(x4)<=EPS and on_segment(c,d,b))
def segment_distance(a,b,c,d):
    if segments_intersect(a,b,c,d): return 0.0
    return math.sqrt(min(point_segment2(a,c,d),point_segment2(b,c,d),point_segment2(c,a,b),point_segment2(d,a,b)))
def bbox(seg):
    a,b=seg; return (min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1]))
def bbox_distance(a,b):
    dx=max(a[0]-b[2],b[0]-a[2],0.0); dy=max(a[1]-b[3],b[1]-a[3],0.0); return math.hypot(dx,dy)
def key(p): return (round(float(p[0]),7),round(float(p[1]),7))

class DSU:
    def __init__(self,n): self.p=list(range(n))
    def find(self,x):
        while self.p[x]!=x: self.p[x]=self.p[self.p[x]];x=self.p[x]
        return x
    def union(self,a,b):
        a=self.find(a);b=self.find(b)
        if a!=b:self.p[b]=a

def measure(obj,resolution,dilation_px):
    m=obj.data; layer=m.uv_layers.get('LightmapUV')
    if not layer: raise RuntimeError(obj.name+' missing LightmapUV')
    tris=[]
    for poly in m.polygons:
        ls=list(poly.loop_indices)
        for i in range(1,len(ls)-1):
            pts=[]
            for li in (ls[0],ls[i],ls[i+1]):
                uv=layer.data[li].uv; pts.append((float(uv.x),float(uv.y)))
            if abs(cross(*pts))>EPS: tris.append(pts)
    dsu=DSU(len(tris)); edges={}
    for ti,t in enumerate(tris):
        for i in range(3):
            a,b=key(t[i]),key(t[(i+1)%3]); ek=tuple(sorted((a,b))); edges.setdefault(ek,[]).append(ti)
    for owners in edges.values():
        for x in owners[1:]: dsu.union(owners[0],x)
    island_by_root={}; island_of=[]
    for i in range(len(tris)):
        root=dsu.find(i); island_of.append(root); island_by_root.setdefault(root,[]).append(i)
    roots=sorted(island_by_root); root_index={r:i for i,r in enumerate(roots)}
    boundaries=[[] for _ in roots]
    for ek,owners in edges.items():
        owner_islands={root_index[dsu.find(x)] for x in owners}
        # A single UV edge is outer boundary only when its owners belong to one island.
        if len(owners)==1:
            boundaries[next(iter(owner_islands))].append((ek[0],ek[1]))
    bboxes=[]
    for segs in boundaries:
        xs=[p[0] for s in segs for p in s]; ys=[p[1] for s in segs for p in s]
        bboxes.append((min(xs),min(ys),max(xs),max(ys)) if xs else (0,0,0,0))
    best=float('inf'); pair=None; best_non_touch=float('inf'); pair_non_touch=None
    for i in range(len(boundaries)):
        for j in range(i+1,len(boundaries)):
            if bbox_distance(bboxes[i],bboxes[j])>=best: continue
            for si in boundaries[i]:
                bi=bbox(si)
                for sj in boundaries[j]:
                    if bbox_distance(bi,bbox(sj))>=best: continue
                    d=segment_distance(*si,*sj)
                    if d<best: best=d;pair={'island_a':i,'island_b':j,'edge_a':si,'edge_b':sj}
                    endpoint_touch=any(dist2(a,b)<=EPS for a in si for b in sj)
                    if not endpoint_touch and d<best_non_touch:
                        best_non_touch=d;pair_non_touch={'island_a':i,'island_b':j,'edge_a':si,'edge_b':sj}
    edge_min=min([min(x,1-x,y,1-y) for tri in tris for x,y in tri],default=None)
    gap_px=None if best==float('inf') else best*resolution
    gap_non_touch_px=None if best_non_touch==float('inf') else best_non_touch*resolution
    edge_px=None if edge_min is None else edge_min*resolution
    clearance_gap_px=gap_non_touch_px if gap_non_touch_px is not None else gap_px
    return {
        'resolution':resolution,'triangle_count':len(tris),'island_count':len(roots),
        'boundary_segment_count':sum(len(x) for x in boundaries),
        'min_inter_island_uv_distance':None if best==float('inf') else best,
        'min_inter_island_distance_px':gap_px,'closest_island_boundary_pair':pair,
        'min_inter_island_non_endpoint_touch_distance_px':gap_non_touch_px,'closest_non_endpoint_touch_boundary_pair':pair_non_touch,
        'min_island_boundary_to_atlas_edge_px':edge_px,
        'dilation_px_configured':dilation_px,
        'two_chart_requirement_dilation_plus_1px_bilinear_each_side_px':2*dilation_px+2,
        'clearance_budget_basis':'minimum non-endpoint-touch island separation; endpoint-only contacts are reported separately and not treated as a gutter width',
        'geometric_inter_island_clearance_after_two_dilations_px':None if clearance_gap_px is None else clearance_gap_px-2*dilation_px,
        'conservative_clearance_after_dilation_plus_1px_bilinear_each_side_px':None if clearance_gap_px is None else clearance_gap_px-(2*dilation_px+2),
        'atlas_edge_requirement_dilation_plus_1px_bilinear_px':dilation_px+1,
        'edge_clearance_after_dilation_plus_1px_bilinear_px':None if edge_px is None else edge_px-(dilation_px+1),
    }

pods=sorted([o for o in bpy.data.objects if re.fullmatch(r'R19_P\d\d_closed_receiver',o.name or '')],key=lambda o:o.name)
shell=bpy.data.objects.get('R19_shell_receiver')
out={'method':'UV2 connected components via exact shared UV edges; minimum Euclidean distance between boundary segments of distinct components. Pixel distance = UV distance * map resolution.',
     'interpretation':{'bilinear_footprint_assumption_px':1,'pod_dilation_px':4,'shell_dilation_px':6,'pod_two_chart_conservative_requirement_px':10,'shell_two_chart_conservative_requirement_px':14,'pod_atlas_edge_requirement_px':5,'shell_atlas_edge_requirement_px':7,
     'warning':'This is UV geometry only. It does not inspect baked EXR gutter texels or denoiser bleed. Runtime sampler/import checks are a separate audit. Pod atlas outer-edge distance is 0px and is explicitly not claimed as padding.'},
     'pods':{},'shell':None,'failures':[]}
for pod in pods:
    try: out['pods'][pod.name]=measure(pod,1024,4)
    except Exception as e: out['failures'].append({'object':pod.name,'error':str(e)})
if shell:
    try: out['shell']=measure(shell,2048,6)
    except Exception as e: out['failures'].append({'object':shell.name,'error':str(e)})
else: out['failures'].append({'object':'R19_shell_receiver','error':'missing'})
OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('INDEPENDENT_UV2_SPACING',json.dumps({'pods':len(out['pods']),'failures':len(out['failures']),'output':str(OUT)},ensure_ascii=False))
