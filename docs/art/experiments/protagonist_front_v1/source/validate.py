from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
original=Image.open(EXP/'raw/front.png').convert('RGBA');readback=Image.open(HERE/'readback_front.png').convert('RGBA')
a=np.array(original);result=json.loads((EXP/'result_front.json').read_text(encoding='utf8'))
checks={'native_requested192x256':original.size==(192,256),'transparent_background':bool((a[:,:,3]==0).any()),'opaque_subject':bool((a[:,:,3]==255).any()),'ASE_exact_pixel_readback':np.array_equal(a,np.array(readback)),'one_completed_job':result['status']=='completed' and result['background_job_id']=='cbfee5a0-f73c-414b-a0d9-6ff2e6ac7deb','actual9_generations':result['usage']=={'type':'generations','generations':9.0},'editable_master':(EXP/'editable/front_design_v1.aseprite').stat().st_size>0}
out={'result':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'raw_sha256':hashlib.sha256((EXP/'raw/front.png').read_bytes()).hexdigest(),'alpha_bbox':original.getbbox(),'local_resizing':False,'manual_art_edits':0,'scene_changes':False,'user_visual_approval':False,'scope':'Front design candidate only; not a final game asset or a 3D modeling approval.'}
(HERE/'validation.json').write_text(json.dumps(out,indent=2),encoding='utf8');assert out['result']=='PASS';print('FRONT_SOURCE_PASS',len(checks),'checks')
