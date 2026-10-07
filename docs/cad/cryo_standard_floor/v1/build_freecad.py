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
doc=App.newDocument('CryoStandardFloor_v1');doc.Label='标准休眠层 v1 | 二维工程验证 / 疏散设计待完善'
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
for name,value in [('SourceCommit','71ba4633094de972cbd229a2e890946e740f04ab'),('BriefBlob','905b68ca5956c0b50074a85574eb855160a5b25f'),('Scope','2D ONLY / walls are 1mm plan-hatch extrusions, NOT building height'),('UpdateInstructions','Native geometry/live A404 update; merged-wall topology and A401-A403 snapshots must be regenerated with scripts after design changes.'),('EvacuationStatus','OPEN: maximum center-to-nearest-stair 106.95m; no capacity or fire-code approval')]:
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
 o=doc.addObject('Part::Extrusion',r['id']);o.Base=s;o.Solid=True;o.DirMode='Normal';o.setExpression('LengthFwd','Parameters.PlanThickness');o.Label=r['id']+' | 1mm平面填充';wg.addObject(o);solids.append(o);plans.append(s)
 if App.GuiUp:o.ViewObject.ShapeColor=(.28,.28,.28);o.ViewObject.LineColor=(.28,.28,.28)
for r in data['rooms']:
 s=sketch(r['id'].replace('-','_')+'_Envelope',r,rg,r['id']+' | 21×9.5 / 20人');s.Visibility=False
for i,r in enumerate(data['corridors']+data['elevator_nodes']+data['stairs']+data['references']+[data['freight_lobby'],data['freight_shaft']]):
 s=sketch('Reference_'+str(i+1),r,cg,r.get('id',r['tag'])+' | 控制线');s.Visibility=False;plans.append(s)
# Live dimensions use a separately constrained overall envelope, not manually typed labels.
env={'expressions':dict(x='-ExternalReach',y='0',w='MaxWidth',d='MainDepth')}
control=sketch('OverallEnvelope',env,cg,'总包络尺寸基准 / 非围护墙');control.Visibility=False;plans.append(control)
doc.recompute()
bad=[dict(name=s.Name,state=s.State,error=s.getStatusString(),expressions=s.ExpressionEngine) for s in sketches if s.Shape.isNull() or not s.FullyConstrained]
if bad:print(json.dumps(bad[:4],ensure_ascii=False,default=str));raise RuntimeError('invalid sketches')
assert all(s.Shape.isValid() for s in sketches)
assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in solids)
wallshape=Part.makeCompound([o.Shape for o in solids])
collisions=[]
for i,a in enumerate(solids):
 for b in solids[i+1:]:
  aa,bb=a.Shape.BoundBox,b.Shape.BoundBox
  if min(aa.XMax,bb.XMax)>max(aa.XMin,bb.XMin)+1e-5 and min(aa.YMax,bb.YMax)>max(aa.YMin,bb.YMin)+1e-5:
   volume=a.Shape.common(b.Shape).Volume
   if volume>1e-3:collisions.append([a.Name,b.Name,volume])
assert not collisions,collisions
def box(x,y,w,h):return Part.makeBox(w*1000,h*1000,1,App.Vector(x*1000,y*1000,0))
def overlap(shape):
 # Bounding boxes first, then exact OpenCASCADE intersections.
 b=shape.BoundBox;volume=0
 for o in solids:
  a=o.Shape.BoundBox
  if min(a.XMax,b.XMax)>max(a.XMin,b.XMin)+1e-5 and min(a.YMax,b.YMax)>max(a.YMin,b.YMin)+1e-5:volume+=shape.common(o.Shape).Volume
 return volume
door_failures=[]
for door in data['doors']:
 x,y,w=door['x'],door['y'],door['width'];eps=1e-5
 probe=box(x-w/2+eps,y-.1,w-2*eps,.2) if door['orientation']=='H' else box(x-.1,y-w/2+eps,.2,w-2*eps)
 vol=overlap(probe)
 if vol>1e-2:door_failures.append(dict(door=door,volume_mm3=vol))
assert not door_failures,door_failures
interior_failures=[]
for r in data['rooms']:
 vol=overlap(box(r['x1']+.20001,r['y1']+.20001,20.59998,9.09998))
 if vol>1e-2:interior_failures.append(r['id'])
