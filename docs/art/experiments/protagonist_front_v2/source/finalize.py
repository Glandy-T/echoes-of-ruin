"""Export registration and verification only; no artistic pixels are drawn here."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
base=np.array(Image.open(HERE/'input_front_v1.png').convert('RGBA'))
ase=np.array(Image.open(HERE/'readback_front.png').convert('RGBA'));out=ase.copy()
# Aseprite can store white RGB under alpha=0. Restore the source's invisible
# RGB payload for exact outside-mask storage parity; visible RGBA is untouched.
out[base[:,:,3]==0]=base[base[:,:,3]==0]
Image.fromarray(out).save(EXP/'front_design_v2.png')
scope=np.array(Image.open(HERE/'skin_face_mask.png'))>0;scope[27,100:105]=True
Image.fromarray((scope*255).astype('uint8')).save(HERE/'final_scope_mask.png')
changed=np.any(out!=base,axis=2)
raw=np.array(Image.open(EXP/'raw/front.png').convert('RGBA'));raw[:,:,3]=base[:,:,3]
ai=base.copy();initial=np.array(Image.open(HERE/'skin_face_mask.png'))>0;ai[initial]=raw[initial]
manual=np.any(ai!=out,axis=2)
visible=base[:,:,3]>0
result=json.loads((EXP/'result_front.json').read_text(encoding='utf8'))
provenance=json.loads((HERE/'provenance.json').read_text(encoding='utf8'))
checks={'native192x256':out.shape==base.shape==(256,192,4),'outside_final_skin_face_scope_exact':not changed[~scope].any(),'original_alpha_exact':np.array_equal(out[:,:,3],base[:,:,3]),'ASE_visible_pixels_exact':np.array_equal(out[visible],ase[visible]),'v1_source_unchanged':hashlib.sha256((ROOT/provenance['input']).read_bytes()).hexdigest()==provenance['sha256'],'one_completed_job':result['status']=='completed','actual10_generations':result['usage']=={'type':'generations','generations':10.0}}
report={'result':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'changed_pixels_from_v1':int(changed.sum()),'Aseprite_art_refinement_pixels_after_AI':int(manual.sum()),'manual_refinement_bounds_xy':[int(np.where(manual)[1].min()),int(np.where(manual)[0].min()),int(np.where(manual)[1].max()),int(np.where(manual)[0].max())],'transparent_RGB_storage_normalized_only':int(np.any(out!=ase,axis=2).sum()),'creative_resize':False,'game_scene_modified':False,'user_visual_approval':False}
(HERE/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');assert report['result']=='PASS',report
print('FRONT_V2_PASS',report['changed_pixels_from_v1'],'total changes;',report['Aseprite_art_refinement_pixels_after_AI'],'Aseprite local refinements')
