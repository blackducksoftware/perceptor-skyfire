import json
import requests
# import urllib3
import datetime 
import time
from kubernetes import client, config
import logging 
from util import *
import podformat

''' 
Data Scrape Classes - Data Access Objects for Dumps
'''

# Data Access Object for Kube Dump
class KubeScrape:
    def __init__(self, dump={}):
        self.time_stamp = get_current_datetime()
        self.dump = dump

        # Kube Information
        self.pod_names = []
        self.ns_pod_names = []     # ns = namespace, <ns>/<pod-name>  (unique to cluster)
        self.uids = []
        self.namespaces = []
        self.container_names = []
        self.image_repos = []      # <repo>:<tag>

        # Data Access by Namespaced Pod Name
        self.ns_pod_name_to_uid = {}
        self.ns_pod_name_to_annotations = {}
        self.ns_pod_name_to_labels = {}
        self.ns_pod_name_to_containers = {}

        self.load_dump(dump)

    def load_dump(self, dump):
        for pod_name, pod_data in dump.items():
            self.pod_names.append(pod_name) 
            ns_pod_name = "{}/{}".format(pod_data['namespace'],pod_name)
            self.ns_pod_names.append(ns_pod_name)
            self.namespaces.append(pod_data['namespace'])
            self.ns_pod_name_to_uid[ns_pod_name] = pod_data['uid']
            self.ns_pod_name_to_annotations[ns_pod_name] = pod_data['annotations']
            self.ns_pod_name_to_labels[ns_pod_name] = pod_data['labels']
            self.ns_pod_name_to_containers[ns_pod_name] = pod_data['containers']
            for container_name, container_data in pod_data['containers'].items():
                self.container_names.append(container_name)
                self.image_repos.append(container_data['image'])

        # Remove Duplicates
        self.pod_names = list(set(self.pod_names))
        self.namespaces = list(set(self.namespaces))
        self.container_names = list(set(self.container_names))
        self.image_repos = list(set(self.image_repos))

    def viz_dump(self):
        viz = {}
        for pod_name, pod_data in self.dump.items():
            pod_node = pod_data['node']
            pod_namespace = pod_data['namespace']
            pod_containers = pod_data['containers'].keys()
            if pod_node in viz:
                if pod_namespace in viz[pod_node]:
                    viz[pod_node][pod_namespace][pod_name] = {}
                    for container in pod_containers:
                        viz[pod_node][pod_namespace][pod_name][container] = True 
                else:
                    viz[pod_node][pod_namespace] = {pod_name : {}}
                    for container in pod_containers:
                        viz[pod_node][pod_namespace][pod_name][container] = True 
            else:
                viz[pod_node] = {}
                viz[pod_node][pod_namespace] = {pod_name : {}}
                for container in pod_containers:
                    viz[pod_node][pod_namespace][pod_name][container] = True 
        viz_out = {
            'name' : 'cluster',
            'children' : []
        }
        for node_name, node_data in viz.items():
            node = {
                'name' : node_name,
                'children' : []
            }
            for ns_name, ns_data in node_data.items():
                ns = {
                    'name' : ns_name,
                    'children' : []
                }
                for pod_name, pod_data in ns_data.items():
                    pod = {
                        'name' : pod_name,
                        'children' : []
                    }
                    for container_name, container_data in pod_data.items():
                        container = {
                            'name' : container_name,
                            'size' :  40
                        }
                        pod['children'].append(container)
                    ns['children'].append(pod)
                node['children'].append(ns)
            viz_out['children'].append(node)
        return viz_out 

