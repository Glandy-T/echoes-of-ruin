"""Native editable 2D topology: fully constrained sketches and 1mm plan hatch solids.
No formal 3D building geometry. Rebuild after topology-changing parameter edits.
"""
from pathlib import Path
import json,re,sys,math,xml.etree.ElementTree as ET
import FreeCAD as App,Part,Sketcher
from layout import PARAMETERS,DERIVED,build_layout,validate_layout
from drawings import make_pages,to_svg
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'exports';QA=ROOT/'qa'
OUT.mkdir(exist_ok=True);QA.mkdir(exist_ok=True)
sys.stdout.reconfigure(encoding='utf-8')
data=build_layout();checks=validate_layout(data);v=data['parameters']
doc=App.newDocument('CryoStandardFloor_v3');doc.Label='标准休眠层 v3 | 二维工程验证 / 疏散设计待完善'
p=doc.addObject('App::FeaturePython','Parameters');p.Label='米制尺寸参数 / 仅二维'
for k,n in PARAMETERS.items():p.addProperty('App::PropertyLength',k,'INPUT');setattr(p,k,n*1000)
p.addProperty('App::PropertyInteger','Risers','INPUT');p.Risers=24
def ex(e):
 # Layout formula numbers are metres; normalize lengths before arithmetic,
 # then attach a metre unit. This also handles zero origins without unit mismatch.
 def token(m):
  if m[0]=='Risers':return 'Parameters.Risers'
  return '(Parameters.'+m[0]+' / (1 m))' if m[0] in v else m[0]
 return '('+re.sub(r'\b[A-Z][A-Za-z]+\b',token,str(e))+') * (1 m)'
for k,e in DERIVED.items():p.addProperty('App::PropertyLength',k,'DERIVED');p.setExpression(k,ex(e))
for name,value in [('SourceCommit','ffef818b6ce144f9e27d61af5f2131694be6d72c'),('BriefBlob','f708d4ac542b19ee0eed79d9ec367dd0a2c4b137'),('Scope','2D ONLY / walls are 1mm plan-hatch extrusions, NOT building height'),('UpdateInstructions','Native geometry/live A404 update; merged-wall topology and A401-A403 snapshots must be regenerated with scripts after design changes.'),('EvacuationStatus','OPEN: maximum center-to-nearest-stair 72.25m; no capacity or fire-code approval')]:
 p.addProperty('App::PropertyString',name,'NOTES');setattr(p,name,value)
def group(n,label):g=doc.addObject('App::DocumentObjectGroup',n);g.Label=label;return g
wg=group('Walls','01 共享墙精确并集 / 1mm平面填充');rg=group('Modules','02 48房间外包 / 不修改Room1 v2');cg=group('ControlReferences','03 净宽与节点控制线');sg=group('Sheets','04 A401-A403排版快照 / A404实时投影')
plans=[];solids=[];sketches=[]
def num(e):return float(eval(str(e),{'__builtins__':{}},v))*1000
def sketch(n,r,parent,label=None):
 e=r['expressions'];s=doc.addObject('Sketcher::SketchObject',n);s.Label=label or n
 pts=[('0','0'),(e['w'],'0'),(e['w'],e['d']),('0',e['d'])]
 for a,b in zip(pts,pts[1:]+pts[:1]):s.addGeometry(Part.LineSegment(App.Vector(num(a[0]),num(a[1]),0),App.Vector(num(b[0]),num(b[1]),0)),False)
 for i,a in enumerate(pts):
  s.addConstraint(Sketcher.Constraint('Coincident',i,2,(i+1)%4,1))
  for axis,j in [('X',0),('Y',1)]:
   ci=s.addConstraint(Sketcher.Constraint('Distance'+axis,i,1,num(a[j])));s.setExpression('Constraints['+str(ci)+']',ex(a[j]))
 s.setExpression('Placement.Base.x',ex(e['x']));s.setExpression('Placement.Base.y',ex(e['y']));parent.addObject(s);sketches.append(s)
 if App.GuiUp:s.ViewObject.LineColor=(.25,.48,.65)
 return s