assert not interior_failures,interior_failures
route_failures=[];route_checks=0
for e in data['routes']['edges']:
 a=data['routes']['nodes'][e['a']];b=data['routes']['nodes'][e['b']]
 if e['length']<1e-8:continue
 x1,x2=sorted([a['x'],b['x']]);y1,y2=sorted([a['y'],b['y']]);half=.225
 assert abs(x1-x2)<1e-6 or abs(y1-y2)<1e-6
 probe=box(x1-half,y1-half,x2-x1+2*half,y2-y1+2*half)
 vol=overlap(probe);route_checks+=1
 if vol>1e-2:route_failures.append(dict(edge=e,volume_mm3=vol))
assert not route_failures,route_failures
turn_checks=[]
for x,y,name in [(v['SpineCenterX'],v['CrossCenterY'],'6x4_intersection'),(91.6,39.5,'4x4_freight_lobby')]:
 probe=Part.makeCylinder(checks['turn_circle_diameter_m']/2*1000,1,App.Vector(x*1000,y*1000,0));vol=overlap(probe);assert vol<1e-2,(name,vol);turn_checks.append(dict(location=name,wall_overlap_mm3=vol))
# Straight carrier swept envelopes, turning is covered by the bounding circle.
carrier_checks=[]
for r,name in [(box(84.85,38.65,8.3,1.7),'spine_to_lobby_horizontal'),(box(90.75,37.95,1.7,7.2),'lobby_to_car_vertical')]:
 vol=overlap(r);assert vol<1e-2,(name,vol);carrier_checks.append(dict(location=name,wall_overlap_mm3=vol))
checks.update(native_fully_constrained_sketch_count=len(sketches),native_plan_hatch_solids=len(solids),exact_wall_collisions=collisions,
 door_void_count=len(data['doors']),door_void_failures=door_failures,clear_room_interiors=48,
 route_450mm_probe_count=route_checks,route_probe_failures=route_failures,turn_circle_checks=turn_checks,carrier_swept_checks=carrier_checks)
pages=make_pages(data,checks)
blank=OUT/'A2_blank.svg';blank.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420"/>',encoding='utf-8')
for page_data in pages:
 content=to_svg(page_data);(OUT/(page_data['code']+'_v1.svg')).write_text(content,encoding='utf-8')
 page=doc.addObject('TechDraw::DrawPage',page_data['code']);page.Label=page_data['code']+' '+page_data['title'];t=doc.addObject('TechDraw::DrawSVGTemplate',page_data['code']+'_Template');t.Template=str(blank);page.Template=t
 symbol=doc.addObject('TechDraw::DrawViewSymbol',page_data['code']+'_Snapshot');r=ET.fromstring(content);r.set('width','594');r.set('height','420');symbol.Symbol=ET.tostring(r,encoding='unicode');page.addView(symbol);symbol.X=297;symbol.Y=210;symbol.ScaleType='Custom';symbol.Scale=10;symbol.LockPosition=True;symbol.Caption='';sg.addObject(page)
 page.addProperty('App::PropertyString','Status','说明');page.Status='Publication snapshot: regenerate after parameter edits.'
lt=OUT/'A2_live.svg';lt.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420"><rect x="12" y="12" width="570" height="396" fill="none" stroke="black" stroke-width="0.3"/><text x="22" y="27" font-size="5" font-family="SimSun">A404 标准层原生实时二维投影 / 1:500</text><text x="22" y="398" font-size="3.2" font-family="SimSun">尺寸单位见标注 / 围护为1mm平面填充；不代表正式三维。A401-A403为排版快照，编辑后需重建。</text></svg>',encoding='utf-8')
live=doc.addObject('TechDraw::DrawPage','A404');live.Label='A404 原生实时二维投影';t=doc.addObject('TechDraw::DrawSVGTemplate','LiveTemplate');t.Template=str(lt);live.Template=t;sg.addObject(live)
view=doc.addObject('TechDraw::DrawViewPart','NativePlan');view.Source=plans;view.Direction=App.Vector(0,0,1);view.ScaleType='Custom';view.Scale=.002;view.X=297;view.Y=220;view.Caption='';live.addView(view)
doc.recompute()
(ROOT/'floor_layout.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'floor_validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'drawing_data.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf-8')
doc.saveAs(str(ROOT/'standard_floor_v1.FCStd'));App.closeDocument(doc.Name)
print(json.dumps({k:checks[k] for k in ['native_fully_constrained_sketch_count','native_plan_hatch_solids','door_void_count','route_450mm_probe_count','main_envelope_m','maximum_envelope_m','maximum_room_center_to_nearest_stair_m']},ensure_ascii=False))
