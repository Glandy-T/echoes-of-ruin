"""A precise PixelLab repair of four generated near-black material pixels.

The script creates a technical mask/guide; every replacement art pixel is AI.
"""
from pathlib import Path
import base64,json,time,hashlib
from PIL import Image,ImageFilter
import numpy as np
from pixellab_api import credential,request
from jobs import encoded,find
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
JOB=HERE/'job_shell_end_fix.json';RESULT=EXP/'result_shell_end_fix.json'
def main():
    token=credential(True)
    if RESULT.exists():print('R21_END_REPAIR_ALREADY_COMPLETE');return
    if JOB.exists():
        saved=json.loads(JOB.read_text());assert saved.get('background_job_id'),'Uncertain prior POST; do not duplicate'
        jid=saved['background_job_id']
    else:
        original=Image.open(EXP/'raw/shell_end.png').convert('RGBA');a=np.array(original)
        editable=np.array(Image.open(HERE/'mask_shell_end.png').convert('L'))>0
        core=(a[:,:,:3].max(axis=2)<32)&editable;assert 0<int(core.sum())<30
        enlarged=np.array(Image.fromarray(core.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))
        mask=Image.fromarray(np.where(editable,enlarged,0).astype('uint8'));mask.save(HERE/'mask_end_repair.png')
        clean=np.array(Image.open(HERE/'guide_shell_end.png').convert('RGBA'))
        # Restore only known rejected pixels from the clean ORIGINAL guide as
        # generation input, not as delivered art. PixelLab edits the whole mask.
        a[core]=clean[core];Image.fromarray(a).save(HERE/'guide_end_repair.png')
        prompt='Repair only the white mask on this flat original cryopod UV texture. The casing is INTACT, not chipped through. Replace black hole-like marks with opaque ceramic ivory or medium cool slate-gray material matching each existing color zone. Keep the bold coarse stepped pixel-art look, not fine dots. No pure black, void, cutout, crack or deep cavity in the material face. Preserve all other pixel groups, exact panel shape, ID and design. Flat albedo, no lighting gradient.'
        (HERE/'prompt_end_repair.txt').write_text(prompt,encoding='utf-8')
        meta={'endpoint':'/inpaint-v3','input':'raw/shell_end.png','guide':'source/guide_end_repair.png','mask':'source/mask_end_repair.png','prompt':'source/prompt_end_repair.txt','seed':2026103051,'rejected_native_pixels':int(core.sum()),'repair_mask_native_pixels':int((np.array(mask)>0).sum()),'input_guide_operation':'Only rejected near-black pixels restored from original clean guide before PixelLab edits; never used directly as final art.','reason':'In actual Godot image, generated near-black material was read as a missing/chipped corner, not intended graphic shading.'}
        (HERE/'repair_request.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
        JOB.write_text(json.dumps({'status':'submitting','endpoint':'/inpaint-v3'}),encoding='utf-8')
        response=request('POST','/inpaint-v3',token,{'description':prompt,'inpainting_image':encoded(HERE/'guide_end_repair.png'),'mask_image':encoded(HERE/'mask_end_repair.png'),'seed':meta['seed'],'no_background':False,'crop_to_mask':False})
        safe={k:response.get(k) for k in ['background_job_id','status','usage']};assert safe['background_job_id'];jid=safe['background_job_id']
        JOB.write_text(json.dumps(safe,indent=2),encoding='utf-8');print('SUBMITTED shell_end_fix',jid,flush=True)
    while True:
        time.sleep(15);response=request('GET','/background-jobs/'+jid,token);status=response.get('status')
        if status=='completed':
            data=find(response.get('last_response'));assert data
            (EXP/'raw/shell_end_fix.png').write_bytes(base64.b64decode(data.split(',')[-1],validate=True))
            RESULT.write_text(json.dumps({'name':'shell_end_fix','endpoint':'/inpaint-v3','background_job_id':jid,'status':'completed','usage':response.get('usage')},indent=2),encoding='utf-8')
            print('COMPLETED shell_end_fix',json.dumps(response.get('usage')),flush=True);return
        if status in ['failed','cancelled']:raise RuntimeError('Repair job '+status)
if __name__=='__main__':main()
