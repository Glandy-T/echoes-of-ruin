"""Official PixelLab REST API helper. Never writes or prints credentials.

Prefer PIXELLAB_API_TOKEN. --use-aseprite-account explicitly reads the already
configured official extension's credential in memory, for this same service.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

BASE = 'https://api.pixellab.ai/v2'

def credential(use_aseprite):
    token = os.environ.get('PIXELLAB_API_TOKEN')
    if not token and use_aseprite:
        manifest = Path(os.environ['APPDATA']) / 'Aseprite/extensions/PixelLab/package.json'
        token = json.loads(manifest.read_text(encoding='utf-8'))['secret']
    if not token:
        raise RuntimeError('No credential configured; use environment or explicit extension option.')
    return token

def request(method, endpoint, token, payload=None):
    if not endpoint.startswith('/') or '://' in endpoint:
        raise ValueError('Only official API relative endpoints are allowed.')
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(BASE + endpoint, data=data, method=method,
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    # Do not follow authenticated redirects to an unverified host.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=180) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        # No response body/header dump: it may contain private account details.
        raise RuntimeError(f'PixelLab HTTP {exc.code}; request was not retried.') from None

def main():
    p=argparse.ArgumentParser()
    p.add_argument('action', choices=['balance', 'generate', 'job'])
    p.add_argument('--use-aseprite-account', action='store_true')
    p.add_argument('--payload', type=Path)
    p.add_argument('--endpoint', default='/create-image-pixen')
    p.add_argument('--job-id')
    p.add_argument('--output', type=Path, required=True)
    a=p.parse_args()
    token=credential(a.use_aseprite_account)
    endpoint='/balance' if a.action=='balance' else (
        '/background-jobs/'+a.job_id if a.action=='job' else a.endpoint)
    payload=json.loads(a.payload.read_text(encoding='utf-8-sig')) if a.payload else None
    result=request('POST' if a.action=='generate' else 'GET', endpoint, token, payload)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    # Store only safe useful fields; no arbitrary account response or image URLs.
    safe={k:result[k] for k in ('usage','enhance_usage','background_job_id','id','status') if k in result}
    if a.action=='balance':
        safe={key:result.get(key) for key in ('credits','subscription')}
    img=result.get('image')
    if img and img.get('base64'):
        encoded=img['base64'].split(',')[-1]
        image_path=a.output.with_suffix('.png')
        image_path.write_bytes(base64.b64decode(encoded,validate=True))
        safe['image_file']=image_path.name
    a.output.write_text(json.dumps(safe,indent=2),encoding='utf-8')
    print(json.dumps(safe))

if __name__=='__main__':
    try:
        main()
    except (RuntimeError,urllib.error.URLError) as exc:
        print(str(exc),file=sys.stderr)
        sys.exit(1)
