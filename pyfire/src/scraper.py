import time
import threading
import metrics
import sys
import logging 


class Scraper(object):
    def __init__(self, delegate, perceptor_client, kube_client, hub_clients, perceptor_pause=30, kube_pause=30, hub_pause=60):
        self.delegate = delegate

        self.perceptor_client = perceptor_client
        self.perceptor_thread = threading.Thread(target=self.perceptor)
        self.perceptor_pause = perceptor_pause

        self.kube_client = kube_client
        self.kube_thread = threading.Thread(target=self.kube)
        self.kube_pause = kube_pause

        # TODO
        #  1. allow creation, deletion of hub clients dynamically
        #  2. use one thread per hub client
        self.hub_clients = {}
        self.hub_threads = {}
        for url in my_config["Hub"]["Hosts"]:
            self.hub_clients[url] = HubClient(url, my_config["Hub"]["User"], my_config["Hub"]["PasswordEnvVar"], my_config["Skyfire"]["UseInClusterConfig"])
            self.hub_threads[url] = threading.Thread(target=self.hub(url))
        self.hub_pause = hub_pause

        self.is_running = False
    
    def start(self):
        """
        TODO this can't safely be called more than once
        """
        self.is_running = True
        self.perceptor_thread.start()
        self.kube_thread.start()
        for hub_url, hub_thread in self.hub_threads.items():
            hub_thread.start()
    
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
            scrape = self.perceptor_client.get_scrape()
            self.delegate.perceptor_dump(scrape)
            logging.debug("got perceptor dump")
            metrics.record_event("perceptorDump")
            time.sleep(self.perceptor_pause)
    
    def kube(self):
        while self.is_running:
            scrape = self.kube_client.get_scrape()
            self.delegate.kube_dump(scrape)
            logging.debug("got kube dump")
            metrics.record_event("kubeDump")
            time.sleep(self.kube_pause)

    def hub(self, hub_host):
        def hub_thread():
            while self.is_running:
                scrape = self.hub_clients[hub_host].get_scrape()
                self.delegate.hub_dump(hub_host, scrape)
                logging.debug("got hub dump")
                metrics.record_event("hubDump"+hub_host)
                time.sleep(self.hub_pause)
        return hub_instance

class MockDelegate:
    def __init__(self):
        import queue
        self.q = queue.Queue()
    def perceptor_dump(self, dump):
        self.q.put(("perceptor", dump))
    def kube_dump(self, dump):
        self.q.put(("kube", dump))
    def hub_dump(self, host, dump):
        self.q.put(("hub", dump, host))
    
class MockScraper:
    def __init__(self, name):
        self.name = name
    def get_scrape(self):
        return {'scrape_type': self.name}


def reader():
    """
    This is just an example, don't use it in production data centers!
    """
    delegate = MockDelegate()
    hub_clients = {
        'abc': MockScraper("hubabc"),
        'def': MockScraper("hubdef")
    }
    s = Scraper(
        delegate,
        MockScraper("perceptor"),
        MockScraper("kube"), 
        hub_clients, 
        perceptor_pause=2, 
        kube_pause=3, 
        hub_pause=4)
    s.start()

    while True:
        item = delegate.q.get()
        print("got next:", item)
        if item is None:
            break
#        f(item)
        delegate.q.task_done()

def real_reader(conf):
    """
    Another example not to be used in PDCs!
    """
    from cluster_clients import PerceptorClient, KubeClientWrapper, HubClient

    perceptor_client = PerceptorClient(conf['Perceptor']['Host'])

    kube_client = KubeClientWrapper(conf["Skyfire"]["UseInClusterConfig"])

    hub_clients = {}
    for host in conf["Hub"]["Hosts"]:
        hub_clients[host] = HubClient(host, conf["Hub"]["User"], conf["Hub"]["PasswordEnvVar"])

    delegate = MockDelegate()
    s = Scraper(delegate, perceptor_client, kube_client, hub_clients, perceptor_pause=15, kube_pause=15, hub_pause=30)
    s.start()

    while True:
        item = delegate.q.get()
        print("got next:", item)
        if item is None:
            break
        delegate.q.task_done()


if __name__ == "__main__":
    run_demo_1 = True
    if run_demo_1:
        t = threading.Thread(target=reader)
        t.start()
    else:
        import json
        config_path = sys.argv[1]
        with open(config_path) as f:
            config_json = json.load(f)

        real_reader(config_json)
