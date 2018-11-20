import json
import sys
from ..cluster_clients import KubeClient


def main():
    if len(sys.argv) != 1:
        print("USAGE: ")
        print("python3 Example_KubeDump.py")
        sys.exit()

    # Create a Kube Client
    kube_client = KubeClient(in_cluster=False)

    # Get a Kube Scrape from the Client
    kube_scrape, err = kube_client.get_scrape()

    # Print the Dump
    print(json.dumps(kube_scrape.dump, indent=2))


if __name__ == "__main__":
    main()