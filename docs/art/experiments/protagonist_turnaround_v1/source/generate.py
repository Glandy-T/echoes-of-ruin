from pathlib import Path
import json,base64,time
from PIL import Image
from pixellab_api import credential,request
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
def find(v):
 if isinstance(v,dict):
  if isinstance(v.get('base64'),str):return v['base64']
  for child in v.values():
   out=find(child)
   if out:return out
 if isinstance(v,list):
  for child in v:
   out=find(child)
   if out:return out
def main():
 token=credential(True);active=[]
 for job in json.loads((HERE/'requests.json').read_text(encoding='utf8')):
  name=job['name'];state=HERE/f'job_{name}.json'
  if (EXP/f'result_{name}.json').exists():continue
  if state.exists():saved=json.loads(state.read_text(encoding='utf8'));assert saved.get('background_job_id'),'Uncertain submission; never duplicate POST'
  else:
   payload={'image':{'base64':'data:image/png;base64,'+base64.b64encode((HERE/job['input']).read_bytes()).decode()},'method':'text','description':(HERE/job['prompt']).read_text(encoding='utf8'),'no_background':True,'seed':job['seed']}
   state.write_text(json.dumps({'status':'submitting','endpoint':job['endpoint']}),encoding='utf8')
   reply=request('POST',job['endpoint'],token,payload);saved={k:reply.get(k) for k in ['background_job_id','status','usage','source_image_id']};assert saved['background_job_id'];state.write_text(json.dumps(saved,indent=2),encoding='utf8')
   print('SUBMITTED',name,saved['background_job_id'],flush=True)
  active.append((job,saved['background_job_id']))
 for _ in range(60):
  if not active:print('TURNAROUND_QUEUE_COMPLETE',flush=True);return
  time.sleep(10);pending=[]
  for job,jid in active:
   r=request('GET','/background-jobs/'+jid,token);status=r.get('status')
   if status=='completed':
    last=r.get('last_response');data=find(last);assert data,'No encoded result; keep job and do not retry POST'
    dest=EXP/'raw'/f"{job['name']}.png";dest.write_bytes(base64.b64decode(data.split(',')[-1],validate=True))
    safe={'name':job['name'],'endpoint':job['endpoint'],'background_job_id':jid,'status':status,'usage':r.get('usage'),'native_size':list(Image.open(dest).size),'source_image_id':last.get('source_image_id') if isinstance(last,dict) else None}
    (EXP/f"result_{job['name']}.json").write_text(json.dumps(safe,indent=2),encoding='utf8');print('COMPLETED',job['name'],json.dumps(safe['usage']),flush=True)
   elif status in ['failed','cancelled']:raise RuntimeError(job['name']+' '+status+'; do not repeat POST')
   else:pending.append((job,jid))
  active=pending
 raise RuntimeError('Polling timeout; resume saved task IDs without new submission')
if __name__=='__main__':main()
