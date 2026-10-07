"""Build portable native parametric FreeCAD geometry. No custom proxy needed."""
from pathlib import Path
import json, argparse, re, math, sys, xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8')
import FreeCAD as App, Part, Sketcher, TechDraw
from layout import PARAMETERS,layout,validate
from drawings import make_pages,to_svg
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'exports';OUT.mkdir(exist_ok=True)
QA=ROOT/'qa';QA.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--parameters-from',type=Path);args=parser.parse_args()
overrides={}
if args.parameters_from:
 old=App.openDocument(str(args.parameters_from.resolve()))
 overrides={k:getattr(old.Parameters,k).Value/1000 for k in PARAMETERS};App.closeDocument(old.Name)
v,pods=layout(overrides);checks=validate(v,pods)
doc=App.newDocument('CryoRoom1_v1');doc.Label='Room 1 v1 | 20舱十字布局 / 工程实尺验证'
params=doc.addObject('App::FeaturePython','Parameters');params.Label='参数 | P暂定 / 基准 / 目标'
for k,(value,status,label) in PARAMETERS.items():
 params.addProperty('App::PropertyLength',k,status,label);setattr(params,k,v[k]*1000)
derived={'InnerWidth':'RoomWidth-2*Wall','InnerDepth':'RoomDepth-2*Wall','BlockWidth':'5*PodWidth+4*Gap',
         'SideMargin':'(InnerWidth-LongAisle-2*BlockWidth)/2','EndMargin':'(InnerDepth-CrossAisle-2*PodLength)/2'}
for k,e in derived.items():
 params.addProperty('App::PropertyLength',k,'DERIVED');params.setExpression(k,re.sub(r'\b[A-Z][A-Za-z]+\b',lambda m:'Parameters.'+m[0],e))
params.addProperty('App::PropertyString','SourceCommit','来源');params.SourceCommit='fcc0863e925a7063eaae074f54cba030a677b315'
params.addProperty('App::PropertyString','BriefBlob','来源');params.BriefBlob='98292957a63963c5decd88b17b559bbce49381cf'
params.addProperty('App::PropertyString','UpdateInstructions','说明');params.UpdateInstructions='几何与A304原生投影实时联动；A301-A303为快照，编辑后用build_freecad.py --parameters-from 文件.FCStd重建，再导出PDF。'
table=doc.addObject('Spreadsheet::Sheet','ParameterTable');table.Label='米制参数 / 状态'
for c,t in zip('ABCD',['参数','m','状态','含义']):table.set(c+'1',t)
for row,(k,(_,status,label)) in enumerate(PARAMETERS.items(),2):
 for c,t in zip('ABCD',[k,f'=Parameters.{k} / (1000 mm)',status,label]):table.set(c+str(row),t)
for c,w in [('A',180),('B',90),('C',120),('D',300)]:table.setColumnWidth(c,w)
def group(n,label,parent=None):
 o=doc.addObject('App::DocumentObjectGroup',n);o.Label=label
 if parent:parent.addObject(o)
 return o
room=group('Room','01 房间围护 / 真实后墙中央门洞')
equipment=group('Pods','02 20休眠舱 | 四区各5 / 原生分层实体')
reference=group('Reference','03 通道控制线 / 人体平面参考（非实体）')
sheets=group('Sheets','04 工程图页 | A301-A303快照 / A304实时')
def ex(e):
 return re.sub(r'\b[A-Z][A-Za-z]+\b',lambda m:'Parameters.'+m[0] if m[0] in PARAMETERS or m[0] in derived else m[0],str(e))
def num(e):return float(eval(str(e).replace(' m',''),{'__builtins__':{}},v))*1000
def sketch(n,points,x,y,z,parent):
 s=doc.addObject('Sketcher::SketchObject',n)
 for p,q in zip(points,points[1:]+points[:1]):s.addGeometry(Part.LineSegment(App.Vector(num(p[0]),num(p[1]),0),App.Vector(num(q[0]),num(q[1]),0)),False)
 for i,p in enumerate(points):
  s.addConstraint(Sketcher.Constraint('Coincident',i,2,(i+1)%len(points),1))
  for axis,j in [('X',0),('Y',1)]:
   ci=s.addConstraint(Sketcher.Constraint('Distance'+axis,i,1,num(p[j])));s.setExpression('Constraints['+str(ci)+']',ex(p[j]))
 for a,e in zip('xyz',[x,y,z]):s.setExpression('Placement.Base.'+a,ex(e))
 parent.addObject(s);s.Visibility=False;return s
