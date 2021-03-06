import threading
import json
import queue
import logging
from reports import *
import util
import metrics 
from testsuite import TestSuite

import sys


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
    def __init__(self, skyfire_port=80, in_cluster=True):
        self.logger = logging.getLogger("Skyfire")

        # Thread for reading requests off the Queue
        self.q = queue.Queue()
        self.event_thread = threading.Thread(target=self.handle_requests)
        self.event_thread.daemon = True
        self.is_running = True
        self.event_thread.start()

        # Report objects - Represent latest state of Skyfire
        self.kube_scrape = None
        self.perceptor_scrapes = {}
        self.hub_scrapes = {}

        # Testing object
        self.tester = TestSuite(skyfire_port, in_cluster)
        self.test_report = {}
    
    def stop(self):
        self.is_running = False
        self.event_thread.join()
        self.logger.info("Skyfire Event Thread is terminated")
    
    ### Read requests and scrapes off the Queue

    def handle_requests(self):
        self.logger.info("Started Skyfire Requests Queue")
        while self.is_running:
            request_type, request = self.q.get()
            self.logger.debug("Got a Request off the Queue - %s", request_type)
            metrics.record_skyfire_request_event("received_queue_request")
            try:
                request()
            except Exception as e:
                self.logger.error("Unable to process Request: %s", e)
                metrics.record_error("failed_queue_request")
            self.logger.debug("Finished processing Request from the Queue")
            self.q.task_done()
        self.logger.warning("Skyfire Request Thread is terminated")
    
    ### Scraper Delegate interface - Put scrapes requests onto the Queue

    def enqueue_kube_scrape(self, scrape, err):
        if err is not None:
            self.logger.error(str(err))
            metrics.record_error("Kube Scrape Error")
            return 
        def request():
            self.kube_scrape = scrape
            metrics.record_skyfire_request_event("kube_scrape")
            metrics.record_kube_report(KubeReport(self.kube_scrape))
        self.q.put(("kube",request))

    def enqueue_perceptor_scrape(self, host, scrape, err):
        if err is not None:
            self.logger.error(str(err))
            metrics.record_error("Perceptor Scrape Error")
            return
        def request():
            self.perceptor_scrapes[host] = scrape
            metrics.record_skyfire_request_event("perceptor_scrape")
            metrics.record_opssight_report(PerceptorReport(list(self.perceptor_scrapes.values())))
        self.q.put(("perceptor",request))

    def enqueue_hub_scrape(self, host, scrape, err):
        if err is not None:
            self.logger.error(str(err))
            metrics.record_error("Hub Scrape Error")
            return 
        def request():
            self.hub_scrapes[host] = scrape
            metrics.record_skyfire_request_event("hub_scrape")
            metrics.record_hub_report(HubReport(list(self.hub_scrapes.values())))
        self.q.put(("hub",request))

    ### Web Server interface - Put server requests onto the queue

    def get_latest_report(self):
        self.logger.debug("skyfire: get_latest_report")
        # All threads stop executing at their wait() until 2 have called wait(), then all proceed
        barrier = threading.Barrier(2)

        # this nasty `wrapper` hack is because python doesn't like capturing+mutating strings
        report_wrapper = {} # wrapper remains in this scope but can be accessed from where the function is called
        def request():
            
            metrics.record_skyfire_request_event("get_latest_report")
            skyfire_report = {
                'kube-report' : KubeReport(self.kube_scrape),
                'opssight-reports' : dict([(host,PerceptorReport([scrape])) for (host,scrape) in self.perceptor_scrapes.items()]),
                'mult-opssight-reports' : PerceptorReport(list(self.perceptor_scrapes.values())),
                'hub-reports' : dict([(host,HubReport([scrape])) for (host,scrape) in self.hub_scrapes.items()]),
                'mult-hub-reports' : HubReport(list(self.hub_scrapes.values())),
                'mult-perceptor-kube-report' : PerceptorKubeReport(list(self.perceptor_scrapes.values()), self.kube_scrape), 
                'mult-hub-mult-perceptor-report' : HubPerceptorReport(list(self.hub_scrapes.values()), list(self.perceptor_scrapes.values()))
            }
            report_wrapper['report_json'] = json.dumps(skyfire_report, default=util.default_json_serializer, indent=2)
            self.logger.debug("Waiting in queue in request function")
            barrier.wait()

        self.q.put(("latestreport",request))

        # Wait until request is executed on the queue and updates wrapper
        self.logger.debug("Waiting for queued request in get_latest_report")
        barrier.wait()
        return report_wrapper['report_json']

            
    def start_test_suite(self):
        self.logger.debug("skyfire: start_test_suite")
        def request():
            metrics.record_skyfire_request_event("start_test_suite")
            self.tester.start()
        self.q.put(('starttestsuite',request))

    def get_test_suite(self):
        self.logger.debug("skyfire: get_test_suite")
        barrier = threading.Barrier(2)
        report_wrapper = {}
        def request():
            metrics.record_skyfire_request_event("get_test_suite")
            self.test_report = self.tester.get_results()
            report_wrapper['report_json'] = json.dumps(self.test_report, default=util.default_json_serializer, indent=2)
            self.logger.debug("Waiting in queue in request function")
            barrier.wait()
        self.q.put(('gettestsuite',request))
        self.logger.debug("Waiting for queued request in get_test_suite")
        barrier.wait()
        return report_wrapper['report_json']