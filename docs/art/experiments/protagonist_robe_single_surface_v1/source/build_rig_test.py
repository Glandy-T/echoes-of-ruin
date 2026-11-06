"""Rig a clean quad garment by its construction loops, not AI shell proximity."""
from pathlib import Path
from collections import defaultdict
import bpy,bmesh,json,math,hashlib
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
EXP=Path(__file__).resolve().parents[1]
BODY=EXP.parent/'protagonist_tripo_body_v2/model/body_v2_motion_probe.blend'
GARMENT=EXP/'model/robe_single_surface.blend'
LIB=EXP.parent/'protagonist_tripo_body_v1/source/body_topology_check.py'
qa={'__file__':str(LIB),'__name__':'geometry_library'}
exec(compile(LIB.read_text(encoding='utf-8').split("\nbefore={'glb':")[0],str(LIB),'exec'),qa)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)
def rotate(rig,name,axis,degree):
 p=rig.pose.bones[name];p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion(rig.data.bones[name].matrix_local.to_quaternion().inverted()@Vector(axis),math.radians(degree))
def evalmesh(ob):
 e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();me.calc_loop_triangles();vs=[e.matrix_world@v.co for v in me.vertices];ts=[tuple(t.vertices) for t in me.loop_triangles];return e,me,vs,ts
def collisions(a,b):
 ea,ma,va,ta=evalmesh(a);eb,mb,vb,tb=evalmesh(b);ba=BVHTree.FromPolygons(va,ta,all_triangles=True);bb=BVHTree.FromPolygons(vb,tb,all_triangles=True);hits=[]
 for ai,bi in ba.overlap(bb):
  row=qa['triangle_intersection']([va[i] for i in ta[ai]],[vb[i] for i in tb[bi]])
  if row['kind'] in ('proper_crossing','edge_crossing','coplanar_overlap'):hits.append({'body_triangle':ai,'garment_triangle':bi,'kind':row['kind'],'points':row.get('points',[])})
 ea.to_mesh_clear();eb.to_mesh_clear();return {'count':len(hits),'samples':hits[:20]}
hashes={str(p):sha(p) for p in (BODY,GARMENT)}
bpy.ops.wm.open_mainfile(filepath=str(BODY));scene=bpy.context.scene;scene.frame_set(1)
body=next(o for o in scene.objects if o.type=='MESH');rig=next(o for o in scene.objects if o.type=='ARMATURE');body.name='Body_Full_Source_Retained';rig.name='Shared_Humanoid_Prototype'
for ob in list(scene.objects):
 if ob not in (body,rig):bpy.data.objects.remove(ob,do_unlink=True)
rig.animation_data_clear()
for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=(1,0,0,0)
rotate(rig,'upper_arm.L',(1,0,0),-15);rotate(rig,'upper_arm.R',(1,0,0),15);bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
for mod in list(body.modifiers):
 if mod.type=='ARMATURE':bpy.ops.object.modifier_apply(modifier=mod.name)
body.select_set(False);rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='POSE');bpy.ops.pose.armature_apply(selected=False);bpy.ops.object.mode_set(mode='EDIT')
for front,sx in [('front',1),('back',-1)]:
 for side,sy in [('L',1),('R',-1)]:
  b=rig.data.edit_bones.new(f'skirt_{front}.{side}');b.head=(sx*.02,sy*.05,.49);b.tail=(sx*.08,sy*.08,.12);b.parent=rig.data.edit_bones['pelvis']
bpy.ops.object.mode_set(mode='OBJECT');bm=body.modifiers.new('Shared_Linear_Skin','ARMATURE');bm.object=rig;bm.use_deform_preserve_volume=False
with bpy.data.libraries.load(str(GARMENT),link=False) as (src,dst):dst.objects=src.objects
meshes=[]
for ob in dst.objects:
 if ob is not None and ob.type=='MESH':scene.collection.objects.link(ob);meshes.append(ob)
