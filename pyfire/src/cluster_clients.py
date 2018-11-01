import json
import requests
# import urllib3
import datetime 
import time
from kubernetes import client, config
import logging 


def get_current_datetime():
    return str(datetime.datetime.now())

class kubeScrape:
    def __init__(self):
        self.time_stamp = get_current_datetime()
        self.data = []
    
    def __repr__(self):
        output = "== Kube Analysis ==\n"
        num_images = len(self.data)
        output += "Num Images: "+str(num_images)+"\n"
        return output
    
class KubeClientWrapper:
    def __init__(self, in_cluster):
        if in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self.v1 = client.CoreV1Api()

    def get_scrape(self):
        kube_scrape = KubeScrape()
        kube_scrape.data = self.get_images()
        return kube_scrape 

    def get_namespaces(self):
        return [ns.metadata.name for ns in self.v1.list_namespace()]

    def get_pods(self, namespace="all-namespaces"):
        if namespace == "all-namespaces":
            return self.v1.list_pod_for_all_namespaces(watch=False)
        else:
            return self.v1.list_namespaced_pod(namespace)

    def get_containers(self):
        containers = []
        for pod in self.v1.list_pod_for_all_namespaces().items:
            containers.extend(pod.spec.containers)
        return containers

    def get_images(self):
        images = []
        for pod in self.v1.list_pod_for_all_namespaces().items:
            for container in pod.spec.containers:
                images.append(container.image)
        return images

    def get_annotations(self):
        return [pod.metadata.annotations for pod in self.v1.list_pod_for_all_namespaces()]

    def get_labels(self):
        return [pod.metadata.labels for pod in self.v1.list_pod_for_all_namespaces()]

class HubScrape():
    def __init__(self, data={}):
        self.time_stamp = get_current_datetime()
        self.data = data

        self.project_urls = []
        self.version_urls = []
        self.code_location_urls = []
        self.shas = []

        self.project_to_versions = {}

        self.version_to_risk_profile = {}
        self.version_to_policy_status = {}

        self.code_location_to_scans = {}

        self.sha_to_code_location_url = {}
        self.sha_to_version_url = {}
        self.sha_to_project_url = {}
        self.sha_to_scans = {}

        self.load_data(data)

    def __repr__(self):
        output = "== Hub Analysis ==\n"
        num_projects = len(self.data.keys())
        num_code_locations = 0
        for project_ID, project_data in self.data.items():
            for version_ID, version_data in project_data["versions"].items():
                num_code_locations += len(version_data['codelocations'].keys())
        output += "Num Projects: "+str(num_projects)+"\n"
        output += "Total Code Locations: "+str(num_code_locations)+"\n"
        return output 

    def load_data(self, data):
        for project_url, project_data in data.items():
            self.project_urls.append(project_url)
            self.project_to_versions[project_url] = []
            for version_url, version_data in project_data['versions'].items():
                self.version_urls.append(version_url)
                self.project_to_versions[project_url].append(version_url)
                self.version_to_risk_profile[version_url] = version_data['riskProfile']
                self.version_to_policy_status[version_url] = version_data['policy-status']
                for code_loc_url, code_loc_data in version_data['codelocations'].items():
                    self.code_location_urls.append(code_loc_url)
                    self.code_location_to_scans[code_loc_url] = code_loc_data['scans']
                    sha = code_loc_data['sha']
                    self.shas.append(sha)
                    self.sha_to_code_location_url[sha] = code_loc_url 
                    self.sha_to_version_url[sha] = version_url 
                    self.sha_to_project_url[sha] = project_url
                    self.sha_to_scans[sha] = code_loc_data['scans']

    def get_code_location_shas(self):
        shas = []
        for project_ID, project_data in self.data.items():
            for version_ID, version_data in project_data["versions"].items():
                for code_location_ID, code_location_data in version_data['codelocations'].items():
                    shas.append(code_location_data['sha'])
        return shas 

