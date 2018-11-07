import threading
import json
import queue
import logging
from reports import PerceptorReport, KubeReport, HubReport
import util
import metrics 


class MockSkyfire():
    def __init__(self):
        self.q = queue.Queue()
    def enqueue_perceptor_scrape(self, scrape):
        self.q.put(("perceptor", scrape))
    def enqueue_kube_scrape(self, scrape):
        self.q.put(("kube", scrape))
    def enqueue_hub_scrape(self, host, scrape):
        self.q.put(("hub", scrape, host))
    def get_latest_report(self):
        return {'abc': 123}

class Skyfire:
    def __init__(self, logger=logging.getLogger("skyfire")):
        self.logger = logger

        # Thread for reading requests off the Queue
        self.q = queue.Queue()
        self.event_thread = threading.Thread(target=self.handle_requests)
        self.event_thread.daemon = True
        self.is_running = True
        self.logger.info("starting skyfire event thread")
        self.event_thread.start()

        # Report objects - Represent latest state of Skyfire
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
    
    ### Read requests and scrapes off the Queue

    def handle_requests(self):
        while self.is_running:
            self.logger.debug("Skyfire: Reading items off the queue...")
            request = self.q.get()
            self.logger.debug("Skyfire: Got a request from the queue")
            try:
                request()
            except Exception as e:
                self.logger.error("Unable to process event: %s", e)
            self.logger.debug("Finished processing item")
            self.q.task_done()
        self.logger.info("Exiting skyfire event thread")
    
    ### Scraper Delegate interface - Put scrapes requests onto the Queue

    def enqueue_perceptor_scrape(self, scrape, err):
        if err is not None:
            logging.error(str(err))
            metrics.record_error("PerceptorDump")
            return
        report = PerceptorReport(scrape)
        def request():
            metrics.record_skyfire_request("perceptor_scrape")
            self.opssight = scrape
            self.opssight_report = report
            metrics.record_opssight_report(report)
        self.q.put(request)

    def enqueue_kube_scrape(self, scrape):
        report = KubeReport(scrape)
        def request():
            metrics.record_skyfire_request("kube_scrape")
            self.kube = scrape
            self.kube_report = report
            metrics.record_kube_report(report)
        self.q.put(request)

    def enqueue_hub_scrape(self, host, scrape):
        report = HubReport(scrape)
        def request():
            metrics.record_skyfire_request("hub_scrape")
            self.hubs[host] = scrape
            hub_report = report
            metrics.record_hub_report(report)
        self.q.put(request)

    ### Web Server interface - Put server requests onto the queue

    def get_latest_report(self):
        self.logger.debug("skyfire: get_latest_report")
        # All threads stop executing at their wait() until 2 have called wait(), then all proceed
        barrier = threading.Barrier(2)

        # this nasty `wrapper` hack is because python doesn't like capturing+mutating strings
        report_wrapper = {} # wrapper remains in this scope but can be accessed from where the function is called
        def request():
            metrics.record_skyfire_request("get_latest_report")
            skyfire_report = {
                'opssight': self.opssight,
                'opssight-report': self.opssight_report,
                'kube': self.kube,
                'kube-report': self.kube_report,
                'hub': dict((host, dump) for (host, dump) in self.hubs.items())
            }
            report_wrapper['report_json'] = json.dumps(skyfire_report, default=util.default_json_serializer, indent=2)
            self.logger.debug("Waiting in queue in request function")
            barrier.wait()

        self.q.put(request)

        # Wait until request is executed on the queue and updates wrapper
        self.logger.debug("Waiting for queued request in get_latest_report")
        barrier.wait()
        return report_wrapper['report_json']
