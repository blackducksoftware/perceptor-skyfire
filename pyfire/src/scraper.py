import time
import threading
import metrics
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

        self.hub_clients = {}
        for (host, client) in hub_clients.items():
            self._add_hub(host, client)
        self.hub_pause = hub_pause

        self.is_running = False
    
    def _add_hub(self, host, client):
        def f():
            self.hub(host)
        thread = threading.Thread(target=f)
        self.hub_clients[host] = [client, thread, self.is_running]
    
    def add_hub(self, host, client):
        self._add_hub(host, client)
        _, thread, _ = self.hub_clients[host]
        if self.is_running:
            thread.start()
    
    def start(self):
        """
        TODO this can't safely be called more than once
        """
        self.is_running = True
        self.perceptor_thread.start()
        self.kube_thread.start()
        for (_, thread, _) in self.hub_clients.values():
            thread.start()
    
    def _stop_hub(self, host):
        self.hub_clients[host][2] = False

    def stop(self):
        """
        TODO this can't safely be called more than once, and
        assumes `start` has already been called
        """
        self.is_running = False
        self.perceptor_thread.join()
        self.kube_thread.join()
        for host in self.hub_clients:
            self._stop_hub(host)
        for (_, thread, _) in self.hub_clients.values():
            thread.join()

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

    def hub(self, host):
        while self.is_running:
            client, _, should_run = self.hub_clients[host]
            if not should_run:
                break
            scrape = client.get_scrape()
            self.delegate.hub_dump(host, scrape)
            logging.debug("got hub dump from %s", host)
            metrics.record_event("hubDump-{}".format(host))
            time.sleep(self.hub_pause)


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
    filenames = {
        'perceptor': './src/staticDumps/staticPerceptorScrape.txt'
    }
    def __init__(self, name):
        self.name = name
    def get_scrape(self):
        import json
        import cluster_clients
        if self.name in MockScraper.filenames:
            with open(MockScraper.filenames[self.name], 'r') as f:
                return cluster_clients.PerceptorScrape(json.load(f))
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


if __name__ == "__main__":
    t = threading.Thread(target=reader)
    t.start()
