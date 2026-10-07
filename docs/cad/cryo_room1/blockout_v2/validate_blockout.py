"""Independent saved-file readback; leave the v2 baseline and blockout untouched."""
from pathlib import Path
import json,hashlib,sys
import FreeCAD as A,Part
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parent
FILE=ROOT/'room1_3d_blockout_v2.FCStd';SOURCE=ROOT.parent/'v2/room1_engineering_v2.FCStd'
before={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in [FILE,SOURCE]}
assert before[str(SOURCE)]=='d7c78d10c9c7ad39abcae5946de28f69b88b2abc461a52de8734ba1ede183bd7'
doc=A.openDocument(str(FILE));source=A.openDocument(str(SOURCE))
original=json.loads((ROOT.parent/'v2/cad_validation.json').read_text(encoding='utf-8'))
for key,entry in original['parameters'].items():
 if key!='CutWallHeight':assert abs(getattr(doc.Parameters,key).Value-entry['value']*1000)<1e-5,key
sketches=[o for o in doc.Objects if o.TypeId=='Sketcher::SketchObject']
solids=[o for o in doc.Objects if o.TypeId in ['Part::Extrusion','Part::Cylinder']]
assert len(sketches)==92 and all(o.FullyConstrained and o.Shape.isValid() for o in sketches)
assert len(solids)==90 and all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in solids)
invalid=[o.Name for o in doc.Objects if any('invalid' in str(s).lower() or 'error' in str(s).lower() for s in o.State)]
assert not invalid,invalid
unchanged=[]
for pod in original['pods']:
 for kind in ['Base','Body','Lid','Window']:
  name=pod['id']+'_'+kind;a=source.getObject(name).Shape;b=doc.getObject(name).Shape
  assert a.cut(b).Volume+b.cut(a).Volume<1e-3,name
  for axis in ['XMin','YMin','ZMin','XLength','YLength','ZLength']:assert abs(getattr(a.BoundBox,axis)-getattr(b.BoundBox,axis))<1e-5,(name,axis)
  unchanged.append(name)
for name in ['Wall_Front','Wall_Left','Wall_Right','Wall_RearLeft','Wall_RearRight']:
 a=source.getObject(name).Shape.BoundBox;b=doc.getObject(name).Shape.BoundBox
 for axis in ['XMin','YMin','XLength','YLength']:assert abs(getattr(a,axis)-getattr(b,axis))<1e-5,(name,axis)
 assert abs(b.ZMin)<1e-5 and abs(b.ZMax-3400)<1e-5
assert source.AuthPanel.Shape.cut(doc.AuthPanel.Shape).Volume+doc.AuthPanel.Shape.cut(source.AuthPanel.Shape).Volume<1e-3
collisions=[]
for i,a in enumerate(solids):
 for b in solids[i+1:]:
  aa,bb=a.Shape.BoundBox,b.Shape.BoundBox
  if all(min(getattr(aa,k+'Max'),getattr(bb,k+'Max'))>max(getattr(aa,k+'Min'),getattr(bb,k+'Min'))+1e-6 for k in 'XYZ'):
   volume=a.Shape.common(b.Shape).Volume
   if volume>1e-4:collisions.append(dict(a=a.Name,b=b.Name,volume_mm3=volume))
