import logging


class PerceptorReport:
    def __init__(self, scrape):
        logging.debug("perceptor report, scrape: ")
        self.hubs = []
        self.num_hubs = 0
        self.num_images = 0
        self.num_pods = 0
        self.parse_scrape(scrape.data)

    def parse_scrape(self, scrape):
        self.hubs = list(scrape["Hubs"].keys())
        self.num_hubs = len(self.hubs)
    
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


