import threading
import json
import queue
import logging
from reports import PerceptorReport


class Skyfire:
    def __init__(self, logger=logging.getLogger("skyfire")):
        self.logger = logger

        self.q = queue.Queue()
        self.event_thread = threading.Thread(target=self.read_events)
        self.event_thread.daemon = True
        self.is_running = True
        self.logger.info("starting skyfire event thread")
        self.event_thread.start()

        self.opssight = None
        self.opssight_report = None

        self.kube = None
        self.kube_report = None
        self.kube_opssight_report = None

        self.hubs = {}
    
    def stop(self):
        self.logger.info("stopping skyfire event thread")
        self.is_running = False
        self.event_thread.join()
    
    def read_events(self):
        while self.is_running:
            self.logger.debug("waiting for item to process")
            item = self.q.get()
            self.logger.debug("got item to process")
            try:
                item()
            except Exception as e:
                self.logger.error("unable to process event: %s", e)
            self.logger.debug("finished processing item")
            self.q.task_done()
        self.logger.info("exiting skyfire event thread")
    
    ### Scraper Delegate interface

    def perceptor_dump(self, dump):
        report = PerceptorReport(dump)
        def f():
            self.opssight = dump
            self.opssight_report = report
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
        self.logger.debug("skyfire: get_latest_report")
        b = threading.Barrier(2)
        # this nasty `wrapper` hack is because python doesn't like capturing+mutating strings
        wrapper = {}
        def f():
            dump_dict = {
                'opssight': self.opssight,
                'opssight-report': self.opssight_report,
                'kube': self.kube,
                'kube-report': self.kube_report,
                'hub': dict((host, dump) for (host, dump) in self.hubs.items())
            }
            wrapper['json'] = json.dumps(dump_dict, default=lambda o: o.__dict__, indent=2)
            self.logger.debug("waiting inside f")
            b.wait()
        self.q.put(f)
        self.logger.debug("waiting after putting item in q")
        b.wait()
        return wrapper['json']
