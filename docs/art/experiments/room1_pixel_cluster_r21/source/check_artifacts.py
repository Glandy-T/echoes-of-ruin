"""Check edit scope, old versions, Aseprite readback and actual API use."""
from pathlib import Path
import hashlib,json
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
checks={}
for key in ['wall_left','pod_lid','pod_shell_side','pod_shell_end']:
    a=np.array(Image.open(HERE/f'readback_{key}.png').convert('RGBA'))
    b=np.array(Image.open(ROOT/f'assets/art/room1_pixel_cluster_r21/{key}.png').convert('RGBA'))
    checks[key]=bool(np.array_equal(a,b));assert checks[key]
baseline=json.loads((HERE/'baseline_file_hashes.json').read_text())
changed=[p for p,h in baseline.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h];assert not changed,changed
results=[json.loads(p.read_text()) for p in EXP.glob('result_*.json')]
assert len(results)>=4 and all(r['status']=='completed' for r in results)
report={'result':'PASS','aseprite_exact':checks,'immutable_files':len(baseline),'changed_baselines':changed,'actual_API_jobs':len(results),'accepted_maps':4,'generations_used':sum(r['usage']['generations'] for r in results)}
(HERE/'artifact_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('R21_ARTIFACTS_PASS',json.dumps(report))
