from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
import threading
import json
import time
import queue
from skyfire import *
import metrics 
import logging 


paths = set(['/latestreport'])

class Handler(BaseHTTPRequestHandler):
    def __init__(self, model, *args, **kwargs):
        logging.info("Init Handler: %s", str(args)+" "+str(kwargs))
        self.model = model
        logging.info("Model: %s", self.model)
        super(Handler, self).__init__(*args, **kwargs)
    
    def _set_headers(self, headers):
        for (key, val) in headers.items():
            self.send_header(key, val)
        self.end_headers()

    def do_GET(self):
        metrics.record_http_request_event("GET")
        if self.path not in paths:
            self.send_response(404)
            self.wfile.write(b'')
            logging.debug("GET request for invalid Path")
            return
        self.send_response(200)
        self._set_headers({'Content-type': 'application/json'})
        report = self.model.get_latest_report()
        self.wfile.write(bytes(report, 'utf-8'))
        logging.debug("GET request successful")

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
    try:
        server.serve_forever()
        logging.info('Started Skyfire http server')
    except:
        logging.error("Could not serve forever")
        server.socket.close()


if __name__ == "__main__":
    start_http_server(3102, MockSkyfire())
