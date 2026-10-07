"""Read back actual saved 3D model, preserving all source CAD; check XY and door voids."""
from pathlib import Path
import json,hashlib,math
import FreeCAD as A,Part
ROOT=Path(__file__).resolve().parent;d=json.loads((ROOT/'sources/accepted_inset_layout.snapshot.json').read_text(encoding='utf-8'));report=json.loads((ROOT/'blockout_validation.json').read_text(encoding='utf-8'))
doc=A.openDocument(str(ROOT/'standard_floor_blockout_v3_frozen.FCStd'));p=doc.Parameters
assert p.SourceCommit=='b53aa9b8e38c7c423703dd946c2ba88d44b9ab37'
all_shapes=[o for o in doc.Objects if hasattr(o,'Shape')];assert all(not o.Shape.isNull() and o.Shape.isValid() for o in all_shapes)
structural=[o.Shape for o in doc.Objects if hasattr(o,'Role') and o.Role in ['wall','lintel','stair_wall_upper']]
def probe(r,z,h):return Part.makeBox((r['x2']-r['x1'])*1000,(r['y2']-r['y1'])*1000,h*1000,A.Vector(r['x1']*1000,r['y1']*1000,z*1000))
def overlap(shape):
 b=shape.BoundBox;total=0
 for s in structural:
  a=s.BoundBox
  if min(a.XMax,b.XMax)>max(a.XMin,b.XMin)+1e-5 and min(a.YMax,b.YMax)>max(a.YMin,b.YMin)+1e-5 and min(a.ZMax,b.ZMax)>max(a.ZMin,b.ZMin)+1e-5:total+=shape.common(s).Volume
 return total
xy_error=0
for r in d['walls']:
 b=doc.getObject(r['id']).Shape.BoundBox
 xy_error=max(xy_error,max(abs(a-z) for a,z in zip([b.XMin,b.YMin,b.XMax,b.YMax],[r[k]*1000 for k in ['x1','y1','x2','y2']])))
assert xy_error<1e-4
doors=[]
for door in d['doors']:
 if door['kind']=='personnel_exclusion':continue
 x,y,w=door['x'],door['y'],door['width'];eps=.00001
 r=dict(x1=x-w/2+eps,x2=x+w/2-eps,y1=y-.1+eps,y2=y+.1-eps) if door['orientation']=='H' else dict(x1=x-.1+eps,x2=x+.1-eps,y1=y-w/2+eps,y2=y+w/2-eps)
 vol=overlap(probe(r,.01,2.38999));assert vol<.01,(door,vol);doors.append(dict(id=door['id'],kind=door['kind'],width_m=w,clear_height_m=2.4,structural_overlap_mm3=vol))
for r in d['corridors']:
 q={k:r[k]+(.00001 if k.endswith('1') else -.00001) for k in ['x1','y1','x2','y2']};assert overlap(probe(q,.01,2.38999))<.01,r
links=[o for o in doc.Objects if o.TypeId=='App::Link'];assert len(links)==48 and sum(o.PodCount for o in links)==960
full=0
for r in d['rooms']:
 o=doc.getObject(r['id'].replace('-','_')+'_Pods');bb=o.Shape.BoundBox
 assert bb.XMin>=r['x1']*1000+200 and bb.XMax<=r['x2']*1000-200 and bb.YMin>=r['y1']*1000+200 and bb.YMax<=r['y2']*1000-200,(r['id'],bb)
 assert abs(bb.ZMin)<1e-4 and abs(bb.ZMax-1000)<1e-4
 expected=80 if r['id'] in report['full_pod_rooms'] else 20;assert len(o.Shape.Solids)==expected,(r['id'],len(o.Shape.Solids));full+=expected==80
 assert o.LinkedObject.Document==doc
assert full==4
steps=[o for o in doc.Objects if hasattr(o,'Role') and o.Role=='stair_tread'];assert len(steps)==88
for side in ['North','South','West','East']:
 stair=next(r for r in d['stairs'] if r['side']==side)
 if side in ['North','South']:assert stair['y1']>=d['parameters']['FloorSouth']-1e-7 and stair['y2']<=d['parameters']['FloorNorth']+1e-7
 for o in [o for o in steps if o.Name.startswith(side)]:
  b=o.Shape.BoundBox;assert b.XMin>=stair['x1']*1000+200-1e-4 and b.XMax<=stair['x2']*1000-200+1e-4 and b.YMin>=stair['y1']*1000+200-1e-4 and b.YMax<=stair['y2']*1000-200+1e-4
assert all(not o.Visibility for o in doc.Roofs.Group)
count=len(doc.Objects);A.closeDocument(doc.Name)
source=ROOT.parents[1]/'cryo_room1/blockout_v2/room1_3d_blockout_v2.FCStd';assert hashlib.sha256(source.read_bytes()).hexdigest()==report['room1_source_sha256']
assert hashlib.sha256((ROOT.parent/'v3_frozen/floor_layout.json').read_bytes()).hexdigest()==report['plan_json_sha256']
renders=json.loads((ROOT/'qa/render_validation.json').read_text(encoding='utf-8'));assert 'error' not in renders and len(renders['views'])==13
report.update(native_file_reopened=True,all_native_shapes_valid=True,native_object_count=count,wall_xy_maximum_error_mm=xy_error,all_doors_and_bypass_full_height_clear=doors,personnel_corridors_full_height_clear=8,
 self_contained_linked_templates=True,all_48_room_pod_envelopes_inside_room_net_bounds=True,full_pod_rooms_verified=4,simple_pod_rooms_verified=44,stair_treads_inside_wells=True,source_cad_unchanged=True,render_status='passed',visual_review='pending')
(ROOT/'blockout_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:report[k] for k in ['native_file_reopened','native_object_count','self_contained_linked_templates','personnel_corridors_full_height_clear']},ensure_ascii=False))
