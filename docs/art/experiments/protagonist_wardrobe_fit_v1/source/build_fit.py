"""Fit a verified repaired robe to body v2 and test one shared temporary rig.

The accepted source silhouette stays a separate immutable reference. Fitting
changes scale/rest pose only, followed by bounded clearance correction.
"""
from pathlib import Path
from collections import defaultdict
import bpy,json,math,hashlib,heapq
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
EXP=Path(__file__).resolve().parents[1]
BODY=EXP.parent/'protagonist_tripo_body_v2/model/body_v2_motion_probe.blend'
ROBE=EXP/'model/DIAGNOSTIC_static_robe.blend'
LIB=EXP.parent/'protagonist_tripo_body_v1/source/body_topology_check.py'
ns={'__file__':str(LIB),'__name__':'geometry_library'}
exec(compile(LIB.read_text(encoding='utf-8').split("\nbefore={'glb':")[0],str(LIB),'exec'),ns)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)
def triangles(ob,evaluated=False):
 if evaluated:
  e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh()
 else:e=ob;me=ob.data
 me.calc_loop_triangles();vs=[e.matrix_world@v.co for v in me.vertices];ts=[tuple(t.vertices) for t in me.loop_triangles]
 return e,me,vs,ts
def cross(a,b):
 ea,ma,va,ta=triangles(a,True);eb,mb,vb,tb=triangles(b,True)
 ba=BVHTree.FromPolygons(va,ta,all_triangles=True);bb=BVHTree.FromPolygons(vb,tb,all_triangles=True)
 pairs=ba.overlap(bb);hits=[]
 for ai,bi in pairs:
  row=ns['triangle_intersection']([va[i] for i in ta[ai]],[vb[i] for i in tb[bi]])
  if row['kind'] in ('proper_crossing','edge_crossing','coplanar_overlap'):hits.append({'body_triangle':ai,'robe_triangle':bi,'kind':row['kind'],'points':row.get('points',[])})
 ea.to_mesh_clear();eb.to_mesh_clear()
 return {'candidate_pairs':len(pairs),'true_crossing_pairs':len(hits),'samples':hits[:24]}
def bary(p,a,b,c):
 u=b-a;v=c-a;w=p-a;uu=u.dot(u);uv=u.dot(v);vv=v.dot(v);wu=w.dot(u);wv=w.dot(v);den=uu*vv-uv*uv
 if abs(den)<1e-20:return (1.,0.,0.)
 y=(vv*wu-uv*wv)/den;z=(uu*wv-uv*wu)/den;wts=[max(0.,1-y-z),max(0.,y),max(0.,z)];total=sum(wts);return [x/total for x in wts]
assert ROBE.exists(),'A verified repaired robe must exist first; do not fall back to the failed raw mesh.'
hashes={str(p):sha(p) for p in (BODY,ROBE)}
bpy.ops.wm.open_mainfile(filepath=str(BODY));scene=bpy.context.scene;scene.frame_set(1)
body=next(o for o in scene.objects if o.type=='MESH');rig=next(o for o in scene.objects if o.type=='ARMATURE');body.name='Body_V2'
for ob in list(scene.objects):
 if ob not in (body,rig):bpy.data.objects.remove(ob,do_unlink=True)
# Match the BODY's A-pose to the garment, rather than warping a wide piecewise
# sleeve field through the robe's waist. Bake only this assembly copy.
rig.animation_data_clear()
for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=(1,0,0,0)
for side,degrees in [('L',-15),('R',15)]:
 p=rig.pose.bones['upper_arm.'+side];axis=rig.data.bones[p.name].matrix_local.to_quaternion().inverted()@Vector((1,0,0));p.rotation_quaternion=Quaternion(axis,math.radians(degrees))
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
for m in list(body.modifiers):
 if m.type=='ARMATURE':bpy.ops.object.modifier_apply(modifier=m.name)
body.select_set(False);rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='POSE');bpy.ops.pose.armature_apply(selected=False);bpy.ops.object.mode_set(mode='OBJECT')
bm=body.modifiers.new('Shared_Humanoid_Skin','ARMATURE');bm.object=rig;bm.use_deform_preserve_volume=True
with bpy.data.libraries.load(str(ROBE),link=False) as (src,dst):dst.objects=[n for n in src.objects if bpy.data.objects.get(n) is None]
new=[]
for ob in dst.objects:
 if ob is not None and ob.type=='MESH':scene.collection.objects.link(ob);new.append(ob)
