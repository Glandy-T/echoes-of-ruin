from pathlib import Path
from PIL import Image
import numpy as np,json,runpy
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
runpy.run_path(str(HERE/'freeze_baseline.py'))
final=Image.open(ROOT/'assets/art/room1_door_material_r29/door_front.png').convert('RGBA');readback=Image.open(HERE/'readback_door.png').convert('RGBA');mask=np.asarray(Image.open(HERE/'door_mask.png'))>0;base=np.asarray(Image.open(HERE/'door_clean_structure.png').convert('RGBA'));raw=Image.open(EXP/'raw/door.png').convert('RGBA');crop=np.asarray(raw.crop((4,4,116,188)))
checks={'runtime_size':final.size==(112,184),'request_size':raw.size==(256,192),'ASE_readback_exact':np.array_equal(np.asarray(final),np.asarray(readback)),'new_material_raw_pixels_exact':np.array_equal(np.asarray(final)[mask],crop[mask]),'protected_seal_status_exact':np.array_equal(np.asarray(final)[~mask],base[~mask]),'opaque':bool(np.all(np.asarray(final)[:,:,3]==255)),'editable_master':(EXP/'editable/door_front_r29.aseprite').stat().st_size>0}
result=json.loads((EXP/'result_door.json').read_text());checks['real_job']=result['status']=='completed' and bool(result['background_job_id']);checks['10_generations']=result['usage']['generations']==10
blend=json.loads((HERE/'blender_readback.json').read_text());checks['blender_only_one_image']=blend['result']=='PASS' and len(blend['image_changes'])==1;checks['blender_dependencies']=not blend['missing'] and not blend['absolute_paths']
assert all(checks.values()),{k:v for k,v in checks.items() if not v}
(HERE/'artifact_validation.json').write_text(json.dumps({'result':'PASS','checks':checks,'used_AI_requests':1,'usage_generations':10,'creative_resizing':False,'manual_paint_edits':0,'scope':'door pixel_map only; all r28 material and existing shader unchanged'},indent=2),encoding='utf8')
print('R29_ARTIFACTS_PASS',len(checks),'checks;10generations')
