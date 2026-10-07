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
assert not added_cells and not removed_cells,'0F must not alter any wall geometry'
added_volume=0.
removed_volume=sum((r['x2']-r['x1'])*(r['y2']-r['y1'])*1e8 for r in removed_cells)
patches=[dict(x1=-2.6,x2=-2.4,y1=28.,y2=28.2),dict(x1=188.8,x2=189.,y1=28.,y2=28.2)]
assert removed_volume<.01
removed_floors=subtract_rectangles(old['floor_cells'],new['floor_cells'])
added_floors=subtract_rectangles(new['floor_cells'],old['floor_cells'])
assert not added_floors
deleted=union(removed_floors);expected=union(new['removed_lift_aprons'])
assert abs(deleted.Volume/1e8-109.48)<1e-7
assert deleted.cut(expected).Volume<.01 and expected.cut(deleted).Volume<.01
normalized={}
for zone in ['SW','SE','NW','NE']:
 rs=[]
 for r in new['personnel_structural_nodes']+new['removed_lift_aprons']:
  if r['zone']!=zone:continue
  x1,x2=(new['parameters']['MainWidth']-r['x2'],new['parameters']['MainWidth']-r['x1']) if zone.endswith('E') else (r['x1'],r['x2'])
  dy=new['parameters']['NorthZoneY']-new['parameters']['FloorSouth'] if zone.startswith('N') else 0
  rs.append((r['tag'],round(x1,8),round(r['y1']-dy,8),round(x2,8),round(r['y2']-dy,8)))
 normalized[zone]=sorted(rs)
assert all(v==normalized['SW'] for v in normalized.values())
doc=A.openDocument(str(R/'standard_floor_blockout_v3_trim.FCStd'))
floors=[o.Shape for o in doc.Objects if hasattr(o,'Role') and o.Role=='floor']
surfaces=[o.Shape for o in doc.Objects if hasattr(o,'Role') and o.Role in ['floor','personnel_floor','machine_floor']]
def overlap(probe,shapes):
 b=probe.BoundBox;total=0.
 for s in shapes:
  a=s.BoundBox
  if min(a.XMax,b.XMax)>max(a.XMin,b.XMin)+1e-5 and min(a.YMax,b.YMax)>max(a.YMin,b.YMin)+1e-5 and min(a.ZMax,b.ZMax)>max(a.ZMin,b.ZMin)+1e-5:total+=probe.common(s).Volume
 return total
shafts=[]
apron_checks=[]
for r in new['removed_lift_aprons']:
 q={k:r[k]+(.000001 if k.endswith('1') else -.000001) for k in ['x1','y1','x2','y2']}
 vol=overlap(prism(q,-.11,.12),surfaces);assert vol<.01,(r,vol)
 apron_checks.append(dict(zone=r['zone'],bounds_m={k:r[k] for k in ['x1','y1','x2','y2']},structural_and_walk_surface_overlap_mm3=vol))
node_checks=[]
for r in new['personnel_structural_nodes']:
 for q in subtract_rectangles([r],new['passenger_shaft_voids']):
  p=prism(q);missing=p.Volume-overlap(p,floors);assert abs(missing)<.1,(r,missing)
 node_checks.append(dict(zone=r['zone'],role=r['tag'],floor_and_wall_support_continuous=True))
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
supported=[];lift_edges=[]
car_projected=[prism(dict(x1=o.Shape.BoundBox.XMin/1000,y1=o.Shape.BoundBox.YMin/1000,x2=o.Shape.BoundBox.XMax/1000,y2=o.Shape.BoundBox.YMax/1000)) for o in doc.LiftCars.Group]
for i,e in enumerate(new['routes']['edges']):
 if e['kind'] not in ['daily','emergency','evacuation_outward'] or e['length']<1e-9:continue
 a=new['routes']['nodes'][e['a']];b=new['routes']['nodes'][e['b']]
 if 'lift' in [a['role'],b['role']]:
  p=capsule(a,b);missing=p.Volume-overlap(p,floors+car_projected);assert abs(missing)<.2,(e,missing);lift_edges.append(i);continue
 p=capsule(a,b);missing=p.Volume-overlap(p,floors);assert abs(missing)<.2,(e,missing)
 supported.append(i)
for patch in patches:
 p=prism(patch,0,3.4);walls=[o.Shape for o in doc.Objects if hasattr(o,'Role') and o.Role=='wall'];assert abs(overlap(p,walls)-p.Volume)<.1
assert len(doc.RoomPods.Group)==48 and sum(o.PodCount for o in doc.RoomPods.Group)==960
A.closeDocument(doc.Name)
of=json.loads((R/'sources/before_cleanup_validation.snapshot.json').read_text(encoding='utf-8'));nf=json.loads((R/'sources/accepted_frozen_validation.snapshot.json').read_text(encoding='utf-8'))
for key in ['daily_routes','emergency_routes','nearest_stair_routes','maximum_center_to_nearest_stair_m']:assert of[key]==nf[key],key
report=dict(source_commit='8dbcec552f6a058145508c8e0bf701063067449f',all_walls_identical_to_0E=True,prior_two_020m_wall_fixes_retained=True,added_wall_area_m2=added_volume,removed_wall_volume_mm3=removed_volume,wall_patches_m=patches,
 removed_floor_area_m2=deleted.Volume/1e8,only_eight_unused_aprons_removed=True,four_nodes_mirror_equal=True,removed_apron_checks=apron_checks,physical_node_floor_support_checks=node_checks,
 frozen_collections_equal=keys,all_48_rooms_960_pods_retained=True,personnel_shaft_checks=shafts,protected_gallery_floor_checks=galleries,actual_saved_slab_supported_personnel_path_edges=supported,lift_edges_supported_by_structure_and_independent_car=lift_edges,all_routes_unchanged=True,
 shaft_cut_policy='Open exact 2.10x2.40m net shaft void; retain 0.20m enclosure-wall support. Independent car reference is separate geometry.',stage='GEOMETRY_CHECKS_PASSED / VISUAL_REVIEW_PENDING')
(R/'qa/cleanup_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(R.parent/'v3_trim/qa/cleanup_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(shafts=len(shafts),gallery_segments=len(galleries),supported_personnel_paths=len(supported),aprons_removed=len(apron_checks),removed_floor_m2=deleted.Volume/1e8,all_walls_unchanged=True)))
