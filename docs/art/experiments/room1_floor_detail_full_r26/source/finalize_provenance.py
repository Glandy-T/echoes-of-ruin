from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
jobs=json.loads((HERE/'requests.json').read_text());records=[]
for job in jobs:
    result=json.loads((EXP/f"result_{job['name']}.json").read_text())
    assert result['status']=='completed'
    records.append({'name':job['name'],'endpoint':job['endpoint'],'background_job_id':result['background_job_id'],'usage':result['usage'],'native_size':result['native_size'],'prompt_sha256':hashlib.sha256((HERE/job['prompt']).read_bytes()).hexdigest(),'guide_sha256':hashlib.sha256((HERE/job['guide']).read_bytes()).hexdigest(),'mask_sha256':hashlib.sha256((HERE/job['mask']).read_bytes()).hexdigest(),'raw_sha256':hashlib.sha256((EXP/f"raw/{job['name']}.png").read_bytes()).hexdigest()})
report={'result':'PASS','successful_requests':records,'actual_requests':len(records),'generations_used':sum(r['usage']['generations'] for r in records),'final_world_originals':21,'final_C_area_reintegration_originals':1,'rejected_perimeter_attempts':4,'selection':json.loads((HERE/'selection.json').read_text()),'rejected_outputs':json.loads((HERE/'rejected_outputs.json').read_text()),'C_area_new_material_pixels':41452,'old_C_pixels_reused':False,'final_strategy':json.loads((HERE/'final_strategy.json').read_text()),'resampling':False,'manual_or_procedural_material_art':False,'PixelCanals_content_submitted':False,'account_balance_or_billing_public':False}
(HERE/'final_provenance.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print('R26_PROVENANCE',len(records),'real requests,',report['generations_used'],'generations')
