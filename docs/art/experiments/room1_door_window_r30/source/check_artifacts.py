from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
old=np.array(Image.open(ROOT/'assets/art/room1_door_material_r29/door_front.png').convert('RGBA'))
new=np.array(Image.open(ROOT/'assets/art/room1_door_window_r30/door_front.png').convert('RGBA'))
changed=np.any(old!=new,axis=2);outside=changed.copy();outside[61:75,45:67]=False
frozen=json.loads((HERE/'frozen_inputs.json').read_text());drift=[p for p,h in frozen.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
rows=json.loads((EXP/'evidence/capture_record.json').read_text());run=json.loads((HERE/'runtime_validation.json').read_text())
checks={'native112x184':new.shape==old.shape==(184,112,4),'only_window_22x14_region':not outside.any(),'inner_aperture_exact':np.array_equal(new[64:71,51:63],old[64:71,51:63]),'white_bezel_removed':not np.any(np.all(new[61:75,45:67,:3]==[211,214,201],axis=2)),'ASE_export_exact':np.array_equal(new,np.array(Image.open(HERE/'readback_door.png').convert('RGBA'))),'frozen_inputs':not drift,'runtime_PASS':run['result']=='PASS','15_gpu_frames':len(rows)==15}
for r in rows:assert Image.open(EXP/'evidence'/r['file']).size==(1280,720)
for suffix in ['game_door_closed','door_wall_front']:
 a=(EXP/f'evidence/1_a_{suffix}.png').read_bytes();b=(EXP/f'evidence/2_b_{suffix}.png').read_bytes();restore=(EXP/f'evidence/1_a_restore_{suffix}.png').read_bytes()
 checks['ABA_exact_'+suffix]=a==restore and a!=b
report={'result':'PASS' if all(checks.values()) else 'FAIL','checks':{k:bool(v) for k,v in checks.items()},'changed_pixels':int(changed.sum()),'edit_bounds_xy_inclusive':[45,61,66,74],'preserved_inputs':len(frozen),'drift':drift,'new_PixelLab_calls':0,'new_generations':0,'art_refinement':'Aseprite named local layer; remove legacy white bezel, keep one native pixel dark recess; no procedural weathering'}
(HERE/'artifact_validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');assert report['result']=='PASS',report
print('R30_ARTIFACT_PASS',report['changed_pixels'],'local pixels;',len(frozen),'frozen inputs')
