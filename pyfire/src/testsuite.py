import threading 
import logging
from cluster_clients import KubeClient
import subprocess
import requests 
import time
import json 

import random

class TestSuite:
    def __init__(self):
        self.event_thread = threading.Thread(target=self.tests)
        self.event_thread.daemon = True
        self.test_state = "STOPPED"
        self.in_progress = False
        self.accessing_data = False
        self.event_thread.start()
        
        self.test_results = {'state' : 'NO_TESTS', 'summary' : '','data' : {}}

    def start(self):
        if self.in_progress == False:
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
        time.sleep(7)
        val = random.randint(0,10)
        if val <= 8:
            return "PASSED"
        else:
            return "FAILED"

    def opssight_repo_coverage(self, policy):
        dump, err = getSkyfireDump()
        total_repos = 0
        total_repos += len(dump["perceptor-kube-report"]["only_kube_repos"])
        total_repos += len(dump["perceptor-kube-report"]["only_perceptor_repos"])
        total_repos += len(dump["perceptor-kube-report"]["both_repos"])
        num_in_both = len(dump["perceptor-kube-report"]["both_repos"])
        logging.debug("OpsSight Repo Coverage: %f", (num_in_both / float(total_repos))*100.0)
        if (num_in_both / float(total_repos))*100.0 < policy:
            return "FAILED"
        else:
            return "PASSED"

    def opssight_pod_coverage(self, policy):
        dump, err = getSkyfireDump()
        total_pods = 0
        total_pods += len(dump["perceptor-kube-report"]["only_kube_pod_names"])
        total_pods += len(dump["perceptor-kube-report"]["only_perceptor_pod_names"])
        total_pods += len(dump["perceptor-kube-report"]["both_pod_names"])
        num_in_both = len(dump["perceptor-kube-report"]["both_pod_names"])
        logging.debug("OpsSight Pod Coverage: %f", (num_in_both / float(total_pods))*100.0)
        if (num_in_both / float(total_pods))*100.0 < policy:
            return "FAILED"
        else:
            return "PASSED"

    def hub_image_coverage(self, policy):
        dump, err = getSkyfireDump()
        total_images = 0
        total_images += len(dump["mult-hub-perceptor-report"]["only_hub_image_shas"])
        total_images += len(dump["mult-hub-perceptor-report"]["only_perceptor_images"])
        total_images += len(dump["mult-hub-perceptor-report"]["both_images"])
        num_in_both = len(dump["mult-hub-perceptor-report"]["both_images"])
        logging.debug("Hub Image Coverage: %f", (num_in_both / float(total_images))*100.0)
        if (num_in_both / float(total_images))*100.0 < policy:
            return "FAILED"
        else:
            return "PASSED"

    def create_pod_test(self):
        logging.debug("Starting Pod Test")
        k_client = KubeClient(in_cluster=False)

        # Create a namespace
        namespace = 'bd' 

        # Create a pod
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
            logging.info(api_response)
        except Exception as e:
            logging.error("Exception when calling CoreV1Api->create_namespaced_pod: %s\n" % e)

        test_result = "FAILED"

        for i in range(90):
            dump, err = getSkyfireDump()
            if err is not None:
                logging.error(err)
                time.sleep(10)
                continue

            kd = dump['scrapes']['kube']['pod_names']
            pod_in_kube = 'hammer-pod' in kd
            
            pd = dump['scrapes']['perceptor']['pod_names']
            pod_in_opssight = 'bd/hammer-pod' in pd

            if pod_in_kube and pod_in_opssight:
                test_result = "PASSED"
                break
            time.sleep(10)

        try: 
            r = subprocess.run("oc delete pod {} -n {}".format(pod_name,namespace),shell=True,stdout=subprocess.PIPE)
            logging.info(r)
        except Exception as e:
            logging.error("Exception when calling CoreV1Api->create_namespaced_pod: %s\n" % e)

        logging.debug("Finished Pod Test")
        return test_result
            

def getSkyfireDump(host_name="localhost", port=80):
    url = "http://{}:{}/latestreport".format(host_name, 9092)
    r = requests.get(url)
    if 200 <= r.status_code <= 299:
        logging.debug("Skyfire http Dump Request Status Code: %s - %s", r.status_code, url)
        return json.loads(r.text), None
    else:
        logging.error("Could not connect to Skyfire")
        return {}, {'error' : "Skyfire Connection Fail", 'status' : r.status_code, 'url' : url} 