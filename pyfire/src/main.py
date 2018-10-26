from cluster_clients import *
import kubernetes
import time
import json
import sys

def main():
	if len(sys.argv) < 2:
		print("USAGE:")
		sys.exit("Wrong Number of Parameters")

	with open(sys.argv[1]) as f:
		config = json.load(f)

	print("config:" + str(config))

	kube_client = KubeClientWrapper(config.get('use_in_cluster_config'))
	opssight_url = config.get("perceptor_URL")
	hub_url = config.get("hub_URL")
	port = config.get("port")
	usr = config.get("hub_username")
	password = config.get("hub_password")

	i = 0
	while True:
		print("hi! {}".format(i))
		i += 1
		print(kube_client.get_pods())
		time.sleep(1)

main()