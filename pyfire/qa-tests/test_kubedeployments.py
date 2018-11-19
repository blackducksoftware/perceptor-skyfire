#!/usr/bin/python

# Requirements: must be run using pytest and python3.
# Also requires you to have logged into or be inside your cluster before running.
# To run tests on the command line, run "pytest -v test_kubedeployments.py"

from kubernetes import client, utils
from kubernetes.client.rest import ApiException
import logging
import pytest
import qa_opssight_tasks
import time


# Setup & global variables
kubeClient = qa_opssight_tasks.kubeClientSetup()
utilsClient = client.ApiClient()
ns = "default"
assertTimeout = 900  # time in seconds before we give up trying to assert


# Shared assertion template for test cases
def assertTemplate(podName, namespace):
    endTime = time.monotonic() + assertTimeout
    podFoundInKube = False
    podFoundInOpssight = False
    while time.monotonic() < endTime:
        report, err = qa_opssight_tasks.getSkyfireReport()
        if err is not None:
            logging.error(err)
            time.sleep(10)
            continue

        if not podFoundInKube:
            podsInKube = report['kube-report']['scrape']['pod_names']
            podFoundInKube = podName in podsInKube

        if not podFoundInOpssight:
            opssights = report['mult-opssight-reports']['scrapes']
            for i in opssights:
                podsInOpssight = opssights[i]['pod_names']
                if podName in podsInOpssight:
                    podFoundInOpssight = True
                    break

        if podFoundInKube and podFoundInOpssight:
            break
        time.sleep(10)

    assert podFoundInKube  # assert that pod exists in the cluster
    assert podFoundInOpssight  # assert that pod was picked up by OpsSight


# Shared test teardown template for test cases
# This might be removed if we eventually have a method that wipes the whole cluster
def teardownTemplate(podName, namespace):
    logging.log("Teardown - deleting pod {0} in namespace {1}".format(podName, namespace))
    deleteBody = kubeClient.V1DeleteOptions()
    try:
        response = kubeClient.delete_namespaced_pod(name=podName, namespace=ns, body=deleteBody)
        logging.info(response)
    except ApiException as err:
        logging.error("Error occurred when deleting pod {0} in namespace {1}: {2}".format(podName, namespace, err))


@pytest.mark.kubedeployment
def testAddPodFromFile():
    logging.log("Deploying a pod with kubectl create -f in namespace: {}".format(ns))
    podName = "addpodfromfile-ibmjava"
    try:
        response = utils.create_from_yaml(utilsClient, "./ibmjava.yml")
        logging.info(response)
        assertTemplate(podName, ns)
    except ApiException as err:
        logging.error("Error occurred when testing deploying a pod with kubectl create -f: {}".format(err))
        assert False
    # teardownTemplate(podName, ns)


@pytest.mark.kubedeployment
def testAddPodWithRun():
    logging.log("Deploying a pod with kubectl run in namespace: {}".format(ns))
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
        response = kubeClient.create_namespaced_pod(namespace=ns, body=podManifest)
        logging.info(response)
        assertTemplate(podName, ns)
    except ApiException as err:
        logging.error("Error occurred when testing deploying a pod with kubectl run: {}".format(err))
        assert False
    # teardownTemplate(podName, ns)


@pytest.mark.kubedeployment
def testAddPodBySha():
    logging.log("Deploying a pod with kubectl run in namespace: {} using SHA instead of tag".format(ns))
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
        response = kubeClient.create_namespaced_pod(namespace=ns, body=podManifest)
        logging.info(response)
        assertTemplate(podName, ns)
    except ApiException as err:
        logging.error("Error occurred when testing deploying a pod by SHA with kubectl run: {}".format(err))
        assert False
    # teardownTemplate(podName, ns)
