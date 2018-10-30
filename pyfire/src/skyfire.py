import threading
import json


class Skyfire:
    def __init__(self, scraper):
        self.scraper = scraper
        self.scraper_thread = threading.Thread(target=self.read_dumps)
        self.is_running = False
        self.opssight = None
        self.kube = None
        self.hub = None

    def start(self):
        self.scraper_thread.start()
        self.is_running = True
    
    def stop(self):
        self.is_running = False
    
    def read_dumps(self):
        while self.is_running:
            (dump_type, dump) = self.scraper.q.get()
            if dump_type == "opssight":
                self.opssight = dump
            elif dump_type == "kube":
                self.kube = dump
            elif dump_type == "hub":
                self.hub = dump
            else:
                raise Exception("invalid dump type {}".format(dump_type))
            self.scraper.q.task_done()

    def model(self):
        # TODO: this should be made thread-safe
        return json.dumps({
            'opssight': self.opssight,
            'kube': self.kube,
            'hub': self.hub,
        })
