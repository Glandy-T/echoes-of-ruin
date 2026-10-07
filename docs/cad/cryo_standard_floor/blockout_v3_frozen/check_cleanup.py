"""Read actual saved solids: narrowly scoped 0E repairs and frozen layout invariants."""
from pathlib import Path
import json,math,hashlib
import FreeCAD as A,Part
from layout import subtract_rectangles
R=Path(__file__).resolve().parent
old=json.loads((R/'sources/before_cleanup_layout.snapshot.json').read_text(encoding='utf-8'))
new=json.loads((R/'sources/accepted_inset_layout.snapshot.json').read_text(encoding='utf-8'))
keys=['parameters','rooms','corridors','elevator_nodes','stairs','doors','references','freight_shafts','waiting_bays','transfer','plenums','machine_work_areas','routes','bounds','main_envelope_m','maximum_envelope_m']
for key in keys:assert old[key]==new[key],key
def prism(r,z=-.1,h=.1):return Part.makeBox((r['x2']-r['x1'])*1000,(r['y2']-r['y1'])*1000,h*1000,A.Vector(r['x1']*1000,r['y1']*1000,z*1000))
def union(rs):return Part.makeCompound([prism(r) for r in rs])
added_cells=subtract_rectangles(new['walls'],old['walls']);removed_cells=subtract_rectangles(old['walls'],new['walls'])
added=union(added_cells)
removed_volume=sum((r['x2']-r['x1'])*(r['y2']-r['y1'])*1e8 for r in removed_cells)
patches=[dict(x1=-2.6,x2=-2.4,y1=28.,y2=28.2),dict(x1=188.8,x2=189.,y1=28.,y2=28.2)]
expected=union(patches)
assert removed_volume<.01 and abs(added.Volume-8000000)<.1
assert added.cut(expected).Volume<.01 and expected.cut(added).Volume<.01
doc=A.openDocument(str(R/'standard_floor_blockout_v3_frozen.FCStd'))
floors=[o.Shape for o in doc.Objects if hasattr(o,'Role') and o.Role=='floor']
surfaces=[o.Shape for o in doc.Objects if hasattr(o,'Role') and o.Role in ['floor','personnel_floor','machine_floor']]
def overlap(probe,shapes):
 b=probe.BoundBox;total=0.
 for s in shapes:
  a=s.BoundBox
  if min(a.XMax,b.XMax)>max(a.XMin,b.XMin)+1e-5 and min(a.YMax,b.YMax)>max(a.YMin,b.YMin)+1e-5 and min(a.ZMax,b.ZMax)>max(a.ZMin,b.ZMin)+1e-5:total+=probe.common(s).Volume
 return total
shafts=[]
for r in new['passenger_shaft_voids']:
 q={k:r[k]+(.000001 if k.endswith('1') else -.000001) for k in ['x1','y1','x2','y2']}
 vol=overlap(prism(q,-.11,.12),surfaces);assert vol<.01,(r['zone'],vol)
 car=next(o for o in doc.LiftCars.Group if o.Shape.BoundBox.XMin>=r['x1']*1000-.01 and o.Shape.BoundBox.XMax<=r['x2']*1000+.01 and o.Shape.BoundBox.YMin>=r['y1']*1000-.01 and o.Shape.BoundBox.YMax<=r['y2']*1000+.01)
 shafts.append(dict(zone=r['zone'],clear_void_m={k:r[k] for k in ['x1','y1','x2','y2']},structural_and_walk_surface_overlap_mm3=vol,independent_car_floor=car.Name))
galleries=[]
for r in new['protected_gallery_floors']:
 p=prism(r);missing=p.Volume-overlap(p,floors);assert abs(missing)<.1,(r,missing)
 galleries.append(dict(bounds_m={k:r[k] for k in ['x1','y1','x2','y2']},uncovered_slab_volume_mm3=max(0,missing)))
# Actual 450mm path footprint must be supported by saved structural slabs,
# excluding the intentional edge entering the independently modeled elevator car.
def capsule(a,b):
 x1,y1=a['x'],a['y'];x2,y2=b['x'],b['y'];rad=.225;length=math.hypot(x2-x1,y2-y1)
 caps=[Part.makeCylinder(rad*1000,100,A.Vector(x*1000,y*1000,-100)) for x,y in [(x1,y1),(x2,y2)]]
 if length>1e-9:
  nx,ny=-(y2-y1)/length*rad,(x2-x1)/length*rad;ps=[A.Vector(x*1000,y*1000,-100) for x,y in [(x1+nx,y1+ny),(x2+nx,y2+ny),(x2-nx,y2-ny),(x1-nx,y1-ny)]];caps.append(Part.Face(Part.makePolygon(ps+[ps[0]])).extrude(A.Vector(0,0,100)))
 return caps[0].multiFuse(caps[1:])
supported=[]
for i,e in enumerate(new['routes']['edges']):
 if e['kind'] not in ['daily','emergency','evacuation_outward'] or e['length']<1e-9:continue
 a=new['routes']['nodes'][e['a']];b=new['routes']['nodes'][e['b']]
 if 'lift' in [a['role'],b['role']]:continue
 p=capsule(a,b);missing=p.Volume-overlap(p,floors);assert abs(missing)<.2,(e,missing)
 supported.append(i)
for patch in patches:
 p=prism(patch,0,3.4);walls=[o.Shape for o in doc.Objects if hasattr(o,'Role') and o.Role=='wall'];assert abs(overlap(p,walls)-p.Volume)<.1
assert len(doc.RoomPods.Group)==48 and sum(o.PodCount for o in doc.RoomPods.Group)==960
A.closeDocument(doc.Name)
of=json.loads((R/'sources/before_cleanup_validation.snapshot.json').read_text(encoding='utf-8'));nf=json.loads((R/'sources/accepted_frozen_validation.snapshot.json').read_text(encoding='utf-8'))
for key in ['daily_routes','emergency_routes','nearest_stair_routes','maximum_center_to_nearest_stair_m']:assert of[key]==nf[key],key
report=dict(source_commit='b53aa9b8e38c7c423703dd946c2ba88d44b9ab37',only_two_020m_wall_gaps_closed=True,added_wall_area_m2=added.Volume/1e8,removed_wall_volume_mm3=removed_volume,wall_patches_m=patches,
 frozen_collections_equal=keys,all_48_rooms_960_pods_retained=True,personnel_shaft_checks=shafts,protected_gallery_floor_checks=galleries,actual_saved_slab_supported_personnel_path_edges=supported,all_routes_unchanged=True,
 shaft_cut_policy='Open exact 2.10x2.40m net shaft void; retain 0.20m enclosure-wall support. Independent car reference is separate geometry.',stage='GEOMETRY_CHECKS_PASSED / VISUAL_REVIEW_PENDING')
(R/'qa/cleanup_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(R.parent/'v3_frozen/qa/cleanup_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(shafts=len(shafts),gallery_segments=len(galleries),supported_personnel_paths=len(supported),only_two_wall_patches=True)))
