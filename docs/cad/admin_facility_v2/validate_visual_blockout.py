"""Read native 3D shapes, check collisions/LOS and exercise parameters in memory."""
from pathlib import Path
import json,hashlib,math
import FreeCAD as App
import Part
ROOT=Path(__file__).resolve().parent
target=ROOT/'admin_facility_3d_blockout_v1.FCStd'
before=hashlib.sha256(target.read_bytes()).hexdigest()
doc=App.openDocument(str(target));doc.recompute()
objects=[o for o in doc.Objects if o.Name.startswith('B3_')]
assert len(objects)==302
assert all(o.Shape.isValid() and o.Shape.Volume>0 for o in objects)
assert not [o.Name for o in objects if any(s in o.Name for s in ['Lift','Stair','Floor2','Cabinet'])]
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==v['sha256'] for k,v in manifest.items())
physical=[o for o in objects if o.Name not in ['B3_Roof','B3_Floor']]
collisions=[];inherited=[];intentional=[]
def overlaps(a,b):
 return all(min(getattr(a,s+'Max'),getattr(b,s+'Max'))-max(getattr(a,s+'Min'),getattr(b,s+'Min'))>1e-4 for s in ['X','Y','Z'])
for i,a in enumerate(physical):
 for b in physical[i+1:]:
  if not overlaps(a.Shape.BoundBox,b.Shape.BoundBox):continue
  volume=a.Shape.common(b.Shape).Volume
  if volume<1.:continue
  record={'objects':[a.Name,b.Name],'volume_m3':volume/1e9}
  if a.BlockRole==b.BlockRole=='wall':inherited.append(record)
  elif (a.Name.endswith('_Back') and a.BlockRole=='chair' and b.BlockRole=='chair') or (b.Name.endswith('_Back') and a.BlockRole=='chair' and b.BlockRole=='chair'):intentional.append(record)
  else:collisions.append(record)
wall_shapes=[o for o in physical if o.BlockRole=='wall']
def visible(pos,target):
 line=Part.makeLine(App.Vector(*[x*1000 for x in pos]),App.Vector(*[x*1000 for x in target]))
 hits=[]
 for o in wall_shapes:
  intersection=line.common(o.Shape)
  if not intersection.isNull() and intersection.Length>.1:hits.append(o.Name)
 return {'unobstructed':not hits,'wall_occluders':hits}
los={}
for x in [3.25,16.25,29.25,35.75,48.75,61.75]:
 eye=(x,9,1.6);result={}
 for name in ['GuideLeft','GuideRight']:
  b=doc.getObject('B3_'+name).Shape.BoundBox;result[name]=visible(eye,((b.XMin+b.XMax)/2000,b.YMin/1000,1.6))
 result['rear_exits']=[visible(eye,(x,44.69,1.6)) for x in [10.5,32.5,54.5]]
 los[str(x)]=result
parameter_tests=[]
for key,new in [('StaffX',23500),('PublicWCWidth',8500),('Partition',250)]:
 old=getattr(doc.Parameters,key);setattr(doc.Parameters,key,new);doc.recompute()
 for o in objects:
  if o.TypeId=='Part::Extrusion':
   b=o.Shape.BoundBox;s=o.Base.Shape.BoundBox
   assert all(abs(getattr(b,k)-getattr(s,k))<1e-4 for k in ['XMin','XMax','YMin','YMax']),o.Name
 assert all(o.Shape.isValid() for o in objects)
 parameter_tests.append({'parameter':key,'trial_mm':new,'XY_follow_native_plan':True});setattr(doc.Parameters,key,old);doc.recompute()
old=doc.BlockParameters.WallHeight;doc.BlockParameters.WallHeight=6000;doc.recompute()
assert all(abs(o.Shape.BoundBox.ZMax-6000)<1e-5 for o in wall_shapes)
parameter_tests.append({'parameter':'WallHeight','trial_mm':6000,'all_walls_and_lintels_follow':True});doc.BlockParameters.WallHeight=old;doc.recompute()
App.closeDocument(doc.Name)
assert hashlib.sha256(target.read_bytes()).hexdigest()==before
result={'native_3d_shapes_valid':302,'original_28_artifacts_unchanged':True,'new_entity_collisions':collisions,'inherited_wall_overlap_records':inherited,'intentional_furniture_join_records':intentional,'parameter_tests':parameter_tests,'line_of_sight_tests':los,'source_file_unchanged_by_readback':True,'fcstd_sha256':before,'collision_note':'Positive-volume intersections tested in native OCC. Shared inherited wall strips are recorded separately; coplanar contact has zero volume.'}
(ROOT/'evidence/visual_blockout/native_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'shapes':302,'new_entity_collisions':collisions,'inherited_wall_overlaps':len(inherited),'parameter_tests':parameter_tests,'line_of_sight_tests':los}))
