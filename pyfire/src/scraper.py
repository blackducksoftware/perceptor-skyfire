import queue
import time
import threading
from cluster_clients import PerceptorClient, KubeClientWrapper, HubClient
import metrics
import json 
import sys
import logging 


class Scraper(object):
    def __init__(self, perceptor_client, kube_client, hub_clients, perceptor_pause=30, kube_pause=30, hub_pause=60):
        self.q = queue.Queue()

        self.perceptor_client = perceptor_client
        self.perceptor_thread = threading.Thread(target=self.perceptor)
        self.perceptor_pause = perceptor_pause

        self.kube_client = kube_client
        self.kube_thread = threading.Thread(target=self.kube)
        self.kube_pause = kube_pause

        # TODO
        #  1. allow creation, deletion of hub clients dynamically
        #  2. use one thread per hub client
        self.hub_clients = dict((host, client) for (host, client) in hub_clients.items())
        self.hub_thread = threading.Thread(target=self.hub)
        self.hub_pause = hub_pause

        self.is_running = False
    
    def start(self):
        """
        TODO this can't safely be called more than once
        """
        self.is_running = True
        self.perceptor_thread.start()
        self.kube_thread.start()
        self.hub_thread.start()
    
    def stop(self):
        """
        TODO this can't safely be called more than once, and
        assumes `start` has already been called
        """
        self.is_running = False
        self.perceptor_thread.join()
        self.kube_thread.join()
        self.hub_thread.join()

    def perceptor(self):
        while self.is_running:
            perceptor_scrape = self.perceptor_client.get_scrape()
            self.q.put(perceptor_scrape)
            logging.debug("got perceptor dump")
            metrics.record_event("perceptorDump")
            time.sleep(self.perceptor_pause)
    
    def kube(self):
        while self.is_running:
            kube_scrape = self.kube_client.get_scrape()
            self.q.put(kube_scrape)
            logging.debug("got kube dump")
            metrics.record_event("kubeDump")
            time.sleep(self.kube_pause)

    def hub(self):
        while self.is_running:
            hub_scrape = self.hub_clients[list(self.hub_clients.keys())[0]].get_scrape()
            self.q.put(hub_scrape)
            logging.debug("got hub dump")
            metrics.record_event("hubDump")
            time.sleep(self.hub_pause)


def reader():
    """
    This is just an example, don't use it in production data centers!
    """
    class MockScraper:
        def __init__(self, name):
            self.name = name
        def get_scrape(self):
            return {'scrape_type': self.name}
    hub_clients = {
        'abc': MockScraper("hubabc"),
        'def': MockScraper("hubdef")
    }
    s = Scraper(MockScraper("perceptor"), MockScraper("kube"), hub_clients, perceptor_pause=1.0, kube_pause=1.5, hub_pause=2.0)
    s.start()
    while True:
        item = s.q.get()
        print("got next:", item)
        if item is None:
            break
#        f(item)
        s.q.task_done()

def real_reader(conf):
    """
    Another example not to be used in PDCs!
    """
    perceptor_client = PerceptorClient(conf['Perceptor']['Host'])

    kube_client = KubeClientWrapper(conf["Skyfire"]["UseInClusterConfig"])

    hub_clients = {}
    for host in conf["Hub"]["Hosts"]:
        hub_clients[host] = HubClient(host, conf["Hub"]["User"], conf["Hub"]["PasswordEnvVar"])

    s = Scraper(perceptor_client, kube_client, hub_clients, perceptor_pause=15, kube_pause=15, hub_pause=30)
    s.start()
    while True:
        item = s.q.get()
        print("got next:", item)
        if item is None:
            break
        s.q.task_done()


if __name__ == "__main__":
    config_path = sys.argv[1]
    with open(config_path) as f:
        config_json = json.load(f)

    real_reader(config_json)  
