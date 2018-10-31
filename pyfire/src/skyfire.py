import threading
import json
import queue


class Skyfire:
    def __init__(self):
        self.q = queue.Queue()
        self.event_thread = threading.Thread(target=self.read_events)
        self.is_running = False
        self.opssight = None
        self.kube = None
        self.hubs = {}

    def start(self):
        self.event_thread.start()
        self.is_running = True
    
    def stop(self):
        self.is_running = False
        self.event_thread.join()
    
    def read_events(self):
        while self.is_running:
            item = self.q.get()
            (dump_type, dump) = item[0], item[1]
            if dump_type == "opssight":
                self.opssight = dump
            elif dump_type == "kube":
                self.kube = dump
            elif dump_type == "hub":
                host = item[2]
                self.hubs[host] = dump
            else:
                raise Exception("invalid dump type {}".format(dump_type))
            self.q.task_done()
    
    ### Scraper Delegate interface

    def perceptor_dump(self, dump):
        self.q.put(("perceptor", dump))

    def kube_dump(self, dump):
        self.q.put(("kube", dump))

    def hub_dump(self, host, dump):
        self.q.put(("hub", dump, host))

    ### Web Server interface

    def get_latest_report(self):
        # TODO: this should be made thread-safe
        return json.dumps({
            'opssight': self.opssight,
            'kube': self.kube,
            'hub': self.hubs,
        })