assert len(new)==1,'Clean source must contain one garment mesh.'
robe=new[0];robe.name='Robe_Fitted_Separate_Mesh'
bpy.ops.object.select_all(action='DESELECT');robe.select_set(True);bpy.context.view_layer.objects.active=robe;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
source_normals={}
for p in robe.data.polygons:
 for li in p.loop_indices:source_normals[robe.data.loops[li].vertex_index]=robe.data.corner_normals[li].vector.copy()
body.data.calc_loop_triangles();bv=[body.matrix_world@v.co for v in body.data.vertices];bt=[tuple(t.vertices) for t in body.data.loop_triangles];bvh=BVHTree.FromPolygons(bv,bt,all_triangles=True);body_groups={g.index:g.name for g in body.vertex_groups}
fitting_moves=[];rest_normals=[]
for v in robe.data.vertices:
 raw=v.co.copy();p=raw*.74+Vector((0,0,.11));sign=1 if raw.y>=0 else -1
 amount=0.
 center=Vector((0,sign*.081,.798));rot=Quaternion((1,0,0),math.radians(sign*15*amount));v.co=center+rot@(p-center)
 rest_normals.append(rot@source_normals[v.index])
 fitting_moves.append((v.co-p).length)
robe.data.normals_split_custom_set_from_vertices(rest_normals);robe.data.update()
# Nearest-body interpolation is used only above the skirt, where anatomy and
# sleeve/chest cloth have corresponding surfaces. The hem has auxiliary bones.
body.data.calc_loop_triangles();bv=[body.matrix_world@v.co for v in body.data.vertices];bt=[tuple(t.vertices) for t in body.data.loop_triangles];bvh=BVHTree.FromPolygons(bv,bt,all_triangles=True)
clearance_moves=[];initial_close_vertices=[]
for v in robe.data.vertices:
 hit,normal,index,distance=bvh.find_nearest(v.co)
 signed=(v.co-hit).dot(normal)
 if distance<.04 and signed<.004:
  initial_close_vertices.append({'vertex':v.index,'signed_gap':signed})
robe.data.update()
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for front,sx in [('front',1),('back',-1)]:
 for side,sy in [('L',1),('R',-1)]:
  b=rig.data.edit_bones.new(f'skirt_{front}.{side}');b.head=(sx*.02,sy*.05,.49);b.tail=(sx*.08,sy*.08,.12);b.parent=rig.data.edit_bones['pelvis']
bpy.ops.object.mode_set(mode='OBJECT')
for g in list(robe.vertex_groups):robe.vertex_groups.remove(g)
groups={b.name:robe.vertex_groups.new(name=b.name) for b in rig.data.bones}
body_groups={g.index:g.name for g in body.vertex_groups};weight_record=[];weight_fields=[]
# Semantic sleeve ownership follows mesh geodesics, not the nearest naked-skin
# surface (a wide inner cuff can be closer to the ribcage than to the arm).
adj=[[] for _ in robe.data.vertices]
for edge in robe.data.edges:
 a,b=edge.vertices;length=(robe.data.vertices[a].co-robe.data.vertices[b].co).length;adj[a].append((b,length));adj[b].append((a,length))
def geodesic(seeds):
 ds=[float('inf')]*len(adj);heap=[]
 for i in seeds:ds[i]=0.;heapq.heappush(heap,(0.,i))
 while heap:
  distance,i=heapq.heappop(heap)
  if distance!=ds[i]:continue
  for j,cost in adj[i]:
   value=distance+cost
   if value<ds[j]:ds[j]=value;heapq.heappush(heap,(value,j))
 return ds
arm_distance=geodesic([v.index for v in robe.data.vertices if abs(v.co.y)>.1702 and v.co.z>.48])
torso_distance=geodesic([v.index for v in robe.data.vertices if v.co.z<.48 or abs(v.co.y)<.055])
def segment_distance(p,a,b):
 d=b-a;t=max(0.,min(1.,(p-a).dot(d)/max(d.length_squared,1e-12)));return (p-(a+d*t)).length
def torso_weights(z):
 if z<.56:return {'pelvis':1.}
 if z<.67:
  t=smooth(.56,.67,z);return {'pelvis':1-t,'spine':t}
 t=smooth(.67,.78,z);n=.5*smooth(.81,.86,z);return {'spine':(1-t)*(1-n),'chest':t*(1-n),'neck':n}
