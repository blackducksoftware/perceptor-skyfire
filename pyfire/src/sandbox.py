import sys 
import os
import json
from cluster_clients import *

def main():
    if len(sys.argv) < 2:
        print("USAGE:")
        print("python3 run.py <config_file_path>")
        sys.exit("Wrong Number of Parameters")

    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    logging.debug("Starting Tests")
    
    # Read parameters from config file
    test_config_path = sys.argv[1]

    with open(test_config_path) as f:
        test_config_json = json.load(f)

    incluster = test_config_json["use_in_cluster_config"]
    opssight_url = test_config_json["perceptor_URL"]
    hub_url = test_config_json["hub_URL"] 
    port = test_config_json["port"]
    usr = test_config_json["hub_username"]
    password = test_config_json["hub_password"]

    # Create Kubernetes, OpsSight, and Hub Clients
    opssight_client = OpsSightClient(opssight_url, incluster)
    hub_client = HubClient(hub_url, usr, password, incluster)

    # TO DO - Add Functinality to the Hub
    print(json.dumps( hub_client.get_projects_dump() ,indent=2))

    print(hub_client.get_projects_names())
    print(hub_client.get_projects_link("versions"))



main()