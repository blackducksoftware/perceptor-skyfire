import json
import requests
# import urllib3
import datetime 
import time
from kubernetes import client, config
import logging 
from util import *
import podreader 

'''
Data Scrape Classes
'''

class KubeScrape:
    def __init__(self, dump={}):
        self.time_stamp = get_current_datetime()
        self.dump = dump

        self.namespaces = []
        self.pod_names = []
        self.pod_annotations = []
        self.pod_labels = []
        

        self.container_names = []
        self.container_images = []

        self.image_to_namespace = {}

        self.load_dump(dump)

    def load_dump(self, dump):
        for pod_name, pod_data in dump.items():
            self.pod_names.append(pod_name) 
            self.namespaces.append(pod_data['namespace'])
            self.pod_annotations.append(pod_data['annotations'])
            self.pod_labels.append(pod_data['labels'])
            for container_name, container_data in pod_data['containers'].items():
                self.container_names.append(container_name)
                self.container_images.append(container_data['image'])
                self.image_to_namespace[container_data['image']] = pod_data['namespace']

    def get_opssight_labels(self, pod_name):
        expected = set(podreader.get_all_labels(len(self.container_names)))
        actual = set(self.dump[pod_name]['labels'].keys())
        present = expected.intersection(actual)
        missing = expected - actual
        return (missing, present)
    
    def has_all_labels(self, pod_name):
        missing, _ = self.get_opssight_labels(pod_name)
        return len(missing) == 0
    
    def is_partially_labeled(self, pod_name):
        missing, present = self.get_opssight_labels(pod_name)
        return len(missing) > 0 and len(present) > 0

    def get_opssight_annotations(self, pod_name):
        expected = set(podreader.get_all_annotations(len(self.container_names)))
        actual = set(self.dump[pod_name]['annotations'].keys())
        present = expected.intersection(actual)
        missing = expected - actual
        return (missing, present)
    
    def has_all_annotations(self, pod_name):
        missing, _ = self.get_opssight_annotations(pod_name)
        return len(missing) == 0
    
    def is_partially_annotated(self, pod_name):
        missing, present = self.get_opssight_annotations(pod_name)
        return len(missing) > 0 and len(present) > 0


class HubScrape():
    def __init__(self, dump={}):
        self.time_stamp = get_current_datetime()
        self.dump = dump

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

        self.load_dump(dump)

    def load_dump(self, dump):
        if dump == {}:
            return 
        for project_url, project_data in dump.items():
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

class PerceptorScrape:
    def __init__(self, dump={}):
        self.time_stamp = get_current_datetime()
        self.dump = dump

        self.hub_names = []
        self.hub_shas = []
        self.hub_to_shas = {}

        self.pod_names = []
        self.pod_shas = []
        self.container_names = []
        self.repositories = []
        self.pod_namespaces = []

        self.image_shas = []
        self.image_repositories = []
        self.image_sha_to_risk_profile = {}
        self.image_sha_to_policy_status = {}
        self.image_sha_to_scans = {}
        self.image_sha_to_respositories = {}

        self.load_dump(dump)

    def load_dump(self, dump):
        for hub_name, hub_data in dump["Hubs"].items():
            self.hub_names.append(hub_name)
            shas = list(hub_data["CodeLocations"].keys())
            self.hub_to_shas[hub_name] = shas 
            self.hub_shas.extend(shas)

        for pod_name, pod_data in dump["CoreModel"]["Pods"].items():
            self.pod_names.append(pod_name)
            self.pod_namespaces.append(pod_data["Namespace"])
            for container in pod_data["Containers"]:
                self.repositories.append(container["Image"]["Repository"])
                self.pod_shas.append(container["Image"]["Sha"])
                self.container_names.append(container["Name"])

        for image_sha, image_data in dump["CoreModel"]["Images"].items():
            self.image_shas.append(image_sha)
            if image_data["ScanResults"] is not None:
                self.image_sha_to_risk_profile[image_sha] = image_data["ScanResults"]["RiskProfile"]
                self.image_sha_to_policy_status[image_sha] = image_data["ScanResults"]["PolicyStatus"]
                self.image_sha_to_scans[image_sha] = image_data["ScanResults"]["ScanSummaries"]
            self.image_sha_to_respositories[image_sha] = []
            for repo in image_data["RepoTags"]:
                self.image_sha_to_respositories[image_sha].append(repo["Repository"]) 
                self.image_repositories.append(repo["Repository"])

        for image_sha in dump["CoreModel"]["ImageScanQueue"]:
            pass 


