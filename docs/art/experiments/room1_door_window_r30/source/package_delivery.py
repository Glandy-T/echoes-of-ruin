from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4];files=[]
for folder in [EXP,ROOT/'assets/art/room1_door_window_r30']:
 for p in sorted(folder.rglob('*')):
  if not p.is_file() or p.suffix in ('.log','.err','.blend1','.pyc','.uid','.import') or '__pycache__' in p.parts or '.log.' in p.name or p.name.startswith('balance_') or p.name=='delivery_manifest.json':continue
  files.append(p)
files += [ROOT/p for p in ['scripts/dev/room1_door_window_r30.gd','scripts/dev/capture_room1_door_window_r30.gd','scripts/dev/verify_room1_door_window_r30.gd','scenes/dev/room1_door_window_r30.tscn','scenes/dev/room1_door_window_r30_capture.tscn','scenes/dev/room1_door_window_r30_verify.tscn']]
out={'scope':'Only authentication-window bezel pixels refined in door pixel_map; all approvedr28 room materials,geometry,UV,shader,lights and behavior unchanged.','files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(HERE/'delivery_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print('R30_DELIVERY_MANIFEST',len(files),'files;',sum(p.stat().st_size for p in files),'bytes')