assert len(meshes)==1
robe=meshes[0];robe.name='Robe_Single_Outer_Surface'
# Orient the connected open garment consistently before assigning normals.
b=bmesh.new();b.from_mesh(robe.data);bmesh.ops.recalc_face_normals(b,faces=list(b.faces))
score=sum(f.normal.dot(Vector((f.calc_center_median().x,f.calc_center_median().y,0))) for f in b.faces if f.calc_center_median().z<.60)
if score<0:bmesh.ops.reverse_faces(b,faces=list(b.faces))
b.to_mesh(robe.data);b.free();robe.data.update()
for p in robe.data.polygons:p.use_smooth=True
parts=[x.value for x in robe.data.attributes['garment_part'].data];us=[x.value for x in robe.data.attributes['ring_u'].data]
for part in (1,2):assert all((v.co.y>0)==(part==1) for v in robe.data.vertices if parts[v.index]==part),'Sleeve attribute side mismatch'
groups={bone.name:robe.vertex_groups.new(name=bone.name) for bone in rig.data.bones}
def torso_weights(p):
 if p.z<=.56:w={'pelvis':1.}
 elif p.z<.67:
  t=smooth(.56,.67,p.z);w={'pelvis':1-t,'spine':t}
 else:
  t=smooth(.67,.78,p.z);w={'spine':1-t,'chest':t}
 side='L' if p.y>=0 else 'R';clav=.55*smooth(.055,.095,abs(p.y))*smooth(.69,.80,p.z)
 return {**{n:v*(1-clav) for n,v in w.items()},f'clavicle.{side}':clav}
weight_rows=[]
for v in robe.data.vertices:
 p=v.co;part=parts[v.index];u=us[v.index];w=defaultdict(float)
 if part==0:
  w.update(torso_weights(p))
  if p.z<.52:
   skirt=1-smooth(.20,.52,p.z);theta=math.atan2(p.y,p.x);front=.5+.5*math.cos(theta);left=.5+.5*math.sin(theta)
   w=defaultdict(float,{n:value*(1-skirt) for n,value in w.items()})
   for n,value in [('skirt_front.L',front*left),('skirt_front.R',front*(1-left)),('skirt_back.L',(1-front)*left),('skirt_back.R',(1-front)*(1-left))]:w[n]+=skirt*value
 else:
  side='L' if part==1 else 'R';root=smooth(0.,.24,u);elbow=smooth(.32,.68,u)
  for n,value in torso_weights(p).items():w[n]+=(1-root)*value
  w[f'upper_arm.{side}']+=root*(1-elbow);w[f'forearm.{side}']+=root*elbow
 kept=sorted(((n,value) for n,value in w.items() if value>1e-9),key=lambda x:x[1],reverse=True)[:4];total=sum(value for n,value in kept);assert total>0
 for n,value in kept:groups[n].add([v.index],value/total,'REPLACE')
 weight_rows.append({'vertex':v.index,'part':part,'u':u,'weights':{n:value/total for n,value in kept}})
skin=robe.modifiers.new('Shared_Linear_Skin','ARMATURE');skin.object=rig;skin.use_deform_preserve_volume=False;robe.parent=rig
# Explicit per-outfit coverage is non-destructive; it never masks the garment.
body_names={g.index:g.name for g in body.vertex_groups};visible=body.vertex_groups.new(name='Outfit_Visible_Skin')
for v in body.data.vertices:
 hand=max([g.weight for g in v.groups if body_names.get(g.group,'').startswith('hand.')],default=0.)
 if v.co.z>.80 or v.co.z<.15 or hand>.35:visible.add([v.index],1.,'REPLACE')
