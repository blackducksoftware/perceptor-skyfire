import json
import sys
from webserver import start_http_server
from scraper import Scraper
from skyfire import Skyfire
import metrics
import logging
from cluster_clients import *
import os
import urllib3
import kubernetes.client


# TODO is this the right way to turn off annoying logging?
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
kubernetes.client.rest.logger.setLevel("INFO")


class Config:
    def __init__(self, config_dict):
        skyfire = config_dict['Skyfire']
        perceptor = config_dict['Perceptor']
        hub = config_dict['Hub']

        self.log_level = config_dict['LogLevel']
        self.skyfire_port = skyfire['Port']
        self.prometheus_port = skyfire['PrometheusPort']
        self.use_in_cluster_config = skyfire['UseInClusterConfig']
        self.use_mock_mode = skyfire.get("UseMockMode", False)

        self.hub_client_timeout_seconds = skyfire['HubClientTimeoutSeconds']
        self.hub_dump_pause_seconds = skyfire['HubDumpPauseSeconds']
        self.kub_dump_interval_seconds = skyfire['KubeDumpIntervalSeconds']
        self.perceptor_dump_interval_seconds = skyfire['PerceptorDumpIntervalSeconds']
        
        self.perceptor_host = perceptor['Host']
        self.perceptor_port = perceptor['Port']
        self.hub_hosts = hub['Hosts']
        self.hub_user = hub['User']
        self.hub_port = hub['Port']
        self.hub_password_env_var = hub['PasswordEnvVar']
        
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
    k_client = KubeClient(config.use_in_cluster_config)
    h_clients = {}
    hub_password = os.getenv(config.hub_password_env_var)
    for host in config.hub_hosts:
        h_clients[host] = HubClient(host, config.hub_port, config.hub_user, hub_password, config.hub_client_timeout_seconds)
    return p_client, k_client, h_clients

def main():
    # Check parameters and load config file
    if len(sys.argv) != 2:
        message = "\n   Usage: python3 main.py <congig_file>\n   BD_HUB_PASSWORD must be set in environment"
        logging.error(message)
        sys.exit()

    try:
        with open(sys.argv[1]) as f:
            config_dict = json.load(f)
        config = Config(config_dict)
    except Exception as err:
        logging.error("Bad Config File: "+str(err))
        sys.exit()
    
    logging.getLogger().setLevel(config.log_level.upper())

    logging.info("Config: " + json.dumps(config_dict, indent=2))

    # Instantiate Skyfire Objects
    logging.info("Starting Skyfire!!!")
    skyfire = Skyfire()

    if config.use_mock_mode:
        logging.info("Skyfire is using mock Clients")
        perceptor_client, kube_client, hub_clients = instantiate_mock_clients()
    else:
        logging.info("Skyfire is using live Clients")
        perceptor_client, kube_client, hub_clients = instantiate_clients(config)

    scraper = Scraper(skyfire, perceptor_client, kube_client, hub_clients)
    logging.info("Instantiated Scraper: %s", str(scraper))

    metrics.start_http_server(config.prometheus_port)
    logging.info("Started Prometheus server on port %d", config.prometheus_port)

    start_http_server(config.skyfire_port, skyfire)
    logging.info("Started Skyfire http server on port %d", config.skyfire_port)


main()

