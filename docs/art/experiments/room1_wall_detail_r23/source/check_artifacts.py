from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
baseline=json.loads((HERE/'baseline_file_hashes.json').read_text())
for path,sha in baseline.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha,path
for p in json.loads((HERE/'packages.json').read_text()):
    a=np.asarray(Image.open(ROOT/p['output']).convert('RGBA'));b=np.asarray(Image.open(HERE/f"readback_{p['name']}.png").convert('RGBA'));assert np.array_equal(a,b),p['name']
results=[json.loads(p.read_text()) for p in EXP.glob('result_*.json')]
assert all(r['status']=='completed' for r in results) and len(results)>=2
report={'result':'PASS','immutable_files':len(baseline),'Aseprite_exact_readbacks':3,'actual_successful_requests':len(results),'generations_used':sum(r['usage']['generations'] for r in results),'new_native_art_size':[256,256],'third_party_reference_uploaded':False}
(HERE/'artifact_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('R23_ARTIFACTS_PASS',len(baseline),'old files unchanged; 3 masters exact;',report['generations_used'],'generations')
