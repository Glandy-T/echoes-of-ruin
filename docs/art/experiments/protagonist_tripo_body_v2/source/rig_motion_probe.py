"""Temporary body-only deformation probe; never modifies the clean body master.

One explicitly provisional humanoid skeleton and heat weighting. This is a
diagnostic before final topology/UV, not a shipping animation or a wardrobe rig.
"""
from pathlib import Path
import bpy,json,math,hashlib
from mathutils import Vector,Quaternion
EXP=Path(__file__).resolve().parents[1]
MASTER=EXP/'model/protagonist_body_v2.blend'
LIB=EXP.parent/'protagonist_tripo_body_v1/source/body_topology_check.py'
qa_namespace={'__file__':str(LIB),'__name__':'probe_geometry_library'}
exec(compile(LIB.read_text(encoding='utf-8').split("\nbefore={'glb':")[0],str(LIB),'exec'),qa_namespace)
before_hash=hashlib.sha256(MASTER.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(MASTER));scene=bpy.context.scene
meshes=[o for o in scene.objects if o.type=='MESH'];assert len(meshes)==1
body=meshes[0]
for ob in list(scene.objects):
 if ob!=body:bpy.data.objects.remove(ob,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
data=bpy.data.armatures.new('PROBE_Humanoid');rig=bpy.data.objects.new('PROBE_Humanoid_NOT_FINAL',data);scene.collection.objects.link(rig)
rig.show_in_front=True;bpy.context.view_layer.objects.active=rig;rig.select_set(True);body.select_set(False);bpy.ops.object.mode_set(mode='EDIT')
specs=[('pelvis',(0,0,.48),(0,0,.56),None),('spine',(0,0,.56),(0,0,.67),'pelvis'),('chest',(0,0,.67),(0,0,.80),'spine'),('neck',(0,0,.80),(0,0,.865),'chest'),('head',(0,0,.865),(0,0,.99),'neck')]
for side,s in [('L',1),('R',-1)]:
 specs +=[(f'clavicle.{side}',(0,0,.79),(0,s*.081,.798),'chest'),(f'upper_arm.{side}',(0,s*.081,.798),(0,s*.181,.685),f'clavicle.{side}'),(f'forearm.{side}',(0,s*.181,.685),(0,s*.275,.585),f'upper_arm.{side}'),(f'hand.{side}',(0,s*.275,.585),(.002,s*.318,.545),f'forearm.{side}'),(f'thigh.{side}',(0,s*.048,.493),(0,s*.043,.278),'pelvis'),(f'shin.{side}',(0,s*.043,.278),(0,s*.043,.055),f'thigh.{side}'),(f'foot.{side}',(0,s*.043,.055),(.055,s*.047,.011),f'shin.{side}')]
for name,head,tail,parent in specs:
 b=data.edit_bones.new(name);b.head=head;b.tail=tail
 if parent:b.parent=data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
mods=[m for m in body.modifiers if m.type=='ARMATURE'];assert len(mods)==1 and mods[0].object==rig
mods[0].use_deform_preserve_volume=True
names={g.index:g.name for g in body.vertex_groups};bone_names=set(data.bones.keys())
heat_rows=[]
for v in body.data.vertices:
 active=[(names[g.group],g.weight) for g in v.groups if names[g.group] in bone_names and g.weight>0]
 heat_rows.append((v.index,active))
assert all(sum(w for _,w in active)>0 for _,active in heat_rows),'Heat weighting left unweighted vertices.'
pruned_vertices=0
for index,active in heat_rows:
 kept=sorted(active,key=lambda x:x[1],reverse=True)[:4];pruned_vertices+=len(active)>4;total=sum(w for _,w in kept)
 for name,_ in active:body.vertex_groups[name].remove([index])
 for name,weight in kept:body.vertex_groups[name].add([index],weight/total,'REPLACE')
weights=[]
for v in body.data.vertices:
 active=[(names[g.group],g.weight) for g in v.groups if names[g.group] in bone_names and g.weight>1e-6]
 weights.append({'vertex':v.index,'sum':sum(w for _,w in active),'influences':len(active)})
assert all(r['sum']>0 for r in weights),'Heat weighting left unweighted vertices; stop rather than report a bound body.'
scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.62,.65,.65);scene.display.shading.background_type='WORLD';scene.world=bpy.data.worlds.new('Probe background');scene.world.color=(.045,.055,.06)
scene.display.shading.show_shadows=True;scene.display.shading.show_cavity=True;scene.display.shading.cavity_type='BOTH';scene.display.shading.show_specular_highlight=False
camdata=bpy.data.cameras.new('PROBE_Camera');cam=bpy.data.objects.new('PROBE_Camera',camdata);scene.collection.objects.link(cam);camdata.type='ORTHO';camdata.ortho_scale=2.35;scene.camera=cam
def rotate(name,axis,degrees):
 p=rig.pose.bones[name];local=data.bones[name].matrix_local.to_quaternion().inverted()@Vector(axis);p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion(local,math.radians(degrees))
