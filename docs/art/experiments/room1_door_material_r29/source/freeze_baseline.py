from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
paths=list(json.loads((ROOT/'docs/art/experiments/room1_pod_age_full_r28/source/baseline_hashes.json').read_text()))
paths += [(p.relative_to(ROOT).as_posix()) for p in (ROOT/'assets/art/room1_pod_age_full_r28').rglob('*.png')]
paths += ['assets/art/room1_pod_age_full_r28/layout_variants.json','docs/art/experiments/room1_pod_age_full_r28/room1_pod_age_full_r28.blend','assets/art/room1_integrated_door_pixellab_v7/door_front.png','assets/art/room1_integrated_door_v3/room1_integrated_door_v3.glb','scripts/dev/room1_integrated_door_v3.gdshader','scripts/dev/room1_door_inner_light_r17.gd','scripts/dev/room1_door_soft_glow_r18.gd']
current={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths};out=HERE/'baseline_hashes.json'
if out.exists():assert json.loads(out.read_text())==current;print('R29_BASELINE_PASS',len(current))
else:out.write_text(json.dumps(current,indent=2),encoding='utf8');print('R29_BASELINE_FROZEN',len(current))
