from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parent.parent
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def log_message(self,*args):pass
print('TURNAROUND_PREVIEW http://127.0.0.1:8884/preview.html',flush=True)
ThreadingHTTPServer(('127.0.0.1',8884),Handler).serve_forever()
