"""Independent readback of saved FCStd; no mutation or re-save."""
from pathlib import Path
import json,sys,hashlib
import FreeCAD as A,Part
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parent
path=ROOT/'room1_engineering_v1.FCStd';doc=A.openDocument(str(path))
report=json.loads((ROOT/'cad_validation.json').read_text(encoding='utf-8'))
for k,p in report['parameters'].items():assert abs(getattr(doc.Parameters,k).Value-p['value']*1000)<1e-5,k
sketches=[o for o in doc.Objects if o.TypeId=='Sketcher::SketchObject'];solids=[o for o in doc.Objects if o.TypeId=='Part::Extrusion']
assert len(sketches)==89 and len(solids)==86
assert all(o.FullyConstrained and o.Shape.isValid() for o in sketches)
assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in solids)
invalid=[o.Name for o in doc.Objects if any('invalid' in str(s).lower() or 'error' in str(s).lower() for s in o.State)]
assert not invalid,invalid
for p in report['pods']:
 bb=Part.makeCompound([doc.getObject(p['id']+'_'+s).Shape for s in ['Base','Body','Lid','Window']]).BoundBox
 for axis,val in [('XMin',p['x']),('YMin',p['y']),('XLength',p['w']),('YLength',p['d']),('ZLength',p['h'])]:assert abs(getattr(bb,axis)-val*1000)<1e-5,(p['id'],axis)
collisions=[]
for i,a in enumerate(solids):
 for b in solids[i+1:]:
  aa,bb=a.Shape.BoundBox,b.Shape.BoundBox
  if all(min(getattr(aa,k+'Max'),getattr(bb,k+'Max'))>max(getattr(aa,k+'Min'),getattr(bb,k+'Min'))+1e-6 for k in 'XYZ'):
   vol=a.Shape.common(b.Shape).Volume
   if vol>1e-4:collisions.append(dict(a=a.Name,b=b.Name,mm3=vol))
assert not collisions
dims=[o for o in doc.Objects if o.TypeId=='TechDraw::DrawViewDimension'];assert len(dims)==5,len(dims)
expect={'Dim_OuterWidth':20000,'Dim_OuterDepth':9500,'Dim_DoorOpening':1600,'Dim_LongAisle':1600,'Dim_CrossAisle':3500}
for name,val in expect.items():assert abs(float(doc.getObject(name).getRawValue())-val)<1e-5,(name,val)
out=dict(saved_readback_passed=True,native_sketch_count=len(sketches),fully_constrained=True,native_solid_count=len(solids),
 pod_envelope_readback=True,positive_volume_collisions=collisions,native_dimensions_mm=expect,invalid_objects=invalid,
 fcstd_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
(ROOT/'qa/saved_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2));A.closeDocument(doc.Name)
