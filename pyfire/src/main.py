from cluster_clients import KubeClientWrapper
import kubernetes
import time
import json
import sys
from webserver import start_http_server
from scraper import Scraper
from skyfire import Skyfire

def main():
	if len(sys.argv) < 2:
		print("USAGE:")
		sys.exit("Wrong Number of Parameters")

	with open(sys.argv[1]) as f:
		config = json.load(f)

	print("config: " + json.dumps(config, indent=2))

	scraper = Scraper()
	scraper.start()

	skyfire = Skyfire(scraper)

	start_http_server(int(config['Skyfire']['Port']), skyfire)


main()


#	kube_client = KubeClientWrapper(config.get('use_in_cluster_config'))
#	i = 0
#	while True:
#		print("hi! {}".format(i))
#		i += 1
#		print(kube_client.get_pods())
#		time.sleep(1)
