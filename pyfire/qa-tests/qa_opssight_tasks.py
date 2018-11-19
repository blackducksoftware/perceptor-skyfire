#!/usr/bin/python

from configparser import SafeConfigParser
from kubernetes import client, config
import logging
import os
import requests


opsConfig = SafeConfigParser(os.environ)
opsConfig.read('./qa-opssight.cfg')


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


# ===== Skyfire-related tasks =====
# Get and return the skyfire report in JSON format
# Output: Skyfire report Dict object
def getSkyfireReport():
    skyfireReportUrl = opsConfig['SKYFIRE']['reportUrl']
    response = requests.get(url=skyfireReportUrl)
    if 200 <= response.status_code <= 299:
        logging.debug("http request to {0} returned status code: {1}".format(skyfireReportUrl, response.status_code))
        return response.json(), None
    else:
        logging.error("Error connecting to Skyfire")
        return {}, {'error': "Skyfire Connection Fail", 'status': response.status_code, 'url': skyfireReportUrl}
