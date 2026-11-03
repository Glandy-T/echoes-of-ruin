from pathlib import Path
import json,base64,time
from PIL import Image
from pixellab_api import credential,request
HERE=Path(__file__).resolve().parent;EXP=HERE.parent
def encoded(p):
 im=Image.open(p);return {'image':{'base64':'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()},'size':{'width':im.width,'height':im.height}}
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
def main():
 token=credential(True);state=HERE/'job_back.json';dest=EXP/'result_back.json'
 if dest.exists():print('EXISTING_RESULT_NO_NEW_CALL');return
 if state.exists():saved=json.loads(state.read_text(encoding='utf8'));assert saved.get('background_job_id'),'Uncertain submission; do not duplicate POST'
 else:
  cfg=json.loads((HERE/'request.json').read_text(encoding='utf8'))
  payload={'description':(HERE/cfg['description_file']).read_text(encoding='utf8'),'inpainting_image':encoded(HERE/cfg['input']),'mask_image':encoded(HERE/cfg['mask']),'seed':cfg['seed'],'no_background':True,'crop_to_mask':False}
  state.write_text(json.dumps({'status':'submitting','endpoint':cfg['endpoint']}),encoding='utf8')
  reply=request('POST',cfg['endpoint'],token,payload);saved={k:reply.get(k) for k in ['background_job_id','status','usage']};assert saved['background_job_id'];state.write_text(json.dumps(saved,indent=2),encoding='utf8');print('SUBMITTED',saved['background_job_id'],flush=True)
 for _ in range(60):
  r=request('GET','/background-jobs/'+saved['background_job_id'],token);status=r.get('status')
  if status=='completed':
   data=find(r.get('last_response'));assert data
   p=EXP/'raw/back.png';p.write_bytes(base64.b64decode(data.split(',')[-1],validate=True))
   dest.write_text(json.dumps({'endpoint':'/inpaint-v3','background_job_id':saved['background_job_id'],'status':status,'usage':r.get('usage'),'native_size':list(Image.open(p).size)},indent=2),encoding='utf8');print('COMPLETED',json.dumps(r.get('usage')),flush=True);return
  if status in ['failed','cancelled']:raise RuntimeError('PixelLab '+status+'; no automatic retry')
  time.sleep(10)
 raise RuntimeError('Polling timeout; resume saved job without repeated POST')
if __name__=='__main__':main()
