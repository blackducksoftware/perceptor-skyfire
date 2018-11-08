import logging
import podreader 

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
        self.hubs = []

        self.num_hubs = 0
        self.num_images = 0
        self.num_pods = 0
        self.num_containers = 0
        self.num_images_in_multiple_containers = 0
        self.num_shas_in_hubs = 0
        self.num_pod_namespaces = 0

        self.has_all_labels_val = False 
        self.is_partially_labeled_val = False 
        self.has_all_annotations_val = False 
        self.is_partially_annotated_val = False 

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

        self.has_all_labels_val = self.has_all_labels("",scrape) 
        self.is_partially_labeled_val = self.is_partially_labeled("", scrape) 
        self.has_all_annotations_val = self.has_all_annotations("", scrape) 
        self.is_partially_annotated_val = self.is_partially_annotated("", scrape)  


    def get_opssight_labels(self, pod_name, scrape):
        expected = set(podreader.get_all_labels(len(scrape.container_names)))
        actual = set(scrape.dump[pod_name]['labels'].keys())
        present = expected.intersection(actual)
        missing = expected - actual
        return (missing, present)
    
    def has_all_labels(self, pod_name, scrape):
        missing, _ = scrape.get_opssight_labels(pod_name)
        return len(missing) == 0
    
    def is_partially_labeled(self, pod_name, scrape):
        missing, present = scrape.get_opssight_labels(pod_name)
        return len(missing) > 0 and len(present) > 0

    def get_opssight_annotations(self, pod_name, scrape):
        expected = set(podreader.get_all_annotations(len(scrape.container_names)))
        actual = set(scrape.dump[pod_name]['annotations'].keys())
        present = expected.intersection(actual)
        missing = expected - actual
        return (missing, present)
    
    def has_all_annotations(self, pod_name, scrape):
        missing, _ = scrape.get_opssight_annotations(pod_name)
        return len(missing) == 0
    
    def is_partially_annotated(self, pod_name, scrape):
        missing, present = scrape.get_opssight_annotations(pod_name)
        return len(missing) > 0 and len(present) > 0


class HubReport:
    def __init__(self, scrape):
        self.num_projects = 0
        self.num_versions = 0
        self.num_projects_with_one_version = 0
        self.num_projects_with_multiple_versions = 0
        self.num_projects_with_no_versions = 0
        self.num_code_locations = 0
        self.num_shas = 0
        self.num_unique_shas = 0
        self.num_scans = 0
        self.num_code_locations_with_scans = 0
        self.num_code_locations_with_no_scans = 0

        self.parse_scrape(scrape)

    def parse_scrape(self, scrape):
        self.num_projects = len(scrape.project_urls)
        self.num_versions = len(scrape.version_urls)
        self.num_code_locations = len(scrape.code_location_urls)
        self.num_shas = len(scrape.shas)
        self.num_unique_shas = len(set(scrape.shas))

        

        for code_loc in scrape.code_location_urls:
            num_scans = len(scrape.code_location_to_scans[code_loc].keys())
            self.num_scans += num_scans
            if num_scans > 0:
                self.num_code_locations_with_scans += 1
            else:
                self.num_code_locations_with_no_scans += 1
                
        for project in scrape.project_urls:
            if len(scrape.project_to_versions[project]) == 1:
                self.num_projects_with_one_version += 1
            elif len(scrape.project_to_versions[project]) > 1:
                self.num_projects_with_multiple_versions += 1
            else:
                self.num_projects_with_no_versions += 1
            

class MultipleHubReport:
    def __init__(self, scrapes):
        self.projects = []
        self.versions = []
        self.code_locations = []
        self.shas = []

        self.num_projects = 0
        self.num_versions = 0
        self.num_code_locations = 0
        self.num_shas_in_projects = 0
        self.num_unique_shas = 0

        self.parse_scrapes(scrapes)

    def parse_scrapes(self, scrapes):
        for scrape in scrapes:
            self.projects.extend(scrape.project_urls)
            self.versions.extend(scrape.version_urls)
            self.code_locations.extend(scrape.code_location_urls)
            self.shas.extend(scrape.shas)
        self.num_projects = len(set(self.projects))
        self.num_versions = len(set(self.versions))
        self.num_code_locations = len(set(self.code_locations))
        self.num_shas_in_projects = len(self.shas)
        self.num_unique_shas = len(set(self.shas))
        
        

