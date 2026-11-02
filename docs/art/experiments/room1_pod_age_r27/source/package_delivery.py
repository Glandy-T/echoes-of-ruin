"""Hash the exact portable deliverable, excluding caches, logs and private records."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
files=[]
for p in sorted(EXP.rglob('*')):
 if not p.is_file() or p.suffix in ('.log','.err','.blend1','.pyc','.uid','.import') or '__pycache__' in p.parts or '.log.' in p.name or p.name.startswith('balance_') or p.name=='delivery_manifest.json':continue
 files.append(p)
files+=sorted((ROOT/'assets/art/room1_pod_age_r27').glob('*.png'))
files += [ROOT/p for p in ['scripts/dev/room1_pod_age_r27.gd','scripts/dev/capture_room1_pod_age_r27.gd','scripts/dev/verify_room1_pod_age_r27.gd','scenes/dev/room1_pod_age_r27.tscn','scenes/dev/room1_pod_age_r27_capture.tscn','scenes/dev/room1_pod_age_r27_verify.tscn']]
manifest={'scope':'P12 exterior color maps only; r26 room and formal F5 unchanged','files':[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(HERE/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print('R27_DELIVERY_MANIFEST',len(files),'files;',sum(p.stat().st_size for p in files),'bytes')
