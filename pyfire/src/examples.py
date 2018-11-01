import json
from scraper import MockDelegate, Scraper
import sys


def real_reader(conf):
    """
    Another example not to be used in PDCs!
    """
    from cluster_clients import PerceptorClient, KubeClientWrapper, HubClient

    perceptor_client = PerceptorClient(conf['Perceptor']['Host'])

    kube_client = KubeClientWrapper(conf["Skyfire"]["UseInClusterConfig"])

    hub_clients = {}
    for host in conf["Hub"]["Hosts"]:
        hub_clients[host] = HubClient(host, conf["Hub"]["User"], conf["Hub"]["PasswordEnvVar"])

    delegate = MockDelegate()
    s = Scraper(delegate, perceptor_client, kube_client, hub_clients, perceptor_pause=15, kube_pause=15, hub_pause=30)
    s.start()

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
