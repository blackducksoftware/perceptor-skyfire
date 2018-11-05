from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
import threading
import json
import time
import queue
from skyfire import *


paths = set(['/latestreport'])

class Handler(BaseHTTPRequestHandler):
    def __init__(self, model, *args, **kwargs):
        print("init handler: ", args, kwargs)
        self.model = model
        print("model:", self.model)
        super(Handler, self).__init__(*args, **kwargs)
    
    def _set_headers(self, headers):
        for (key, val) in headers.items():
            self.send_header(key, val)
        self.end_headers()

    def do_GET(self):
        if self.path not in paths:
            self.send_response(404)
            self.wfile.write(b'')
            return
        self.send_response(200)
        self._set_headers({'Content-type': 'application/json'})
        report = self.model.get_latest_report()
        self.wfile.write(bytes(report, 'utf-8'))

#    def do_HEAD(self):
#        self._set_headers()
#        
#    def do_POST(self):
#        self._set_headers()
#        self.wfile.write(b"{}")


def get_server_handler(model):
    def handler(*args, **kwargs):
        return Handler(model, *args, **kwargs)
    return handler

def start_http_server(port, skyfire):
    server = ThreadingHTTPServer(('', port), get_server_handler(skyfire))
    print('Starting http server...')
    try:
        server.serve_forever()
    except:
        server.socket.close()

    print('finished starting')


if __name__ == "__main__":
    start_http_server(3102, MockSkyfire())
