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

    incluster = test_config_json["use_in_cluster_config"]
    opssight_url = test_config_json["perceptor_URL"]
    hub_url = test_config_json["hub_URL"] 
    port = test_config_json["port"]
    usr = test_config_json["hub_username"]
    password = test_config_json["hub_password"]

    # Create Kubernetes, OpsSight, and Hub Clients
    opssight_client = OpsSightClient(opssight_url, incluster)
    hub_client = HubClient(hub_url, usr, password, incluster)
    kube_client = KubeClientWrapper(False)

    # TO DO - Hub Testing
    #print(json.dumps( hub_client.get_projects_dump() ,indent=2))

    hub_analysis = hub_client.analyze_hub()
    print(hub_analysis)
    #print(hub_analysis.get_code_location_shas())
    #print(json.dumps( hub_analysis.data ,indent=2))
    
    #r = hub_client.api_get("https://engsreepath471-engsreepath471.10.1.176.130.xip.io/api/projects/30e2417e-339c-44e3-a235-a4cfff088676/versions/9d3e6876-f001-4a41-8ec6-a61b555c7501/policy-status")
    #print(json.dumps( r.json() ,indent=2))


    # TO DO - OpsSight Testing
    opssight_analysis = opssight_client.get_analysis()
    print(opssight_analysis)
    #print(json.dumps( opssight_analysis.data ,indent=2))
    #print(opssight_analysis.get_pods_images())

    print("== OpsSight vs Hub ==")
    opssight_pod_images = set(opssight_analysis.get_pods_images())
    hub_code_location_images = set(hub_analysis.get_code_location_shas())
    print("OpsSight Images: " + str(len(opssight_pod_images)))
    print("Hub Images: "+str(len(hub_code_location_images)))
    inter = opssight_pod_images.intersection(hub_code_location_images)
    print("Images From Hub that OpsSight Found: "+str(len(inter)))
    

    print("")
    print("== OpsSight vs Cluster ==")
    opsight_repositories = set(opssight_analysis.get_pods_repositories())
    kube_images = set([x.split(":")[0] for x in kube_client.get_images()])
    print("Images in Cluster: "+str(len(kube_images)))
    inter = kube_images.intersection(opsight_repositories)
    print("Images in Cluster that OpsSight Found: "+str(len(inter)))
    diff_images = kube_images.difference(opsight_repositories)
    print("Images Untracked in Cluster: "+str(len(diff_images)))
    

main()