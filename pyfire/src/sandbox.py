import sys 
import os
import json
from cluster_clients import *

def main():
    if len(sys.argv) < 2:
        print("USAGE:")
        print("python3 run.py <config_file_path>")
        sys.exit("Wrong Number of Parameters")

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logging.debug("Starting Tests")
    
    # Read parameters from config file
    test_config_path = sys.argv[1]

    with open(test_config_path) as f:
        test_config_json = json.load(f)

    incluster = test_config_json["Skyfire"]["UseInClusterConfig"]
    perceptor_url = test_config_json["Perceptor"]["URL"]
    #hub_urls = test_config_json["Hub"]["Hosts"]
    #usr = test_config_json["Hub"]["User"]
    #password = test_config_json["Hub"]["PasswordEnvVar"]

    # Create Kubernetes, OpsSight, and Hub Clients
    perceptor_client = PerceptorClient(perceptor_url, False)
    #hub_clients = {}
    #for url in hub_urls:
    #    hub_clients[url] = HubClient(url, usr, password, incluster)
    #kube_client = KubeClientWrapper(False)

    # TODO - Calculate metrics from dumps

    erceptorScrape = perceptor_client.get_scrape()
    print(json.dumps( erceptorScrape.data ,indent=2))

    

main()