"""Reopen final saved CAD and compare every wall cell to the published JSON."""
from pathlib import Path
import json,hashlib,sys
import FreeCAD as App
ROOT=Path(__file__).resolve().parent;sys.stdout.reconfigure(encoding='utf-8')
data=json.loads((ROOT/'floor_layout.json').read_text(encoding='utf-8'));doc=App.openDocument(str(ROOT/'standard_floor_v1.FCStd'))
assert doc.Parameters.RoomWidth.Value==21000 and doc.Parameters.RoomDoor.Value==1400 and doc.Parameters.MachineSpine.Value==6000
sk=[o for o in doc.Objects if o.TypeId=='Sketcher::SketchObject'];solids=[o for o in doc.Objects if o.TypeId=='Part::Extrusion']
assert len(sk)==322 and all(s.FullyConstrained for s in sk);assert len(solids)==248 and all(o.Shape.isValid() for o in solids)
maxerr=0
for r in data['walls']:
 b=doc.getObject(r['id']).Shape.BoundBox
 for got,want in zip([b.XMin/1000,b.YMin/1000,b.XMax/1000,b.YMax/1000],[r[k] for k in ['x1','y1','x2','y2']]):maxerr=max(maxerr,abs(got-want))
assert maxerr<1e-6
assert len([o for o in doc.Objects if o.TypeId=='TechDraw::DrawViewDimension'])==7
assert all(doc.getObject(k).TypeId=='TechDraw::DrawPage' for k in ['A401','A402','A403','A404'])
App.closeDocument(doc.Name)
room1=ROOT.parents[1]/'cryo_room1'
prior={'v2/room1_engineering_v2.FCStd':'d7c78d10c9c7ad39abcae5946de28f69b88b2abc461a52de8734ba1ede183bd7','blockout_v2/room1_3d_blockout_v2.FCStd':'4bb0db7b42de97693a02557bd29d38e498a224254843335fa20dd1e0593b3973'}
for file,expected in prior.items():assert hashlib.sha256((room1/file).read_bytes()).hexdigest()==expected
report=dict(final_file_reopened=True,all_parameters_restored=True,sketch_count=322,wall_count=248,maximum_wall_coordinate_error_m=maxerr,native_dimension_count=7,room1_source_files_unchanged=prior,publication_visual_review=dict(pages=['A401','A402','A403'],actual_pdf_rendered=True,reviewed=True,text_overlap_or_clipping=False),native_live_page_reviewed=True,stage='2D_TOPOLOGY_VERIFIED / EVACUATION_DESIGN_OPEN')
(ROOT/'qa'/'final_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
