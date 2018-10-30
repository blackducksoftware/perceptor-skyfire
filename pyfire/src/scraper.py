import queue
import time
import threading
from cluster_clients import *


class Scraper(object):
    def __init__(self, perceptor_pause=30, kube_pause=30, hub_pause=60, my_config=None):
        self.q = queue.Queue()
        p = my_config['Perceptor']['URL']
        self.perceptor_client = PerceptorClient(p, my_config["Skyfire"]["UseInClusterConfig"])
        self.perceptor_thread = threading.Thread(target=self.perceptor)
        self.perceptor_pause = perceptor_pause

        self.kube_client = KubeClientWrapper(my_config["Skyfire"]["UseInClusterConfig"])
        self.kube_thread = threading.Thread(target=self.kube)
        self.kube_pause = kube_pause

        self.hub_clients = {}
        for url in my_config["Hub"]["Hosts"]:
            self.hub_clients[url] = HubClient(url, my_config["Hub"]["User"], my_config["Hub"]["PasswordEnvVar"], my_config["Skyfire"]["UseInClusterConfig"])
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

    def perceptor(self):
        i = 0
        while self.is_running:
#            print("perceptor", i)
            perceptor_scrape = self.perceptor_client.get_scrape()
            self.q.put(perceptor_scrape)
            i += 1
            time.sleep(self.perceptor_pause)
    
    def kube(self):
        i = 0
        while self.is_running:
#            print("kube", i)
            kube_scrape = self.kube_client.get_scrape()
            self.q.put(kube_scrape)
            i += 1
            time.sleep(self.kube_pause)

    def hub(self):
        i = 0
        while self.is_running:
#            print("hub", i)
            hub_scrape = self.hub_clients[list(self.hub_clients.keys())[0]].get_scrape()
            self.q.put(hub_scrape)
            i += 1
            time.sleep(self.hub_pause)

def reader():
    s = Scraper(perceptor_pause=1.0, kube_pause=1.5, hub_pause=2.0, my_config=c)
    s.start()
    while True:
        item = s.q.get()
        print("got next:", item)
        if item is None:
            break
#        f(item)
        s.q.task_done()

def my_reader(c):
    s = Scraper(perceptor_pause=1.0, kube_pause=1.5, hub_pause=2.0, my_config=c)
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

    my_reader(config_json)
    

    
