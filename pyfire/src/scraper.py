import time
import threading
import metrics
import logging 
from cluster_clients import MockClient 

class Scraper(object):
    def __init__(self, logger, skyfire_delegate, perceptor_client, kube_client, hub_clients, perceptor_pause, kube_pause, hub_pause):
        self.logger = logger
        self.skyfire_delegate = skyfire_delegate
        self.is_running = True

        # Start perceptor thread to put scrapes onto the queue
        self.perceptor_client = perceptor_client
        self.perceptor_pause = perceptor_pause
        self.perceptor_thread = threading.Thread(target=self.perceptor_scrape_thread)
        self.perceptor_thread.daemon = True
        self.perceptor_thread.start()

        # Start kube thread to put scrapes onto the queue
        self.kube_client = kube_client
        self.kube_pause = kube_pause
        self.kube_thread = threading.Thread(target=self.kube_scrape_thread)
        self.kube_thread.daemon = True
        self.kube_thread.start()

        # Start hub threads to put scrapes onto the queue
        self.hub_clients = {}
        self.hub_pause = hub_pause
        for (host, client) in hub_clients.items():
            thread = threading.Thread(target=self.get_hub_scrape_thread(host))
            thread.daemon = True
            self.hub_clients[host] = {'client' : client, 'thread' : thread, 'should_run' : True}
            thread.start()

    def perceptor_scrape_thread(self):
        self.logger.info("Starting the Perceptor Scrape Thread")
        while self.is_running:
            try:
                scrape, err = self.perceptor_client.get_scrape()
                self.logger.debug("Received Perceptor Scrape")
                metrics.record_scrape_event("perceptor_scrape")
                self.skyfire_delegate.enqueue_perceptor_scrape(scrape, err)
            except Exception as e:
                metrics.record_error("failed_perceptor_scrape")
                self.logger.error("Uncaught Exception in Perceptor Scrape Thread: %s", str(e))
            time.sleep(self.perceptor_pause)
        self.logger.warning("Perceptor Scrape Thread terminated")
    
    def kube_scrape_thread(self):
        self.logger.info("Starting the Kube Scrape Thread")
        while self.is_running:
            try:
                scrape, err = self.kube_client.get_scrape()
                self.logger.debug("Received Kube Scrape")
                metrics.record_scrape_event("kube_scrape")
                self.skyfire_delegate.enqueue_kube_scrape(scrape, err)
            except Exception as e:
                metrics.record_error("failed_kube_scrape")
                self.logger.error("Uncaught Exception in Kube Scrape Thread: %s", str(e))
            time.sleep(self.kube_pause)
        self.logger.warning("Kube Scrape Thread terminated")

    def hub_scrape_thread(self, host):
        self.logger.info("Starting the Hub Scrape thread for %s", host)
        while self.is_running:
            client = self.hub_clients[host]['client']
            should_run = self.hub_clients[host]['should_run']
            if not should_run:
                break
            try:
                scrape, err = client.get_scrape()
                self.logger.debug("Received Hub Scrape from %s", host)
                metrics.record_scrape_event("hub_scrape")
                self.skyfire_delegate.enqueue_hub_scrape(host, scrape, err)
            except Exception as e:
                metrics.record_error("failed_hub_scrape")
                self.logger.error("Uncaught Exception in Hub %s scrape thread: %s", host, str(e))
            time.sleep(self.hub_pause)
        self.logger.warning("Hub Scrape Thread terminated - %s", host)


    def get_hub_scrape_thread(self, host):
        def hub_scrape_thread_wrapper():
            self.hub_scrape_thread(host)
        return hub_scrape_thread_wrapper

    def stop(self):
        """
        TODO this can't safely be called more than once
        """
        if self.is_running:
            self.is_running = False
            self.perceptor_thread.join()
            self.kube_thread.join()
            for host in self.hub_clients:
                self.stop_hub(host)
            self.logger.info("All Scraper Threads terminated")
        else:
            self.logger.warning("Scraper Threads already stopped")

    def stop_hub(self, host):
        self.hub_clients[host]['should_run'] = False
        self.hub_clients[host]['thread'].join()
        del self.hub_clients[host]











def reader():
    """
    This is just an example, don't use it in production data centers!
    """
    from skyfire import MockSkyfire
    delegate = MockSkyfire()
    hub_clients = {
        'abc': MockClient("hubabc"),
        'def': MockClient("hubdef")
    }
    s = Scraper(
        delegate,
        MockClient("perceptor"),
        MockClient("kube"), 
        hub_clients, 
        perceptor_pause=2,
        kube_pause=3,
        hub_pause=4)
    logging.debug("instantiated scraper: %s", str(s))

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
