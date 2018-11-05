import json
import sys
from webserver import start_http_server
from scraper import Scraper
from skyfire import Skyfire
import metrics
import logging
from cluster_clients import PerceptorClient, KubeClientWrapper, HubClient, MockClient 
import os
import urllib3
import kubernetes.client


# TODO is this the right way to turn off annoying logging?
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
kubernetes.client.rest.logger.setLevel("DEBUG")


class Config:
    def __init__(self, config_dict):
        self.log_level = config_dict['LogLevel']
        skyfire = config_dict['Skyfire']
        perceptor = config_dict['Perceptor']
        hub = config_dict['Hub']
        self.skyfire_port = skyfire['Port']
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
        self.use_mock_mode = skyfire.get("UseMockMode", False)

def instantiate_mock_clients():
    perceptor_client = MockClient("perceptor")
    kube_client = MockClient("kube")
    hub_clients = {
        'hub_name_1': MockClient("hub1"),
        'hub_name_2': MockClient("hub2")
    }
    return perceptor_client, kube_client, hub_clients

def instantiate_clients(config):
    p_client = PerceptorClient(config.perceptor_host, config.perceptor_port)
    k_client = KubeClientWrapper(config.use_in_cluster_config)
    h_clients = {}
    hub_password = os.getenv(config.hub_password_env_var)
    for host in config.hub_hosts:
        h_clients[host] = HubClient(host, config.hub_port, config.hub_user, hub_password, config.hub_client_timeout_seconds)
    return p_client, k_client, h_clients

def main():
    # Check parameters and load config file
    if len(sys.argv) < 2:
        message = "Missing path to config file"
        logging.error(message)
        sys.exit(message)
    with open(sys.argv[1]) as f:
        config_dict = json.load(f)
    print("config: " + json.dumps(config_dict, indent=2))
    config = Config(config_dict)
    logging.getLogger().setLevel(config.log_level.upper())

    # Instantiate Skyfire Objects
    skyfire = Skyfire()

    if config.use_mock_mode:
        perceptor_client, kube_client, hub_clients = instantiate_mock_clients()
    else:
        perceptor_client, kube_client, hub_clients = instantiate_clients(config)

    scraper = Scraper(skyfire, perceptor_client, kube_client, hub_clients)
    logging.info("instantiated scraper: %s", str(scraper))

    # Instantiate Skyfire Metrics Recording
    print("starting prometheus server on port", config.prometheus_port)
    metrics.start_http_server(config.prometheus_port)

    metrics.record_error("oops")
    metrics.record_problem('nope', 4)

    # Instantiate Skyfire server to access data
    print("starting http server on port", config.skyfire_port)
    start_http_server(config.skyfire_port, skyfire)


main()