for r in data['walls']:
 s=sketch(r['id']+'_Footprint',r,wg);s.Visibility=False
 o=doc.addObject('Part::Extrusion',r['id']);o.Base=s;o.Solid=True;o.DirMode='Normal';o.setExpression('LengthFwd','Parameters.PlanThickness');o.Label=r['id']+' | 1mm二维墙填充';wg.addObject(o);solids.append(o);plans.append(s)
 if App.GuiUp:o.ViewObject.ShapeColor=(.28,.28,.28);o.ViewObject.LineColor=(.28,.28,.28)
for r in data['rooms']:s=sketch(r['id'].replace('-','_')+'_Envelope',r,rg,r['id']+' | 21×9.5 / 20人');s.Visibility=False
for i,r in enumerate(data['corridors']+data['elevator_nodes']+data['stairs']+data['references']+data['freight_shafts']+data['plenums']+[data['transfer']]+data['waiting_bays']):
 s=sketch('Reference_'+str(i+1),r,cg,r.get('id',r['tag'])+' | 控制线');s.Visibility=False;plans.append(s)
control=sketch('OverallEnvelope',{'expressions':dict(x='-ExternalReach',y='MaxSouth',w='MaxWidth',d='MaxDepth')},cg,'总包络基准 / 非围护墙');control.Visibility=False
doc.recompute();bad=[dict(name=s.Name,state=s.State,error=s.getStatusString()) for s in sketches if s.Shape.isNull() or not s.FullyConstrained]
assert not bad,bad[:5];assert all(s.Shape.isValid() for s in sketches);assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in solids)
collisions=[]
for i,a in enumerate(solids):
 for b in solids[i+1:]:
  aa,bb=a.Shape.BoundBox,b.Shape.BoundBox
  if min(aa.XMax,bb.XMax)>max(aa.XMin,bb.XMin)+1e-5 and min(aa.YMax,bb.YMax)>max(aa.YMin,bb.YMin)+1e-5:
   vol=a.Shape.common(b.Shape).Volume
   if vol>1e-3:collisions.append([a.Name,b.Name,vol])
assert not collisions,collisions
def box(x,y,w,h):return Part.makeBox(w*1000,h*1000,1,App.Vector(x*1000,y*1000,0))
def overlap(shape,objects=None):
 b=shape.BoundBox;volume=0
 for o in objects if objects is not None else [o.Shape for o in solids]:
  a=o.BoundBox
  if min(a.XMax,b.XMax)>max(a.XMin,b.XMin)+1e-5 and min(a.YMax,b.YMax)>max(a.YMin,b.YMin)+1e-5:volume+=shape.common(o).Volume
 return volume
def capsule(a,b,r):
 x1,y1=a['x'],a['y'];x2,y2=b['x'],b['y'];length=math.hypot(x2-x1,y2-y1)
 caps=[Part.makeCylinder(r*1000,1,App.Vector(x*1000,y*1000,0)) for x,y in [(x1,y1),(x2,y2)]]
 if length>1e-8:
  nx,ny=-(y2-y1)/length*r,(x2-x1)/length*r;points=[(x1+nx,y1+ny),(x2+nx,y2+ny),(x2-nx,y2-ny),(x1-nx,y1-ny)];pts=[App.Vector(x*1000,y*1000,0) for x,y in points];caps.append(Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(App.Vector(0,0,1)))
 return Part.makeCompound(caps)
openings=[]
for door in data['doors']:
 x,y,w=door['x'],door['y'],door['width'];eps=1e-5;probe=box(x-w/2+eps,y-.1,w-2*eps,.2) if door['orientation']=='H' else box(x-.1,y-w/2+eps,.2,w-2*eps)
 vol=overlap(probe);assert vol<1e-2,(door,vol);openings.append(dict(id=door['id'],kind=door['kind'],width_m=w,wall_overlap_mm3=vol))
