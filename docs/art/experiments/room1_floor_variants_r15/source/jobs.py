"""Bounded two-job queue, persistent safe metadata, no duplicate POST retries."""
from pathlib import Path
from PIL import Image
import json,base64,sys,time
from pixellab_api import credential,request
HERE=Path(__file__).resolve().parent
def image(path):
    w,h=Image.open(path).size
    return {'image':{'base64':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()},'size':{'width':w,'height':h}}
def find(v):
    if isinstance(v,dict):
        if isinstance(v.get('base64'),str):return v['base64']
        for c in v.values():
            out=find(c)
            if out:return out
    if isinstance(v,list):
        for c in v:
            out=find(c)
            if out:return out
def run():
    jobs=json.loads((HERE/'requests.json').read_text());token=credential(True)
    if len(sys.argv)>1:jobs=[j for j in jobs if j['name'] in sys.argv[1:]]
    pending=[];active=[]
    for j in jobs:
        f=HERE/f"job_{j['name']}.json"
        if (HERE.parent/f"result_{j['name']}.json").exists():continue
        if f.exists():
            data=json.loads(f.read_text())
            assert data.get('background_job_id'),'Uncertain prior submission; do not resubmit: '+j['name']
            active.append((j,data['background_job_id']))
        else:pending.append(j)
    while active or pending:
        while pending and len(active)<2:
            j=pending.pop(0);payload={'description':(HERE/j['prompt']).read_text(encoding='utf-8'),'seed':j['seed'],'no_background':False}
            if j['endpoint']=='/generate-image-v2':
                payload.update({'image_size':{'width':256,'height':256},'target_palette':j['palette']})
                if j.get('style'):payload.update({'style_image':image(HERE/j['style']),'style_options':{'color_palette':False,'outline':True,'detail':True,'shading':True}})
            else:payload.update({'inpainting_image':image(HERE/j['guide']),'mask_image':image(HERE/j['mask']),'crop_to_mask':False})
            f=HERE/f"job_{j['name']}.json"
            f.write_text(json.dumps({'status':'submitting','endpoint':j['endpoint']}),encoding='utf-8')
            r=request('POST',j['endpoint'],token,payload)
            safe={k:r.get(k) for k in ['background_job_id','status','usage']};assert safe['background_job_id']
            f.write_text(json.dumps(safe,indent=2),encoding='utf-8')
            print('SUBMITTED',j['name'],safe['background_job_id'],flush=True);active.append((j,safe['background_job_id']))
        time.sleep(15)
        still=[]
        for j,jid in active:
            r=request('GET','/background-jobs/'+jid,token)
            if r.get('status')=='completed':
                encoded=find(r.get('last_response'));assert encoded
                (HERE.parent/'raw'/f"{j['name']}.png").write_bytes(base64.b64decode(encoded.split(',')[-1],validate=True))
                safe={'variant':j['name'],'endpoint':j['endpoint'],'background_job_id':jid,'status':'completed','usage':r.get('usage')}
                (HERE.parent/f"result_{j['name']}.json").write_text(json.dumps(safe,indent=2),encoding='utf-8')
                print('COMPLETED',j['name'],json.dumps(safe['usage']),flush=True)
            elif r.get('status') in ['failed','cancelled']:raise RuntimeError('Job failed: '+j['name'])
            else:still.append((j,jid))
        active=still
    print('QUEUE COMPLETE',flush=True)
if __name__=='__main__':run()