mask=body.modifiers.new('Outfit_Coverage_Full_Body_Retained','MASK');mask.vertex_group=visible.name
for ob,color in [(body,(.36,.40,.40,1)),(robe,(.78,.79,.74,1))]:
 mat=bpy.data.materials.new(ob.name+'_Preview_Only');mat.diffuse_color=color;mat.use_backface_culling=False;ob.data.materials.clear();ob.data.materials.append(mat)
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.display.shading.light='STUDIO';scene.display.shading.color_type='MATERIAL';scene.display.shading.background_type='WORLD';scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=False;scene.world=bpy.data.worlds.new('Study Background');scene.world.color=(.045,.055,.06)
cd=bpy.data.cameras.new('Study_Camera');cam=bpy.data.objects.new(cd.name,cd);scene.collection.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.ortho_scale=2.35
poses=[('rest',1,[]),('reach',20,[('upper_arm.L',(1,0,0),45),('upper_arm.R',(1,0,0),-45)]),('bend_elbows',40,[('forearm.L',(0,1,0),-75),('forearm.R',(0,1,0),-75)]),('step',60,[('thigh.L',(0,1,0),-30),('shin.L',(0,1,0),55),('thigh.R',(0,1,0),18),('shin.R',(0,1,0),10),('skirt_front.L',(0,1,0),-10),('skirt_front.R',(0,1,0),-10),('skirt_back.L',(0,1,0),14),('skirt_back.R',(0,1,0),14)]),('stress_raise',80,[('clavicle.L',(1,0,0),15),('clavicle.R',(1,0,0),-15),('upper_arm.L',(1,0,0),75),('upper_arm.R',(1,0,0),-75)])]
out=EXP/'evidence';out.mkdir(exist_ok=True);records=[]
for name,frame,changes in poses:
 scene.frame_set(frame)
 for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=(1,0,0,0)
 for n,axis,degrees in changes:rotate(rig,n,axis,degrees)
 for p in rig.pose.bones:p.keyframe_insert(data_path='rotation_quaternion',frame=frame)
 bpy.context.view_layer.update();e,me,vs,ts=evalmesh(robe);crosses=qa['self_intersections'](me,e.matrix_world);finite=all(math.isfinite(x) for p in vs for x in p);e.to_mesh_clear()
 mask.show_viewport=False;bpy.context.view_layer.update();covered=collisions(body,robe);mask.show_viewport=True;bpy.context.view_layer.update();exposed=collisions(body,robe)
 for view,direction in [('front',(1,0,0)),('side',(0,-1,0)),('back',(-1,0,0)),('quarter',(.8,-1,.25))]:
  target=Vector((0,0,.53));cam.location=target+Vector(direction).normalized()*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/f'{name}_{view}.png');bpy.ops.render.render(write_still=True)
 records.append({'pose':name,'frame':frame,'rotations':changes,'finite_vertices':finite,'garment_self_crossings':crosses['true_nonadjacent_intersection_count'],'self_crossing_samples':crosses['true_nonadjacent_intersections_sample'][:16],'visible_skin_crossings':exposed,'covered_full_body_crossings':covered})
scene.frame_start=1;scene.frame_end=80;scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(EXP/'model/protagonist_fitted.blend'))
assert {str(p):sha(p) for p in (BODY,GARMENT)}==hashes
passed=all(r['finite_vertices'] and r['garment_self_crossings']==0 and r['visible_skin_crossings']['count']==0 for r in records)
report={'status':'PASS_POSE_DIAGNOSTIC' if passed else 'FAIL_POSE_DIAGNOSTIC','sources_unchanged_sha256':hashes,'body_rest_pose_change':'Assembly copy upper arms lowered15deg; immutable bodyv2 master unchanged.','skin_method':'Loop-semantic weights, <=4 normalized; LINEAR skin matching glTF, no dual-quaternion or corrective-smooth dependencies.','shared_armature_bones':len(rig.data.bones),'garment_vertices':len(robe.data.vertices),'garment_faces':len(robe.data.polygons),'weight_rows':weight_rows,'poses':records,'body_coverage':'Head/neck, hands, lowercalves/feet visible; covered body retained with non-destructive MASK. Both full and visible collision counts reported.','scope':'Single-layer garment study. No thickness, UV, pixel texture, hair, finished locomotion, Godot runtime or final user art approval.'}
(EXP/'source/rig_test_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(report['status'],[(r['pose'],r['garment_self_crossings'],r['visible_skin_crossings']['count']) for r in records])
