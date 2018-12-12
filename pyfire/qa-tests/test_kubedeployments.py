#!/usr/bin/python

# Contains tests for the various ways one can deploy containers into a Kubernetes cluster.
# Requirements: must be run using pytest and python3.
# Also requires you to have logged into or be inside your cluster before running.
# At the moment, it assumes OpsSight exists in your cluster already.
# To run tests on the command line, run "pytest -v test_kubedeployments.py"

from kubernetes import client
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
# Input: image name, name of pod, name of namespace it's located in
def assertTemplate(imageName, podName, namespace):
    endTime = time.monotonic() + assertTimeout
    podFoundInKube, podFoundInOpssight, podLabeled, podAnnotated, projectFoundInBD = False, False, False, False, False
    nsPodName = "{0}/{1}".format(namespace, podName)
    logging.info("Searching for pod {0} in Kube and OpsSight for {1} seconds".format(
        podName, assertTimeout))
    while time.monotonic() < endTime:
        report, err = qa_opssight_tasks.getSkyfireReport()
        if err is not None:
            logging.debug("Could not get Skyfire report: {}".format(err))
            time.sleep(10)
            continue

        if not podFoundInKube:  # check that pod exists in the cluster
            nsPodsInKube = report['kube-report']['scrape']['ns_pod_names']
            podFoundInKube = nsPodName in nsPodsInKube

        if not podFoundInOpssight:  # check that pod was picked up by OpsSight
            for pScrape in report['mult-opssight-reports']['scrapes']:
                nsPodsInOpssight = pScrape['ns_pod_names']
                if nsPodName in nsPodsInOpssight:
                    podFoundInOpssight = True
                    break

        if not podLabeled:  # check that pod was labeled with Black Duck info
            nsPodsToLabels = report['kube-report']['scrape']['ns_pod_name_to_labels']
            if nsPodName in nsPodsToLabels:
                podLabels = nsPodsToLabels[nsPodName]
                if "pod.overall-status" and "pod.policy-violations" and "pod.vulnerabilities" in podLabels:
                    podLabeled = True

        if not podAnnotated:  # check that pod was annotated with Black Duck info
            nsPodsToAnnotations = report['kube-report']['scrape']['ns_pod_name_to_annotations']
            if nsPodName in nsPodsToAnnotations:
                podAnnotations = nsPodsToAnnotations[nsPodName]
                if "pod.overall-status" and "pod.policy-violations" and "pod.vulnerabilities" in podAnnotations:
                    podAnnotated = True

        if not projectFoundInBD:  # check that a relative project exists in a Black Duck instance
            for hScrape in report['mult-hub-reports']['scrapes']:
                projectNames = hScrape['project_names']
                if imageName in projectNames:
                    projectFoundInBD = True
                    break

        if podFoundInKube and podFoundInOpssight and podLabeled and podAnnotated:
            break
        time.sleep(10)

    assert podFoundInKube
    assert podFoundInOpssight
    assert podLabeled
    assert podAnnotated


# Shared test teardown template for test cases
# This might be removed if we eventually have a method that wipes the whole cluster
# Input: namespace to delete
@pytest.fixture(scope="module")
def teardownTemplate(request):
    def fin():
        logging.info("Teardown - deleting namespace {}".format(ns))
        qa_opssight_tasks.deleteNamespace(kubeClient, ns)
    request.addfinalizer(fin)


# Deploy a Pod from a file
@pytest.mark.kubedeployment
@pytest.mark.usefixtures("teardownTemplate")
def testAddPodFromFile():
    podName = "addpodfromfile-ibmjava"
    if qa_opssight_tasks.createPodFromFile(utilsClient, podName, ns, "./ibmjava.yml"):
        assertTemplate("ibmjava", podName, ns)
    else:
        logging.debug("Issue deploying pod {} for testAddPodFromFile; asserting False".format(podName))
        assert False


# Deploy a Pod using 'kubectl run'
@pytest.mark.kubedeployment
@pytest.mark.usefixtures("teardownTemplate")
def testAddPodWithRun():
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
    if qa_opssight_tasks.createPodWithRun(kubeClient, podName, ns, podManifest):
        assertTemplate("docker.io/rabbitmq", podName, ns)
    else:
        logging.debug("Issue deploying pod {} for testAddPodWithRun; asserting False".format(podName))
        assert False


# Deploy a Pod by SHA instead of <imageName>:<tag>
@pytest.mark.kubedeployment
@pytest.mark.usefixtures("teardownTemplate")
def testAddPodBySha():
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
    if qa_opssight_tasks.createPodWithRun(kubeClient, podName, ns, podManifest):
        assertTemplate("gcr.io/gke-verification/blackducksoftware/perceptor", podName, ns)
    else:
        logging.debug("Issue deploying pod {} for testAddPodBySha; asserting False".format(podName))
        assert False
