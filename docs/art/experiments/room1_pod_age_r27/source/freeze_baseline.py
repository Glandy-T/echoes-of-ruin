from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
paths=['project.godot','scenes/areas/military_facility/cryo_room_4f_01_3d.tscn','scenes/props/cryopod_standard_v8.tscn','scripts/props/cryopod_standard_v8_surface.gdshader','scripts/dev/room1_camera_follow_test.gd','scripts/dev/room1_complete_surface_r19.gdshader','assets/art/cryopod_standard_v8/cryopod_standard_v8.glb','assets/art/room1_complete_r19/layout.json','assets/art/room1_complete_r19/lighting/P12_closed.exr','assets/art/room1_complete_r19/lighting/P12_open.exr','assets/art/room1_floor_detail_full_r26/floor_with_leaks.png']
paths+=['assets/art/room1_wall_detail_full_r24/wall_'+s+'.png' for s in ['left','right','front','rear']]
paths+=['assets/art/room1_pixel_unify_r22/numbered/P12_'+s+'.png' for s in ['lid','shell_end']]
out=HERE/'baseline_hashes.json'
current={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
if out.exists():assert json.loads(out.read_text())==current;print('R27_BASELINE_HASH_PASS',len(current))
else:out.write_text(json.dumps(current,indent=2),encoding='utf8');print('R27_BASELINE_FROZEN',len(current))