assert not collisions,collisions
door=Part.makeBox(1399.98,199.98,2399.98,A.Vector(9800.01,9300.01,.01))
wall_shapes=[o.Shape for o in solids if o.Name.startswith('Wall_') or o.Name=='DoorLintel']
assert sum(s.common(door).Volume for s in wall_shapes)<1e-4,'Door opening must be truly empty'
lintel=doc.DoorLintel.Shape.BoundBox
assert all(abs(a-b)<1e-5 for a,b in zip([lintel.XMin,lintel.XLength,lintel.YLength,lintel.ZMin,lintel.ZMax],[9800,1400,200,2400,3400]))
assert abs(doc.Floor.Shape.BoundBox.ZMax)<1e-5 and abs(doc.Floor.Shape.BoundBox.ZMin+100)<1e-5
assert abs(doc.Roof.Shape.BoundBox.ZMin-3400)<1e-5 and abs(doc.Roof.Shape.BoundBox.ZMax-3550)<1e-5
# Camera positions are reference points only: never carve or move geometry to
# make a shot. Validate each human viewpoint lies outside all physical solids.
cameras=json.loads((ROOT/'cameras.json').read_text(encoding='utf-8'));camera_checks=[]
for camera in cameras:
 if camera['projection']!='perspective':continue
 point=A.Vector(*[v*1000 for v in camera['position_m']]);hits=[o.Name for o in solids if o.Shape.isInside(point,1e-5,False)]
 assert not hits,(camera['name'],hits)
 assert camera['position_m'][2]==1.6
 camera_checks.append(dict(name=camera['name'],eye_height_m=1.6,inside_any_solid=False))
# Physically demonstrate available room around an upright scale footprint.
# This is a static clearance test; it does not simulate sitting, turning or lids.
for x,y in [(2650,1850),(10500,8700),(10500,4750)]:
 probe=Part.makeCylinder(225,1680,A.Vector(x,y,0))
 assert sum(probe.common(o.Shape).Volume for o in solids if o.Name!='ReferenceColumn')<1e-4,(x,y)
tests=[]
for key,trial,checks in [
 ('ClearHeight',3500,[('Wall_Front','ZMax',3500),('DoorLintel','ZMax',3500),('Roof','ZMin',3500)]),
 ('DoorHeight',2500,[('DoorLintel','ZMin',2500),('DoorLintel','ZLength',900)]),
 ('FloorThickness',120,[('Floor','ZMin',-120),('Floor','ZMax',0)]),
 ('RoofThickness',200,[('Roof','ZMax',3600)]),
 ('ReferenceHeight',1700,[('ReferenceColumn','ZMax',1700)])]:
 old=getattr(doc.Parameters,key).Value;setattr(doc.Parameters,key,trial);doc.recompute()
 measured=[]
 for name,axis,expected in checks:
  got=getattr(doc.getObject(name).Shape.BoundBox,axis);assert abs(got-expected)<1e-5,(key,name,axis,got,expected)
  measured.append(dict(object=name,axis=axis,measured_mm=got))
 tests.append(dict(parameter=key,trial_mm=trial,measurements=measured,passed=True))
 setattr(doc.Parameters,key,old);doc.recompute()
A.closeDocument(source.Name);A.closeDocument(doc.Name)
for path,sha in before.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha
saved=dict(saved_readback_passed=True,fcstd_sha256=before[str(FILE)],v2_source_sha256=before[str(SOURCE)],source_file_unchanged=True,
 frozen_xy_parameters=True,unchanged_pod_layers=len(unchanged),pod_solids_identical_to_v2_without_translation=True,
 original_wall_xy_footprints_unchanged=True,auth_panel_shape_and_position_unchanged=True,
 native_sketch_count=92,native_solid_count=90,fully_constrained=True,invalid_objects=invalid,
 positive_volume_collisions=collisions,real_door_opening_verified=True,door_clear_m=[1.4,2.4],lintel_bottom_m=2.4,
 static_scale_column_diameter_m=.45,static_scale_column_fits_at_pod_gap_and_entry_and_cross_center=True,
 gap_after_static_45cm_column_each_side_m=.125,door_after_static_45cm_column_each_side_m=.475,
 human_camera_positions=camera_checks,parameter_edit_tests=tests,scope='static closed-pod geometry; not ergonomic or opening sweep certification')
(ROOT/'qa/saved_validation.json').write_text(json.dumps(saved,ensure_ascii=False,indent=2),encoding='utf-8')
report=json.loads((ROOT/'visual_blockout_validation.json').read_text(encoding='utf-8'));report['geometry_verification']=saved
(ROOT/'visual_blockout_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:saved[k] for k in ['saved_readback_passed','unchanged_pod_layers','positive_volume_collisions','real_door_opening_verified','fcstd_sha256']},indent=2))
