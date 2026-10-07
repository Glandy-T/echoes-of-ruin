"""Full-floor native FreeCAD blockout from accepted inset plan; metre input, mm CAD.
Only schematic architecture and verified pod envelopes. No authored materials/lights.
"""
from pathlib import Path
from layout import subtract_rectangles
import json,re,hashlib,sys
import FreeCAD as A,Part
ROOT=Path(__file__).resolve().parent;ROOT.mkdir(exist_ok=True);(ROOT/'qa').mkdir(exist_ok=True);(ROOT/'views').mkdir(exist_ok=True);(ROOT/'sources').mkdir(exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8')
PLAN=ROOT.parent/'v3_frozen/floor_layout.json';SOURCE=ROOT.parents[1]/'cryo_room1/blockout_v2/room1_3d_blockout_v2.FCStd'
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest();assert source_hash=='4bb0db7b42de97693a02557bd29d38e498a224254843335fa20dd1e0593b3973'
d=json.loads(PLAN.read_text(encoding='utf-8'));v=d['parameters'];assert len(d['rooms'])==48 and v['MaxSouth']==v['FloorSouth'] and v['MaxNorth']==v['FloorNorth']
doc=A.newDocument('StandardFloorBlockout_v3_frozen');doc.Label='标准休眠层 / 0E 收尾冻结 / 整层3D空间验证'
p=doc.addObject('App::FeaturePython','Parameters');p.Label='冻结平面 + 暂定三维尺度'
for key,n in dict(RoomClearHeight=3.4,StoreyHeight=3.8,DoorHeight=2.4,FloorThickness=.1,RoofThickness=.15,HumanHeight=1.68,HumanDiameter=.45).items():p.addProperty('App::PropertyLength',key,'3D PROVISIONAL');setattr(p,key,n*1000)
for key,n in dict(MainWidth=186.4,MainDepth=77.8,RoomWidth=21.,RoomDepth=9.5,PersonnelCorridor=2.4,MachineSpine=6.,MachineCross=4.,TransferClear=11.2).items():p.addProperty('App::PropertyLength',key,'ACCEPTED PLAN');setattr(p,key,n*1000)
for key,s in [('SourceCommit','b53aa9b8e38c7c423703dd946c2ba88d44b9ab37'),('PlanFileSHA256',hashlib.sha256(PLAN.read_bytes()).hexdigest()),('Room1BlockoutSHA256',source_hash),('Scope','Single-floor spatial blockout; frozen XY from v3_inset JSON. Heights/slabs/thresholds provisional. No materials, lights, facade or 20-floor stack.')]:p.addProperty('App::PropertyString',key,'PROVENANCE');setattr(p,key,s)
groups={}
def group(name,label,parent=None):
 g=doc.addObject('App::DocumentObjectGroup',name);g.Label=label;groups[name]=g
 if parent:parent.addObject(g)
 return g
floor=group('Floor','01 实际整层楼板 / Z=0完成面');walls=group('Architecture','02 真实共享墙和门楣 / 洞口净高2.40 P');rooms=group('RoomEnvelopes','03 48个21×9.5房间外包参照 / 默认隐藏')
circulation=group('Circulation','04 人员廊 / 电梯节点 / 连续机器作业区');stairg=group('Stairs','05 四座U形楼梯 / 24级实尺体块');lifts=group('LiftCars','06 四人员轿厢与四货梯 / 净空地面参照')
pods=group('RoomPods','07 48室×20舱 / 四代表室完整复用、其余简化外包');templates=group('PodTemplates','08 共享舱模板 / 默认隐藏');refs=group('ScaleReferences','09 1.68m尺度柱 / 纯参照');roofs=group('Roofs','10 可隐藏顶板 / 暂定净高3.40 P');gates=group('EmergencyGates','11 应急核心隔断 / 默认开放隐藏')
objects=[];wall_objects=[];lintels=[];pod_links=[];stair_steps=[];plan_boxes=[]
def metadata(o,role):o.addProperty('App::PropertyString','Role','BLOCKOUT');o.Role=role
def box(name,r,z,height,parent,role,height_expr=None,z_expr=None):
 o=doc.addObject('Part::Box',name);o.Length=(r['x2']-r['x1'])*1000;o.Width=(r['y2']-r['y1'])*1000;o.Height=height*1000;o.Placement.Base=A.Vector(r['x1']*1000,r['y1']*1000,z*1000);metadata(o,role);parent.addObject(o);objects.append(o)
 if height_expr:o.setExpression('Height',height_expr)
 if z_expr:o.setExpression('Placement.Base.z',z_expr)
 return o
def rect(x,y,w,h):return dict(x1=x,y1=y,x2=x+w,y2=y+h)
for i,r in enumerate(d['floor_cells']):box('Slab_'+str(i+1),r,-.1,.1,floor,'floor',height_expr='Parameters.FloorThickness',z_expr='-Parameters.FloorThickness')
for r in d['walls']:
 o=box(r['id'],r,0,3.4,walls,'wall',height_expr='Parameters.RoomClearHeight');wall_objects.append(o)
 # Stair enclosure reaches the provisional storey height, with the same XY walls.
 for st in d['stairs']:
  a,b,c,e=max(r['x1'],st['x1']),max(r['y1'],st['y1']),min(r['x2'],st['x2']),min(r['y2'],st['y2'])
  if c>a+1e-7 and e>b+1e-7:box('StairWallTop_'+str(len(objects)),dict(x1=a,y1=b,x2=c,y2=e),3.4,.4,stairg,'stair_wall_upper',height_expr='Parameters.StoreyHeight-Parameters.RoomClearHeight',z_expr='Parameters.RoomClearHeight')
for door in d['doors']:
 x,y,w=door['x'],door['y'],door['width'];r=rect(x-w/2,y-.1,w,.2) if door['orientation']=='H' else rect(x-.1,y-w/2,.2,w)
 if door['kind']=='personnel_exclusion':
  o=box('CoreGate_'+door['id'],r,0,3.4,gates,'emergency_gate',height_expr='Parameters.RoomClearHeight');o.Label=door['tag']+' / 平时开放，应急关闭全宽19.60';o.Visibility=False;continue
 h=3.8 if door['kind']=='stair' else 3.4
 o=box('Lintel_'+door['id'],r,2.4,h-2.4,walls,'lintel',height_expr='Parameters.'+('StoreyHeight' if door['kind']=='stair' else 'RoomClearHeight')+'-Parameters.DoorHeight',z_expr='Parameters.DoorHeight');o.Label=door['tag']+' / 门楣，洞净宽'+str(round(w,2));lintels.append(o)
for r in d['rooms']:
 o=box(r['id'].replace('-','_')+'_Envelope',r,0,3.4,rooms,'room_envelope',height_expr='Parameters.RoomClearHeight');o.Label=r['id']+' | 外包21×9.5，20舱';o.Visibility=False;plan_boxes.append(o)
for i,r in enumerate(d['corridors']+d['elevator_nodes']+d['machine_work_areas']):
 for j,rr in enumerate(subtract_rectangles([r],d['passenger_shaft_voids'])):
  o=box('ZoneFloor_'+str(i+1)+'_'+str(j),rr,.001,.003,circulation,'personnel_floor' if r in d['corridors']+d['elevator_nodes'] else 'machine_floor');o.Label=r.get('id',r['tag'])+' | 工作地面参照 / 井道扣除'
for r in d['references']:
 if r['tag'] in ['passenger_car','freight_car']:
  o=box('CarFloor_'+str(len(objects)),r,.005,.003,lifts,'lift_car_floor');o.Label=r.get('id',r.get('zone',''))+' | 轿厢真实净空地面'
 if r['tag']=='lane_marking':
  for x in [r['x1'],r['x2']]:box('Lane_'+str(len(objects)),rect(x-.025,r['y1'],.05,r['y2']-r['y1']),.005,.002,circulation,'lane_marking')
for r in d['waiting_bays']:
 o=box('Wait_'+str(len(objects)),r,.005,.004,circulation,'waiting_bay');o.Label=r['id']+' | 1.70×3.10整车等待位'
 # Small front/rear posts mark the reserved footprint without filling robot volume.
for st in d['stairs']:
 sg=group(st['side']+'Stair',st['side']+' / 实尺U形24级',stairg);axis='Y' if st['side'] in ['North','South'] else 'X'
 flights=[r for r in d['references'] if r['tag']=='stair_flight' and r['side']==st['side']]
 landings=[r for r in d['references'] if r['tag']=='stair_landing' and r['side']==st['side']]
 # The lower floor already exists. A full-width far landing is at half-storey.
 far=max(landings,key=lambda r:r['y1']) if st['side']=='North' else min(landings,key=lambda r:r['y1']) if st['side']=='South' else max(landings,key=lambda r:r['x1']) if st['side']=='West' else min(landings,key=lambda r:r['x1'])
 box(st['side']+'_MidLanding',far,1.75,.15,sg,'stair_mid_landing',z_expr='Parameters.StoreyHeight/2-(150 mm)')
 near=next(r for r in landings if r is not far);f2=flights[1]
 upper=rect(f2['x1'],near['y1'],f2['x2']-f2['x1'],near['y2']-near['y1']) if axis=='Y' else rect(near['x1'],f2['y1'],near['x2']-near['x1'],f2['y2']-f2['y1'])
 box(st['side']+'_UpperLanding',upper,3.65,.15,sg,'stair_upper_landing',z_expr='Parameters.StoreyHeight-(150 mm)')
 for fi,f in enumerate(flights):
  # 11 treads plus landing riser = 12 risers per flight. Opposite flights reverse.
  forward=st['side'] in ['North','West'];forward=forward if fi==0 else not forward
  for i in range(11):
   idx=i if forward else 10-i
   rr=rect(f['x1'],f['y1']+idx*.3,f['x2']-f['x1'],.3) if axis=='Y' else rect(f['x1']+idx*.3,f['y1'],.3,f['y2']-f['y1'])
   z=.15833333333333333*(i+1)+(1.9 if fi else 0)
   o=box(st['side']+'_F'+str(fi+1)+'_T'+str(i+1),rr,z-.15,.15,sg,'stair_tread',z_expr=f'Parameters.StoreyHeight*({i+1+fi*12}/24)-(150 mm)');stair_steps.append(o)
# Reuse only the already verified closed pod geometry, not Room1 walls/furniture.
sd=A.openDocument(str(SOURCE));A.setActiveDocument(doc.Name);full=[];simple=[];pod_envelopes=[]
for i in range(1,21):
 shapes=[sd.getObject(f'P{i:02}_{s}').Shape.copy() for s in ['Base','Body','Lid','Window']];compound=Part.makeCompound(shapes);bb=compound.BoundBox
 for j,s in enumerate(shapes):
  o=doc.addObject('Part::Feature',f'ClosedPod_{i:02}_{j}');o.Shape=s;metadata(o,'pod_'+['base','body','lid','window'][j]);templates.addObject(o);full.append(o);o.Visibility=False
 r=rect(bb.XMin/1000,bb.YMin/1000,bb.XLength/1000,bb.YLength/1000);o=box(f'SimplePod_{i:02}',r,bb.ZMin/1000,bb.ZLength/1000,templates,'simple_pod');o.Visibility=False;simple.append(o);pod_envelopes.append(dict(id=f'P{i:02}',**r,z1=bb.ZMin/1000,z2=bb.ZMax/1000))
A.closeDocument(sd.Name);A.setActiveDocument(doc.Name)
for n,parts in [('FullPodsTemplate',full),('SimplePodsTemplate',simple)]:
 o=doc.addObject('Part::Compound',n);o.Links=parts;templates.addObject(o);metadata(o,'pod_template');o.Visibility=False
representatives=['SW-06','SE-06','NW-06','NE-06']
for r in d['rooms']:
 o=doc.addObject('App::Link',r['id'].replace('-','_')+'_Pods');o.setLink(doc.getObject('FullPodsTemplate' if r['id'] in representatives else 'SimplePodsTemplate'));o.LinkPlacement=A.Placement(A.Vector(r['x1']*1000,r['y1']*1000,0),A.Rotation());pods.addObject(o);metadata(o,'pods_instance');o.addProperty('App::PropertyString','RoomID');o.RoomID=r['id'];o.addProperty('App::PropertyInteger','PodCount');o.PodCount=20;o.Label=r['id']+' / 20舱 / '+('完整闭舱' if r['id'] in representatives else '简化外包');pod_links.append(o)
for i,(x,y) in enumerate([(35,14.35),(70,42.2),(90.8,68),(26.2,20.35)]):
 o=doc.addObject('Part::Cylinder','PersonScale_'+str(i+1));o.Radius=225;o.Height=1680;o.Placement.Base=A.Vector(x*1000,y*1000,0);o.setExpression('Height','Parameters.HumanHeight');o.setExpression('Radius','Parameters.HumanDiameter/2');refs.addObject(o);metadata(o,'person_scale');o.Label='尺度柱1.68m / 非角色'
# Ceiling retains actual exterior footprint, excluding stair wells (separate 3.8m roofs).
cuts=Part.makeCompound([Part.makeBox((s['x2']-s['x1'])*1000,(s['y2']-s['y1'])*1000,10000,A.Vector(s['x1']*1000,s['y1']*1000,0)) for s in d['stairs']])
for i,r in enumerate(d['floor_cells']):
 shape=Part.makeBox((r['x2']-r['x1'])*1000,(r['y2']-r['y1'])*1000,150,A.Vector(r['x1']*1000,r['y1']*1000,3400)).cut(cuts)
 if shape.isNull() or shape.Volume<1e-5:continue
 o=doc.addObject('Part::Feature','Ceiling_'+str(i+1));o.Shape=shape;roofs.addObject(o);metadata(o,'ceiling');o.Visibility=False
# The upper landing is the next-floor datum +3.80m, not a roof.
# Stair wells continue upward beyond this one-floor cut; do not cap the landing.
doc.recompute()
bad=[o.Name for o in doc.Objects if hasattr(o,'Shape') and (o.Shape.isNull() or not o.Shape.isValid())];assert not bad,bad
assert len(pod_links)==48 and sum(o.PodCount for o in pod_links)==960 and len(stair_steps)==88
for r in d['walls']:
 b=doc.getObject(r['id']).Shape.BoundBox;assert max(abs(a-z) for a,z in zip([b.XMin,b.YMin,b.XMax,b.YMax],[r[k]*1000 for k in ['x1','y1','x2','y2']]))<1e-4
for o in full+simple+[doc.FullPodsTemplate,doc.SimplePodsTemplate]:o.Visibility=False
for o in pod_links:o.Visibility=True
native_count=len(doc.Objects);doc.saveAs(str(ROOT/'standard_floor_blockout_v3_frozen.FCStd'));A.closeDocument(doc.Name)
(ROOT/'sources/accepted_inset_layout.snapshot.json').write_bytes(PLAN.read_bytes());(ROOT/'sources/STANDARD_FLOOR_ENGINEERING_BRIEF.snapshot.md').write_bytes((ROOT.parent/'v3_frozen/sources/STANDARD_FLOOR_ENGINEERING_BRIEF.snapshot.md').read_bytes())
report=dict(source_commit='b53aa9b8e38c7c423703dd946c2ba88d44b9ab37',plan_json_sha256=hashlib.sha256(PLAN.read_bytes()).hexdigest(),room1_source_sha256=source_hash,
 room_count=48,pod_count=960,full_pod_rooms=representatives,simple_pod_rooms=44,pods_per_room=20,door_clear_height_m=2.4,room_clear_height_m=3.4,storey_height_m=3.8,slab_thickness_m=.1,
 main_envelope_m=d['main_envelope_m'],maximum_envelope_m=d['maximum_envelope_m'],walls=len(wall_objects),lintels=len(lintels),native_object_count=native_count,
 exact_accepted_plan_wall_coordinates=True,all_native_shapes_valid=True,stairs=4,stair_treads=88,riser_count_per_stair=24,flight_run_m=3.3,stair_embedded_m=dict(West=4.7,East=4.7,North=7.3,South=7.3),
 roof_default_hidden=True,all_walls_retained_in_all_views=True,pod_template_envelopes=pod_envelopes,render_status='pending',limitations=['Single storey only','Vertical dimensions/slabs/door heights are provisional spatial-test values','No structural, fire-code, evacuation capacity/time or actual robot motion approval','No authored materials, lighting, facade detail or final pixel artwork'])
(ROOT/'blockout_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:report[k] for k in ['room_count','pod_count','walls','lintels','main_envelope_m']},ensure_ascii=False))
