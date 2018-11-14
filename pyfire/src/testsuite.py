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
            self.test_results["data"]['MockTest1'] = ""
            self.test_results["data"]['MockTest2'] = ""
            self.test_results["data"]['MockTest3'] = ""
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

            r = self.mock_test()
            while self.accessing_data:
                pass
            self.accessing_data = True
            self.test_results["data"]['MockTest3'] = r
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
        time.sleep(10)
        val = random.randint(0,10)
        if val <= 8:
            return "PASSED"
        else:
            return "FAILED"


    def pod_test(self):
        logging.debug("Starting Pod Test")
        k_client = KubeClient(in_cluster=False)

        skyfire_path = "localhost"

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
            dump, err = getSkyfireDump(skyfire_path)
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
            

def getSkyfireDump(host_name="localhost"):
    url = "http://{}:{}/latestreport".format(host_name, 80)
    r = requests.get(url)
    if 200 <= r.status_code <= 299:
        logging.debug("Skyfire http Dump Request Status Code: %s - %s", r.status_code, url)
        return json.loads(r.text), None
    else:
        logging.error("Could not connect to Skyfire")
        return {}, {'error' : "Skyfire Connection Fail", 'status' : r.status_code, 'url' : url} 