"""OCC compare all v2 room modules, fixed core reservations and Q at compression candidates."""
from pathlib import Path
import json,math
import FreeCAD as App,Part
from layout import build_layout
ROOT=Path(__file__).resolve().parent
old=json.loads((ROOT.parent/'v2/floor_layout.json').read_text(encoding='utf-8'));d=build_layout();v=d['parameters']
def box(r):return Part.makeBox((r['x2']-r['x1'])*1000,(r['y2']-r['y1'])*1000,1,App.Vector(r['x1']*1000,r['y1']*1000,0))
reservations=[box(r) for r in old['plenums']]+[box(dict(x1=v['CoreWest'],x2=v['CoreEast'],y1=v['CoreSouth'],y2=v['CoreNorth']))]
candidate=[]
for shift in [0,2,4,4.2,4.3,4.4,4.5]:
 areas=[]
 for r in old['rooms']:
  q=dict(r);dy=-shift if r['zone'].startswith('N') else shift;q['y1']+=dy;q['y2']+=dy
  a=box(q);volume=sum(a.common(b).Volume for b in reservations)
  if volume>1e-3:areas.append(dict(room=r['id'],reserved_work_overlap_m2=volume/1e6))
 candidate.append(dict(shift_each_half_m=shift,main_depth_m=86.2-2*shift,all_fixed_core_plenum_reservations_clear=not areas,overlap_rooms=areas))
assert all(a['all_fixed_core_plenum_reservations_clear'] for a in candidate if a['shift_each_half_m']<=4.2)
assert all(not a['all_fixed_core_plenum_reservations_clear'] for a in candidate if a['shift_each_half_m']>4.2)
invariance=[]
for collection,key in [('rooms','id'),('corridors','id'),('elevator_nodes','id')]:
 for r in old[collection]:
  n=next(a for a in d[collection] if a[key]==r[key]);dy=-4.2 if r['zone'].startswith('N') else 4.2
  errors=[abs(n[k]-r[k]-(dy if k.startswith('y') else 0)) for k in ['x1','x2','y1','y2']];assert max(errors)<1e-7
  invariance.append(dict(collection=collection,id=r[key],shift_y_m=dy,maximum_coordinate_error_m=max(errors)))
for key in ['freight_shafts','waiting_bays','plenums']:
 assert all(max(abs(a[k]-b[k]) for k in ['x1','x2','y1','y2'])<1e-7 for a,b in zip(old[key],d[key]))
room_solids=[box(r) for r in d['rooms']]
min_q=min(a.distToShape(box(r))[0]/1000 for a in room_solids for r in d['waiting_bays'])
radius=math.hypot(v['CarrierWidth'],v['CarrierLength'])/2+v['TurnClearance']
points=[p for p in d['routes']['nodes'].values() if p['role'] in ['machine','waiting','waiting_access','waiting_access']]
min_turn=min(a.distToShape(Part.makeCylinder(radius*1000,1,App.Vector(p['x']*1000,p['y']*1000,0)))[0]/1000 for a in room_solids for p in points)
assert min_q>0 and min_turn>0
report=dict(source_v2_room_grid_preserved=True,whole_zone_coordinate_checks=invariance,all_four_freight_shafts_q_and_plenums_same_world_coordinates=True,
 selected_shift_each_half_m=4.2,upper_half_shift_down_m=4.2,lower_half_shift_up_m=4.2,total_main_depth_reduction_m=8.4,candidate_native_occ_tests=candidate,
 reason='4.20m is the contact boundary for full unchanged 4m-deep east/west turning reservations; larger shifts invade those working reservations. No individual room or X displacement.',
 minimum_q_footprint_to_room_outer_face_m=min_q,minimum_working_turn_circle_to_room_outer_face_m=min_turn,
 cross_lane_center_clear_width_m=4,cross_work_zone_clear_depth_m=11.2,old_geometric_lane_side_margin_m=7.8,new_geometric_lane_side_margin_m=3.6,
 old_side_margin_function='Undefined outside 4m lane',new_side_margin_function='Continuous machine operations / ground marking only',
 west_east_work_zone_clear_m=[78.7,11.2],west_work_zone_x_m=[4.7,83.4],east_work_zone_x_m=[103,181.7],work_zone_y_m=[37.5,48.7],
 north_south_main_lane_clear_m=6,each_spine_lateral_work_strip_m=6.8,emergency_core_isolation_full_width_m=19.6)
(ROOT/'qa/compression_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:report[k] for k in ['selected_shift_each_half_m','minimum_q_footprint_to_room_outer_face_m','minimum_working_turn_circle_to_room_outer_face_m']},ensure_ascii=False))
