import threading 
import logging
from cluster_clients import KubeClient
import subprocess
import requests 
import time
import json 

import random

class TestSuite:
    def __init__(self, skyfire_port, in_cluster):
        self.logger = logging.getLogger("TestSuite")

        self.event_thread = threading.Thread(target=self.tests)
        self.event_thread.daemon = True
        self.test_state = "STOPPED"
        self.in_progress = False
        self.accessing_data = False
        self.event_thread.start()

        self.skyfire_port = skyfire_port

        self.k_client = KubeClient(in_cluster=in_cluster)

        self.test_results = {'state' : 'NO_TESTS', 'summary' : '','data' : {}}

    def start(self):
        if not self.in_progress:
            self.in_progress = True
        else:
            self.logger.error("Test Already Started")

    def get_results(self):
        self.logger.debug("Getting the Test Results")
        while self.accessing_data:
            pass
        self.accessing_data = True
        self.logger.debug("Got the Test Results")
        r = self.test_results
        self.accessing_data = False
        return r

    def tests(self):
        self.logger.info("Starting Test Thread")
        while True:
            while self.in_progress == False:
                pass
            self.logger.info("Starting Test Suite")

            suite_mock = {
                'MockTest1' : lambda: self.test_mock(),
                'MockTest2' : lambda: self.test_mock(),
                'MockTest3' : lambda: self.test_mock(),
            }

            suite_kube_client = {
                'CreatingPod' : lambda: self.test_create_pod()
            }

            suite_opssight = {
                'OpsSightRepoCoverage': lambda: self.test_opssight_repo_coverage(50),
                'OpsSightPodCoverage' : lambda: self.test_opssight_pod_coverage(90),
                'HubImageCoverage' : lambda: self.test_hub_image_coverage(90)
            }

            suite = {
                'MockTest1' : lambda: self.test_mock(),
                'MockTest2' : lambda: self.test_mock(),
                'OpsSightRepoCoverage': lambda: self.test_opssight_repo_coverage(50),
                'OpsSightPodCoverage' : lambda: self.test_opssight_pod_coverage(90),
                'HubImageCoverage' : lambda: self.test_hub_image_coverage(90),
                'CreatingPod' : lambda: self.test_create_pod()
            }

            # Initialize data for test suite
            while self.accessing_data:
                pass
            self.accessing_data = True
            self.test_results["state"] = "IN_PROGRESS"
            self.test_results["summary"] = ""
            self.test_results["data"] = {}
            for key in suite.keys():
                self.test_results["data"][key] = ""
            self.accessing_data = False

            # Run tests in suite and update data
            for test_name, test in suite.items():
                r = test()
                while self.accessing_data:
                    pass
                self.accessing_data = True
                self.test_results["data"][test_name] = r
                self.accessing_data = False

            # Change test state to finished
            while self.accessing_data:
                pass
            self.accessing_data = True
            self.test_results["state"] = "FINISHED"
            if "FAILED" in self.test_results['data'].values():
                self.test_results["summary"] = "FAILED"
            else:
                self.test_results["summary"] = "PASSED"
            self.accessing_data = False

            self.logger.info("Finished Test Suite")
            self.in_progress = False

    def test_mock(self):
        self.logger.debug("Starting Mock Test")
        time.sleep(7)
        val = random.randint(0,10)
        self.logger.debug("Finished Mock Test")
        if val <= 8:
            return "PASSED"
        else:
            return "FAILED"

    def test_opssight_repo_coverage(self, policy):
        self.logger.debug("Starting OpsSight Repo Coverage Test")
        dump, err = getSkyfireDump(host_name="localhost", port=self.skyfire_port)
        if err is not None:
            self.logger.debug("Could not get Skyfire Report: %s" % err)
            return "FAILED"
        self.logger.debug("OpsSight Repo Coverage: %f", dump["mult-perceptor-kube-report"]["repo_coverage"])
        if dump["mult-perceptor-kube-report"]["repo_coverage"] < policy:
            return "FAILED"
        else:
            return "PASSED"

    def test_opssight_pod_coverage(self, policy):
        self.logger.debug("Starting OpsSight Pod Coverage Test")
        dump, err = getSkyfireDump(host_name="localhost", port=self.skyfire_port)
        if err is not None:
            self.logger.debug("Could not get Skyfire Report: %s" % err)
            return "FAILED"
        self.logger.debug("OpsSight Pod Coverage: %f", dump["mult-perceptor-kube-report"]["pod_coverage"])
        if dump["mult-perceptor-kube-report"]["pod_coverage"] < policy:
            return "FAILED"
        else:
            return "PASSED"

    def test_hub_image_coverage(self, policy):
        self.logger.debug("Starting Hub Image Coverage Test")
        dump, err = getSkyfireDump(host_name="localhost", port=self.skyfire_port)
        if err is not None:
            self.logger.debug("Could not get Skyfire Report: %s" % err)
            return "FAILED"
        self.logger.debug("Hub Image Coverage: %f", dump["mult-hub-mult-perceptor-report"]["image_coverage"])
        if dump["mult-hub-mult-perceptor-report"]["image_coverage"] < policy:
            return "FAILED"
        else:
            return "PASSED"

    def create_namespace(self, namespace):
        namespace_body = {
            'apiVersion' : 'v1',
            'kind' : 'Namespace',
            'metadata' : {
                'name' : namespace
            }
        }
        return kubeApiBackOff(lambda: self.k_client.v1.create_namespace(body=namespace_body), 2, 10)

    def create_pod(self, namespace, pod_name):
        pod_body = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': pod_name
            },
            'spec': {
                'containers': [{
                    'image': 'rabbitmq:3.6',
                    'name': 'rabbitmq36',
                    'args': ['sleep', '3600']
                }]
            }
        }
        return kubeApiBackOff(lambda: self.k_client.v1.create_namespaced_pod(namespace=namespace, body=pod_body), 2, 10)

    def delete_namespace(self, namespace):
        return kubeApiBackOff(lambda: self.k_client.v1.delete_namespace(name=namespace, body={}), 2, 10)


    def test_create_pod(self):
        self.logger.debug("Starting Creating a Pod Test")
        test_result = "FAILED"

        # Create a namespace
        self.logger.debug("Creating namespace test-space")
        namespace = 'test-space' 
        success, err = self.create_namespace(namespace)
        if not success:
            self.logger.error("Failed to create Namesapce: %s" % err)
            return test_result

        # Create a pod
        self.logger.debug("Creating a Pod in %s namespace" % namespace)
        pod_name = "hammer-pod"
        success, err = self.create_pod(namespace, pod_name)
        if not success:
            self.logger.error("Failed to create Pod: %s" % err)
            return test_result

        # Check for the pod in Skyfire Reports
        self.logger.debug("Searching for Pod in Kube and OpsSight for 2 minutes")
        for i in range(24):
            dump, err = getSkyfireDump(host_name="localhost", port=self.skyfire_port)
            if err is not None:
                self.logger.debug("Could not get Skyfire Report: %s" % err)
                return test_result

            kd = dump['kube-report']['scrape']['pod_names']
            pod_in_kube = pod_name in kd
            
            pod_in_opssight = False
            for perceptor_scrape in dump['mult-opssight-reports']['scrapes']:
                pd = perceptor_scrape['pod_names']
                pod_in_opssight = pod_name in pd 
                if pod_in_opssight:
                    break 
            self.logger.debug("Checking for Test Pod. Kube: {}. OpsSight: {}".format(str(pod_in_kube),str(pod_in_opssight)))

            if pod_in_kube and pod_in_opssight:
                test_result = "PASSED"
                break
            time.sleep(5)

        # Clean up the test namespace
        self.logger.debug("Deleting Namespace {}".format(namespace))
        success, err = self.delete_namespace(namespace)
        if not success:
            self.logger.error("Failed to delete Namespace {}: {}".format(namespace, err))
            return test_result 

        self.logger.debug("Finished Pod Test")
        return test_result
            

def getSkyfireDump(host_name="localhost", port=80):
    self.logger.debug("Getting Skyfire Dump for a Test")
    url = "http://{}:{}/latestreport".format(host_name, port)
    r = requests.get(url)
    if 200 <= r.status_code <= 299:
        self.logger.debug("Skyfire http Dump Request Status Code: %s - %s", r.status_code, url)
        return json.loads(r.text), None
    else:
        self.logger.error("Could not connect to Skyfire")
        return {}, {'error' : "Skyfire Connection Fail", 'status' : r.status_code, 'url' : url} 
        

def kubeApiBackOff(f, pause=2, repeats=10):
    for i in range(repeats):
        try:
            api_response = f()
            self.logger.debug(api_response)
            return True, None
        except Exception as e:
            self.logger.warning("Exception from Kube Client: %s\n" % e)
        time.sleep(pause)
    return False, e