def poly(w,l,c):return [(c,'0'),(f'{w}-{c}','0'),(w,c),(w,f'{l}-{c}'),(f'{w}-{c}',l),(c,l),('0',f'{l}-{c}'),('0',c)]
def rect(w,l):return [('0','0'),(w,'0'),(w,l),('0',l)]
solids=[];plans=[]
def solid(n,label,pts,x,y,z,h,parent,color,transparent=0):
 s=sketch(n+'_Footprint',pts,x,y,z,parent);s.Label=label+' | 全约束足迹'
 o=doc.addObject('Part::Extrusion',n);o.Label=label;o.Base=s;o.DirMode='Normal';o.Solid=True;o.setExpression('LengthFwd',ex(h))
 o.addProperty('App::PropertyString','Status','说明');o.Status='PROVISIONAL / 工程占位'
 parent.addObject(o);solids.append(o)
 if App.GuiUp:o.ViewObject.ShapeColor=color;o.ViewObject.LineColor=(.20,.22,.24);o.ViewObject.Transparency=transparent
 return o,s
W,D,T='RoomWidth','RoomDepth','Wall'
for n,pts,x,y in [
 ('Front',rect(W,T),'0','0'),('Left',rect(T,'RoomDepth-2*Wall'),'0',T),
 ('Right',rect(T,'RoomDepth-2*Wall'),'RoomWidth-Wall',T),
 ('RearLeft',rect('(RoomWidth-DoorWidth)/2',T),'0','RoomDepth-Wall'),
 ('RearRight',rect('(RoomWidth-DoorWidth)/2',T),'(RoomWidth+DoorWidth)/2','RoomDepth-Wall')]:
 o,s=solid('Wall_'+n,'墙 '+n+' | 3D剖切显示',pts,x,y,'0','CutWallHeight',room,(.73,.75,.77));plans.append(s)
o,s=solid('AuthPanel','门旁壁面认证面板 P',rect('PanelWidth','PanelDepth'),'(RoomWidth+DoorWidth)/2+PanelOffset','RoomDepth-Wall-PanelDepth','0.95 m','0.3 m',room,(.32,.40,.43));plans.append(s)
for p in pods:
 g=group(p['id'],p['id']+' | '+['前','后'][p['row']]+['左','右'][p['side']]+'区',equipment)
 x=f'Wall+SideMargin+{p["side"]}*(BlockWidth+LongAisle)+{p["col"]}*(PodWidth+Gap)'
 y=f'Wall+EndMargin+{p["row"]}*(PodLength+CrossAisle)'
 layers=[('Base','底座',poly('PodWidth','PodLength','BaseChamfer'),x,y,'0','0.20*PodHeight',(.48,.53,.56),0),
 ('Body','内收主体',poly('(PodWidth-2*BodyInset)','(PodLength-2*BodyInset)','0.14 m'),x+'+BodyInset',y+'+BodyInset','0.24*PodHeight','0.40*PodHeight',(.70,.73,.75),0),
 ('Lid','独立低舱盖',poly('(PodWidth-2*LidInset)','(PodLength-2*LidInset)','0.16 m'),x+'+LidInset',y+'+LidInset','0.68*PodHeight','0.30*PodHeight',(.82,.84,.85),0),
 ('Window','头部磨砂观察区',poly('(PodWidth-2*WindowInset)','WindowLength','0.07 m'),x+'+WindowInset',
    y+('+WindowEndInset' if p['row']==0 else '+PodLength-WindowEndInset-WindowLength'),'0.98*PodHeight','0.02*PodHeight',(.43,.63,.69),45)]
 for suffix,label,pts,xx,yy,z,h,color,tr in layers:
  o,s=solid(p['id']+'_'+suffix,p['id']+' '+label+' P',pts,xx,yy,z,h,g,color,tr);plans.append(s)
controls=[]
for n,x,y,w,l in [
 ('LongAxis','(RoomWidth-LongAisle)/2','Wall','LongAisle','InnerDepth'),
 ('CrossAxis','Wall','(RoomDepth-CrossAisle)/2','InnerWidth','CrossAisle'),
 ('Envelope','0','0','RoomWidth','RoomDepth')]:
 s=sketch(n,rect(w,l),x,y,'0',reference);controls.append(s)