poses=[('rest',1,[]),('raise_arms',20,[(f'upper_arm.{s}',(1,0,0),a) for s,a in [('L',75),('R',-75)]]),('bend_elbows',40,[(f'forearm.{s}',(0,1,0),-75) for s in ('L','R')]),('step',60,[('thigh.L',(0,1,0),-30),('shin.L',(0,1,0),55),('thigh.R',(0,1,0),18),('shin.R',(0,1,0),10)])]
records=[];out=EXP/'evidence';out.mkdir(exist_ok=True)
for name,frame,changes in poses:
 scene.frame_set(frame)
 for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=(1,0,0,0)
 for bone,axis,degrees in changes:rotate(bone,axis,degrees)
 for p in rig.pose.bones:p.keyframe_insert(data_path='rotation_quaternion',frame=frame)
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();evaluated=body.evaluated_get(deps);me=evaluated.to_mesh();coords=[evaluated.matrix_world@v.co for v in me.vertices]
 finite=all(math.isfinite(n) for p in coords for n in p);assert finite
 inter=qa_namespace['self_intersections'](me,evaluated.matrix_world)
 ratios=[]
 for edge in body.data.edges:
  a,b=edge.vertices;old=(body.data.vertices[a].co-body.data.vertices[b].co).length
  if old>1e-9:ratios.append((coords[a]-coords[b]).length/old)
 ratios.sort()
 bounds={'min':[min(p[k] for p in coords) for k in range(3)],'max':[max(p[k] for p in coords) for k in range(3)]};evaluated.to_mesh_clear()
 for view,direction in [('front',(1,0,0)),('side',(0,-1,0)),('quarter',(.8,-1,.25))]:
  target=Vector((0,0,.53));cam.location=target+Vector(direction).normalized()*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/f'probe_{name}_{view}.png');bpy.ops.render.render(write_still=True)
 records.append({'name':name,'frame':frame,'rotations':[{'bone':bone,'axis_world_rest':axis,'degrees':degrees} for bone,axis,degrees in changes],'finite_deformed_vertices':finite,'deformed_bounds':bounds,'nonadjacent_crossings':inter['true_nonadjacent_intersection_count'],'crossing_classifications':inter['classification_counts'],'crossing_samples':inter['true_nonadjacent_intersections_sample'][:12],'edge_length_ratio':{'maximum':ratios[-1],'p99':ratios[int(.99*(len(ratios)-1))]},'note':'Crossing counts and edge-length ratios are diagnostic, not final visual/weight acceptance.'})
scene.frame_start=1;scene.frame_end=60;scene.frame_set(1)
for ob in list(bpy.context.selected_objects):ob.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(EXP/'model/body_v2_motion_probe.blend'))
assert hashlib.sha256(MASTER.read_bytes()).hexdigest()==before_hash
report={'status':'TEMPORARY_BODY_ONLY_PROBE_RENDERED','master_unchanged_sha256':before_hash,'bone_specs':[{'name':n,'head':h,'tail':t,'parent':p} for n,h,t,p in specs],'weighting':'Blender automatic heat, preserve volume; top4 influences retained and normalized. Provisional, not hand-corrected production weights. No finger bones.','initial_heat_max_weight_sum_error':max(abs(sum(w for _,w in a)-1) for _,a in heat_rows),'vertices_pruned_to_four_influences':pruned_vertices,'vertices':len(weights),'unweighted_vertices':sum(r['sum']<=0 for r in weights),'maximum_weight_sum_error':max(abs(r['sum']-1) for r in weights),'maximum_influences':max(r['influences'] for r in weights),'poses':records,'not_validated':['No garment fit or garment skinning. Gown v2 has known structural crossings.','No Godot import or animation playback.','These are rendered deformation keyframes, not a production walk-cycle or animation export.','No final joint/topology/skin-weight/art approval.','Model stays in original normalized units; final meter height not locked here.']}
(EXP/'source/motion_probe_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('BODY_MOTION_PROBE_RENDERED')
