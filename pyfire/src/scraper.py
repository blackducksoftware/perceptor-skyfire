import queue
import time
import threading
from cluster_clients import *
import metrics
import json 
import sys

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

    def perceptor(self):
        i = 0
        while self.is_running:
            perceptor_scrape = self.perceptor_client.get_scrape()
            self.q.put(perceptor_scrape)
            metrics.record_event("perceptorDump")
            i += 1
            time.sleep(self.perceptor_pause)
    
    def kube(self):
        i = 0
        while self.is_running:
            kube_scrape = self.kube_client.get_scrape()
            self.q.put(kube_scrape)
            metrics.record_event("kubeDump")
            i += 1
            time.sleep(self.kube_pause)

    def hub(self, hub_url):
        def hub_instance():
            i = 0
            while self.is_running:
                hub_scrape = self.hub_clients[hub_url].get_scrape()
                self.q.put(hub_scrape)
                metrics.record_event("hubDump:"+hub_url)
                i += 1
                time.sleep(self.hub_pause)
        return hub_instance

def reader(c):
    s = Scraper(perceptor_pause=15.0, kube_pause=15.5, hub_pause=15.0, my_config=c)
    s.start()

    perceptor_scrape = None 
    kube_scrape = None 
    hub_scrapes = {}
    for url in c["Hub"]["Hosts"]:
        hub_scrapes[url] = None

    while True:
        item = s.q.get()
        #print("got next:", item)
        if item is None:
            break

        if isinstance(item, kubeScrape):
            kube_scrape = item 
        elif isinstance(item, PerceptorScrape):
            perceptor_scrape = item
        else:
            hub_scrapes[item.hub] = item
        
        if perceptor_scrape != None and True in [True for x in list(hub_scrapes.values()) if x != None]:
            print("== Perceptor vs Hub ==")
            opssight_pod_images = set(perceptor_scrape.get_pods_images())
            hub_code_location_images = []
            for hub_url, hub_scrape in hub_scrapes.items():
                if hub_scrape != None:
                    hub_code_location_images.extend(hub_scrape.get_code_location_shas())
                else:
                    print("Missing Data for Hub:",hub_url)
            hub_code_location_images = set(hub_code_location_images)
            inter = opssight_pod_images.intersection(hub_code_location_images)

            print("OpsSight Images: " + str(len(opssight_pod_images)))
            print("Hub Images: "+str(len(hub_code_location_images)))
            print("Images From Hub that OpsSight Found: "+str(len(inter)))
        else:
            print("No Hub Data or Perceptor Data Available")
        print("")
    
        if perceptor_scrape != None and kube_scrape != None:
            print("== Perceptor vs Kube ==")
            opsight_repositories = set(perceptor_scrape.get_pods_repositories())
            kube_images = set([x.split(":")[0] for x in kube_scrape.data])
            inter = kube_images.intersection(opsight_repositories)
            diff_images = kube_images.difference(opsight_repositories)

            print("Images in Cluster: "+str(len(kube_images)))
            print("Images in Cluster that OpsSight Found: "+str(len(inter)))
            print("Images Untracked in Cluster: "+str(len(diff_images)))
        else:
            print("No Perceptor or Kube Data Available")
        print("")

        s.q.task_done()



if __name__ == "__main__":
    config_path = sys.argv[1]
    with open(config_path) as f:
        config_json = json.load(f)

    reader(config_json)
    

    
