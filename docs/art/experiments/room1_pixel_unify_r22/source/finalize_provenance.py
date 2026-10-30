"""Read back actual accepted output paths, paid requests and technical composition."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
jobs=json.loads((HERE/'requests.json').read_text())
results={r['name']:r for r in [json.loads(p.read_text()) for p in EXP.glob('result_*.json')]}
assert set(results)=={j['name'] for j in jobs}
records=[]
for j in jobs:
    r=results[j['name']]
    records.append({'name':j['name'],'endpoint':j['endpoint'],'background_job_id':r['background_job_id'],'usage':r['usage'],'native_size':r['native_size'],'prompt_sha256':hashlib.sha256((HERE/j['prompt']).read_bytes()).hexdigest(),'guide_sha256':hashlib.sha256((HERE/j['guide']).read_bytes()).hexdigest(),'mask_sha256':hashlib.sha256((HERE/j['mask']).read_bytes()).hexdigest(),'raw_sha256':hashlib.sha256((EXP/f"raw/{j['name']}.png").read_bytes()).hexdigest()})
accepted={'walls':{'existing_r20':'original accepted wall pair','new':['wall_1','wall_2','wall_3','wall_4','wall_5'],'portal':'portal_fix'},'pod_a':'reused accepted r20 lid / shell_side / shell_end','pod_b':['b_lid_fix','b_shell_side','b_shell_end'],'pod_c':['c_lid','c_shell_side','c_shell_end'],'pod_d':['d_lid_fix','d_shell_side','d_shell_end'],'floor':'8 world-aligned tiles; tile 02 exact native repair composite with floor_02_fix, tile 08 uses floor_08_fix'}
report={'actual_completed_jobs':records,'accepted_art_sources':accepted,'rejected':json.loads((HERE/'rejected_outputs.json').read_text()),'current_floor_layout':json.loads((HERE/'floor_tile_layout.json').read_text()),'failed_request_record':'failed_floor_1_status.json','withdrawn_without_POST':['floor_2'],'model_UVs_layout_camera_light_parameters_changed':False,'reference_content_submitted':False,'manual_material_painting':False,'shared_interior_glass_screens_lamps_door':'existing accepted assets unchanged','generation_total':sum(r['usage']['generations'] for r in results.values())}
(HERE/'final_provenance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('R22_FINAL_PROVENANCE',len(records),'successful requests',report['generation_total'],'generations')
