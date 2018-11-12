#!/usr/bin/python

# Requirements: must be run using pytest
# Download this with "pip install pytest"
# To run tests on the command line, run "pytest -v opssightTestCases.py"

from configparser import SafeConfigParser
from kubernetes import client, config
import os
import pytest
import time


opsConfig = SafeConfigParser(os.environ)
opsConfig.read('./qa-opssight.cfg')
if opsConfig['CLUSTER']['runInCluster'] == "True":
    config.load_incluster_config()
else:
    config.load_kube_config()
kubeClient = client.CoreV1Api()
ns = opsConfig['CLUSTER']['namespace']
kubeClient.create_namespace(kubeClient.V1Namespace(metadata=client.V1ObjectMeta(name=ns)))


# ===== Simple Example Tests =====
@pytest.mark.example
def testCreatePod():
    print("Creating a pod in namespace: {}".format(ns))
    podName = "rabbitmq-36-test"
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
                'args': ['sleep', '3600']
            }]
        }
    }
    response = kubeClient.create_namespaced_pod(namespace=ns, body=podManifest)
    assert response.metadata.name == podName  # will prob delete this eventually
    assert response.status.phase  # will prob delete this eventually
    time.sleep(180)  # not the best but this should do for now
    # curl skyfire data
    # read skyfire data
    # assert that skyfire records that pod was created
