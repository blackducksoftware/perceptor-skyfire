from kubernetes import config, client
import time


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
