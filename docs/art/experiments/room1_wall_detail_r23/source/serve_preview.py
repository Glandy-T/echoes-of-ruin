"""Read-only loopback preview when the app's local HTML file viewer cannot load."""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import unquote,urlsplit
import argparse
EXP=Path(__file__).resolve().parent.parent
class PreviewHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parts=unquote(urlsplit(self.path).path).replace('\\','/').split('/')
        if any(p.lower().startswith('balance_') or p.lower().endswith('.log') or p=='__pycache__' for p in parts):
            self.send_error(403);return
        super().do_GET()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8874);args=p.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(PreviewHandler,directory=str(EXP)))
    print(f'Room 1 r23 preview: http://127.0.0.1:{args.port}/preview.html',flush=True)
    server.serve_forever()
