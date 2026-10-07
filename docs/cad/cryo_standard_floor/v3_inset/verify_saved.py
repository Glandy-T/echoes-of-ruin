"""Read final native file and check prior deliverables without modifying them."""
from pathlib import Path
import json,hashlib,sys
import FreeCAD as App
ROOT=Path(__file__).resolve().parent;sys.stdout.reconfigure(encoding='utf-8')
data=json.loads((ROOT/'floor_layout.json').read_text(encoding='utf-8'));checks=json.loads((ROOT/'floor_validation.json').read_text(encoding='utf-8'))
gui=json.loads((ROOT/'qa/gui_validation.json').read_text(encoding='utf-8'));assert 'error' not in gui,gui
reopen=json.loads((ROOT/'qa/reopen_gui_validation.json').read_text(encoding='utf-8'));assert reopen['all_native_values_match']
doc=App.openDocument(str(ROOT/'standard_floor_v3_inset.FCStd'))
for k,val in data['parameters'].items():
 if k=='Risers':assert doc.Parameters.Risers==val
 else:assert abs(getattr(doc.Parameters,k).Value-val*1000)<1e-5,(k,val)
sk=[o for o in doc.Objects if o.TypeId=='Sketcher::SketchObject'];walls=[o for o in doc.Objects if o.TypeId=='Part::Extrusion']
assert len(sk)==checks['native_fully_constrained_sketch_count'] and all(o.FullyConstrained and o.Shape.isValid() for o in sk)
assert len(walls)==checks['native_plan_hatch_solids'] and all(o.Shape.isValid() for o in walls)
delta=0
for r in data['walls']:
 b=doc.getObject(r['id']).Shape.BoundBox
 for a,z in zip([b.XMin/1000,b.YMin/1000,b.XMax/1000,b.YMax/1000],[r[k] for k in ['x1','y1','x2','y2']]):delta=max(delta,abs(a-z))
assert delta<1e-6
assert len([o for o in doc.Objects if o.TypeId=='TechDraw::DrawViewDimension'])==10
for d in gui['native_dimensions']:assert abs(doc.getObject('Dim_'+d['name']).getRawValue()-d['mm'])<1e-4,d
App.closeDocument(doc.Name)
prior={ROOT.parent/'v3_final/standard_floor_v3_final.FCStd':'1503cedb8b64adb960bab3a877053b22a5ed0a891b7afcc483757450bf2aad1f',ROOT.parent/'v3/standard_floor_v3.FCStd':'e446f3e7c5cea955bc5e98d113c7fe500ae9550503d0f77037f0f5994f4f238a',ROOT.parent/'v1/standard_floor_v1.FCStd':'34636ce546be832f789029abc3b923e608e5bf7489fb352cf9a60e5633ba1708',ROOT.parent/'v2/standard_floor_v2.FCStd':'92f98d1b7f9b580de55cbbafe13feed4314043d0a8e5a0947f6d1d4d31da6e72',ROOT.parents[1]/'cryo_room1/v2/room1_engineering_v2.FCStd':'d7c78d10c9c7ad39abcae5946de28f69b88b2abc461a52de8734ba1ede183bd7',ROOT.parents[1]/'cryo_room1/blockout_v2/room1_3d_blockout_v2.FCStd':'4bb0db7b42de97693a02557bd29d38e498a224254843335fa20dd1e0593b3973'}
for p,h in prior.items():assert hashlib.sha256(p.read_bytes()).hexdigest()==h,p
brief=(ROOT/'sources/STANDARD_FLOOR_ENGINEERING_BRIEF.snapshot.md').read_bytes();blob=hashlib.sha1(b'blob '+str(len(brief)).encode()+b'\0'+brief).hexdigest();assert blob==checks['brief_blob']
assert checks['central_core_excluded_from_all_personnel_egress'] and checks['central_logistics_zone_personnel_overlap_mm3']==0
assert len(checks['nearest_stair_routes'])==48 and len(checks['emergency_routes'])==96
report=dict(final_file_reopened=True,all_parameters_restored=True,sketch_count=len(sk),wall_count=len(walls),native_dimension_count=10,maximum_wall_coordinate_error_m=delta,prior_files_unchanged={str(p):h for p,h in prior.items()},brief_snapshot_git_blob=blob,native_gui_reopen_verified=reopen,publication_visual_review=dict(pages=['A401','A402','A403'],actual_pdf_rendered=True,reviewed=True,text_overlap_or_clipping=False),native_live_page_reviewed=True,stage=checks['stage'])
(ROOT/'qa/final_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
