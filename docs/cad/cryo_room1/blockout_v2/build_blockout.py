"""Independent native 3D blockout, inheriting the complete v2 pod geometry."""
from pathlib import Path
import sys,json,hashlib,re
import FreeCAD as A, Part, Sketcher
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'v2/room1_engineering_v2.FCStd'
BASELINE_HASH='d7c78d10c9c7ad39abcae5946de28f69b88b2abc461a52de8734ba1ede183bd7'
source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert source_hash==BASELINE_HASH,'v2 engineering source must remain unchanged'
baseline=json.loads((ROOT.parent/'v2/cad_validation.json').read_text(encoding='utf-8'))
doc=A.openDocument(str(SOURCE));doc.Label='Room 1 v2 | 3D空间验证 / 3.40m P'
# Publication pages remain in the original v2. The independent blockout contains
# native editable geometry and a separate height table, without snapshot pages.
for obj in list(doc.Objects)[::-1]:
 if obj.TypeId.startswith('TechDraw::'):doc.removeObject(obj.Name)
doc.removeObject('Sheets')
p=doc.Parameters
height_params={'ClearHeight':(3400,'室内暂定净高 / 本轮视觉测试'),
 'DoorHeight':(2400,'后墙门洞暂定净高'),
 'FloorThickness':(100,'地板显示厚度，位于Z=0以下'),
 'RoofThickness':(150,'顶板显示厚度，默认隐藏'),
 'ReferenceHeight':(1680,'纯尺度参考柱高'),
 'ReferenceDiameter':(450,'纯尺度参考柱直径')}
for key,(value,label) in height_params.items():
 p.addProperty('App::PropertyLength',key,'3D PROVISIONAL',label);setattr(p,key,value)
p.setExpression('CutWallHeight','Parameters.ClearHeight')
p.addProperty('App::PropertyString','BlockoutSourceCommit','来源');p.BlockoutSourceCommit='501140a94cdd17f79dcc03b32abfc7c544014820'
p.addProperty('App::PropertyString','EngineeringSourceCommit','来源');p.EngineeringSourceCommit='b8191893b746d127da957f61bcba63bfeda58b14'
p.addProperty('App::PropertyString','EngineeringSourceSHA256','来源');p.EngineeringSourceSHA256=source_hash
p.addProperty('App::PropertyString','Scope','说明');p.Scope='冻结v2平面与闭舱几何；墙高3.40m、门高2.40m仅为空间感测试；顶板默认隐藏。'
for row,(key,(value,label)) in enumerate(height_params.items(),22):
 for col,text in zip('ABCD',[key,f'=Parameters.{key} / (1000 mm)','3D PROVISIONAL',label]):doc.ParameterTable.set(col+str(row),text)
extra=doc.addObject('App::DocumentObjectGroup','BlockoutArchitecture');extra.Label='03 3D验证新增 | 门楣 / 地板 / 可隐藏顶板'
references=doc.addObject('App::DocumentObjectGroup','ScaleReference');references.Label='04 尺度参照 | 1.68m柱体'
def e(expr):
 return re.sub(r'\b[A-Z][A-Za-z]+\b',lambda m:'Parameters.'+m[0] if m[0] in p.PropertiesList else m[0],str(expr))
