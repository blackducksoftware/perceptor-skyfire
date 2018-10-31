import json
import requests
import urllib3
import datetime 
import time
from kubernetes import client, config
import logging 


class KubeScrape:
    def __init__(self, data=[]):
        self.time_stamp = datetime.datetime.now()
        self.data = data
    
    def pretty_print(self):
        output = "== Kube Analysis ==\n"
        num_images = len(self.data)
        output += "Num Images: "+str(num_images)+"\n"
        print(output)

    def load_data(self, data):
        self.data = data

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
        self.time_stamp = datetime.datetime.now()
        self.hub = ""
        self.data = data

    def pretty_print(self):
        output = "== Hub Analysis ==\n"
        num_projects = len(self.data.keys())
        num_code_locations = 0
        for project_ID, project_data in self.data.items():
            for version_ID, version_data in project_data["versions"].items():
                num_code_locations += len(version_data['codelocations'].keys())
        output += "Num Projects: "+str(num_projects)+"\n"
        output += "Total Code Locations: "+str(num_code_locations)+"\n"
        print(output)

    def load_data(self, data):
        self.data = data

    def get_code_location_shas(self):
        shas = []
        for project_ID, project_data in self.data.items():
            for version_ID, version_data in project_data["versions"].items():
                for code_location_ID, code_location_data in version_data['codelocations'].items():
                    shas.append(code_location_data['sha'])
        return shas 

class HubClient():
    def __init__(self, host_name, username, password):
        self.host_name = host_name
        self.username = username
        self.password = password 
        self.secure_login_cookie = self.get_secure_login_cookie()
        self.max_projects = 10000000

    def get_secure_login_cookie(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        security_headers = {'Content-Type':'application/x-www-form-urlencoded'}
        security_data = {'j_username': self.username,'j_password': self.password}
        # verify=False does not verify SSL connection - insecure
        r = requests.post("https://"+self.host_name+":443/j_spring_security_check", verify=False, data=security_data, headers=security_headers)
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
        hub_scrape.hub = self.host_name
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
        self.time_stamp = datetime.datetime.now()
        self.data = data

    def pretty_print(self):
        output = "== OpsSight Analysis ==\n"
        output += "Hub Count: "+str(len(self.get_hubs_IDs()))+"\n"
        output += "Total Pod Count: "+str(len(self.get_pods_IDs()))+"\n"
        output += "Total Image Count: "+str(len(self.get_images_IDs()))+"\n"
        output += " - Images Scanned: "+str(len(self.get_images_IDs()) - len(self.get_scan_queue_images()))+"\n"
        output += " - Images Queued: "+str(len(self.get_scan_queue_images()))+"\n"
        print(output)

    def load_data(self, data):
        self.data = data

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
    def __init__(self, host_name):
        self.host_name = host_name

    def get_scrape(self):
        perceptor_scrape = PerceptorScrape()
        dump = self.get_dump()
        perceptor_scrape.data = dump 
        return perceptor_scrape

    def get_dump(self):
        for i in range(50):
            print("http://"+self.host_name+"/model")
            r = requests.get("http://"+self.host_name+"/model")
            if r.status_code == 200:
                return json.loads(r.text)
        print(r.status_code)



