import logging
import podformat 

def find_duplicated_items(item_list):
    duplicates = []
    found_items = {}
    for item in item_list:
        if item in found_items:
            duplicates.append(item)
        else:
            found_items[item] = True
    return duplicates

class KubeReport:
    def __init__(self, scrape):
        self.scrape = scrape 

        self.num_namespaces = 0
        self.num_pods = 0
        self.num_containers = 0
        self.num_images = 0

        self.num_pods_fully_labeled = 0
        self.num_pods_partially_labeled = 0
        self.num_pods_fully_annotated = 0 
        self.num_pods_partially_annotated = 0

        self.pods_fully_labeled = []
        self.pods_partially_labeled = []
        self.pods_fully_annotated = []
        self.pods_partially_annotated = []

        self.parse_scrape(scrape)

    def parse_scrape(self, scrape):
        if scrape is None:
            return 
        self.num_namespaces = len(scrape.namespaces)
        self.num_pods = len(scrape.uids)
        self.num_containers = len(scrape.ns_pod_name_to_containers.values())
        self.num_images = len(scrape.image_repos)

        self.pods_fully_labeled = [pod_name for pod_name in scrape.ns_pod_names if self.has_all_labels(pod_name,scrape)]
        self.pods_partially_labeled = [pod_name for pod_name in scrape.ns_pod_names if self.is_partially_labeled(pod_name,scrape)]
        self.pods_not_labeled = [pod_name for pod_name in scrape.ns_pod_names if self.has_no_labels(pod_name,scrape)]

        self.pods_fully_annotated = [pod_name for pod_name in scrape.ns_pod_names if self.has_all_annotations(pod_name,scrape)]
        self.pods_partially_annotated = [pod_name for pod_name in scrape.ns_pod_names if self.is_partially_annotated(pod_name,scrape)]
        self.pods_not_annotated = [pod_name for pod_name in scrape.ns_pod_names if self.has_no_annotations(pod_name,scrape)]

        self.num_pods_fully_labeled = len(self.pods_fully_labeled)
        self.num_pods_partially_labeled = len(self.pods_partially_labeled)
        self.pods_not_labeled = len(self.pods_not_labeled)

        self.num_pods_fully_annotated = len(self.pods_fully_annotated)
        self.num_pods_partially_annotated = len(self.pods_partially_annotated)
        self.pods_not_annotated = len(self.pods_not_annotated)

    def get_opssight_labels(self, pod_name, scrape):
        expected = set(podformat.get_all_labels(len(scrape.container_names)))
        actual = set()
        if scrape.ns_pod_name_to_labels[pod_name] is not None:
            actual = set(scrape.ns_pod_name_to_labels[pod_name].keys())
        present = expected.intersection(actual)
        missing = expected - actual
        return (missing, present)

    def has_all_labels(self, pod_name, scrape):
        missing, _ = self.get_opssight_labels(pod_name, scrape)
        return len(missing) == 0
    
    def is_partially_labeled(self, pod_name, scrape):
        missing, present = self.get_opssight_labels(pod_name, scrape)
        return len(missing) > 0 and len(present) > 0

    def has_no_labels(self, pod_name, scrape):
        _, present = self.get_opssight_labels(pod_name, scrape)
        return len(present) == 0

    def get_opssight_annotations(self, pod_name, scrape):
        expected = set(podformat.get_all_annotations(len(scrape.container_names)))
        actual = set()
        if scrape.ns_pod_name_to_annotations[pod_name] is not None:
            actual = set(scrape.ns_pod_name_to_annotations[pod_name].keys())
        present = expected.intersection(actual)
        missing = expected - actual
        return (missing, present)
    
    def has_all_annotations(self, pod_name, scrape):
        missing, _ = self.get_opssight_annotations(pod_name, scrape)
        return len(missing) == 0
    
    def is_partially_annotated(self, pod_name, scrape):
        missing, present = self.get_opssight_annotations(pod_name, scrape)
        return len(missing) > 0 and len(present) > 0

    def has_no_annotations(self, pod_name, scrape):
        _, present = self.get_opssight_annotations(pod_name, scrape)
        return len(present) == 0

    
