"""Read back final FCStd in native FreeCAD; exercise expressions without saving."""
from pathlib import Path
import hashlib,json,math,re
import FreeCAD as App
from plan_layout import PARAMETERS,COUNTS,make_layout,check_layout
ROOT=Path(__file__).resolve().parent
target=ROOT/'admin_facility_v2.FCStd';before=hashlib.sha256(target.read_bytes()).hexdigest()
gui=json.loads((ROOT/'qa/gui_review.json').read_text(encoding='utf-8'));assert 'error' not in gui,gui
doc=App.openDocument(str(target));doc.recompute()
def validate_geometry(overrides=None):
    v,features=make_layout(overrides);checks=check_layout(v,features)
    for f in features:
        s=doc.getObject(f['name']);assert s.FullyConstrained and s.Shape.isValid(),s.Name
        a=f['values'];kind=f['kind'];b=s.Shape.BoundBox
        if kind=='rect':expected=[a['x'],a['y'],a['x']+a['w'],a['y']+a['d']]
        elif kind=='line':expected=[min(a['x1'],a['x2']),min(a['y1'],a['y2']),max(a['x1'],a['x2']),max(a['y1'],a['y2'])]
        elif kind=='circle':expected=[a['x']-a['r'],a['y']-a['r'],a['x']+a['r'],a['y']+a['r']]
        else:
            start=math.radians(a['angle']);pts=[(a['x']+a['r']*math.cos(start+j*math.pi/2),a['y']+a['r']*math.sin(start+j*math.pi/2)) for j in [0,1]]
            expected=[min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)]
        actual=[b.XMin,b.YMin,b.XMax,b.YMax]
        assert all(abs(x-y*1000)<1e-4 for x,y in zip(actual,expected)),(s.Name,actual,expected)
    return checks
checks=validate_geometry()
sketches=[s for s in doc.Objects if s.TypeId=='Sketcher::SketchObject'];assert len(sketches)==250
assert all(s.FullyConstrained and s.Shape.isValid() for s in sketches)
assert not any(re.search(r'Floor2|2F|Lift|Stair|^WS_|Screen|Cabinet',s.Name) for s in doc.Objects)
for code in ['A201','A202','A203']:
    p=doc.getObject(code);assert len(p.Views)==1
    s=p.Views[0];assert s.TypeId=='TechDraw::DrawViewSymbol' and s.Scale==10 and s.X.Value==297 and s.Y.Value==210 and s.LockPosition
for dim in gui['native_dimensions']:
    d=doc.getObject(dim['name']);assert d.Type==dim['type'] and d.ShowUnits and d.LockPosition
    assert list(d.References2D[0][1])==['Vertex'+str(i) for i in dim['vertices']]
    assert not d.Arbitrary
assert len([s for s in doc.CAD_Live.Views if s.TypeId=='TechDraw::DrawViewDimension'])==4
assert len(doc.ViewPlan.Source)==248
for key,(value,status,label) in PARAMETERS.items():assert abs(getattr(doc.Parameters,key).Value-value*1000)<1e-5,key
tested=[]
for key,value in [('StaffY',22.),('StaffX',23.75),('PublicWCWidth',8.5),('OuterWall',.35),('GateWide',1.3),('EnvelopeWidth',66.)]:
    old=getattr(doc.Parameters,key).Value;setattr(doc.Parameters,key,value*1000);doc.recompute();validate_geometry({key:value})
    assert all(s.FullyConstrained for s in sketches)
    tested.append({'parameter':key,'test_value_m':value,'all_native_features_match_layout':True})
    setattr(doc.Parameters,key,old);doc.recompute()
validate_geometry()
errors=[s.Name for s in doc.Objects if any('error' in str(q).lower() or 'invalid' in str(q).lower() for q in s.State)];assert not errors,errors
assert abs(doc.AreaReview.GrossArea.getValueAs('m^2').Value-2925)<1e-8
assert abs(doc.AreaReview.StaffArea.getValueAs('m^2').Value-216)<1e-8
assert abs(doc.AreaReview.PublicWCCombinedArea.getValueAs('m^2').Value-160)<1e-8
App.closeDocument(doc.Name);assert hashlib.sha256(target.read_bytes()).hexdigest()==before
report=dict(revision='v2-R1',saved_fcstd_sha256=before,fully_constrained_sketches=250,
    native_shape_readback='all 248 features match metre layout',parameter_tests=tested,cad_errors=errors,
    actual_placement_verified=True,obstacle_fit_verified=True,geometric_checks=checks,
    toilet_code_compliance_verified=False,egress_verified=False,throughput_verified=False,file_unchanged_by_validation=True)
(ROOT/'qa/saved_model_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