for v in robe.data.vertices:
 p=v.co;weights=defaultdict(float)
 a=smooth(.20,.80,torso_distance[v.index]/max(arm_distance[v.index]+torso_distance[v.index],1e-12));side='L' if p.y>=0 else 'R'
 chain={}
 for name in (f'upper_arm.{side}',f'forearm.{side}',f'hand.{side}'):
  bone=rig.data.bones[name];chain[name]=1/max(.02,segment_distance(p,bone.head_local,bone.tail_local))**4
 total=sum(chain.values())
 for name,value in torso_weights(p.z).items():weights[name]+=(1-a)*value
 for name,value in chain.items():weights[name]+=a*value/total
 if p.z<.51:
  skirt=smooth(.51,.23,p.z);front=smooth(-.06,.06,p.x);left=smooth(-.10,.10,p.y)
  weights=defaultdict(float,{k:val*(1-skirt) for k,val in weights.items()})
  for name,wt in [('skirt_front.L',front*left),('skirt_front.R',front*(1-left)),('skirt_back.L',(1-front)*left),('skirt_back.R',(1-front)*(1-left))]:weights[name]+=skirt*wt
 weight_fields.append(dict(weights))
# Couple the inner and outer wall's skin weights with the same smooth 3D field.
# Independent nearest-body choices across a ~5mm wall can otherwise invert it.
kd=KDTree(len(robe.data.vertices))
for v in robe.data.vertices:kd.insert(v.co,v.index)
kd.balance();neighbors=[[(i,math.exp(-distance*distance/(2*.010*.010))) for co,i,distance in kd.find_range(v.co,.018)] for v in robe.data.vertices]
for _ in range(2):
 updated=[]
 for row in neighbors:
  blend=defaultdict(float);den=sum(w for i,w in row)
  for i,w in row:
   for name,value in weight_fields[i].items():blend[name]+=value*w/den
  updated.append(dict(blend))
 weight_fields=updated
# Pair opposite walls through short inward rays, so the fabric thickness shares
# a skin field instead of receiving unrelated nearest-body assignments.
robe.data.calc_loop_triangles();cloth_bvh=BVHTree.FromPolygons([v.co for v in robe.data.vertices],[tuple(t.vertices) for t in robe.data.loop_triangles],all_triangles=True);cloth_tris=[tuple(t.vertices) for t in robe.data.loop_triangles];wall_pairs=[]
for v in robe.data.vertices:
 normal=v.normal.normalized();hit,n,index,distance=cloth_bvh.ray_cast(v.co-normal*.00002,-normal,.014)
 if hit is not None and n.dot(normal)<-.35:
  tri=cloth_tris[index];factors=bary(hit,*[robe.data.vertices[i].co for i in tri]);wall_pairs.append((v.index,list(zip(tri,factors))))
for _ in range(24):
 updated=[dict(row) for row in weight_fields]
 for i,row in wall_pairs:
  blend=defaultdict(float,{name:value*.5 for name,value in weight_fields[i].items()})
  for j,factor in row:
   for name,value in weight_fields[j].items():blend[name]+=value*factor*.5
  updated[i]=dict(blend)
 weight_fields=updated
for v,weights in zip(robe.data.vertices,weight_fields):
 kept=sorted(weights.items(),key=lambda x:x[1],reverse=True)[:4];total=sum(w for _,w in kept);assert total>0
 for name,w in kept:groups[name].add([v.index],w/total,'REPLACE')
 weight_record.append({'vertex':v.index,'sum':sum(w/total for _,w in kept),'influences':len(kept)})