'''
Client Classes
'''

class MockClient():
    static_data_files = {
        'perceptor': './src/staticDumps/staticPerceptorScrape.txt',
        'kube' : './src/staticDumps/staticKubeScrape.txt',
        'hub1' : './src/staticDumps/staticHubScrape1.txt',
        'hub2' : './src/staticDumps/staticHubScrape2.txt'
    }
    def __init__(self, name):
        self.name = name

    def get_scrape(self):
        if self.name in MockClient.static_data_files:
            with open(MockClient.static_data_files[self.name], 'r') as f:
                if self.name == 'perceptor':
                    return PerceptorScrape(json.load(f)), None 
                elif self.name == 'kube':
                    return KubeScrape(json.load(f)), None
                else:
                    return HubScrape(json.load(f)), None
        logging.error("Mock Client "+self.name+" does not exist")
        return None, {'error' : 'Could not create Mock'}

class PerceptorClient():
    def __init__(self, host_name, port):
        self.host_name = host_name
        self.port = port

    def get_scrape(self):
        dump, err = self.get_dump()
        if err is None:
            return PerceptorScrape(dump), None
        return None, err

    def get_dump(self):
        url = "http://{}:{}/model".format(self.host_name, self.port)
        logging.debug("Perceptor URL: %s",url)
        r = requests.get(url)
        if r.status_code == 200:
            return json.loads(r.text), None
        else:
            logging.error("Could not connect to Perceptor")
            return {}, {'error' : "Perceptor Connection Fail", 'status' : r.status_code, 'url' : url} 

