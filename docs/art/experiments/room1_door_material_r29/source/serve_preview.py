from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parent.parent
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def do_GET(self):
  if any(s in self.path for s in ['balance_','.log','.err','__pycache__','.blend1']):self.send_error(403);return
  super().do_GET()
 def log_message(self,*args):pass
print('R29_PREVIEW http://127.0.0.1:8880/preview.html',flush=True)
ThreadingHTTPServer(('127.0.0.1',8880),Handler).serve_forever()
