"""Rebuild measured single-storey plan with installed FreeCAD 1.1.4.

Run with its bin/python.exe; finish_in_freecad.FCMacro verifies GUI projections.
P values are authorized by REDRAW_BRIEF, not final engineering dimensions.
No external custom proxy is required to reopen/edit the native document.
"""
from pathlib import Path
import json, math, re, argparse
import xml.etree.ElementTree as ET
import FreeCAD as App
import Part, Sketcher, TechDraw
from plan_layout import PARAMETERS, COUNTS, make_layout, check_layout
from paper_drawings import make_pages, to_svg
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'exports';OUT.mkdir(exist_ok=True)
SOURCE_MAIN='c1ab4d25e5945b579517f8ceb956dcdd7502223f'
SPEC_BLOB='e0543c128fc1271f0cb5bdd8d7ea3a7e77307551'
BRIEF_BLOB='fe1c57e0679fb7e88592f53ada9d12c0749c1d86'
FINAL_PASS_BLOB='d52cb9060b030ce59c1af88d0c80fd68468c2aea'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--parameters-from',type=Path,help='Read editable Parameters from an existing FCStd; do not save that source document.')
args=parser.parse_args();overrides={}
if args.parameters_from:
    edited=App.openDocument(str(args.parameters_from.resolve()))
    overrides={k:getattr(edited.Parameters,k).Value/1000 for k in PARAMETERS if k in edited.Parameters.PropertiesList}
    overrides.update({k:getattr(edited.Parameters,k) for k in COUNTS if k in edited.Parameters.PropertiesList});App.closeDocument(edited.Name)
values,features=make_layout(overrides);checks=check_layout(values,features)
doc=App.newDocument('AdminFacilityV2_Final');doc.Label='管理设施 v2-FINAL | 单层建筑方案平面图'
def group(name,label):
    o=doc.addObject('App::DocumentObjectGroup',name);o.Label=label;return o
def prop(o,t,n,g,value):
    o.addProperty(t,n,g);setattr(o,n,value)
params=doc.addObject('App::FeaturePython','Parameters');params.Label='参数 | 基准 / 已确认 / PROVISIONAL'
prop(params,'App::PropertyString','Revision','说明','v2-FINAL')
for key,(value,status,label) in PARAMETERS.items():
    params.addProperty('App::PropertyLength',key,status,label);setattr(params,key,values[key]*1000)
for key,(value,status,label) in COUNTS.items():
    params.addProperty('App::PropertyInteger',key,status,label);setattr(params,key,values[key])
prop(params,'App::PropertyString','CoordinateConvention','说明','O=外包左前角；+X左至右；+Y前至后；CAD内部mm / 参数与图示m')
prop(params,'App::PropertyString','PublicationUpdate','说明','A204实时；出版页运行build_freecad.py --parameters-from 已修改文件.FCStd，再运行GUI宏及render_pdf.py；数量修改须重建')
table=doc.addObject('Spreadsheet::Sheet','ParameterTable');table.Label='参数表 | P为设计阶段暂定'
for col,val in zip('ABCD',['参数','米制值 / 数量','状态','含义']):table.set(col+'1',val)
for row,(key,(value,status,label)) in enumerate(list(PARAMETERS.items())+list(COUNTS.items()),2):
    table.set('A'+str(row),key);table.set('B'+str(row),f'=Parameters.{key} / (1000 mm)' if key in PARAMETERS else f'=Parameters.{key}')
    table.set('C'+str(row),status);table.set('D'+str(row),label)
table.setColumnWidth('A',180);table.setColumnWidth('B',95);table.setColumnWidth('C',115);table.setColumnWidth('D',380)
def expr(source):
    # Use dimensionless metre values, then return a native length quantity.
    def repl(m):
        k=m.group(0)
        return f'(Parameters.{k} / (1000 mm))' if k in PARAMETERS else f'Parameters.{k}' if k in COUNTS else k
    return '('+re.sub(r'[A-Za-z_][A-Za-z_0-9]*',repl,str(source))+') * (1000 mm)'
geo=group('PlanGeometry','01 米制平面几何 | 参数驱动');groups={}
for key,label in [('Outer','外墙与真实门洞'),('Auth','认证组隔墙'),('Staff','工作人员区 / 内部厕所'),('PublicL','左公共厕所'),('PublicR','右公共厕所'),('Guide','极简地图占位')]:
    groups[key]=group('Geo_'+key,label);geo.addObject(groups[key])
