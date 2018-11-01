import json
import sys
from webserver import start_http_server
from scraper import Scraper
from skyfire import Skyfire
import metrics
import logging
from cluster_clients import PerceptorClient, KubeClientWrapper, HubClient
import os


class Config:
    def __init__(self, blob):
        skyfire = blob['Skyfire']
        perceptor = blob['Perceptor']
        hub = blob['Hub']
        self.port = skyfire['Port']
        self.prometheus_port = skyfire['PrometheusPort']
        self.use_in_cluster_config = skyfire['UseInClusterConfig']
        self.hub_client_timeout_seconds = skyfire['HubClientTimeoutSeconds']
        self.kub_dump_interval_seconds = skyfire['KubeDumpIntervalSeconds']
        self.perceptor_dump_interval_seconds = skyfire['PerceptorDumpIntervalSeconds']
        self.hub_dump_pause_seconds = skyfire['HubDumpPauseSeconds']
        self.perceptor_host = perceptor['Host']
        self.perceptor_port = perceptor['Port']
        self.hub_hosts = hub['Hosts']
        self.hub_user = hub['User']
        self.hub_port = hub['Port']
        self.hub_password_env_var = hub['PasswordEnvVar']
        self.log_level = blob['LogLevel']
        self.use_mock_mode = skyfire.get("UseMockMode", False)

def instantiate_mock_clients():
    from scraper import MockScraper
    perceptor_client = MockScraper("perceptor")
    kube_client = MockScraper("kube")
    hub_clients = {
        'abc': MockScraper("hubabc"),
        'def': MockScraper("hubdef")
    }
    return perceptor_client, kube_client, hub_clients

def instantiate_clients(config):
    prc = PerceptorClient(config.perceptor_host, config.perceptor_port)
    kube = KubeClientWrapper(config.use_in_cluster_config)
    hubs = {}
    hub_password = os.getenv(config.hub_password_env_var)
    for host in config.hub_hosts:
        hubs[host] = HubClient(host, config.hub_port, config.hub_user, hub_password, config.hub_client_timeout_seconds)
    return prc, kube, hubs

def main():
    if len(sys.argv) < 2:
        message = "Missing path to config file"
        logging.error(message)
        sys.exit(message)

    with open(sys.argv[1]) as f:
        config_blob = json.load(f)

    print("config: " + json.dumps(config_blob, indent=2))

    config = Config(config_blob)

    logging.getLogger().setLevel(config.log_level.upper())

    skyfire = Skyfire()

    if config.use_mock_mode:
        perceptor_client, kube_client, hub_clients = instantiate_mock_clients()
    else:
        perceptor_client, kube_client, hub_clients = instantiate_clients(config)
    scraper = Scraper(skyfire, perceptor_client, kube_client, hub_clients)

    logging.info("instantiated scraper: %s", str(scraper))

    prometheus_port = config.prometheus_port
    print("starting prometheus server on port", prometheus_port)
    metrics.start_http_server(prometheus_port)

    metrics.record_error("oops")
    metrics.record_problem('nope', 4)

    skyfire_port = config.port
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