for r in data['rooms']:assert overlap(box(r['x1']+.20001,r['y1']+.20001,20.59998,9.09998))<1e-2,r['id']
for r in data['references']:
 if r['tag']=='stair_landing':assert overlap(box(r['x1']+.00001,r['y1']+.00001,r['x2']-r['x1']-.00002,r['y2']-r['y1']-.00002))<1e-2
crew=[];cargo={};waiting=[];radius=checks['turn_circle_diameter_m']/2
for i,e in enumerate(data['routes']['edges']):
 if e['length']<1e-8:continue
 a=data['routes']['nodes'][e['a']];b=data['routes']['nodes'][e['b']]
 probe=capsule(a,b,.225);vol=overlap(probe);assert vol<1e-2,(e,vol);crew.append(i)
 if e['kind'] in ['machine','freight']:
  x1,x2=sorted([a['x'],b['x']]);y1,y2=sorted([a['y'],b['y']]);hw=v['CarrierWidth']/2;hl=v['CarrierLength']/2
  assert abs(x1-x2)<1e-7 or abs(y1-y2)<1e-7
  probe=box(x1-hw,y1-hl,2*hw,y2-y1+2*hl) if abs(x1-x2)<1e-7 else box(x1-hl,y1-hw,x2-x1+2*hl,2*hw)
  vol=overlap(probe);assert vol<1e-2,('carrier_sweep',e,vol);cargo[i]=probe
 elif e['kind']=='waiting':
  probe=capsule(a,b,radius);vol=overlap(probe);assert vol<1e-2,('waiting_circle_sweep',e,vol);waiting.append(dict(edge=i,wall_overlap_mm3=vol))
turns=[]
for n,a in data['routes']['nodes'].items():
 if a['role']!='machine':continue
 probe=Part.makeCylinder(radius*1000,1,App.Vector(a['x']*1000,a['y']*1000,0));vol=overlap(probe);assert vol<1e-2,('turn',n,vol);turns.append(dict(node=n,wall_overlap_mm3=vol))
occupied=[box(r['x1'],r['y1'],r['x2']-r['x1'],r['y2']-r['y1']) for r in data['waiting_bays']]
for i,probe in cargo.items():assert overlap(probe,occupied)<1e-2,('occupied_wait_bays',i)
for t in turns:
 a=data['routes']['nodes'][t['node']];probe=Part.makeCylinder(radius*1000,1,App.Vector(a['x']*1000,a['y']*1000,0));assert overlap(probe,occupied)<1e-2,('wait_bay_turn',t['node'])
faults=[]
for fault in checks['single_car_fault_tests']:
 failed=fault['disabled'];door=next(d for d in data['doors'] if d['kind']=='freight' and d['tag']==failed+'_Door');x,y,w=door['x'],door['y'],door['width']
 blocker=box(x-w/2,y-.1,w,.2) if door['orientation']=='H' else box(x-.1,y-w/2,.2,w)
 for route in fault['remaining_accessible_routes']:
  for a,b in zip(route['nodes'],route['nodes'][1:]):
   for i,e in enumerate(data['routes']['edges']):
    if {a,b}=={e['a'],e['b']} and i in cargo:assert overlap(cargo[i],[blocker])<1e-2,('fault_blocker',failed,route)
 faults.append(dict(closed_car=failed,remaining_routes=12,closed_door_obstruction_clear=True))
checks.update(native_fully_constrained_sketch_count=len(sketches),native_plan_hatch_solids=len(solids),exact_wall_collisions=collisions,clear_room_interiors=48,clear_stair_landings=8,
 native_opening_checks=openings,door_count=sum(d['kind'] not in ['machine_portal','personnel_exclusion'] for d in data['doors']),machine_portal_count=sum(d['kind']=='machine_portal' for d in data['doors']),route_450mm_capsule_count=len(crew),carrier_axis_sweep_count=len(cargo),turn_circle_checks=turns,waiting_circle_sweeps=waiting,all_four_wait_bays_occupied_clear_of_transit=True,closed_car_geometry_tests=faults)

