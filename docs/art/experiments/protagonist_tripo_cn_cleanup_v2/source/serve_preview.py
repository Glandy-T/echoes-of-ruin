from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import unquote,urlsplit
ROOT=Path(__file__).resolve().parent.parent
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        file=(ROOT/unquote(urlsplit(self.path).path).lstrip('/')).resolve()
        if not file.is_relative_to(ROOT) or file.is_dir() or any(s in file.name for s in ('account_','full_ui','.log','.blend1')) or '__pycache__' in file.parts:
            self.send_error(403);return
        super().do_GET()
    def log_message(self,*args):pass
print('CHARACTER_CLEANUP_PREVIEW http://127.0.0.1:8896/preview.html',flush=True)
ThreadingHTTPServer(('127.0.0.1',8896),Handler).serve_forever()
