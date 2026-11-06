"""Derive a single garment skin from a clean fitted closed fabric volume.

Opposite-wall rays compare signed body distance. The zero field cuts each rim
at its middle. Unlike the failed raw-shell face deletion, triangles are clipped
continuously and shared cut vertices are reused.
"""
from pathlib import Path
from collections import Counter,defaultdict
import bpy,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
EXP=Path(__file__).resolve().parents[1]
def derive(body,robe):
 bm=body.data;bm.calc_loop_triangles();bvs=[body.matrix_world@v.co for v in bm.vertices];bts=[tuple(t.vertices) for t in bm.loop_triangles];bb=BVHTree.FromPolygons(bvs,bts,all_triangles=True)
 me=robe.data;me.calc_loop_triangles();vs=[v.co.copy() for v in me.vertices];ts=[tuple(t.vertices) for t in me.loop_triangles];cb=BVHTree.FromPolygons(vs,ts,all_triangles=True)
 geometric=[Vector() for _ in vs]
 for tri in ts:
  a,b,c=[vs[i] for i in tri];n=(b-a).cross(c-a)
  for i in tri:geometric[i]+=n
 geometric=[v.normalized() for v in geometric]
 def sdf(p):
  hit,n,i,d=bb.find_nearest(p);return (p-hit).dot(n),n
 scores=[];paired=0
 for p,n in zip(vs,geometric):
  value,bn=sdf(p);score=n.dot(bn);hit,hn,ti,d=cb.ray_cast(p-n*.00002,-n,.014)
  if hit is not None and hn.dot(n)<-.35:
   other,_=sdf(hit);gap=value-other
   if abs(gap)>max(.0001,(p-hit).length*.15):score=1. if gap>0 else -1.;paired+=1
  scores.append(score)
 source_normals=[Vector() for _ in vs]
 for face in me.polygons:
  for li in face.loop_indices:source_normals[me.loops[li].vertex_index]=me.corner_normals[li].vector.copy()
 source_weights=[{g.group:g.weight for g in v.groups} for v in me.vertices]
 points=[];normal_values=[];weight_values=[];lookup={};faces=[]
 def point(key,a,b=None,t=0.):
  if key in lookup:return lookup[key]
  i=len(points);lookup[key]=i
  if b is None:points.append(vs[a]);normal_values.append(source_normals[a]);weight_values.append(source_weights[a])
  else:
   points.append(vs[a].lerp(vs[b],t));normal_values.append(source_normals[a].lerp(source_normals[b],t).normalized());w=defaultdict(float)
   for g,v in source_weights[a].items():w[g]+=v*(1-t)
   for g,v in source_weights[b].items():w[g]+=v*t
   weight_values.append(dict(w))
  return i
 for tri in ts:
  poly=[]
  for a,b in zip(tri,tri[1:]+tri[:1]):
   sa,sb=scores[a],scores[b]
   if sa>=0:poly.append(point(('v',a),a))
   if (sa>=0)!=(sb>=0):poly.append(point(('e',min(a,b),max(a,b)),a,b,sa/(sa-sb)))
  if len(poly)>=3 and len(set(poly))==len(poly):faces.append(poly)
 out=bpy.data.meshes.new('Derived_Outer_Skin');out.from_pydata(points,[],faces);out.update()
 for p in out.polygons:p.use_smooth=True
 out.normals_split_custom_set_from_vertices(normal_values)
 uses=Counter()
 for p in out.polygons:
  for a,b in p.edge_keys:uses[tuple(sorted((a,b)))]+=1
 adj=defaultdict(set)
 for (a,b),count in uses.items():
  if count==1:adj[a].add(b);adj[b].add(a)
 unseen=set(adj);loops=[]
 while unseen:
  start=next(iter(unseen));stack=[start];component=set()
  while stack:
   i=stack.pop()
   if i in component:continue
   component.add(i);unseen.discard(i);stack.extend(adj[i]-component)
  loops.append({'vertices':len(component),'simple':all(len(adj[i])==2 for i in component),'bounds':{'min':[min(points[i][k] for i in component) for k in range(3)],'max':[max(points[i][k] for i in component) for k in range(3)]}})
 report={'paired_vertices':paired,'source_vertices':len(vs),'outer_vertices':len(points),'outer_faces':len(faces),'boundary_edges':sum(v==1 for v in uses.values()),'nonmanifold_edges':sum(v>2 for v in uses.values()),'boundary_loops':loops,'four_simple_loops':len(loops)==4 and all(row['simple'] for row in loops)}
 return out,weight_values,report
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=str(EXP/'model/REJECTED_shared_rig_fit_v1.blend'));scene=bpy.context.scene;scene.frame_set(1)
 body=bpy.data.objects['Body_V2'];robe=bpy.data.objects['Robe_Fitted_Separate_Mesh'];out,weights,report=derive(body,robe)
 for m in list(robe.modifiers):robe.modifiers.remove(m)
 robe.data=out
 (EXP/'source/derived_outer_trial.json').write_text(json.dumps(report,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(EXP/'scratch/derived_outer_trial.blend'));print('DERIVED_OUTER',json.dumps(report))
