import sys 
import os
import json
from cluster_clients import *

def main():
    if len(sys.argv) < 2:
        print("USAGE:")
        print("python3 run.py <config_file_path>")
        sys.exit("Wrong Number of Parameters")

    logging.basicConfig(level=logging.ERROR, stream=sys.stdout)
    logging.debug("Starting Tests")
    
    # Read parameters from config file
    test_config_path = sys.argv[1]

    test_config_json = None
    with open(test_config_path) as f:
        test_config_json = json.load(f)

    opssight_url = test_config_json["PerceptorURL"]
    hub_url = test_config_json["HubURL"] 
    port = test_config_json["Port"]
    usr = test_config_json["Username"]
    password = test_config_json["Password"]

    # Create Kubernetes, OpsSight, and Hub Clients
    opssight_client = OpsSightClient(opssight_url)
    hub_client = HubClient(hub_url, usr, password)
    #hub_client = HubClient("???", usr, password)
    #hub_client = HubClient("???", usr, password)
    #hub_client = HubClient("???", usr, password)

    # TO DO - Add Functinality to the Hub
    print(json.dumps( hub_client.get_projects_dump() ,indent=2))

    print(hub_client.get_projects_names())
    print(hub_client.get_projects_link("versions"))



main()