import logging

def find_duplicated_items(item_list):
    duplicates = []
    found_items = {}
    for item in item_list:
        if item in found_items:
            duplicates.append(item)
        else:
            found_items[item] = True
    return duplicates

class PerceptorReport:
    def __init__(self, scrape):
        logging.debug("perceptor report, scrape: ")

        self.hubs = []
        self.num_hubs = 0
        self.num_images = 0
        self.num_pods = 0
        self.num_containers = 0
        self.num_images_in_multiple_containers = 0
        self.num_shas_in_hubs = 0
        self.num_pod_namespaces = 0

        self.parse_scrape(scrape)

    def parse_scrape(self, scrape):
        self.hubs = scrape.hub_names
        self.num_hubs = len(scrape.hub_names)
        self.num_pods = len(scrape.pod_names)
        self.num_containers = len(scrape.container_names)
        self.num_images = len(scrape.image_shas)
        duplicate_shas = find_duplicated_items(scrape.pod_shas)
        self.num_images_in_multiple_containers = len(duplicate_shas)
        self.num_shas_in_hubs = len(scrape.hub_shas)
        self.num_pod_namespaces = len(set(scrape.pod_namespaces))
    
    def json(self):
        return {
            'num_hubs': self.num_hubs,
            'num_shas_in_hubs' : self.num_shas_in_hubs,
            'num_containers' : self.num_containers,
            'num_images': self.num_images,
            'num_pods': self.num_pods,
            'num_images_in_multiple_containers': self.num_images_in_multiple_containers,
            'num_pod_namespaces' : self.num_pod_namespaces
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

    def json(self):
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
        self.respositories = []
        self.num_repositories = 0
        self.parse_scrape(scrape)

    def parse_scrape(self, scrape):
        self.respositories = scrape.data 
        self.num_repositories = len(self.respositories)

    def json(self):
        pass

class perceptorKubeReport:
    def __init__(self, perceptor_scrape, kube_scrape):
        self.all_kube_repositories = set()
        self.all_perceptor_repositories = set()
        self.only_perceptor_repositories = set()
        self.only_kube_repositories = set()
        self.intersection_repositories = set()

        self.parse_scrapes(perceptor_scrape, kube_scrape)

    def parse_scrapes(self, perceptor_scrape, kube_scrape):
        self.all_kube_repositories = set( [x.split(":")[0] for x in kube_scrape.data] )
        self.all_perceptor_repositories = set(perceptor_scrape.image_repositories)
        self.only_perceptor_repositories = self.all_perceptor_repositories.difference(self.all_kube_repositories)
        self.only_kube_repositories = self.all_kube_repositories.difference(self.all_perceptor_repositories)
        self.intersection_repositories = self.all_kube_repositories.intersection(self.all_perceptor_repositories)

    def json(self):
        return {
            "all_kube_repositories" : len(self.all_kube_repositories),
            "all_perceptor_repositories" : len(self.all_perceptor_repositories),
            "only_perceptor_repositories" :len(self.only_perceptor_repositories),
            "only_kube_repositories" : len(self.only_kube_repositories),
            "intersection_repositories" : len(self.intersection_repositories)
        }


class HubPerceptorReport:
    def __init__(self, hub_scrape, perceptor_scrape):
        self.all_hub_shas = set()
        self.all_perceptor_shas = set()
        self.only_hub_shas = set()
        self.only_perceptor_shas = set()
        self.intersection_shas = set()

        self.parse_scrape(hub_scrape, perceptor_scrape)
    
    def parse_scrape(self, hub_scrape, perceptor_scrape):
        self.all_hub_shas = set(hub_scrape.shas)
        self.all_perceptor_shas = set(perceptor_scrape.image_shas)
        self.only_hub_shas = self.only_hub_shas.difference(self.only_perceptor_shas)
        self.only_perceptor_shas = self.only_perceptor_shas.difference(self.only_hub_shas)
        self.intersection_shas = self.only_hub_shas.intersection(self.only_perceptor_shas)

    def json(self):
        return {
            "all_hub_shas" : len(self.all_hub_shas),
            "all_perceptor_shas" : len(self.all_perceptor_shas),
            "only_hub_shas" : len(self.only_hub_shas),
            "only_perceptor_shas" : len(self.only_perceptor_shas),
            "intersection_shas" : len(self.intersection_shas)
        }

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