# Data Access Object for Hub Dump
class HubScrape():
    def __init__(self, dump={}):
        self.time_stamp = get_current_datetime()
        self.dump = dump
        
        # Project Data and Data Access
        self.project_urls = []
        self.project_names = []

        self.project_url_to_version_urls = {}

        # Version Data and Data Access
        self.version_urls = []

        self.version_url_to_risk_profile = {}
        self.version_url_to_policy_status = {}
        self.version_url_to_code_loc_urls = {}
        self.version_url_to_code_loc_shas = {}

        # Code Location URL and Data Access
        self.code_loc_urls = []

        self.code_loc_url_to_code_loc_sha = {}
        self.code_loc_url_to_scans = {}

        # Code Location Sha and Data Access
        self.code_loc_shas = []

        self.code_loc_sha_to_code_loc_url = {}
        self.code_loc_sha_to_scans = {}

        self.code_loc_sha_to_project_urls = {}
        self.code_loc_sha_to_version_urls = {}

        self.load_dump(dump)

    def load_dump(self, dump):
        if dump == {}:
            return 
        # Parse Project URL Data
        for project_url, project_data in dump.items():

            self.project_names.append(project_data['name'])
            self.project_urls.append(project_url)

            # Parse Version URL Data
            for version_url, version_data in project_data['versions'].items():
                if project_url not in self.project_url_to_version_urls:
                    self.project_url_to_version_urls[project_url] = []
                self.project_url_to_version_urls[project_url].append(version_url)

                self.version_urls.append(version_url)
                self.version_url_to_risk_profile[version_url] = version_data["riskProfile"]
                self.version_url_to_policy_status[version_url] = version_data["policy-status"]

                # Partse Code Loc URL and Code Loc Sha Data
                for code_loc_url, code_loc_data in version_data['codelocations'].items():
                    self.code_loc_urls.append(code_loc_url)

                    # Parse Code Loc URL Data
                    if version_url not in self.version_url_to_code_loc_urls:
                        self.version_url_to_code_loc_urls[version_url] = []
                    self.version_url_to_code_loc_urls[version_url].append(code_loc_url)
                    
                    code_loc_sha = code_loc_data['sha']

                    if version_url not in self.version_url_to_code_loc_shas:
                        self.version_url_to_code_loc_shas[version_url] = []
                    self.version_url_to_code_loc_shas[version_url].append(code_loc_sha)

                    self.code_loc_url_to_code_loc_sha[code_loc_url] = code_loc_sha  
                    self.code_loc_url_to_scans[code_loc_url] = code_loc_data['scans']

                    # Parse Code Loc Sha Data
                    self.code_loc_shas.append(code_loc_sha)

                    self.code_loc_sha_to_code_loc_url[code_loc_sha] = code_loc_url 
                    self.code_loc_sha_to_scans[code_loc_sha] = code_loc_data['scans']

                    if code_loc_sha not in self.code_loc_sha_to_project_urls: # Code Loc can be in multiple Projects
                        self.code_loc_sha_to_project_urls[code_loc_sha] = []
                    if project_url not in self.code_loc_sha_to_project_urls[code_loc_sha]:
                        self.code_loc_sha_to_project_urls[code_loc_sha].append(project_url)

                    if code_loc_sha not in self.code_loc_sha_to_version_urls: # Code Loc can be in multiple Versions
                        self.code_loc_sha_to_version_urls[code_loc_sha] = []
                    self.code_loc_sha_to_version_urls[code_loc_sha].append(version_url)

        # Remove Duplicates
        self.project_names = list(set(self.project_names))
        self.code_loc_shas = list(set(self.code_loc_shas))


