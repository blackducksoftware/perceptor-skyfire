import json
import sys
from webserver import start_http_server
from scraper import Scraper
from skyfire import Skyfire
import metrics


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

    prometheus_port = 3201
    print("starting prometheus server on port", prometheus_port)
    metrics.start_http_server(prometheus_port)

    metrics.record_error("oops")
    metrics.record_problem('nope', 4)

    skyfire_port = int(config['Skyfire']['Port'])
    print("starting http server on port", skyfire_port)
    start_http_server(skyfire_port, skyfire)


main()


#    kube_client = KubeClientWrapper(config.get('use_in_cluster_config'))
#    i = 0
#    while True:
#        print("hi! {}".format(i))
#        i += 1
#        print(kube_client.get_pods())
#        time.sleep(1)