class KubeReport:
    def __init__(self, scrape):
        self.num_namespaces = 0
        self.num_pods = 0
        self.num_annotations = 0
        self.num_labels = 0
        self.num_containers = 0
        self.num_images = 0
        self.num_unique_images = 0

        self.parse_scrape(scrape)

    def parse_scrape(self, scrape):
        self.num_namespaces = len(scrape.namespaces)
        self.num_pods = len(scrape.pod_names)
        self.num_annotations = len(scrape.pod_annotations)
        self.num_labels = len(scrape.pod_labels)
        self.num_containers = len(scrape.container_names)
        self.num_images = len(scrape.container_images)
        self.num_unique_images = len(set(scrape.container_images))

    

class perceptorKubeReport:
    def __init__(self, perceptor_scrape, kube_scrape):
        self.all_kube_repositories = set()
        self.all_perceptor_repositories = set()
        self.only_perceptor_repositories = set()
        self.only_kube_repositories = set()
        self.intersection_repositories = set()

        self.num_all_kube_repositories = 0
        self.num_all_perceptor_repositories = 0
        self.num_only_perceptor_repositories = 0
        self.num_only_kube_repositories = 0
        self.num_intersection_repositories = 0

        self.parse_scrapes(perceptor_scrape, kube_scrape)

    def parse_scrapes(self, perceptor_scrape, kube_scrape):
        self.all_kube_repositories = set( [x.split(":")[0] for x in kube_scrape.container_images] )
        self.all_perceptor_repositories = set(perceptor_scrape.image_repositories)
        self.only_perceptor_repositories = self.all_perceptor_repositories.difference(self.all_kube_repositories)
        self.only_kube_repositories = self.all_kube_repositories.difference(self.all_perceptor_repositories)
        self.intersection_repositories = self.all_kube_repositories.intersection(self.all_perceptor_repositories)

        self.num_all_kube_repositories = len(self.all_kube_repositories)
        self.num_all_perceptor_repositories = len(self.all_perceptor_repositories)
        self.num_only_perceptor_repositories = len(self.only_perceptor_repositories)
        self.num_only_kube_repositories = len(self.only_kube_repositories)
        self.num_intersection_repositories = len(self.intersection_repositories)

class HubPerceptorReport:
    def __init__(self, hub_scrape, perceptor_scrape):
        self.all_hub_shas = set()
        self.all_perceptor_shas = set()
        self.only_hub_shas = set()
        self.only_perceptor_shas = set()
        self.intersection_shas = set()

        self.num_all_hub_shas = 0
        self.num_all_perceptor_shas = 0
        self.num_only_hub_shas = 0
        self.num_only_perceptor_shas = 0
        self.num_intersection_shas = 0

        self.parse_scrape(hub_scrape, perceptor_scrape)
    
    def parse_scrape(self, hub_scrape, perceptor_scrape):
        self.all_hub_shas = set(hub_scrape.shas)
        self.all_perceptor_shas = set(perceptor_scrape.image_shas)
        self.only_hub_shas = self.all_hub_shas.difference(self.all_perceptor_shas)
        self.only_perceptor_shas = self.all_perceptor_shas.difference(self.all_hub_shas)
        self.intersection_shas = self.all_hub_shas.intersection(self.all_perceptor_shas)

        self.num_all_hub_shas = len(self.all_hub_shas)
        self.num_all_perceptor_shas = len(self.all_perceptor_shas)
        self.num_only_hub_shas = len(self.only_hub_shas)
        self.num_only_perceptor_shas = len(self.only_perceptor_shas)
        self.num_intersection_shas = len(self.intersection_shas)

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