class HubClient():
    def __init__(self, host_name, port, username, password, client_timeout_seconds):
        self.host_name = host_name
        self.port = port
        self.username = username
        self.password = password
        self.secure_login_cookie = self.get_secure_login_cookie()
        self.max_projects = 10000000
        # TODO do something with this
        self.client_timeout_seconds = client_timeout_seconds

    def get_secure_login_cookie(self):
        security_headers = {'Content-Type':'application/x-www-form-urlencoded'}
        security_data = {'j_username': self.username,'j_password': self.password}
        # verify=False does not verify SSL connection - insecure
        url = "https://{}:{}/j_spring_security_check".format(self.host_name, self.port)
        r = requests.post(url, verify=False, data=security_data, headers=security_headers)
        return r.cookies 

    def api_get(self, url):
        # Try to request data 50 times
        for i in range(50):
            r = requests.get(url, verify=False, cookies=self.secure_login_cookie)
            if r.status_code == 200:
                return r
        print("Could not contact: "+url)

    def get_scrape(self):
        hub_scrape = HubScrape()
        hub_scrape.data = self.crawl_hub()
        return hub_scrape 

    def crawl_hub(self):
        dump = self.api_get("https://"+self.host_name+":443/api"+"/projects?limit="+str(self.max_projects)).json()
        projects = {}
        for project in dump['items']:
            project_href = project['_meta']['href'] 
            project_name = project['name']
            # map link to link name
            project_links = {}
            for link in project['_meta']['links']:
                project_links[link['rel']] = link['href']
            # get data from version url
            project_versions = self.crawl_version(project_links['versions'])
            projects[project_href] = {"name" : project_name, "links" : project_links, "versions" : project_versions}
        return projects 
    
    def crawl_version(self, version_url):
        dump = self.api_get(version_url).json()
        versions = {}
        for version in dump['items']:
            version_href = version['_meta']["href"]
            # map link to link name
            version_links = {}
            for link in version['_meta']["links"]:
                version_links[link['rel']] = link['href']
            version_risk_profile = self.crawl_risk_profile(version_links['riskProfile'])
            version_policy_status = self.crawl_policy_status(version_links['policy-status'])
            version_code_locations = self.crawl_code_location(version_links['codelocations'])
            versions[version_href] = {
                "links" : version_links, 
                "policy-status" : version_policy_status,
                "riskProfile" : version_risk_profile, 
                "codelocations" : version_code_locations
            }
        return versions 

    def crawl_policy_status(self, policy_status_url):
        dump = self.api_get(policy_status_url).json()
        policy_status_overall_status = dump['overallStatus']
        try:
            policy_status_updated_at = dump['updatedAt']
        except:
            policy_status_updated_at = None
        # map component count name to value
        policy_status_component_version_status_counts = {}
        for status_count in dump['componentVersionStatusCounts']:
            policy_status_component_version_status_counts[status_count['name']] = status_count['value']
        return {'overallStatus' : policy_status_overall_status, 
                'updatedAt' : policy_status_updated_at,
                'compnentVersionStatusCounts' : policy_status_component_version_status_counts
                }

    def crawl_risk_profile(self, risk_profile_url):
        dump = self.api_get(risk_profile_url).json()
        return {'categories' : dump['categories']}

    def crawl_code_location(self, code_location_url):
        dump = self.api_get(code_location_url).json()
        code_locations = {}
        for code_location in dump['items']:
            code_location_href = code_location['_meta']['href'] 
            code_location_sha = code_location['name']
            code_location_links = {}
            for link in code_location['_meta']['links']:
                code_location_links[link['rel']] = link['href']
            code_location_scan_summaries = self.crawl_scan_summary(code_location_links['scans'])
            code_locations[code_location_href] = {
                'sha' : code_location_sha,
                'links' : code_location_links,
                'scans' : code_location_scan_summaries
            }
        return code_locations

    def crawl_scan_summary(self, scan_summary_url):
        dump = self.api_get(scan_summary_url).json()
        scan_summaries = {}
        for scan_summary in dump['items']:
            scan_summary_href = scan_summary['_meta']['href']
            scan_summary_status = scan_summary["createdAt"]
            scan_summary_created_at = scan_summary["createdAt"]
            scan_summary_updated_at = scan_summary["updatedAt"]
            scan_summaries[scan_summary_href] = {
                'createdAt' : scan_summary_created_at,
                'status' : scan_summary_status,
                'updatedAt' : scan_summary_updated_at
            }
        return scan_summaries 


