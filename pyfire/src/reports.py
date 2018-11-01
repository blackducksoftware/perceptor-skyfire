import logging
'''
    opssight_analysis = opssight_client.get_analysis()
    print(opssight_analysis)
    #print(json.dumps( opssight_analysis.data ,indent=2))
    #print(opssight_analysis.get_pods_images())

    print("== OpsSight vs Hub ==")
    opssight_pod_images = set(opssight_analysis.get_pods_images())
    hub_code_location_images = set(hub_analysis.get_code_location_shas())
    print("OpsSight Images: " + str(len(opssight_pod_images)))
    print("Hub Images: "+str(len(hub_code_location_images)))
    inter = opssight_pod_images.intersection(hub_code_location_images)
    print("Images From Hub that OpsSight Found: "+str(len(inter)))
    

    print("")
    print("== OpsSight vs Cluster ==")
    opsight_repositories = set(opssight_analysis.get_pods_repositories())
    kube_images = set([x.split(":")[0] for x in kube_client.get_images()])
    print("Images in Cluster: "+str(len(kube_images)))
    inter = kube_images.intersection(opsight_repositories)
    print("Images in Cluster that OpsSight Found: "+str(len(inter)))
    diff_images = kube_images.difference(opsight_repositories)
    print("Images Untracked in Cluster: "+str(len(diff_images)))
'''
class PerceptorReport:
    def __init__(self, scrape):
        logging.debug("perceptor report, scrape: ")
        self.hubs = []
        self.num_hubs = 0
        self.num_images = 0
        self.num_pods = 0
        self.parse_scrape(scrape.data)

    def parse_scrape(self, scrape):
        self.hubs = scrape.hubs
        self.num_hubs = len(scrape.hubs)
        
    
    def json(self):
        return {
            'num_hubs': self.num_hubs,
            'num_images': self.num_images,
            'num_pods': self.num_pods
        }

class HubReport:
    def __init__(self, scrape):
        self.images = []
        self.num_images = 0
        self.versions = []
        self.num_versions = 0
        self.parse_scrape(scrape)

    def parse_scrape(self, scrape):
        pass

class MultipleHubReport:
    def __init__(self, scrapes):
        self.images = []
        self.num_images = 0
        self.parse_scrapes(scrapes)

    def parse_scrapes(self, scrapes):
        pass

class KubeReport:
    def __init__(self, scrape):
        self.images = []
        self.num_images = 0
        self.parse_scrape(scrape)

    def parse_scrape(self, scrape):
        pass

class perceptorKubeReport:
    def __init__(self, perceptor_scrape, kube_scrape):
        self.parse_scrapes(perceptor_scrape, kube_scrape)

    def parse_scrapes(self, perceptor_scrape, kube_scrape):
        pass 

class HubPerceptorReport:
    def __init__(self, hub_scrape, perceptor_scrape):
        self.parse_scrape(hub_scrape, perceptor_scrape)
    
    def parse_scrape(self, hub_scrape, perceptor_scrape):
        pass

class MultipleHubPerceptorReport:
    def __init__(self, hub_scrapes, perceptor_scrape):
        self.parse_scrapes(hub_scrapes, perceptor_scrape)
    
    def parse_scrapes(self, hub_scrapes, perceptor_scrape):
        pass

class HubKubeReport:
    def __init__(self, hub_scrape, kube_scrape):
        self.parse_scrapes(hub_scrape, kube_scrape)

    def parse_scrapes(self, hub_scrape, kube_scrape):
        pass

class MultipleHubKubeReport:
    def __init__(self, hub_scrapes, kube_scrape):
        self.parse_scrapes(hub_scrapes, kube_scrape)

    def parse_scrapes(self, hub_scrapes, kube_scrape):
        pass