for letter in 'ABCDEFGHIJ':groups['Auth'+letter]=group('Geo_Auth'+letter,letter+'组认证设备 P');geo.addObject(groups['Auth'+letter])
def sketch(f):
    a=f['values'];k=f['kind'];s=doc.addObject('Sketcher::SketchObject',f['name']);s.Label=f['name']+' | P'
    prop(s,'App::PropertyString','Role','方案',f['role']);prop(s,'App::PropertyString','Status','方案','PROVISIONAL / 方案占位，非施工值')
    if k=='rect':
        w,d=a['w']*1000,a['d']*1000;pts=[(0,0),(w,0),(w,d),(0,d)]
        for p,q in zip(pts,pts[1:]+pts[:1]):s.addGeometry(Part.LineSegment(App.Vector(*p,0),App.Vector(*q,0)),False)
        for i in range(4):s.addConstraint(Sketcher.Constraint('Coincident',i,2,(i+1)%4,1))
        for i,t in enumerate(['Horizontal','Vertical','Horizontal','Vertical']):s.addConstraint(Sketcher.Constraint(t,i))
        s.addConstraint(Sketcher.Constraint('Coincident',0,1,-1,1))
        for i,dimension in [(0,'w'),(1,'d')]:
            ci=s.addConstraint(Sketcher.Constraint('Distance',i,a[dimension]*1000));s.setExpression(f'Constraints[{ci}]',expr(f[dimension]))
        basekeys=['x','y']
    elif k=='line':
        dx,dy=a['x2']-a['x1'],a['y2']-a['y1'];length=math.hypot(dx,dy)*1000
        s.addGeometry(Part.LineSegment(App.Vector(0,0,0),App.Vector(length,0,0)),False)
        s.addConstraint(Sketcher.Constraint('Coincident',0,1,-1,1));s.addConstraint(Sketcher.Constraint('Horizontal',0))
        ci=s.addConstraint(Sketcher.Constraint('Distance',0,length));part='x' if abs(dx)>1e-9 else 'y';sign=1 if (dx if part=='x' else dy)>0 else -1
        s.setExpression(f'Constraints[{ci}]',expr(f'(({f[part+"2"]})-({f[part+"1"]}))*{sign}'))
        s.Placement.Rotation=App.Rotation(App.Vector(0,0,1),math.degrees(math.atan2(dy,dx)));basekeys=['x1','y1']
    else:
        c=Part.Circle(App.Vector(0,0,0),App.Vector(0,0,1),a['r']*1000);s.addGeometry(c if k=='circle' else Part.ArcOfCircle(c,0,math.pi/2),False)
        s.addConstraint(Sketcher.Constraint('Coincident',0,3,-1,1));ci=s.addConstraint(Sketcher.Constraint('Radius',0,a['r']*1000));s.setExpression(f'Constraints[{ci}]',expr(f['r']))
        if k=='arc':
            s.addConstraint(Sketcher.Constraint('DistanceY',0,1,0));s.addConstraint(Sketcher.Constraint('DistanceX',0,2,0));s.Placement.Rotation=App.Rotation(App.Vector(0,0,1),a['angle'])
        basekeys=['x','y']
    for axis,key in zip(['x','y'],basekeys):s.setExpression('Placement.Base.'+axis,expr(f[key]))
    groups[f['owner']].addObject(s);s.Visibility=False;return s
native=[sketch(f) for f in features]
boundaries=group('ConfirmedBoundaries','02 基准与PROVISIONAL边界 | 隐藏控制线')
envelope=sketch(dict(kind='rect',name='Envelope',role='boundary',owner='Outer',x='0',y='0',w='EnvelopeWidth',d='EnvelopeDepth',values=dict(x=0,y=0,w=values['EnvelopeWidth'],d=values['EnvelopeDepth'])))
staff=sketch(dict(kind='rect',name='StaffBoundary',role='boundary',owner='Staff',x='StaffX',y='StaffY',w='StaffWidth',d='StaffDepth',values=dict(x=values['StaffX'],y=values['StaffY'],w=values['StaffWidth'],d=values['StaffDepth'])))
groups['Outer'].removeObject(envelope);groups['Staff'].removeObject(staff);boundaries.addObject(envelope);boundaries.addObject(staff)
envelope.Label='外包65×45 m | 当前验证基准';staff.Label='工作人员20×14 m | FINAL_PASS测试边界';envelope.Status='BASELINE';staff.Status='PROVISIONAL / 本阶段测试尺寸与XY'
area=doc.addObject('App::FeaturePython','AreaReview');area.Label='边界面积 | 含各区墙体，非净使用面积'
for n,e in [('GrossArea','Parameters.EnvelopeWidth * Parameters.EnvelopeDepth'),('StaffArea','Parameters.StaffWidth * Parameters.StaffDepth'),('StaffWCIncludedArea','Parameters.StaffWCWidth * Parameters.StaffWCDepth'),('PublicWCCombinedArea','2 * Parameters.PublicWCWidth * Parameters.PublicWCDepth')]:
    area.addProperty('App::PropertyArea',n,'平方米');area.setExpression(n,e)
