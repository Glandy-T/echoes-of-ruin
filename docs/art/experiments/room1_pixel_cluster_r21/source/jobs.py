"""Official PixelLab API, bounded queue; no duplicate paid submission retries."""
from pathlib import Path
import base64,json,time,sys
from PIL import Image
from pixellab_api import credential,request
HERE=Path(__file__).resolve().parent; EXP=HERE.parent
def encoded(p):
    w,h=Image.open(p).size
    return {'image':{'base64':'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()},'size':{'width':w,'height':h}}
def find(value):
    if isinstance(value,dict):
        if isinstance(value.get('base64'),str):return value['base64']
        for child in value.values():
            result=find(child)
            if result:return result
    if isinstance(value,list):
        for child in value:
            result=find(child)
            if result:return result
def main():
    jobs=json.loads((HERE/'requests.json').read_text()); token=credential(True)
    if len(sys.argv)>1:jobs=[j for j in jobs if j['name'] in sys.argv[1:]]
    pending=[];active=[]
    for job in jobs:
        name=job['name']; path=HERE/f'job_{name}.json'
        if (EXP/f'result_{name}.json').exists():continue
        if path.exists():
            saved=json.loads(path.read_text());assert saved.get('background_job_id'),'Uncertain submission, do not duplicate POST'
            active.append((job,saved['background_job_id']))
        else:pending.append(job)
    while pending or active:
        while pending and len(active)<2:
            job=pending.pop(0); name=job['name'];path=HERE/f'job_{name}.json'
            payload={'description':(HERE/job['prompt']).read_text(encoding='utf-8'),'inpainting_image':encoded(HERE/job['guide']),'mask_image':encoded(HERE/job['mask']),'seed':job['seed'],'no_background':False,'crop_to_mask':False}
            path.write_text(json.dumps({'status':'submitting','endpoint':job['endpoint']}),encoding='utf-8')
            response=request('POST',job['endpoint'],token,payload)
            safe={k:response.get(k) for k in ['background_job_id','status','usage']};assert safe['background_job_id']
            path.write_text(json.dumps(safe,indent=2),encoding='utf-8')
            active.append((job,safe['background_job_id']));print('SUBMITTED',name,safe['background_job_id'],flush=True)
        time.sleep(15)
        still=[]
        for job,jid in active:
            response=request('GET','/background-jobs/'+jid,token);status=response.get('status')
            if status=='completed':
                data=find(response.get('last_response'));assert data
                raw=base64.b64decode(data.split(',')[-1],validate=True)
                (EXP/'raw'/f"{job['name']}.png").write_bytes(raw)
                safe={'name':job['name'],'endpoint':job['endpoint'],'background_job_id':jid,'status':status,'usage':response.get('usage'),'native_size':list(Image.open(EXP/'raw'/f"{job['name']}.png").size)}
                (EXP/f"result_{job['name']}.json").write_text(json.dumps(safe,indent=2),encoding='utf-8')
                print('COMPLETED',job['name'],json.dumps(safe['usage']),flush=True)
            elif status in ['failed','cancelled']:raise RuntimeError('PixelLab job '+status+': '+job['name'])
            else:still.append((job,jid))
        active=still
    print('R21_PIXELLAB_QUEUE_COMPLETE',flush=True)
if __name__=='__main__':main()
