from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
a=json.loads((ROOT.parent/'v3_final/floor_layout.json').read_text(encoding='utf-8'));b=json.loads((ROOT/'floor_layout.json').read_text(encoding='utf-8'))
for key in ['rooms','corridors','elevator_nodes','freight_shafts','waiting_bays','plenums','machine_work_areas']:
 assert len(a[key])==len(b[key])
 for x,y in zip(a[key],b[key]):assert all(abs(x[k]-y[k])<1e-7 for k in ['x1','y1','x2','y2']),(key,x,y)
stairs=[]
for x,y in zip(a['stairs'],b['stairs']):
 dy=-2.6 if x['side']=='North' else 2.6 if x['side']=='South' else 0
 assert all(abs(x[k]+(dy if k[0]=='y' else 0)-y[k])<1e-7 for k in ['x1','y1','x2','y2'])
 if dy:assert y['y1']>=b['parameters']['FloorSouth']-1e-7 and y['y2']<=b['parameters']['FloorNorth']+1e-7
 stairs.append(dict(side=x['side'],shift_y_m=dy,old_bounds_m={k:x[k] for k in ['x1','y1','x2','y2']},new_bounds_m={k:y[k] for k in ['x1','y1','x2','y2']}))
old=json.loads((ROOT.parent/'v3_final/floor_validation.json').read_text(encoding='utf-8'));new=json.loads((ROOT/'floor_validation.json').read_text(encoding='utf-8'))
delta=[]
for r in new['emergency_routes']:
 x=next(p for p in old['emergency_routes'] if p['room']==r['room'] and p['stair']==r['stair']);expect=-2.6 if r['stair'] in ['North','South'] else 0
 assert abs(r['length_m']-x['length_m']-expect)<1e-7;delta.append(dict(room=r['room'],stair=r['stair'],path_change_m=expect))
report=dict(accepted_plan_unchanged_except_north_south_stairs=True,all_fixed_collections_checked=True,stairs=stairs,north_south_stairs_fully_within_main_envelope=True,
 main_envelope_m=b['main_envelope_m'],maximum_envelope_m=b['maximum_envelope_m'],path_comparisons=delta,previous_maximum_center_m=old['maximum_center_to_nearest_stair_m'],current_maximum_center_m=new['maximum_center_to_nearest_stair_m'],
 note='All 48 north/south route options shorten 2.60m. West/east routes remain identical. Global nearest-stair maximum stays 66.95m because the governing rooms still choose unchanged side stairs.')
(ROOT/'qa/inset_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:report[k] for k in ['accepted_plan_unchanged_except_north_south_stairs','main_envelope_m','maximum_envelope_m','current_maximum_center_m']}))
