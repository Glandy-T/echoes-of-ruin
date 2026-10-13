"""Submit/poll one official Pro wall edit; keep credentials and signed URLs private."""
from pathlib import Path
import argparse, base64, importlib.util, json, sys, urllib.request

ROOT=Path(__file__).resolve().parents[1]
HELPER=ROOT.parent/'pixellab_direct_api_check_v1/source/pixellab_direct.py'
spec=importlib.util.spec_from_file_location('pixellab_direct',HELPER)
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)

def main():
 p=argparse.ArgumentParser();p.add_argument('action',choices=['submit','poll','balance'])
 a=p.parse_args();token=api.credential(True)
 (ROOT/'raw').mkdir(exist_ok=True)
 if a.action=='balance':
  r=api.request('GET','/balance',token)
  print(json.dumps({k:r.get(k) for k in ('credits','subscription')}));return
 if a.action=='submit':
  if (ROOT/'source/job_record.json').exists():
   raise RuntimeError('Job already submitted. Poll the recorded job; no automatic resubmission.')
  payload={'method':'edit_with_text','edit_images':[{'width':400,'height':272,
   'image':{'type':'base64','base64':base64.b64encode((ROOT/'guides/wall_layout.png').read_bytes()).decode()}}],
   'image_size':{'width':400,'height':272},
   'description':(ROOT/'source/wall_edit_prompt.txt').read_text(encoding='utf-8'),
   'seed':2026101301,'no_background':False}
  r=api.request('POST','/edit-images-v2',token,payload)
  safe={k:r[k] for k in ('background_job_id','status','usage') if k in r}
  (ROOT/'source/job_record.json').write_text(json.dumps(safe,indent=2),encoding='utf-8')
  print(json.dumps(safe));return
 job=json.loads((ROOT/'source/job_record.json').read_text())['background_job_id']
 r=api.request('GET','/background-jobs/'+job,token)
 safe={k:r.get(k) for k in ('id','status','usage')}
 last=r.get('last_response') or {}
 safe['result_keys']=list(last)
 # Only image metadata is output; do not dump response bodies or signed URLs.
 if r.get('status')=='completed':
  imgs=last.get('images') or ([last['image']] if last.get('image') else [])
  if isinstance(imgs,dict):imgs=[imgs]
  saved=[]
  for i,img in enumerate(imgs):
   if isinstance(img,dict) and img.get('base64'):
    path=ROOT/'raw'/f'wall_pro_{i:02d}.png'
    path.write_bytes(base64.b64decode(img['base64'].split(',')[-1],validate=True));saved.append(path.name)
   else:
    safe['image_result_shapes']=[list(x) if isinstance(x,dict) else type(x).__name__ for x in imgs]
  safe['saved_images']=saved
 elif r.get('status')=='processing':
  safe['queue_position']=last.get('queue_position')
  safe['estimated_wait_seconds']=last.get('estimated_wait_seconds')
 (ROOT/'source/job_status.json').write_text(json.dumps(safe,indent=2),encoding='utf-8')
 print(json.dumps(safe))

if __name__=='__main__':
 try:main()
 except Exception as e:
  # Avoid credential-bearing request or response dumps.
  print(f'{type(e).__name__}: {str(e) if isinstance(e,RuntimeError) else "Request failed; no automatic retry."}',file=sys.stderr)
  sys.exit(1)
