import threading 
import logging
from cluster_clients import KubeClient
import subprocess
import requests 
import time
import json 

import random

class TestSuite:
    def __init__(self, skyfire_port):
        self.event_thread = threading.Thread(target=self.tests)
        self.event_thread.daemon = True
        self.test_state = "STOPPED"
        self.in_progress = False
        self.accessing_data = False
        self.event_thread.start()

        self.skyfire_port = skyfire_port
        
        self.test_results = {'state' : 'NO_TESTS', 'summary' : '','data' : {}}

    def start(self):
        if not self.in_progress:
            self.in_progress = True
        else:
            logging.error("Test Already Started")

    def get_results(self):
        logging.debug("Getting the Test Results")
        while self.accessing_data:
            pass
        self.accessing_data = True
        logging.debug("Got the Test Results")
        r = self.test_results
        self.accessing_data = False
        return r

    def tests(self):
        logging.info("Starting Test Thread")
        while True:
            while self.in_progress == False:
                pass
            logging.info("Starting Test Suite")

            while self.accessing_data:
                pass
            self.accessing_data = True
            self.test_results["state"] = "IN_PROGRESS"
            self.test_results["summary"] = ""
            self.test_results["data"]['MockTest1'] = ""
            self.test_results["data"]['MockTest2'] = ""
            self.test_results["data"]['OpsSightRepoCoverage'] = ""
            self.test_results["data"]['OpsSightPodCoverage'] = ""
            self.test_results["data"]['HubImageCoverage'] = ""
            self.test_results["data"]['CreatingPod'] = ""
            self.accessing_data = False

            r = self.mock_test()
            while self.accessing_data:
                pass
            self.accessing_data = True
            self.test_results["data"]['MockTest1'] = r
            self.accessing_data = False

            r = self.mock_test()
            while self.accessing_data:
                pass
            self.accessing_data = True
            self.test_results["data"]['MockTest2'] = r
            self.accessing_data = False

            r = self.opssight_repo_coverage(50)
            while self.accessing_data:
                pass
            self.accessing_data = True
            self.test_results["data"]['OpsSightRepoCoverage'] = r
            self.accessing_data = False

            r = self.opssight_pod_coverage(90)
            while self.accessing_data:
                pass
            self.accessing_data = True
            self.test_results["data"]['OpsSightPodCoverage'] = r
            self.accessing_data = False

            r = self.hub_image_coverage(90)
            while self.accessing_data:
                pass
            self.accessing_data = True
            self.test_results["data"]['HubImageCoverage'] = r
            self.accessing_data = False

            r = self.create_pod_test()
            while self.accessing_data:
                pass
            self.accessing_data = True
            self.test_results["data"]['CreatingPod'] = r
            self.accessing_data = False

            while self.accessing_data:
                pass
            self.accessing_data = True
            self.test_results["state"] = "FINISHED"
            if "FAILED" in self.test_results['data'].values():
                self.test_results["summary"] = "FAILED"
            else:
                self.test_results["summary"] = "PASSED"
            self.accessing_data = False

            logging.info("Finished Test Suite")

            self.in_progress = False

    def mock_test(self):
        logging.debug("Starting Mock Test")
        time.sleep(7)
        val = random.randint(0,10)
        logging.debug("Finished Mock Test")
        if val <= 8:
            return "PASSED"
        else:
            return "FAILED"

    def opssight_repo_coverage(self, policy):
        logging.debug("Starting OpsSight Repo Coverage Test")
        dump, err = getSkyfireDump(host_name="localhost", port=self.skyfire_port)
        if err is not None:
            logging.debug("Could not get Skyfire Report: %s" % err)
            return "FAILED"
        logging.debug("OpsSight Repo Coverage: %f", dump["mult-perceptor-kube-report"]["repo_coverage"])
        if dump["mult-perceptor-kube-report"]["repo_coverage"] < policy:
            return "FAILED"
        else:
            return "PASSED"

    def opssight_pod_coverage(self, policy):
        logging.debug("Starting OpsSight Pod Coverage Test")
        dump, err = getSkyfireDump(host_name="localhost", port=self.skyfire_port)
        if err is not None:
            logging.debug("Could not get Skyfire Report: %s" % err)
            return "FAILED"
        logging.debug("OpsSight Pod Coverage: %f", dump["mult-perceptor-kube-report"]["pod_coverage"])
        if dump["mult-perceptor-kube-report"]["pod_coverage"] < policy:
            return "FAILED"
        else:
            return "PASSED"

    def hub_image_coverage(self, policy):
        logging.debug("Starting Hub Image Coverage Test")
        dump, err = getSkyfireDump(host_name="localhost", port=self.skyfire_port)
        if err is not None:
            logging.debug("Could not get Skyfire Report: %s" % err)
            return "FAILED"
        logging.debug("Hub Image Coverage: %f", dump["mult-hub-mult-perceptor-report"]["image_coverage"])
        if dump["mult-hub-mult-perceptor-report"]["image_coverage"] < policy:
            return "FAILED"
        else:
            return "PASSED"

    def create_namespace_test(self, ns):
        logging.debug("Starting Creating a Pod Test")
        k_client = KubeClient(in_cluster=False)

        # Create a namespace
        namespace = ns

        namespace_body = {
            'apiVersion' : 'v1',
            'kind' : 'Namespace',
            'metadata' : {
                'name' : namespace
            }
        }

        try: 
            api_response = k_client.v1.create_namespace(body=namespace_body)
            logging.info(api_response)
        except Exception as e:
            logging.error("Exception when calling CoreV1Api->create_namespaced_pod: %s\n" % e)
            return "FAILED"
        return "PASSED"

    def create_pod_test(self):
        logging.debug("Starting Creating a Pod Test")
        k_client = KubeClient(in_cluster=False)

        # Create a namespace
        logging.debug("Creating namespace test-space")
        namespace = 'test-space' 

        namespace_body = {
            'apiVersion' : 'v1',
            'kind' : 'Namespace',
            'metadata' : {
                'name' : namespace
            }
        }

        try: 
            api_response = k_client.v1.create_namespace(body=namespace_body)
        except Exception as e:
            logging.error("Exception when creating Namespace: %s\n" % e)
            return "FAILED"

        # Create a pod
        logging.debug("Creating a Pod in %s namespace" % namespace)
        pod_name = "hammer-pod"
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
        try: 
            api_response = k_client.v1.create_namespaced_pod(namespace=namespace, body=pod_body)
        except Exception as e:
            logging.error("Exception when creating Pod: %s\n" % e)
            return "FAILED"

        # Check for the pod in Skyfire Reports
        logging.debug("Searching for Pod in Kube and OpsSight for 2 minutes")
        test_result = "FAILED"
        for i in range(24):
            dump, err = getSkyfireDump(host_name="localhost", port=self.skyfire_port)
            if err is not None:
                logging.debug("Could not get Skyfire Report: %s" % err)
                return test_result

            kd = dump['kube-report']['scrape']['pod_names']
            pod_in_kube = pod_name in kd
            
            pod_in_opssight = False
            for perceptor_scrape in dump['mult-opssight-reports']['scrapes']:
                pd = perceptor_scrape['pod_names']
                pod_in_opssight = pod_name in pd 
                if pod_in_opssight:
                    break 
            logging.debug("Checking for Test Pod. Kube: {}. OpsSight: {}".format(str(pod_in_kube),str(pod_in_opssight)))

            if pod_in_kube and pod_in_opssight:
                test_result = "PASSED"
                break
            time.sleep(5)

        # Clean up the pod
        logging.debug("Cleaning up Pod Test")
        try:
            r = subprocess.run("oc delete pod {} -n {}".format(pod_name,namespace),shell=True,stdout=subprocess.PIPE)
            r = subprocess.run("oc delete ns {}".format(namespace),shell=True,stdout=subprocess.PIPE) 
        except Exception as e:
            logging.error("Exception when Cleaning up Pod Test: %s\n" % e)

        logging.debug("Finished Pod Test")
        return test_result
            

def getSkyfireDump(host_name="localhost", port=80):
    logging.debug("Getting Skyfire Dump for a Test")
    url = "http://{}:{}/latestreport".format(host_name, port)
    r = requests.get(url)
    if 200 <= r.status_code <= 299:
        logging.debug("Skyfire http Dump Request Status Code: %s - %s", r.status_code, url)
        return json.loads(r.text), None
    else:
        logging.error("Could not connect to Skyfire")
        return {}, {'error' : "Skyfire Connection Fail", 'status' : r.status_code, 'url' : url} 