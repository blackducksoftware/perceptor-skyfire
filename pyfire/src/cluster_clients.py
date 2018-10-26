import json
import subprocess
import requests
import time
import sys
from kubernetes import client, config
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging 

class myHandler(BaseHTTPRequestHandler):
    def __init__(self):
        self.status = "UNKNOWN"
        self.port = None

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(self.status)

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

class HubClient():
    def __init__(self, host_name=None, username="", password="", in_cluster=False):
        self.kube = KubeClientWrapper(in_cluster)
        self.host_name = host_name
        self.username = username
        self.password = password 
        self.secure_login_cookie = self.get_secure_login_cookie()
        self.max_projects = 10000000

    def get_secure_login_cookie(self):
        security_headers = {'Content-Type':'application/x-www-form-urlencoded'}
        security_data = {'j_username': self.username,'j_password': self.password}
        # verify=False does not verify SSL connection - insecure
        r = requests.post("https://"+self.host_name+":443/j_spring_security_check", verify=False, data=security_data, headers=security_headers)
        return r.cookies 
        
    def get_projects_dump(self): 
        r = requests.get("https://"+self.host_name+":443/api/projects?limit="+str(self.max_projects),verify=False, cookies=self.secure_login_cookie)
        return r.json()

    def get_projects_names(self):
        return [project['name'] for project in self.get_projects_dump()['items']]

    def get_code_locations_dump(self):
        r = requests.get("https://"+self.host_name+":443/api/codelocations?limit="+str(self.max_projects),verify=False, cookies=self.secure_login_cookie)
        return r.json()

    def get_code_locations_names(self):
        return [x['name'] for x in self.get_code_locations_dump()['items']]

    def get_projects_link(self, link_name):
        links = []
        for project in self.get_projects_dump()['items']:
            for link in project['_meta']['links']:
                if link['rel'] == link_name:
                    links.append(link['href'])
        return links

    def get_scan_summaries(self):
        pass

    def get_project_version_risk_profile(self):
        pass 

    def get_project_version_policy_status(self):
        pass 


class OpsSightClient():
    def __init__(self, host_name=None, in_cluster=False):
        self.kube = KubeClientWrapper(in_cluster)
        self.host_name = host_name
    
    def get_dump(self):
        while True:
            r = requests.get("http://"+self.host_name+"/model")
            if r.status_code == 200:
                return json.loads(r.text)
        
    def get_shas_names(self):
        return self.get_dump()['CoreModel']['Images'].keys()