values={key:getattr(p,key).Value for key in p.PropertiesList if getattr(getattr(p,key), 'Value',None) is not None}
def num(expr):return float(eval(str(expr),{'__builtins__':{}},values))
def plate(name,label,w,d,x,y,z,height):
 pts=[('0','0'),(w,'0'),(w,d),('0',d)]
 sk=doc.addObject('Sketcher::SketchObject',name+'_Footprint')
 for a,b in zip(pts,pts[1:]+pts[:1]):sk.addGeometry(Part.LineSegment(A.Vector(num(a[0]),num(a[1]),0),A.Vector(num(b[0]),num(b[1]),0)),False)
 for i,a in enumerate(pts):
  sk.addConstraint(Sketcher.Constraint('Coincident',i,2,(i+1)%4,1))
  for axis,j in [('X',0),('Y',1)]:
   index=sk.addConstraint(Sketcher.Constraint('Distance'+axis,i,1,num(a[j])));sk.setExpression(f'Constraints[{index}]',e(a[j]))
 for axis,expr in zip('xyz',[x,y,z]):sk.setExpression('Placement.Base.'+axis,e(expr))
 sk.Label=label+' | 全约束足迹';extra.addObject(sk)
 obj=doc.addObject('Part::Extrusion',name);obj.Label=label;obj.Base=sk;obj.DirMode='Normal';obj.Solid=True;obj.setExpression('LengthFwd',e(height));extra.addObject(obj)
 return obj
plate('DoorLintel','后门门楣 | 洞口真实留空 / 高2.40m P','DoorWidth','Wall','(RoomWidth-DoorWidth)/2','RoomDepth-Wall','DoorHeight','ClearHeight-DoorHeight')
plate('Floor','地板 | 完成面Z=0','RoomWidth','RoomDepth','0','0','-FloorThickness','FloorThickness')
plate('Roof','顶板 | 默认隐藏 / Z=3.40m P','RoomWidth','RoomDepth','0','0','ClearHeight','RoofThickness')
person=doc.addObject('Part::Cylinder','ReferenceColumn');person.Label='尺度柱 | 高1.68m / 直径0.45m P'
person.setExpression('Radius','Parameters.ReferenceDiameter/2');person.setExpression('Height','Parameters.ReferenceHeight')
person.Placement.Base=A.Vector(5400,4250,0);references.addObject(person)
doc.recompute()
for key,entry in baseline['parameters'].items():
 if key!='CutWallHeight':assert abs(getattr(p,key).Value-entry['value']*1000)<1e-5,key
sketches=[o for o in doc.Objects if o.TypeId=='Sketcher::SketchObject']
solids=[o for o in doc.Objects if o.TypeId in ['Part::Extrusion','Part::Cylinder']]
assert len(sketches)==92 and all(o.FullyConstrained and o.Shape.isValid() for o in sketches)
assert len(solids)==90 and all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in solids)
doc.saveAs(str(ROOT/'room1_3d_blockout_v2.FCStd'));A.closeDocument(doc.Name)
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==source_hash
report=dict(revision='room1-v2-3d-blockout',task_source_commit='501140a94cdd17f79dcc03b32abfc7c544014820',
 task_blob='3d3331cf8cafb23a78ce58e3c57468fd612a1600',engineering_source_commit='b8191893b746d127da957f61bcba63bfeda58b14',
 source_plan_sha256=source_hash,source_plan_unchanged=True,source_plan_parameters_frozen=True,
 envelope_m=[21,9.5],interior_clear_m=[20.6,9.1],wall_height_m=3.4,door_clear_m=[1.4,2.4],
 pod_count=20,quadrant_counts=[5,5,5,5],pod_envelope_m=[1.05,2.3,1.0],pod_state='closed',
 longitudinal_aisle_m=2.4,cross_aisle_m=3.5,pod_gap_m=.7,side_margin_m=1.05,end_margin_m=.5,door_to_aisle_expansion_each_side_m=.5,
 height_parameters={k:dict(value_m=val/1000,status='PROVISIONAL',purpose=label) for k,(val,label) in height_params.items()},
 reference_column=dict(position_m=[5.4,4.25,0],height_m=1.68,diameter_m=.45,role='scale only; not an actor or furniture'),
 native_sketch_count=92,fully_constrained=True,native_solid_count=90,roof_default_hidden=True,
 render_status='pending',visual_review='pending')
(ROOT/'visual_blockout_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Built independent native blockout: 90 solids, 92 fully constrained sketches; source v2 hash unchanged')
