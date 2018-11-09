import json
from scraper import Scraper
from cluster_clients import *
from skyfire import MockSkyfire
import sys


def real_reader(conf):
    """
    Another example not to be used in PDCs!
    """
    from cluster_clients import PerceptorClient, KubeClient, HubClient

    # Create a logger
    root_logger = logging.getLogger()

    # Create Clients
    perceptor_client = PerceptorClient(conf.perceptor_host,conf.perceptor_port)
    kube_client = KubeClient(conf["Skyfire"]["UseInClusterConfig"])
    hub_clients = {}
    for host in conf.hub_hosts:
        hub_clients[host] = HubClient(host, conf.hub_port, conf.hub_user, conf.hub_password_env_var, conf.hub_client_timeout_seconds)

    delegate = MockSkyfire()
    
    s = Scraper(root_logger.getChild("Scraper"), delegate, perceptor_client, kube_client, hub_clients, perceptor_pause=15, kube_pause=15, hub_pause=30)

    while True:
        item = delegate.q.get()
        print("got next:", item)
        if item is None:
            break
        delegate.q.task_done()


config_path = sys.argv[1]
with open(config_path) as f:
    config_json = json.load(f)

real_reader(config_json)
