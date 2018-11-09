import sys
from cluster_clients import *

def main():
    if len(sys.argv) != 2:
        print("USAGE: ")
        print("python3 Example_PerceptorDump.py <perceptor_host>")
        sys.exit()
    perceptor_host = sys.argv[1]

    # Create a Perceptor Client
    perceptor_client = PerceptorClient(perceptor_host, port=80)

    # Get a Perceptor Scrape from the Client
    perceptor_scrape, err = perceptor_client.get_scrape()
    if err is not None:
        print(str(err))

    # Print the Dump
    print(json.dumps(  perceptor_scrape.dump  , indent=2))


if __name__ == "__main__":
    main()