doc.recompute()
sketches=[o for o in doc.Objects if o.TypeId=='Sketcher::SketchObject']
assert all(s.FullyConstrained and s.Shape.isValid() for s in sketches)
assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in solids)
# Exact OpenCASCADE positive-volume collision check. Touching faces are allowed.
collisions=[]
for i,a in enumerate(solids):
 for b in solids[i+1:]:
  ba,bb=a.Shape.BoundBox,b.Shape.BoundBox
  if all(min(getattr(ba,k+'Max'),getattr(bb,k+'Max'))>max(getattr(ba,k+'Min'),getattr(bb,k+'Min'))+1e-6 for k in 'XYZ'):
   volume=a.Shape.common(b.Shape).Volume
   if volume>1e-4:collisions.append(dict(a=a.Name,b=b.Name,volume_mm3=volume))
assert not collisions,collisions
for p in pods:
 shapes=[doc.getObject(p['id']+'_'+s).Shape for s in ['Base','Body','Lid','Window']]
 bb=Part.makeCompound(shapes).BoundBox
 for got,expected in [(bb.XMin,p['x']*1000),(bb.YMin,p['y']*1000),(bb.XLength,p['w']*1000),(bb.YLength,p['d']*1000),(bb.ZLength,p['h']*1000)]:assert abs(got-expected)<1e-5,(p,got,expected)
pages=make_pages(v,pods,checks)
blank=OUT/'A2_blank.svg';blank.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420"/>',encoding='utf-8')
for data in pages:
 content=to_svg(data);(OUT/(data['code']+'_v1.svg')).write_text(content,encoding='utf-8')
 page=doc.addObject('TechDraw::DrawPage',data['code']);page.Label=data['code']+' '+data['title']
 template=doc.addObject('TechDraw::DrawSVGTemplate',data['code']+'_Template');template.Template=str(blank);page.Template=template
 symbol=doc.addObject('TechDraw::DrawViewSymbol',data['code']+'_Snapshot');r=ET.fromstring(content);r.set('width','594');r.set('height','420');symbol.Symbol=ET.tostring(r,encoding='unicode')
 page.addView(symbol);symbol.X=297;symbol.Y=210;symbol.ScaleType='Custom';symbol.Scale=10;symbol.LockPosition=True;symbol.Caption='';sheets.addObject(page)
 page.addProperty('App::PropertyString','PublicationStatus','说明');page.PublicationStatus='排版快照；参数编辑后需重建。实时几何见A304。'
live=doc.addObject('TechDraw::DrawPage','A304');live.Label='A304 原生实时平面投影 / 实尺尺寸'
lt=OUT/'A2_live.svg';lt.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420"><rect x="12" y="12" width="570" height="396" fill="none" stroke="black" stroke-width="0.3"/><text x="22" y="27" font-size="5" font-family="SimSun">A304 Room 1 原生实时平面 / 1:50</text><text x="22" y="398" font-size="3.2" font-family="SimSun">几何与原生尺寸实时联动；编辑后排版页A301-A303需重建。尺寸mm / P为暂定 / 室内净高TBD。</text></svg>',encoding='utf-8')
t=doc.addObject('TechDraw::DrawSVGTemplate','LiveTemplate');t.Template=str(lt);live.Template=t;sheets.addObject(live)
view=doc.addObject('TechDraw::DrawViewPart','NativePlan');view.Source=plans;view.Direction=App.Vector(0,0,1);view.ScaleType='Custom';view.Scale=.02;view.X=297;view.Y=225;view.Caption='';live.addView(view)
doc.recompute()
checks.update(native_fully_constrained_sketch_count=len(sketches),native_solid_count=len(solids),exact_solid_collisions=collisions,
 native_pod_envelopes_readback=True,source_commit=params.SourceCommit,brief_blob=params.BriefBlob)
report=dict(revision='v1',source_commit=params.SourceCommit,parameters={k:dict(value=v[k],unit='m',status=a[1],label=a[2]) for k,a in PARAMETERS.items()},
 derived={k:v[k] for k in derived},pods=pods,checks=checks,pages=pages,
 interpretation='RoomWidth/Depth treated as outer envelope, not interior clear; head zones face front/rear walls; draft extra front arrow is not an extra door.',
 limitations=['static closed-pod geometry only','盖板开启扫掠 / 操作人体回转 / 搬运更换空间待下一阶段验证','室内净高 / 消防 / 机电未锁定'],
 design_status='PROVISIONAL / 静态实尺验证通过，待用户审阅')
(ROOT/'cad_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
doc.saveAs(str(ROOT/'room1_engineering_v1.FCStd'));App.closeDocument(doc.Name)
print(json.dumps(checks,ensure_ascii=False,indent=2))
