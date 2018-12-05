#!/usr/bin/python

from kubernetes import client, config
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


# Check if a namespace with name namespaceName exists in the cluster
# Input: kubernetes client, name of namespace
def doesNamespaceExist(kClient, namespaceName):
    try:
        namespaces = kClient.list_namespace()
    except Exception as err:
        logging.error("Error retrieving list of namespaces: {}".format(err))
        return False
    if namespaces in [ns.metadata.name for ns in namespaces.items]:
        return True
    return False


# Create a namespace with name namespaceName
# Input: kubernetes client, name of namespace
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
    except Exception as err:
        logging.error("Exception when creating namespace {}".format(namespaceName))


# Delete a namespace with name namespaceName
# Input: kubernetes client, name of namespace
def deleteNamespace(kClient, namespaceName):
    logging.debug("Deleting namespace {}".format(namespaceName))
    try:
        kClient.delete_namespace(name=namespaceName, body={})
        while True:
            nsExists = doesNamespaceExist(kClient, namespaceName)
            if not nsExists:
                break
    except Exception as err:
        logging.error(
            "Error occurred when deleting namespace {0}: {1}".format(namespaceName, err))


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