mod=robe.modifiers.new('Shared_Humanoid_Skin','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=True
robe.parent=rig
# Standard per-outfit coverage mask; full body source remains editable. This
# does not hide sleeves or skirt defects, and visible skin is checked separately.
visible=body.vertex_groups.new(name='OUTFIT_Visible_Skin')
for v in body.data.vertices:
 hand=max([g.weight for g in v.groups if body_groups.get(g.group,'').startswith('hand.')],default=0.)
 if v.co.z>.80 or v.co.z<.15 or hand>.35:visible.add([v.index],1.,'REPLACE')
mask=body.modifiers.new('Outfit_Coverage_Full_Body_Retained','MASK');mask.vertex_group=visible.name
for ob,color in [(body,(.35,.39,.39,1)),(robe,(.76,.77,.72,1))]:
 mat=bpy.data.materials.new(ob.name+'_Technical_Gray');mat.diffuse_color=color;ob.data.materials.clear();ob.data.materials.append(mat)
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('Fit review background');scene.world.color=(.045,.055,.06);scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=False
cd=bpy.data.cameras.new('Review_Camera');cam=bpy.data.objects.new('Review_Camera',cd);scene.collection.objects.link(cam);cd.type='ORTHO';cd.ortho_scale=2.35;scene.camera=cam
def rotate(name,axis,degrees):
 p=rig.pose.bones[name];local=rig.data.bones[name].matrix_local.to_quaternion().inverted()@Vector(axis);p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion(local,math.radians(degrees))
pose_extra={'step':[('skirt_front.L',(0,1,0),-8),('skirt_front.R',(0,1,0),-8),('skirt_back.L',(0,1,0),8),('skirt_back.R',(0,1,0),8)]}
records=[];out=EXP/'evidence';out.mkdir(exist_ok=True)
pose_body={'rest':[],'raise_arms':[('upper_arm.L',(1,0,0),90),('upper_arm.R',(1,0,0),-90)],'reach':[('upper_arm.L',(1,0,0),45),('upper_arm.R',(1,0,0),-45)],'bend_elbows':[('forearm.L',(0,1,0),-75),('forearm.R',(0,1,0),-75)],'step':[('thigh.L',(0,1,0),-30),('shin.L',(0,1,0),55),('thigh.R',(0,1,0),18),('shin.R',(0,1,0),10)]}
for name,frame in [('rest',1),('raise_arms',20),('bend_elbows',40),('step',60),('reach',80)]:
 scene.frame_set(frame)
 for b in rig.pose.bones:
  b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0)
 for n,axis,degrees in pose_body[name]:rotate(n,axis,degrees)
 for n,axis,degrees in pose_extra.get(name,[]):rotate(n,axis,degrees)
 for b in rig.pose.bones:
  b.keyframe_insert(data_path='rotation_quaternion',frame=frame)
 bpy.context.view_layer.update();e,me,verts,tris=triangles(robe,True);self_cross=ns['self_intersections'](me,e.matrix_world);finite=all(math.isfinite(x) for p in verts for x in p);e.to_mesh_clear()
 mask.show_viewport=False;bpy.context.view_layer.update();full_collisions=cross(body,robe)
 mask.show_viewport=True;bpy.context.view_layer.update();collisions=cross(body,robe)
 for view,direction in [('front',(1,0,0)),('side',(0,-1,0)),('back',(-1,0,0)),('quarter',(.8,-1,.25))]:
  target=Vector((0,0,.53));cam.location=target+Vector(direction).normalized()*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/f'fit_{name}_{view}.png');bpy.ops.render.render(write_still=True)
 records.append({'pose':name,'frame':frame,'finite_vertices':finite,'robe_self_crossings':self_cross['true_nonadjacent_intersection_count'],'robe_self_samples':self_cross['true_nonadjacent_intersections_sample'][:16],'body_robe_crossings':collisions,'covered_full_body_crossings':full_collisions,'skirt_bone_adjustments':pose_extra.get(name,[])})
scene.frame_start=1;scene.frame_end=80;scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(EXP/'model/REJECTED_shared_rig_fit_v1.blend'))
assert {str(p):sha(p) for p in (BODY,ROBE)}==hashes
report={'status':'FAILED_DEFORMATION_NOT_ADOPTED','adopted':False,'sources_unchanged_sha256':hashes,'body_scale':'Original body normalized height ~1; no final meter height set.','robe_uniform_scale':.74,'robe_z_offset':.11,'sleeve_rest_pose_adjustment':'Smooth sleeve-local spread up to +/-15deg about body shoulders. No global robe redesign.','maximum_rest_pose_spread_distance':max(fitting_moves),'clearance_corrections':{'count':len(clearance_moves),'maximum_distance':max([r['distance'] for r in clearance_moves],default=0),'vertex_samples':clearance_moves[:24]},'shared_rig_bones':len(rig.data.bones),'garment_weighting':'Nearest body-triangle barycentric weight interpolation above pelvis; auxiliary skirt quadrant bones for hem; top4 normalized.','garment_unweighted_vertices':sum(r['sum']<=0 for r in weight_record),'garment_max_weight_sum_error':max(abs(r['sum']-1) for r in weight_record),'poses':records,'limits':['Temporary fitting/pose diagnostic, not production locomotion.','No Godot import, final UV or pixel texture, hair fitting or final user art approval.','No live cloth solver or separate clothing skeleton.']}
(EXP/'source/fit_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('SHARED_RIG_FIT_REVIEW_RENDERED',[(r['pose'],r['robe_self_crossings'],r['body_robe_crossings']['true_crossing_pairs']) for r in records])
