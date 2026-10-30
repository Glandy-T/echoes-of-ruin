from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
jobs=json.loads((HERE/'requests.json').read_text());records=[]
for job in jobs:
    result=json.loads((EXP/f"result_{job['name']}.json").read_text())
    assert result['status']=='completed'
    records.append({'name':job['name'],'endpoint':job['endpoint'],'background_job_id':result['background_job_id'],'usage':result['usage'],'native_size':result['native_size'],'prompt_sha256':hashlib.sha256((HERE/job['prompt']).read_bytes()).hexdigest(),'guide_sha256':hashlib.sha256((HERE/job['guide']).read_bytes()).hexdigest(),'mask_sha256':hashlib.sha256((HERE/job['mask']).read_bytes()).hexdigest(),'raw_sha256':hashlib.sha256((EXP/f"raw/{job['name']}.png").read_bytes()).hexdigest()})
report={'result':'PASS','successful_requests':records,'generations_used':sum(r['usage']['generations'] for r in records),'approved_originals_reused':['room1_wall_detail_r23/raw/a.png','room1_wall_detail_r23/raw/b.png'],'final_new_pair_selection':['c','d','e','f','g_fix','h_fix'],'final_portal_selection':'portal_opening','rejections':json.loads((HERE/'rejected_outputs.json').read_text()),'portal_measured_mask':json.loads((HERE/'portal_mask_scope.json').read_text()),'resampling':False,'manual_or_procedural_material_art':False,'PixelCanals_content_submitted':False}
(HERE/'final_provenance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('R24_PROVENANCE',len(records),'actual jobs',report['generations_used'],'generations')