class PerceptorScrape:
    def __init__(self, data={}):
        self.time_stamp = get_current_datetime()
        self.data = data

        self.hub_names = []
        self.hub_to_shas = {}

        self.pod_names = []
        self.pod_shas = []
        self.container_names = []
        self.repositories = []

        self.image_shas = []
        self.image_repositories = []
        self.image_sha_to_risk_profile = {}
        self.image_sha_to_policy_status = {}
        self.image_sha_to_scans = {}
        self.image_sha_to_respositories = {}

        self.load_data(data)

    
    def json(self):
        return self.data

    def __repr__(self):
        output = "== OpsSight Analysis ==\n"
        output += "Hub Count: "+str(len(self.get_hubs_IDs()))+"\n"
        output += "Total Pod Count: "+str(len(self.get_pods_IDs()))+"\n"
        output += "Total Image Count: "+str(len(self.get_images_IDs()))+"\n"
        output += " - Images Scanned: "+str(len(self.get_images_IDs()) - len(self.get_scan_queue_images()))+"\n"
        output += " - Images Queued: "+str(len(self.get_scan_queue_images()))+"\n"
        return output 

    def load_data(self, data):
        for hub_name, hub_data in data["Hubs"].items():
            self.hub_names.append(hub_name)
            shas = list(hub_data["CodeLocations"].keys())
            self.hub_to_shas[hub_name] = shas 

        for pod_name, pod_data in data["CoreModel"]["Pods"].items():
            self.pod_names.append(pod_name)
            for container in pod_data["Containers"]:
                self.repositories.append(container["Image"]["Repository"])
                self.pod_shas.append(container["Image"]["Sha"])
                self.container_names.append(container["Name"])

        for image_sha, image_data in data["CoreModel"]["Images"].items():
            self.image_shas.append(image_sha)
            self.image_sha_to_risk_profile[image_sha] = image_data["ScanResults"]["RiskProfile"]
            self.image_sha_to_policy_status[image_sha] = image_data["ScanResults"]["PolicyStatus"]
            self.image_sha_to_scans[image_sha] = image_data["ScanResults"]["ScanSummaries"]
            self.image_sha_to_respositories[image_sha] = []
            for repo in image_data["RepoTags"]:
                self.image_sha_to_respositories[image_sha].append(repo["Repository"]) 
                self.image_repositories.append(repo["Repository"])

        for image_sha in data["CoreModel"]["ImageScanQueue"]:
            pass 

    def get_hubs_IDs(self):
        return self.data["Hubs"].keys()

    def get_pods_IDs(self):
        return self.data["CoreModel"]["Pods"].keys()

    def get_pods_images(self):
        images = []
        for pod_ID, pod_data in self.data["CoreModel"]["Pods"].items():
            for container in pod_data["Containers"]:
                images.append(container['Image']['Sha'])
        return images

    def get_pods_repositories(self):
        repositories = []
        for pod_ID, pod_data in self.data["CoreModel"]["Pods"].items():
            for container in pod_data["Containers"]:
                repositories.append(container['Image']['Repository'])
        return repositories
        
    def get_images_IDs(self):
        return self.data["CoreModel"]["Images"].keys()

    def get_scan_queue_images(self):
        images = []
        for elem in self.data["CoreModel"]["ImageScanQueue"]:
            images.append(elem['Key'])
        return images

class PerceptorClient():
    def __init__(self, host_name, port):
        self.host_name = host_name
        self.port = port

    def get_scrape(self):
        dump = self.get_dump()
        return PerceptorScrape(dump)

    def get_dump(self):
        while True:
            r = requests.get("http://{}:{}/model".format(self.host_name, self.port))
            if r.status_code == 200:
                return json.loads(r.text)



