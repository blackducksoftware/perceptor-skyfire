import json
import subprocess
import requests
import urllib3
import datetime 
import time
import sys
from kubernetes import client, config
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging 

class myHandler(BaseHTTPRequestHandler):
    def __init__(self):
        self.data = "UNKNOWN"
        self.port = None

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(self.data)

    def serve(self):
        try:
            server = HTTPServer(('', self.port), myHandler)
            server.serve_forever()
        except:
            server.socket.close()

    def my_own_server_function(self):
        # TO DO
        pass


class KubeClientWrapper:
    def __init__(self, in_cluster):
        if in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self.v1 = client.CoreV1Api()

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

class HubAnalysis():
    def __init__(self):
        self.time_stamp = datetime.datetime.now()
        self.data = {}

    def get_something(self):
        pass 

class HubClient():
    def __init__(self, host_name=None, username="", password="", in_cluster=False):
        self.kube = KubeClientWrapper(in_cluster)
        self.host_name = host_name
        self.username = username
        self.password = password 
        self.secure_login_cookie = self.get_secure_login_cookie()
        # Hub Constants
        self.max_projects = 10000000
        self.analysis = []

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

    def analyze_hub(self):
        hub_analysis = HubAnalysis()
        hub_analysis.data = self.crawl_hub()
        self.analysis.append(hub_analysis)
        return hub_analysis 

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

class OpsSightAnalysis:
    def __init__(self):
        self.time_stamp = datetime.datetime.now()
        self.data = {}

    def get_hubs_names(self):
        return self.data["Hubs"].keys()

    def get_pods_names(self):
        return self.data["CoreModel"]["Pods"].keys()
        
    def get_shas_names(self):
        return self.data["CoreModel"]["Images"].keys()

class OpsSightClient():
    def __init__(self, host_name=None, in_cluster=False):
        self.kube = KubeClientWrapper(in_cluster)
        self.host_name = host_name
        self.analysis = []

    def get_analysis(self):
        opssight_analysis = OpsSightAnalysis()
        dump = self.get_dump()
        opssight_analysis.data = dump 
        self.analysis.append(opssight_analysis)
        return opssight_analysis

    def get_dump(self):
        while True:
            r = requests.get("http://"+self.host_name+"/model")
            if r.status_code == 200:
                return json.loads(r.text)



