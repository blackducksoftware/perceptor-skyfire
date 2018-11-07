import json
import requests
import datetime 
import time
from kubernetes import client, config
import logging
import util
import podreader


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
    
    def opssight_labels(self):
        expected = set(podreader.get_all_labels(len(self.containers)))
        actual = set(self.labels.keys())
        present = expected.intersection(actual)
        missing = expected - actual
        return (missing, present)
    
    def has_all_labels(self):
        missing, _ = self.opssight_labels()
        return len(missing) == 0
    
    def is_partially_labeled(self):
        missing, present = self.opssight_labels()
        return len(missing) > 0 and len(present) > 0

    def opssight_annotations(self):
        expected = set(podreader.get_all_annotations(len(self.containers)))
        actual = set(self.annotations.keys())
        present = expected.intersection(actual)
        missing = expected - actual
        return (missing, present)
    
    def has_all_annotations(self):
        missing, _ = self.opssight_annotations()
        return len(missing) == 0
    
    def is_partially_annotated(self):
        missing, present = self.opssight_annotations()
        return len(missing) > 0 and len(present) > 0


class Dump:
    def __init__(self, pod_blob):
        self.time_stamp = datetime.datetime.now()
        self.pods = list(map(Pod, pod_blob.items))
    
class Client:
    def __init__(self, in_cluster):
        logging.debug("instantiating kube client with in_cluster %s", in_cluster)
        if in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self.v1 = client.CoreV1Api()
        logging.debug("instantiated kubeclient")

    def get_dump(self):
        logging.debug("getting kube dump")
        pod_blob = self.get_pods()
        logging.debug("got kube dump of pods")
        return Dump(pod_blob)
    
    def get_scrape(self):
        """
        This is just a facade because scraper expects this method naming
        """
        return self.get_dump()

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

def example(in_cluster):
    kubeClient = Client(in_cluster)
    dump = kubeClient.get_dump()
    print(json.dumps(dump, default=util.default_json_serializer, indent=2))
    for pod in dump.pods:
        print(pod.name, 
            "\n", pod.opssight_labels(),
            "\n\t", pod.has_all_labels(), pod.is_partially_labeled(), 
            "\n", pod.opssight_annotations(), 
            "\n\t", pod.has_all_annotations(), pod.is_partially_annotated(), "\n")

if __name__ == "__main__":
    import sys
    in_cluster = False
    if len(sys.argv) > 1:
        in_cluster = True if sys.argv[1] == 'true' else False
    example(in_cluster)