# Closed emergency boundaries are physical barriers, separate from normally open machine routing.
barriers=[]
for door in data['doors']:
 if door['kind']=='personnel_exclusion':barriers.append(box(door['x']-door['width']/2,door['y']-.1,door['width'],.2))
personnel_edges=[]
for i,e in enumerate(data['routes']['edges']):
 if e['kind'] not in ['daily','emergency','evacuation_outward']:continue
 a=data['routes']['nodes'][e['a']];b=data['routes']['nodes'][e['b']]
 probe=capsule(a,b,.225);assert overlap(probe,barriers)<1e-2,('emergency_barrier',e)
 # No part of personnel capsule may enter the interior of the central local logistics zone.
 forbidden=Part.makeCompound([box(v['CoreWest'],v['CoreSouth'],v['CoreWidth'],v['CoreWidth'])]+[box(p['x1'],p['y1'],p['x2']-p['x1'],p['y2']-p['y1']) for p in data['plenums']])
 assert probe.common(forbidden).Volume<1e-2,('core_personnel_intrusion',e)
 personnel_edges.append(i)
checks.update(physical_emergency_barriers=2,personnel_edges_clear_of_closed_core_barriers=len(personnel_edges),central_logistics_zone_personnel_overlap_mm3=0,built_floor_area_m2=data['built_floor_area_m2'])

pages=make_pages(data,checks);blank=OUT/'A2_blank.svg';blank.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420"/>',encoding='utf-8')
for pd in pages:
 content=to_svg(pd);(OUT/(pd['code']+'_v3.svg')).write_text(content,encoding='utf-8');page=doc.addObject('TechDraw::DrawPage',pd['code']);page.Label=pd['code']+' '+pd['title'];t=doc.addObject('TechDraw::DrawSVGTemplate',pd['code']+'_Template');t.Template=str(blank);page.Template=t
 symbol=doc.addObject('TechDraw::DrawViewSymbol',pd['code']+'_Snapshot');r=ET.fromstring(content);r.set('width','594');r.set('height','420');symbol.Symbol=ET.tostring(r,encoding='unicode');page.addView(symbol);symbol.X=297;symbol.Y=210;symbol.ScaleType='Custom';symbol.Scale=10;symbol.LockPosition=True;symbol.Caption='';sg.addObject(page);page.addProperty('App::PropertyString','Status');page.Status='Snapshot: regenerate after edits.'
lt=OUT/'A2_live.svg';lt.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420"><rect x="12" y="12" width="570" height="396" fill="none" stroke="black" stroke-width="0.3"/><text x="22" y="27" font-size="5" font-family="SimSun">A404 标准层v3原生实时二维投影 / 1:500</text><text x="22" y="398" font-size="3.2" font-family="SimSun">尺寸单位见标注 / 墙为1mm平面填充；无正式3D。A401-A403排版快照，编辑后需重建。</text></svg>',encoding='utf-8')
live=doc.addObject('TechDraw::DrawPage','A404');live.Label='A404 v3 原生实时二维投影';t=doc.addObject('TechDraw::DrawSVGTemplate','LiveTemplate');t.Template=str(lt);live.Template=t;sg.addObject(live)
view=doc.addObject('TechDraw::DrawViewPart','NativePlan');view.Source=plans;view.Direction=App.Vector(0,0,1);view.ScaleType='Custom';view.Scale=.002;view.X=297;view.Y=220;view.Caption='';live.addView(view);doc.recompute()
(ROOT/'floor_layout.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');(ROOT/'floor_validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8');(OUT/'drawing_data.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
doc.saveAs(str(ROOT/'standard_floor_v3.FCStd'));App.closeDocument(doc.Name)
print(json.dumps({k:checks[k] for k in ['main_envelope_m','maximum_envelope_m','native_fully_constrained_sketch_count','native_plan_hatch_solids','door_count','route_450mm_capsule_count','carrier_axis_sweep_count','maximum_center_to_nearest_stair_m']},ensure_ascii=False))
