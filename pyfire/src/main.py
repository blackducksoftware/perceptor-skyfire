import kubernetes
import time
import json
import sys

def get_kube_client(use_incluster_config):
	"""
	Pass in True to use in-cluster-config.
	Pass in	False to use the cluster that your
	`oc` or `kubectl` is currently pointing to.
	"""
	if use_incluster_config is None:
		kubernetes.config.load_incluster_config()
	else:
		kubernetes.config.load_kube_config()

	return kubernetes.client.CoreV1Api()

def get_pods(kube_client):
	print("Listing pods with their IPs:")
	ret = kube_client.list_pod_for_all_namespaces(watch=False)
	for i in ret.items:
		print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
	return ret


if len(sys.argv) < 2:
	print("USAGE:")
	sys.exit("Wrong Number of Parameters")

with open(sys.argv[1]) as f:
	config = json.load(f)

print("config:" + str(config))

kube_client = get_kube_client(config.get('UseInClusterConfig'))

i = 0
while True:
	print("hi! {}".format(i))
	i += 1
	print(get_pods(kube_client))
	time.sleep(1)
