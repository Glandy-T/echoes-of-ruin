"""Official PixelLab transport; credentials stay in memory, never in artifacts."""
from pathlib import Path
import os,json,urllib.request,urllib.error

def credential(use_aseprite):
    token=os.environ.get('PIXELLAB_API_TOKEN')
    if not token and use_aseprite:
        manifest=Path(os.environ['APPDATA'])/'Aseprite/extensions/PixelLab/package.json'
        token=json.loads(manifest.read_text(encoding='utf-8'))['secret']
    if not token:raise RuntimeError('No configured PixelLab credential.')
    return token

def request(method,endpoint,token,payload=None):
    if not endpoint.startswith('/') or '://' in endpoint:raise ValueError('Official relative endpoint required.')
    data=None if payload is None else json.dumps(payload).encode('utf-8')
    req=urllib.request.Request('https://api.pixellab.ai/v2'+endpoint,data=data,method=method,headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):return None
    opener=urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req,timeout=180) as response:return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'PixelLab HTTP {exc.code}; request not retried.') from None
