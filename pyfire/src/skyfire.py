import threading
import json
import queue
import logging


class Skyfire:
    def __init__(self):
        self.q = queue.Queue()
        self.event_thread = threading.Thread(target=self.read_events)
        self.is_running = False
        self.opssight = None
        self.kube = None
        self.hubs = {}

    def start(self):
        logging.info("starting skyfire event thread")
        self.is_running = True
        self.event_thread.start()
    
    def stop(self):
        logging.info("stopping skyfire event thread")
        self.is_running = False
        self.event_thread.join()
    
    def read_events(self):
        while self.is_running:
            logging.debug("waiting for item to process")
            item = self.q.get()
            logging.debug("got item to process")
            try:
                item()
            except Exception as e:
                logging.error("unable to process event: %s", e)
            logging.debug("finished processing item")
            self.q.task_done()
        logging.info("exiting skyfire event thread")
    
    ### Scraper Delegate interface

    def perceptor_dump(self, dump):
        def f():
            self.opssight = dump
        self.q.put(f)

    def kube_dump(self, dump):
        def f():
            self.kube = dump
        self.q.put(f)

    def hub_dump(self, host, dump):
        def f():
            self.hubs[host] = dump
        self.q.put(f)

    ### Web Server interface

    def get_latest_report(self):
        logging.debug("skyfire: get_latest_report")
        b = threading.Barrier(2)
        # this nasty `wrapper` hack is because python doesn't like capturing+mutating strings
        wrapper = {}
        def f():
            wrapper['json'] = {
                'opssight': self.opssight,
                'kube': self.kube,
                'hub': dict((host, dump) for (host, dump) in self.hubs.items())
            }
            logging.debug("waiting inside f")
            b.wait()
        self.q.put(f)
        logging.debug("waiting after putting item in q")
        b.wait()
        return wrapper['json']
