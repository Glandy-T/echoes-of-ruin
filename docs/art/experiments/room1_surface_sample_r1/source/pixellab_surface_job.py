"""One guarded official PixelLab edit per original surface guide. No secrets saved."""
from pathlib import Path
import argparse,base64,importlib.util,json,sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pixellab_direct',ROOT.parent/'pixellab_direct_api_check_v1/source/pixellab_direct.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['submit','poll']);p.add_argument('surface',choices=['floor','wall']);a=p.parse_args()
 token=api.credential(True);key=a.surface;record=ROOT/'source'/f'{key}_job.json'
 if a.action=='submit':
  if record.exists():raise RuntimeError('Existing job record; poll it, never blindly resubmit.')
  h=128 if key=='floor' else 136
  payload={'method':'edit_with_text','edit_images':[{'width':128,'height':h,
    'image':{'type':'base64','base64':base64.b64encode((ROOT/'guides'/f'{key}_original.png').read_bytes()).decode()}}],
   'image_size':{'width':128,'height':h},'description':(ROOT/'source'/f'{key}_prompt.txt').read_text(encoding='utf-8'),
   'seed':2026102701 if key=='floor' else 2026102702,'no_background':False}
  result=api.request('POST','/edit-images-v2',token,payload)
  safe={k:result.get(k) for k in ['background_job_id','status','usage']}
  record.write_text(json.dumps(safe,indent=2),encoding='utf-8');print(json.dumps(safe));return
 job=json.loads(record.read_text())['background_job_id'];result=api.request('GET','/background-jobs/'+job,token)
 safe={k:result.get(k) for k in ['id','status','usage']};last=result.get('last_response') or {}
 if result.get('status')=='completed':
  imgs=last.get('images') or ([last['image']] if last.get('image') else [])
  if isinstance(imgs,dict):imgs=[imgs]
  saved=[]
  for i,img in enumerate(imgs):
   if isinstance(img,dict) and img.get('base64'):
    file=ROOT/'raw'/f'{key}_pro_{i:02d}.png';file.write_bytes(base64.b64decode(img['base64'].split(',')[-1],validate=True));saved.append(file.name)
  safe['saved_images']=saved
 else:safe['progress']=last.get('progress')
 (ROOT/'source'/f'{key}_status.json').write_text(json.dumps(safe,indent=2),encoding='utf-8');print(json.dumps(safe))

if __name__=='__main__':
 try:main()
 except Exception as e:
  print(str(e) if isinstance(e,RuntimeError) else type(e).__name__+': request failed; no automatic retry',file=sys.stderr);sys.exit(1)
