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

        self.namespace = 'test-space'

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

        # Initialize Test Suites
        suite_mock = {
            'MockTest1' : lambda: self.test_mock(),
            'MockTest2' : lambda: self.test_mock(),
            'MockTest3' : lambda: self.test_mock(),
        }

        suite_kube_client = {
            'CreatingPod' : lambda: self.test_pod_discovery()
        }

        suite_opssight = {
            'OpsSightRepoCoverage': lambda: self.test_opssight_repo_coverage_policy(50),
            'OpsSightPodCoverage' : lambda: self.test_opssight_pod_coverage_policy(90),
            'HubImageCoverage' : lambda: self.test_hub_image_coverage_policy(90)
        }

        suite = {
            'MockTest1' : lambda: self.test_mock(),
            'MockTest2' : lambda: self.test_mock(),
            'OpsSightRepoCoverage': lambda: self.test_opssight_repo_coverage_policy(50),
            'OpsSightPodCoverage' : lambda: self.test_opssight_pod_coverage_policy(90),
            'HubImageCoverage' : lambda: self.test_hub_image_coverage_policy(90),
            'CreatingPod' : lambda: self.test_pod_discovery()
        }

        # Main Thread Loop
        while True:
            while self.in_progress == False:
                pass
            self.logger.info("Starting Test Suite")

            # Initialize data for test suite
            success, err = self.initialize_test_suite(suite)
            if err is not None:
                while self.accessing_data:
                    pass
                self.accessing_data = True
                self.test_results["state"] = "FINISHED"
                self.accessing_data = False
                self.logger.info("Finished Test Suite")
                self.in_progress = False
                continue 

            # Run tests in suite and update data
            for test_name, test in suite.items():
                r = test()
                while self.accessing_data:
                    pass
                self.accessing_data = True
                self.test_results["data"][test_name] = r
                self.accessing_data = False

            # Clean up and finish test suite
            success, err = self.complete_test_suite()
            if err is not None:
                while self.accessing_data:
                    pass
                self.accessing_data = True
                self.test_results["state"] = "FINISHED"
                self.accessing_data = False

            self.logger.info("Finished Test Suite")
            self.in_progress = False
    
    def initialize_test_suite(self, suite):
        # Set test results to show IN_PROGRESS
        self.logger.debug("Initializing Test Results Data")
        while self.accessing_data:
            pass
        self.accessing_data = True
        self.test_results["state"] = "IN_PROGRESS"
        self.test_results["summary"] = ""
        self.test_results["data"] = {}
        for key in suite.keys():
            self.test_results["data"][key] = ""
        self.accessing_data = False

        # Delete test-space namespace if already exists
        self.logger.debug("Checking if Namespace %s exists", self.namespace)
        exists, err = self.k_client.namespace_exists(self.namespace)
        if err is not None:
            self.logger.error("Failed to check if Namespace {} exists: {}".format(self.namespace,err))
            return False, err
        if exists:
            self.logger.debug("Deleteing old namespace %s", self.namespace)
            success, err = kubeApiBackOff(lambda: self.k_client.delete_namespace(self.namespace), 2, 10) 
            if not success:
                self.logger.error("Failed to delete namespace {}: {}".format(self.namespace, err))
                return False, err 

        # Create new namespace test-space
        self.logger.debug("Creating namespace %s", self.namespace)
        success, err = kubeApiBackOff(lambda: self.k_client.create_namespace(self.namespace), 2, 10) 
        if not success:
            self.logger.error("Failed to create Namespace {}: {}".format(self.namespace,err))
            return False, "Failed to create namespace"
        return True, None

    def complete_test_suite(self):
        # Clean up the Namespace
        self.logger.debug("Deleting Namespace %s", self.namespace)
        success, err = kubeApiBackOff(lambda: self.k_client.delete_namespace(self.namespace), 2, 10) 
        if not success:
            self.logger.error("Failed to delete Namespace {}: {}".format(self.namespace, err))
            return False, err

        # Change test state to finished
        self.logger.debug("Finalizing Test Results")
        while self.accessing_data:
            pass
        self.accessing_data = True
        self.test_results["state"] = "FINISHED"
        if "FAILED" in self.test_results['data'].values():
            self.test_results["summary"] = "FAILED"
        else:
            self.test_results["summary"] = "PASSED"
        self.accessing_data = False

        return True, None


    '''
    TESTS
    '''

    def test_mock(self):
        self.logger.debug("Starting Mock Test")
        time.sleep(5)
        val = random.randint(0,10)
        self.logger.debug("Finished Mock Test")
        if val <= 8:
            return "PASSED"
        else:
            return "FAILED"

    def test_opssight_repo_coverage_policy(self, policy):
        self.logger.debug("Starting OpsSight Repo Coverage Test")
        dump, err = getSkyfireDump(host_name="localhost", port=self.skyfire_port)
        if err is not None:
            self.logger.debug("Could not get Skyfire Report: %s", err)
            return "FAILED"
        if dump["mult-perceptor-kube-report"]["repo_coverage"] < policy:
            return "FAILED"
        else:
            return "PASSED"

    def test_opssight_pod_coverage_policy(self, policy):
        self.logger.debug("Starting OpsSight Pod Coverage Test")
        dump, err = getSkyfireDump(host_name="localhost", port=self.skyfire_port)
        if err is not None:
            self.logger.debug("Could not get Skyfire Report: %s", err)
            return "FAILED"
        if dump["mult-perceptor-kube-report"]["pod_coverage"] < policy:
            return "FAILED"
        else:
            return "PASSED"

    def test_hub_image_coverage_policy(self, policy):
        self.logger.debug("Starting Hub Image Coverage Test")
        dump, err = getSkyfireDump(host_name="localhost", port=self.skyfire_port)
        if err is not None:
            self.logger.debug("Could not get Skyfire Report: %s", err)
            return "FAILED"
        self.logger.debug("Hub Image Coverage: %f", dump["mult-hub-mult-perceptor-report"]["image_coverage"])
        if dump["mult-hub-mult-perceptor-report"]["image_coverage"] < policy:
            return "FAILED"
        else:
            return "PASSED"

    def test_pod_label_coverage_policy(self, policy):
        self.logger.debug("Starting test_pod_discovery")
        test_result = "FAILED"

        # TODO Check pod label metric from reports

        self.logger.debug("Finished test_opssight_sends_pod_to_hub")
        return test_result

    def test_pod_annotation_coverage_policy(self, policy):
        self.logger.debug("Starting test_pod_discovery")
        test_result = "FAILED"

        # TODO Check pod annotation metric from reports

        self.logger.debug("Finished test_opssight_sends_pod_to_hub")
        return test_result

    def test_pod_discovery(self):
        self.logger.debug("Starting test_pod_discovery")
        test_result = "FAILED"

        # Create a pod
        self.logger.debug("Creating a Pod in %s namespace", self.namespace)
        pod_name = "test-pod"
        success, err = kubeApiBackOff(lambda: self.k_client.create_pod(self.namespace, pod_name), 2, 10) 
        if not success:
            self.logger.error("Failed to create Pod: %s" % err)
            return test_result

        # Test if pod appears in Kube and OpsSight reports
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

        self.logger.debug("Finished test_pod_discovery")
        return test_result

    def test_opssight_sends_pod_to_hub(self):
        self.logger.debug("Starting test_opssight_sends_pod_to_hub")
        test_result = "FAILED"

        # Create a pod
        self.logger.debug("Creating a Pod in %s namespace", self.namespace)
        pod_name = "test-pod"
        success, err = kubeApiBackOff(lambda: self.k_client.create_pod(self.namespace, pod_name), 2, 10) 
        if not success:
            self.logger.error("Failed to create Pod: %s" % err)
            return test_result

        # TODO Check for pod in OpsSight report

        # TODO Check for pod in Hub report

        self.logger.debug("Finished test_opssight_sends_pod_to_hub")
        return test_result



    def test_opssight_annotates_pod(self):
        self.logger.debug("Starting test_opssight_annotates_pod")
        test_result = "FAILED"

        # TODO Check annotations on Pod

        self.logger.debug("Finished test_opssight_annotates_pod")
        return test_result

    def test_opssight_labels_pod(self):
        self.logger.debug("Starting test_opssight_labels_pod")
        test_result = "FAILED"

        # TODO check labels on Pod

        self.logger.debug("Finished test_opssight_labels_pod")
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


# Retries a function - Sometimes functions execute too quickly so this retries a few times
def kubeApiBackOff(f, pause=2, repeats=10):
    for i in range(repeats):
        err = f()
        if err is None:
            return True, None
        time.sleep(pause)
    return False, err 
            



