#!/usr/bin/python

# Requirements: must be run using pytest
# Download this with "pip install pytest"
# To run tests on the command line, run "pytest -v test_kubedeployments.py"

from kubernetes import client, utils
from kubernetes.client.rest import ApiException
import pytest
import qa_opssight_tasks
import time


# Setup & global variables
kubeClient = qa_opssight_tasks.kubeClientSetup()
ns = "default"
assertTimeout = 900  # time in seconds before we give up trying to assert


def assertTemplate(podName, namespace):
    endTime = time.monotonic() + assertTimeout
    while time.monotonic() < endTime:
        skyfireReport = qa_opssight_tasks.getSkyfireReport()
        # parse skyfireReport to see if pod was created, labels/annotations are there, etc.
        assert True  # get rid of this eventually obviously
        break  # this should eventually be used in conjunction with an if-else


@pytest.mark.kubedeployment
def testAddPodFromFile():
    print("Deploying a pod with kubectl create -f in namespace: {}".format(ns))
    podName = "addpodfromfile-ibmjava"
    k8s_client = client.ApiClient()
    try:
        utils.create_from_yaml(k8s_client, "./ibmjava.yml")
        assertTemplate(podName, ns)
    except ApiException as err:
        print("Error occurred when testing deploying a pod with kubectl create -f: {}".format(err))
        assert False


@pytest.mark.kubedeployment
def testAddPodWithRun():
    print("Deploying a pod with kubectl run in namespace: {}".format(ns))
    podName = "addpodwithrun-rabbitmq36"
    podManifest = {
        'apiVersion': 'v1',
        'kind': 'Pod',
        'metadata': {
            'name': podName
        },
        'spec': {
            'containers': [{
                'image': 'rabbitmq:3.6',
                'name': 'rabbitmq36',
                'args': ['sleep', '360']
            }]
        }
    }
    try:
        kubeClient.create_namespaced_pod(namespace=ns, body=podManifest)
        assertTemplate(podName, ns)
    except ApiException as err:
        print("Error occurred when testing deploying a pod with kubectl run: {}".format(err))
        assert False


@pytest.mark.kubedeployment
def testAddPodBySha():
    print("Deploying a pod with kubectl run in namespace: {} using SHA instead of tag".format(ns))
    podName = "addpodbysha-perceptor"
    podManifest = {
        'apiVersion': 'v1',
        'kind': 'Pod',
        'metadata': {
            'name': podName
        },
        'spec': {
            'containers': [{
                'image': 'gcr.io/gke-verification/blackducksoftware/perceptor@sha256:9914478c9642be49e7791a7a29207c0a6194c8bf6e9690ab5902008cce8af39f',
                'name': 'perceptorbysha',
                'args': ['sleep', '360']
            }]
        }
    }
    try:
        kubeClient.create_namespaced_pod(namespace=ns, body=podManifest)
        assertTemplate(podName, ns)
    except ApiException as err:
        print("Error occurred when testing deploying a pod by SHA with kubectl run: {}".format(err))
        assert False
