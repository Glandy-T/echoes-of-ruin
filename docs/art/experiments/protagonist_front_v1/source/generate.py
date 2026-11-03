"""One bounded PixelLab front concept. Never blindly retry an uncertain paid request."""
from pathlib import Path
import sys,json,time,base64,shutil
from PIL import Image
HERE=Path(__file__).resolve().parent;EXP=HERE.parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE))
from pixellab_api import credential,request

def find_image(v):
 if isinstance(v,dict):
  if isinstance(v.get('base64'),str):return v['base64']
  for child in v.values():
   found=find_image(child)
   if found:return found
 if isinstance(v,list):
  for child in v:
   found=find_image(child)
   if found:return found

def main():
 token=credential(True);state=HERE/'job_front.json';result=EXP/'result_front.json'
 if result.exists():print('EXISTING_RESULT_NO_NEW_CALL');return
 if state.exists():
  saved=json.loads(state.read_text(encoding='utf8'));jid=saved.get('background_job_id');assert jid,'Uncertain submission: do not duplicate POST.'
 else:
  payload=json.loads((HERE/'request.json').read_text(encoding='utf8'))
  state.write_text(json.dumps({'status':'submitting','endpoint':'/create-image-pro-flash'}),encoding='utf8')
  response=request('POST','/create-image-pro-flash',token,payload)
  saved={k:response.get(k) for k in ['background_job_id','status','usage','source_image_id']};jid=saved['background_job_id'];assert jid
  state.write_text(json.dumps(saved,indent=2),encoding='utf8');print('SUBMITTED',jid,flush=True)
 for i in range(60):
  response=request('GET','/background-jobs/'+jid,token);status=response.get('status')
  if status=='completed':
   last=response.get('last_response');data=find_image(last);assert data,'No encoded output; retain job, do not retry POST.'
   raw=base64.b64decode(data.split(',')[-1],validate=True);(EXP/'raw/front.png').write_bytes(raw)
   safe={'endpoint':'/create-image-pro-flash','background_job_id':jid,'status':status,'usage':response.get('usage'),'native_size':list(Image.open(EXP/'raw/front.png').size),'source_image_id':last.get('source_image_id') if isinstance(last,dict) else None,'input':'Text only; no external or NoAI reference uploaded.'}
   result.write_text(json.dumps(safe,indent=2),encoding='utf8');print('COMPLETED',json.dumps(safe),flush=True);return
  if status in ['failed','cancelled']:
   (HERE/'failed_job.json').write_text(json.dumps({'status':status,'background_job_id':jid}),encoding='utf8');raise RuntimeError('PixelLab job '+status+'; no auto retry.')
  print('WAIT',status,i,flush=True);time.sleep(10)
 raise RuntimeError('Timed out polling; resume saved job, do not duplicate POST.')

if __name__=='__main__':main()