pages=make_pages(values,features,checks);drawing=group('DrawingPages','03 建筑方案图 / 实时CAD投影')
blank=OUT/'A2_symbol_template.svg';blank.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420"></svg>',encoding='utf-8')
for data in pages:
    content=to_svg(data);(OUT/(data['code']+'_v2.svg')).write_text(content,encoding='utf-8')
    p=doc.addObject('TechDraw::DrawPage',data['code']);p.Label=data['code']+' '+data['title']
    template=doc.addObject('TechDraw::DrawSVGTemplate',data['code']+'_Template');template.Template=str(blank);p.Template=template
    symbol=doc.addObject('TechDraw::DrawViewSymbol',data['code']+'_Snapshot');r=ET.fromstring(content);r.set('width','594');r.set('height','420');symbol.Symbol=ET.tostring(r,encoding='unicode')
    p.addView(symbol);symbol.X=297;symbol.Y=210;symbol.ScaleType='Custom';symbol.Scale=10;symbol.LockPosition=True;symbol.Caption=''
    prop(p,'App::PropertyString','SnapshotStatus','说明','参数快照；参数修改后重建生成SVG/PDF。');drawing.addObject(p)
live=doc.addObject('TechDraw::DrawPage','CAD_Live');live.Label='A204 实时CAD投影 | 同一建筑坐标'
live_template=OUT/'A2_blank_live.svg'
live_template.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="594mm" height="420mm" viewBox="0 0 594 420"><rect x="12" y="12" width="570" height="396" fill="none" stroke="black" stroke-width="0.3"/><text x="22" y="28" font-size="5" font-family="SimSun">A204 实时参数投影 / 管理设施 v2-FINAL</text><text x="22" y="40" font-size="3.2" font-family="SimSun">左：全平面1:175；右：工作人员区1:150；P参数可编辑。建筑统一原点O=左前角。</text><text x="22" y="394" font-size="3" font-family="SimSun">本页原生投影与尺寸实时；排版页A201–A203及其导出为重建快照。P=PROVISIONAL；合规/吞吐TBD。</text></svg>',encoding='utf-8')
tmpl=doc.addObject('TechDraw::DrawSVGTemplate','LiveTemplate');tmpl.Template=str(live_template);live.Template=tmpl;drawing.addObject(live)
for name,sources,x,y,scale in [('ViewPlan',native,220,214,1/175),('ViewStaff',[s for s,f in zip(native,features) if f['owner']=='Staff'],490,315,1/150)]:
    view=doc.addObject('TechDraw::DrawViewPart',name);view.Source=sources;view.Direction=App.Vector(0,0,1);view.ScaleType='Custom';view.Scale=scale
    live.addView(view);view.X=x;view.Y=y;view.LockPosition=True;view.Caption=''
doc.recompute()
unconstrained=[s.Name for s in native+[envelope,staff] if not s.FullyConstrained or not s.Shape.isValid()];assert not unconstrained,unconstrained
errors=[{'object':o.Name,'state':list(o.State)} for o in doc.Objects if any('invalid' in str(s).lower() or 'error' in str(s).lower() for s in o.State)];assert not errors,errors
fcstd=ROOT/'admin_facility_v2.FCStd';doc.saveAs(str(fcstd))
report=dict(revision='v2-FINAL',source_main=SOURCE_MAIN,spec_blob=SPEC_BLOB,brief_blob=BRIEF_BLOB,final_pass_blob=FINAL_PASS_BLOB,
    coordinate_system='metres in layout; FreeCAD internal mm; O front-left; +X right; +Y rear',
    parameters={k:dict(value=values[k],status=status,label=label,unit='m' if k in PARAMETERS else 'count') for k,(value,status,label) in {**PARAMETERS,**COUNTS}.items()},
    features=features,checks=checks,sketch_count=len(native)+2,fully_constrained=True,pages=pages,
    native_projection=dict(page='CAD_Live',views=['ViewPlan','ViewStaff'],dimensions='created/verified by finish_in_freecad.FCMacro in GUI'),
    removed_features=['2F','stairs','lift','main screen'],
    phase_status='FINAL_PASS geometric fit passed; spatial design complete for this stage',
    privacy_intent='fully enclosed independent toilet rooms; all gender; shared wash area; wide doors, low/no threshold and assistance provision are planning intent',
    provisional_staff_and_toilet_parameters={k:values[k] for k in PARAMETERS if k.startswith(('Staff','Public','Stall','Large'))},
    unresolved=['future throughput inputs only'],construction_deepening_requested=False)
(ROOT/'cad_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
App.closeDocument(doc.Name)
print(json.dumps({'fcstd':str(fcstd),'revision':'v2-FINAL','sketch_count':report['sketch_count'],'fully_constrained':True,'checks':checks},ensure_ascii=False))
