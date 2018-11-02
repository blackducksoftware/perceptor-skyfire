import json
import requests
import datetime 
import time
from kubernetes import client, config
import logging
import util


class Container:
    def __init__(self, blob):
        self.name = blob.name
        self.image = blob.image
        self.image_id = blob.image_id

class Pod:
    def __init__(self, blob):
        self.labels = blob.metadata.labels
        self.annotations = blob.metadata.annotations
        self.name = blob.metadata.name
        self.namespace = blob.metadata.namespace
        self.containers = []
        for cont in blob.status.container_statuses:
            self.containers.append(Container(cont))
        self.uid = blob.metadata.uid

class Dump:
    def __init__(self, pod_blob):
        self.time_stamp = datetime.datetime.now()
        self.pods = list(map(Pod, pod_blob.items))
    
class Client:
    def __init__(self, in_cluster):
        if in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self.v1 = client.CoreV1Api()

    def get_dump(self):
        pod_blob = self.get_pods()
        return Dump(pod_blob)

    def get_namespaces(self):
        return [ns.metadata.name for ns in self.v1.list_namespace()]

    def get_pods(self, namespace=None):
        if namespace is None:
            return self.v1.list_pod_for_all_namespaces(watch=False)
        else:
            return self.v1.list_namespaced_pod(namespace)


def analyze_blobs(blob, count):
    """
    This is just for debug purposes.
    """
    prefix = ' ' * count * 2
    print("dir: ", dir(blob))
    for (k, b) in blob.__dict__.items():
        try:
            print(prefix, k, type(b))
            analyze_blobs(b, count + 1)
        except:# Exception as e:
#            print(prefix, "exception:", e)
#            print(prefix, k, type(b))
            pass

def example():
    kubeClient = Client(in_cluster=False)
    dump = kubeClient.get_dump()
    print(json.dumps(dump, default=util.default_json_serializer, indent=2))

if __name__ == "__main__":
    example()
