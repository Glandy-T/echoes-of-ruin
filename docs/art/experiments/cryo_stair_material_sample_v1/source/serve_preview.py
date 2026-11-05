"""Loopback-only review server, restricted to this sample and its asset directory."""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,unquote

ROOT=Path(__file__).resolve().parents[5]
EXP=ROOT/'docs/art/experiments/cryo_stair_material_sample_v1'
ASSET=ROOT/'assets/art/cryo_stair_material_sample_v1'
URL='/docs/art/experiments/cryo_stair_material_sample_v1/preview.html'
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        if self.path=='/':
            self.send_response(302);self.send_header('Location',URL);self.end_headers();return
        decoded=unquote(urlsplit(self.path).path)
        candidate=(ROOT/decoded.lstrip('/')).resolve()
        allowed=any(candidate.is_relative_to(base) for base in (EXP,ASSET))
        if not allowed or candidate.is_dir() or any(x in candidate.name for x in ('balance_','.log','.blend1')) or '__pycache__' in candidate.parts:
            self.send_error(403);return
        super().do_GET()
    def log_message(self,*args):pass
print('STAIR_PREVIEW http://127.0.0.1:8893'+URL,flush=True)
ThreadingHTTPServer(('127.0.0.1',8893),Handler).serve_forever()
