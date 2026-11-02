from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
old=json.loads((ROOT/'docs/art/experiments/room1_pod_age_r27/source/baseline_hashes.json').read_text())
for path,sha in old.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha
paths=list(old)+['assets/art/room1_pod_age_r27/'+s+'.png' for s in ['lid','shell_side','shell_end']]+['docs/art/experiments/room1_pod_age_r27/room1_pod_age_r27.blend']
current={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths};out=HERE/'baseline_hashes.json'
if out.exists():assert json.loads(out.read_text())==current;print('R28_BASELINE_PASS',len(current))
else:out.write_text(json.dumps(current,indent=2),encoding='utf8');print('R28_BASELINE_FROZEN',len(current))
