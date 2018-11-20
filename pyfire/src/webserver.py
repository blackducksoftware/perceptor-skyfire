from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
import cgi
import threading
import json
import time
import queue
from .skyfire import MockSkyfire
from . import metrics 
import logging 


paths = set(['/latestreport','/testsuite'])

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
        if self.path == '/latestreport':
            report = self.model.get_latest_report()
        elif self.path == '/testsuite':
            report = self.model.get_test_suite()
        self.wfile.write(bytes(report, 'utf-8'))
        logging.debug("GET request successful")

#    def do_HEAD(self):
#        self._set_headers()
#        
    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile, 
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })

        # Begin the response
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes('Path: %s\n' % self.path,'utf-8'))
        print(self.path)
        if self.path == "/starttest":
            self.model.start_test_suite()


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
