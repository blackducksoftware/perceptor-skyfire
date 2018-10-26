from kubernetes import config, client
import time
import json
import sys


if len(sys.argv) < 2:
	print("USAGE:")
	sys.exit("Wrong Number of Parameters")

with open(sys.argv[1]) as f:
	print("config:" + str(json.load(f)))


def get_pods():
	config.load_incluster_config()
	v1 = client.CoreV1Api()
	print("Listing pods with their IPs:")
	ret = v1.list_pod_for_all_namespaces(watch=False)
	for i in ret.items:
		print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
	return ret


i = 0
while True:
	print("hi! {}".format(i))
	i += 1
	print(get_pods())
	time.sleep(1)
