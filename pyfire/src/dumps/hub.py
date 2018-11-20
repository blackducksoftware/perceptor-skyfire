import sys
import json
from ..cluster_clients import HubClient

def main():
    if len(sys.argv) != 4:
        print("USAGE: ")
        print("python3 Example_HubDump.py <hub_username> <hub_password> <hub_host>")
        sys.exit()
    hub_username = sys.argv[1]
    hub_password = sys.argv[2]
    hub_host = sys.argv[3]
    port = 1234
    timeout = 0

    # Create a Hub Client
    hub_client = HubClient(hub_host, port, hub_username, hub_password, timeout)

    # Get a Hub Scrape from the Client
    hub_scrape = hub_client.get_scrape()

    # Print the Dump
    print(json.dumps(hub_scrape.dump, indent=2))


if __name__ == "__main__":
    main()