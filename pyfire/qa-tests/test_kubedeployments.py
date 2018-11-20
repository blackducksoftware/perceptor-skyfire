#!/usr/bin/python

# Contains tests for the various ways one can deploy containers into a Kubernetes cluster.
# Requirements: must be run using pytest and python3.
# Also requires you to have logged into or be inside your cluster before running.
# To run tests on the command line, run "pytest -v test_kubedeployments.py"

from kubernetes import client, utils
from kubernetes.client.rest import ApiException
import logging
import pytest
import qa_opssight_tasks
import time
import urllib3


# Setup & global variables
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
kubeClient = qa_opssight_tasks.kubeClientSetup()
utilsClient = client.ApiClient()
ns = "kubedeployments"
qa_opssight_tasks.createNamespace(kubeClient, ns)
assertTimeout = 180  # time in seconds before we give up trying to assert


# Shared assertion template for test cases
# TODO: add assertions to make sure pod is scanned, project exists in hub,
# and # of vulns in hub matches labels/annotations
# Input: name of pod, name of namespace it's located in
def assertTemplate(podName, namespace):
    endTime = time.monotonic() + assertTimeout
    podFoundInKube = False
    podFoundInOpssight = False
    nsPodName = "{0}/{1}".format(namespace, podName)
    logging.info("Searching for pod {0} in Kube and OpsSight for {1} seconds".format(
        podName, assertTimeout))
    while time.monotonic() < endTime:
        report, err = qa_opssight_tasks.getSkyfireReport()
        if err is not None:
            logging.debug("Could not get Skyfire report: {}".format(err))
            time.sleep(10)
            continue

        if not podFoundInKube:
            nsPodsInKube = report['kube-report']['scrape']['ns_pod_names']
            podFoundInKube = nsPodName in nsPodsInKube

        if not podFoundInOpssight:
            for pScrape in report['mult-opssight-reports']['scrapes']:
                nsPodsInOpssight = pScrape['ns_pod_names']
                if nsPodName in nsPodsInOpssight:
                    podFoundInOpssight = True
                    break

        if podFoundInKube and podFoundInOpssight:
            break
        time.sleep(10)

    assert podFoundInKube  # assert that pod exists in the cluster
    assert podFoundInOpssight  # assert that pod was picked up by OpsSight


# Shared test teardown template for test cases
# This might be removed if we eventually have a method that wipes the whole cluster
# Input: namespace to delete
@pytest.fixture(scope="module")
def teardownTemplate(request):
    def fin():
        logging.info("Teardown - deleting namespace {}".format(ns))
        try:
            response = kubeClient.delete_namespace(name=ns, body={})
            logging.debug(response)
        except ApiException as err:
            logging.error(
                "Error occurred when deleting namespace {0}: {1}".format(ns, err))
    request.addfinalizer(fin)


@pytest.mark.kubedeployment
@pytest.mark.usefixtures("teardownTemplate")
def testAddPodFromFile():
    logging.info(
        "Deploying a pod with kubectl create -f in namespace: {}".format(ns))
    podName = "addpodfromfile-ibmjava"
    try:
        response = utils.create_from_yaml(utilsClient, "./ibmjava.yml")
        logging.debug(response)
        assertTemplate(podName, ns)
    except ApiException as err:
        logging.error(
            "Error occurred when testing deploying a pod with kubectl create -f: {}".format(err))
        assert False


@pytest.mark.kubedeployment
@pytest.mark.usefixtures("teardownTemplate")
def testAddPodWithRun():
    logging.info(
        "Deploying a pod with kubectl run in namespace: {}".format(ns))
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
        response = kubeClient.create_namespaced_pod(
            namespace=ns, body=podManifest)
        logging.debug(response)
        assertTemplate(podName, ns)
    except ApiException as err:
        logging.error(
            "Error occurred when testing deploying a pod with kubectl run: {}".format(err))
        assert False


@pytest.mark.kubedeployment
@pytest.mark.usefixtures("teardownTemplate")
def testAddPodBySha():
    logging.info(
        "Deploying a pod with kubectl run in namespace: {} using SHA instead of tag".format(ns))
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
        response = kubeClient.create_namespaced_pod(
            namespace=ns, body=podManifest)
        logging.debug(response)
        assertTemplate(podName, ns)
    except ApiException as err:
        logging.error(
            "Error occurred when testing deploying a pod by SHA with kubectl run: {}".format(err))
        assert False