class HubClient():
    def __init__(self, host_name, port, username, password, client_timeout_seconds):
        self.host_name = host_name
        self.port = port
        self.username = username
        self.password = password
        self.secure_login_cookie = None
        self.max_projects = 10000000
        # TODO do something with this
        self.client_timeout_seconds = client_timeout_seconds

    def get_secure_login_cookie(self):
        security_headers = {'Content-Type':'application/x-www-form-urlencoded'}
        security_data = {'j_username': self.username,'j_password': self.password}
        # verify=False does not verify SSL connection - insecure
        url = "https://{}:{}/j_spring_security_check".format(self.host_name, self.port)
        print(url)
        r = requests.post(url, verify=False, data=security_data, headers=security_headers)
        if r.status_code == 200:
            return r.cookies, None
        elif 200 <= r.status_code <= 299:
            logging.debug("Hub HTTP Login Request Status Code: %s",r.status_code)
            return r.cookies, None
        else:
            logging.error("Could not Secure Login to the Hub")
            return None, {'error' : 'Could not Secure Login to the Hub', 'status' : r.status_code}

    def api_get(self, url):
        if self.secure_login_cookie is None:
            self.secure_login_cookie, err = self.get_secure_login_cookie()
            if err is not None:
                return None, err 
        r = requests.get(url, verify=False, cookies=self.secure_login_cookie)
        if r.status_code == 200:
            return r, None
        elif 200 <= r.status_code <= 299:
            logging.debug("Hub HTTP Request Status Code: %s",r.status_code)
            return r, None
        else:
            logging.error("Could not contact: "+url)
            return None, {'error' : 'Hub Connection Fail', 'status' : r.status_code, 'url' : url}

    def get_scrape(self):
        dump, err = self.get_dump()
        if err is None:
            return HubScrape(dump), None 
        return None, err 

    def get_dump(self):
        dump, err = self.api_get("https://"+self.host_name+":443/api"+"/projects?limit="+str(self.max_projects))
        if err is not None:
            return {}, err
        dump = dump.json()
        projects = {}
        for project in dump['items']:
            project_href = project['_meta']['href'] 
            project_name = project['name']
            # map link to link name
            project_links = {}
            for link in project['_meta']['links']:
                project_links[link['rel']] = link['href']
            # get data from version url
            project_versions, err = self.crawl_version(project_links['versions'])
            projects[project_href] = {"name" : project_name, "links" : project_links, "versions" : project_versions}
        return projects, None 
    
    def crawl_version(self, version_url):
        dump, err = self.api_get(version_url)
        if err is None:
            return {}, err 
        dump = dump.json()
        versions = {}
        for version in dump['items']:
            version_href = version['_meta']["href"]
            # map link to link name
            version_links = {}
            for link in version['_meta']["links"]:
                version_links[link['rel']] = link['href']
            version_risk_profile, err = self.crawl_risk_profile(version_links['riskProfile'])
            version_policy_status, err = self.crawl_policy_status(version_links['policy-status'])
            version_code_locations, err = self.crawl_code_location(version_links['codelocations'])
            versions[version_href] = {
                "links" : version_links, 
                "policy-status" : version_policy_status,
                "riskProfile" : version_risk_profile, 
                "codelocations" : version_code_locations
            }
        return versions, None 

    def crawl_policy_status(self, policy_status_url):
        dump, err = self.api_get(policy_status_url)
        if err is None:
            return {}, err 
        dump = dump.json()
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
                } , None

    def crawl_risk_profile(self, risk_profile_url):
        dump, err = self.api_get(risk_profile_url)
        if err is None:
            return {}, err
        dump = dump.json()
        return {'categories' : dump['categories']}, None

    def crawl_code_location(self, code_location_url):
        dump, err = self.api_get(code_location_url)
        if err is None:
            return {}, err
        dump = dump.json()
        code_locations = {}
        for code_location in dump['items']:
            code_location_href = code_location['_meta']['href'] 
            code_location_sha = code_location['name']
            code_location_links = {}
            for link in code_location['_meta']['links']:
                code_location_links[link['rel']] = link['href']
            code_location_scan_summaries, err = self.crawl_scan_summary(code_location_links['scans'])
            code_locations[code_location_href] = {
                'sha' : code_location_sha,
                'links' : code_location_links,
                'scans' : code_location_scan_summaries
            }
        return code_locations, None

    def crawl_scan_summary(self, scan_summary_url):
        dump, err = self.api_get(scan_summary_url)
        if err is None:
            return {}, err 
        dump = dump.json()
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
        return scan_summaries, None 

class KubeClient:
    def __init__(self, in_cluster):
        if in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self.v1 = client.CoreV1Api()

    # TODO - Merge together Matt's Kube Client with this one

    def get_scrape(self):
        dump, err = self.get_dump()
        if err is not None:
            return None, err 
        return KubeScrape(dump), None

    def get_dump(self):
        dump = {}
        pods = self.v1.list_pod_for_all_namespaces().items 
        for pod in pods:
            pod_namespace = pod.metadata.namespace 
            pod_name = pod.metadata.name 
            pod_labels = pod.metadata.labels
            pod_annotations = pod.metadata.annotations
            pod_containers = pod.spec.containers
            container_dict = {}
            for container in pod_containers:
                container_image = container.image 
                container_name = container.name 
                container_dict[container_name] = {'image' : container_image}
            dump[pod_name] = {
                'namespace' : pod_namespace,
                'labels' : pod_labels,
                'annotations' : pod_annotations,
                'containers' : container_dict
            }
        return dump, None 