class HubReport:
    def __init__(self, scrape):
        self.scrapes = scrape 

        self.num_projects = 0
        self.num_versions = 0
        self.num_code_locs = 0
        self.num_code_loc_shas = 0

        self.num_projects_with_one_version = 0
        self.num_projects_with_multiple_versions = 0
        self.num_projects_with_no_versions = 0
        
        self.num_code_locations_with_scans = 0
        self.num_code_locations_with_no_scans = 0

        self.num_code_loc_in_multiple_projects = 0
        self.num_code_loc_in_multiple_versions = 0

        self.parse_scrape(scrape)

    def parse_scrape(self, scrapes):
        #TODO - check logic for combining multiple hubs and not double-couting items
        if scrapes is None:
            return 
        code_loc_shas = []
        for scrape in scrapes:
            self.num_projects += len(scrape.project_urls)
            self.num_versions += len(scrape.version_urls)
            self.num_code_locs += len(scrape.code_loc_urls)
            code_loc_shas.extend(scrape.code_loc_shas)

            for project_url in scrape.project_urls:
                if len(scrape.project_url_to_version_urls[project_url]) == 1:
                    self.num_projects_with_one_version += 1
                elif len(scrape.project_url_to_version_urls[project_url]) > 1:
                    self.num_projects_with_multiple_versions += 1
                else:
                    self.num_projects_with_no_versions += 1

            for code_loc in scrape.code_loc_shas:
                num_scans = len(scrape.code_loc_sha_to_scans[code_loc].keys())
                if num_scans > 0:
                    self.num_code_locations_with_scans += 1
                else:
                    self.num_code_locations_with_no_scans += 1

            for code_loc_sha, project_urls in scrape.code_loc_sha_to_project_urls.items():
                if len(project_urls) > 1:
                    self.num_code_loc_in_multiple_projects += 1

            for code_loc_sha, version_urls in scrape.code_loc_sha_to_version_urls.items():
                if len(version_urls) > 1:
                    self.num_code_loc_in_multiple_versions += 1

        self.num_code_loc_shas += len(set(scrape.code_loc_shas))
                

class PerceptorReport:
    def __init__(self, scrape):
        self.scrape = scrape 

        self.hubs = []

        self.num_hubs = 0
        self.num_images_in_hubs = 0

        self.num_pods = 0
        self.num_containers = 0

        self.num_images_in_multiple_containers = 0



        self.num_code_loc_shas_in_queue = 0

        self.parse_scrape(scrape)

    def parse_scrape(self, scrape):
        if scrape is None:
            return 
        self.hubs = scrape.hub_names
        self.num_hubs = len(scrape.hub_names)
        self.num_images_in_hubs = len(scrape.hub_name_to_shas.values())

        self.num_pods = len(scrape.ns_pod_names)
        self.num_containers = len(scrape.ns_pod_name_to_containers.values())

        sha_per_container = []
        for pod_name, pod_containers in scrape.ns_pod_name_to_containers.items():
            sha_per_container.extend([container['Image']['Sha'] for container in pod_containers])
        duplicate_shas = find_duplicated_items(sha_per_container)
        self.num_images_in_multiple_containers = len(duplicate_shas)

        self.num_code_loc_shas_in_queue = len(scrape.scan_queue_shas)


class PerceptorKubeReport:
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
        if perceptor_scrape is None or kube_scrape is None:
            return 
        return
        #TODO - change to use scrape attributes
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
        if hub_scrape is None or perceptor_scrape is None:
            return 
        return 
        #TODO - change to use scrape attributes
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

class HubKubeReport:
    def __init__(self, hub_scrape, kube_scrape):
        self.parse_scrapes(hub_scrape, kube_scrape)

    def parse_scrapes(self, hub_scrape, kube_scrape):
        if hub_scrape is None or kube_scrape is None:
            return 
        pass