# Data Access Object for Perceptor Dump
class PerceptorScrape:
    def __init__(self, dump={}):
        self.time_stamp = get_current_datetime()
        self.dump = dump

        # Hub Section Data
        self.hub_hosts = []
        self.hub_code_loc_shas = []

        self.hub_host_to_code_loc_shas = {}
        self.hub_host_to_code_locs = {}

        # Pod Section Data
        self.pod_names = []
        self.ns_pod_names = []        # ns = namespace, <ns>/<pod-name>, unique to cluster
        self.pod_namespaces = []
        self.pod_uids = []
        self.pod_container_names = []
        self.pod_image_repos = []     # <repo>:<tag>
        self.pod_image_shas = []
        
        self.ns_pod_name_to_containers = {}

        # Image Section Data
        self.image_shas = []
        self.image_repos = []
        self.image_code_loc_shas = []
        self.image_code_loc_uids = []

        self.image_sha_to_risk_profile = {}
        self.image_sha_to_policy_status = {}
        self.image_sha_to_scans = {}
        self.image_sha_to_repos = {}

        # Scan Queue Section Data
        self.scan_queue_shas = []

        self.load_dump(dump)

    def load_dump(self, dump):
        # Load the Hub Section
        for hub_host, hub_data in dump["Hubs"].items():
            self.hub_hosts.append(hub_host)
            code_loc_shas = list(hub_data["CodeLocations"].keys())
            self.hub_host_to_code_loc_shas[hub_host] = code_loc_shas
            self.hub_code_loc_shas.extend(code_loc_shas)
            self.hub_host_to_code_locs[hub_host] = hub_data["CodeLocations"]
        # Remove duplicates
        self.hub_code_loc_shas = list(set(self.hub_code_loc_shas)) 

        # Load the Pod Section
        for pod_name, pod_data in dump["CoreModel"]["Pods"].items():
            self.ns_pod_names.append(pod_name) 
            self.pod_names.append(pod_data['Name'])
            self.pod_namespaces.append(pod_data["Namespace"])
            self.pod_uids.append(pod_data['UID'])
            self.ns_pod_name_to_containers[pod_name] = pod_data["Containers"]
            for container in pod_data["Containers"]:
                self.pod_container_names.append(container["Name"])
                self.pod_image_repos.append("{}:{}".format(container["Image"]["Repository"],container["Image"]["Tag"]))
                self.pod_image_shas.append(container["Image"]["Sha"])
        # Remove duplicates
        self.pod_names = list(set(self.pod_names))
        self.pod_namespaces = list(set(self.pod_namespaces))
        self.pod_container_names = list(set(self.pod_container_names))
        self.pod_image_repos = list(set(self.pod_image_repos)) 
        self.pod_image_shas = list(set(self.pod_image_shas))

        # Load the Images Section
        for image_sha, image_data in dump["CoreModel"]["Images"].items():
            self.image_shas.append(image_sha)
            if image_data["ScanResults"] is not None:
                self.image_sha_to_risk_profile[image_sha] = image_data["ScanResults"]["RiskProfile"]
                self.image_sha_to_policy_status[image_sha] = image_data["ScanResults"]["PolicyStatus"]
                self.image_sha_to_scans[image_sha] = image_data["ScanResults"]["ScanSummaries"] 
                self.image_code_loc_shas.append(image_data["ScanResults"]["CodeLocationName"]) 
                self.image_code_loc_uids.append(image_data["ScanResults"]["CodeLocationURL"].split(":")[2])
            self.image_sha_to_repos[image_sha] = []
            for repo in image_data["RepoTags"]:
                self.image_sha_to_repos[image_sha].append(repo["Repository"]) 
                self.image_repos.append(repo["Repository"])

        # Load the Scan Queue Section
        for queue_item in dump["CoreModel"]["ImageScanQueue"]:
            self.scan_queue_shas.append(queue_item["Key"])


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
        r = requests.get(url)
        if 200 <= r.status_code <= 299:
            logging.debug("Perceptor http Dump Request Status Code: %s - %s", r.status_code, url)
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
        url = "https://{}:{}/j_spring_security_check".format(self.host_name, self.port) # verify=False does not verify SSL connection - insecure
        r = requests.post(url, verify=False, data=security_data, headers=security_headers)
        if 200 <= r.status_code <= 299:
            logging.debug("Hub http Login Request Status Code: %s",r.status_code)
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
        if 200 <= r.status_code <= 299:
            logging.debug("Hub http Request Status Code: %s - %s", r.status_code, url)
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
            projects[project_href] = {"name" : project_name, "versions" : project_versions}
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

    def get_scrape(self):
        dump, err = self.get_dump()
        if err is not None:
            return None, err 
        return KubeScrape(dump), None
    
    def remove_pod_annotations_and_labels(self):
        pods = self.v1.list_pod_for_all_namespaces()
        for pod in pods.items:
            container_count = len(pod.spec.containers)
            for label_key in podformat.get_all_labels(container_count).keys():
                pod.metadata.labels.pop(label_key, None)
            for annot_key in podformat.get_all_annotations(container_count).keys():
                pod.metadata.annotations.pop(annot_key, None)
            self.v1.patch_namespaced_pod(pod)

    def get_dump(self):
        dump = {}
        pods = self.v1.list_pod_for_all_namespaces().items
        for pod in pods:
            pod_name = pod.metadata.name 
            pod_uid = pod.metadata.uid
            pod_node = pod.spec.node_name
            pod_namespace = pod.metadata.namespace 
            pod_labels = pod.metadata.labels
            pod_annotations = pod.metadata.annotations
            pod_containers = pod.spec.containers
            container_dict = {}
            for container in pod_containers:
                container_name = container.name 
                container_image = container.image 
                container_dict[container_name] = {'image' : container_image}
            dump[pod_name] = {
                'uid' : pod_uid,
                'node' : pod_node,
                'namespace' : pod_namespace,
                'labels' : pod_labels,
                'annotations' : pod_annotations,
                'containers' : container_dict
            }
        return dump, None 