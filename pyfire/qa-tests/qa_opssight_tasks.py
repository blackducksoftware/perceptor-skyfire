#!/usr/bin/python

from kubernetes import client, config, utils
import logging
import requests


# ===== Python Kubernetes Client-related tasks =====
# Set up python kubernetes client
# Input: whether or not this is being run in a cluster (True/False)
# Output: CoreV1Api object
def kubeClientSetup(runInCluster=False):
    if runInCluster:
        config.load_incluster_config()
    else:
        config.load_kube_config()
    kClient = client.CoreV1Api()
    return kClient


# ===== Namespace-related tasks =====
# Check if a namespace with name namespaceName exists in the cluster
# Input: kubernetes client, name of namespace
# Output: True/False
def doesNamespaceExist(kClient, namespaceName):
    try:
        namespaces = kClient.list_namespace()
    except Exception as err:
        logging.error("Error retrieving list of namespaces: {}".format(err))
        return False
    if namespaceName in [ns.metadata.name for ns in namespaces.items]:
        logging.debug("Found namespace {} in cluster".format(namespaceName))
        return True
    return False


# Create a namespace with name namespaceName
# Input: kubernetes client, name of namespace
# Ouput: True/False
def createNamespace(kClient, namespaceName):
    logging.debug("Creating namespace {}".format(namespaceName))
    nsBody = {
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': namespaceName
        }
    }
    try:
        response = kClient.create_namespace(body=nsBody)
        logging.debug(response)
        return doesNamespaceExist(kClient, namespaceName)
    except Exception as err:
        logging.error("Exception when creating namespace {}".format(namespaceName))
        return False


# Delete a namespace with name namespaceName
# Input: kubernetes client, name of namespace
# Ouput: True/False
def deleteNamespace(kClient, namespaceName):
    logging.debug("Deleting namespace {}".format(namespaceName))
    try:
        kClient.delete_namespace(name=namespaceName, body={})
        while True:
            nsExists = doesNamespaceExist(kClient, namespaceName)
            if not nsExists:
                break
        logging.debug("Successfully deleted namespace {}".format(namespaceName))
        return True
    except Exception as err:
        logging.error(
            "Error occurred when deleting namespace {0}: {1}".format(namespaceName, err))
        return False


# ===== Pod and Image Stream-related tasks =====
# Check if a pod with name podName in namespace namespaceName exists in the cluster
# Input: kubernetes client, name of pod, name of namespace
# Output: True/False
def doesPodExist(kClient, podName, namespaceName):
    try:
        nsPods = kClient.list_namespaced_pod()  # might be list_pod_for_all_namespaces instead?
    except Exception as err:
        logging.error("Error retrieving list of pods in namespace {0}: {1}".format(namespaceName, err))
        return False
    if podName in [pod.metadata.name for pod in nsPods.items]:  # need to check if this works
        logging.debug("Found pod {0} in namespace {1}".format(podName, namespaceName))
        return True
    logging.debug("Pod {0} in namespace {1} does not exist".format(podName, namespaceName))
    return False


# Create a pod by providing a file with the pod's definition
# Input: kubernetes utils client, name of pod, name of namespace, path to pod definition file
# Ouput: True/False
def createPodFromFile(kClient, uClient, podName, namespaceName, filePath):
    logging.info("Deploying a pod with kubectl create -f in namespace: {}".format(namespaceName))
    try:
        response = utils.create_from_yaml(uClient, filePath)
        logging.debug(response)
        return doesPodExist(kClient, podName, namespaceName)
    except Exception as err:
        logging.error(
            "Error occurred when deploying a pod with kubectl create -f: {}".format(err))
        return False


# Create a pod using 'kubectl run'
# Input: kubernetes client, name of podd, name of namespace, pod manifest
# Ouput: True/False
def createPodWithRun(kClient, podName, namespaceName, podManifest):
    logging.info("Deploying a pod {0} with kubectl run in namespace: {}".format(podName, namespaceName))
    try:
        response = kClient.create_namespaced_pod(namespace=namespaceName, body=podManifest)
        logging.debug(response)
        return doesPodExist(kClient, podName, namespaceName)
    except Exception as err:
        logging.error(
            "Error occurred when testing deploying a pod with kubectl run: {}".format(err))
        return False


# Delete a pod with name podName in namespace namespaceName
# Input: kubernetes client, name of pod, name of namespace
# Ouput: True/False
def deletePod(kClient, podName, namespaceName):
    logging.debug("Deleting pod {0} in namespace {1}".format(podName, namespaceName))
    try:
        kClient.delete_namespaced_pod(name=podName, namespace=namespaceName, body={})
        while True:
            podExists = doesPodExist(kClient, podName, namespaceName)
            if not podExists:
                break
        logging.debug("Successfully deleted pod {0} in namespace {1}".format(podName, namespaceName))
        return True
    except Exception as err:
        logging.error("Error occurred when deleting pod {0} in namespace {1}: {2}".format(podName, namespaceName, err))
        return False


# ===== Skyfire-related tasks =====
# Get and return the skyfire report in JSON format
# Input: host name, port
# Output: Skyfire report Dict object
def getSkyfireReport(host="localhost", port=80):
    skyfireReportUrl = "http://{}:{}/latestreport".format(host, port)
    logging.info("Getting Skyfire report from {}".format(skyfireReportUrl))
    response = requests.get(url=skyfireReportUrl)
    if 200 <= response.status_code <= 299:
        logging.debug("http request to {0} returned status code: {1}".format(skyfireReportUrl, response.status_code))
        return response.json(), None
    else:
        logging.error("Error connecting to Skyfire")
        return {}, {'error': "Skyfire Connection Fail", 'status': response.status_code, 'url': skyfireReportUrl}
