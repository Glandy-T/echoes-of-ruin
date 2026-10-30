"""Compare editable readback, immutable baseline files, and actual API usage."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
checks={}
for name in ['wall_left','pod_lid','pod_shell_side','pod_shell_end']:
    a=np.array(Image.open(HERE/f'readback_{name}.png').convert('RGBA'))
    b=np.array(Image.open(ROOT/f'assets/art/room1_pixel_cluster_r20/{name}.png').convert('RGBA'))
    checks[name]=bool(np.array_equal(a,b));assert checks[name],name
baseline=json.loads((HERE/'baseline_file_hashes.json').read_text())
changed=[name for name,old in baseline.items() if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=old]
assert not changed,changed
results=[json.loads(p.read_text()) for p in EXP.glob('result_*.json')]
assert len(results)>=4 and all(r['status']=='completed' for r in results)
usage=sum(r['usage']['generations'] for r in results)
report={'result':'PASS','exact_aseprite_composites':checks,'immutable_baseline_files':len(baseline),'changed_baseline_files':changed,'actual_PixelLab_jobs':len(results),'accepted_maps':4,'generations_used':usage}
(HERE/'artifact_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('R20_ARTIFACTS_PASS',json.dumps(report))
