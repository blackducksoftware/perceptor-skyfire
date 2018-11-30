from kubernetes import client, config
import sys
import subprocess 
import logging 
import yaml 
import json 
import time 
import requests

client.rest.logger.setLevel("INFO")


def deployOperator(v1, namespace, reg_key, version):
    jenkins_logger = logging.getLogger("JenkinsScript2")
    jenkins_logger.setLevel("DEBUG")

    # Clean up if Operator already exists
    pods_list = v1.list_pod_for_all_namespaces().items 
    pod_names = [pod.metadata.name for pod in pods_list]
    has_protoform = True in ["synopsys-operator-" in pod_name for pod_name in pod_names]
    has_federator = True in ["federator-" in pod_name for pod_name in pod_names]
    has_prometheus = True in ["prometheus-" in pod_name for pod_name in pod_names]
    if has_protoform or has_federator or has_prometheus:
        jenkins_logger.debug("Cleaning up old operator")
        try:
            command = "./clean-operator/clean-operator.sh {}".format(namespace)
            r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
        except Exception as e:
            jenkins_logger.error(str(e))
            sys.exit(1)

    # Deploy the Operator
    print("Creating new operator")
    try:
        command = "./install-operator/install-operator.sh {} {} {}".format(namespace,reg_key,version)
        jenkins_logger.debug("Operator Command: %s", command)
        r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
    except Exception as e:
        jenkins_logger.error(str(e))
        sys.exit(1)

    # Wait for Pods to appear
    print("Waiting for pods to appear (not be running)") # TODO wait for running
    while True:
        pods_list = v1.list_pod_for_all_namespaces().items 
        pod_names = [pod.metadata.name for pod in pods_list]
        has_protoform = True in ["synopsys-operator-" in pod_name for pod_name in pod_names]
        has_federator = True in ["federator-" in pod_name for pod_name in pod_names]
        has_prometheus = True in ["prometheus-" in pod_name for pod_name in pod_names]
        if has_protoform and has_federator and has_prometheus:
            print("Found the operator pods")
            break


def main():
    jenkins_logger = logging.getLogger("Jenkins")
    jenkins_logger.setLevel("DEBUG")

    if len(sys.argv) != 5:
        print("Usage:\npython3 jenkins-script <hub-host> <cluster-ip:port> <username> <password>")
        sys.exit(1)

    # Parameters to be passed in
    namespace = "opssight-play"
    hub_host = sys.argv[1]
    cluster_ip = "https://" + sys.argv[2]
    username = sys.argv[3]
    password = sys.argv[4]
    jenkins_logger.info("namespace: %s", namespace)
    jenkins_logger.info("hub host: %s", hub_host)
    jenkins_logger.info("cluster ip: %s", cluster_ip)
    jenkins_logger.info("username: %s", username)
    jenkins_logger.info("password: %s", password)

    # Login to the Cluster
    logging.info("Logging In...")
    try:
        command = "oc login {} --username={} --password={} --insecure-skip-tls-verify=true".format(cluster_ip,username,password)
        r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
    except Exception as e:
        logging.error(str(e))
        sys.exit(1)

    # Create Kubernetes Client
    jenkins_logger.info("Creating Kube Client...")
    config.load_kube_config()
    v1 = client.CoreV1Api()

    # Deploy the Synopsys Operator
    operator_namespace = "mybd"
    operator_reg_key = "abcd" # cannot be numbers
    operator_version = "master"
    deployOperator(v1, operator_namespace, operator_reg_key, operator_version)

    # Create OpsSight from Yaml File
    jenkins_logger.info("Creating OpsSight...")
    time.sleep(10)
    try: 
        # Read yaml file and update fields
        with open('opssight-template.yaml') as opssight_file:
            opssight_yaml = yaml.load(opssight_file)
        opssight_yaml['metadata']['name'] = namespace
        opssight_yaml['spec']['namespace'] = namespace
        opssight_yaml['spec']['enableSkyfire'] = True
        with open('opssight-new.yaml','w') as opssight_file:
            yaml.dump(opssight_yaml, opssight_file, default_flow_style=False)

        # Delete namespace if it already Exists
        command = "oc get ns --no-headers"
        r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
        namespaces = r.stdout.split(b'\n')
        ns_names = [ns.split()[0].decode("utf-8") for ns in namespaces if ns != b'']
        jenkins_logger.info(ns_names)
        if namespace in ns_names:
            command = "oc delete ns {}".format(namespace)
            r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)

        # Delete OpsSight if it already Exists
        command = "oc get opssights --no-headers"
        r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
        opssights = r.stdout.split(b'\n')
        opssight_names = [opssight.split()[0].decode("utf-8") for opssight in opssights if opssight != b'']
        jenkins_logger.info(opssight_names)
        if namespace in opssight_names:
            command = "oc delete opssight {}".format(namespace)
            r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)

        # oc client to create OpsSight from yaml
        command = "oc create -f {}".format("opssight-new.yaml")
        r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
    except Exception as e:
        jenkins_logger.error("Exception when creating OpsSight: %s\n" % e)
        sys.exit(1)

    # Wait until all pods are running
    jenkins_logger.info("Waiting for OpsSight Pods...")
    try:
        good = False
        for i in range(15):
            command = "oc get pods -n {} --no-headers".format(namespace)
            r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
            pods = r.stdout.split(b'\n')
            pods_statuses = [pod.split()[2] == b'Running' for pod in pods if pod != b'']
            jenkins_logger.info([pod.split()[0].decode("utf-8")+" : "+pod.split()[2].decode("utf-8") for pod in pods if pod != b''])
            if pods_statuses != [] and False not in pods_statuses:
                good = True
                break
            time.sleep(5)
        if not good:
            jenkins_logger.error("Pods Did not Start")
            sys.exit(1)
    except Exception as e:
        jenkins_logger.error("Exception while waiting for OpsSight to start: %s\n" % e)
        sys.exit(1)


    # Edit OpsSight Config to have hub url
    jenkins_logger.info("Adding Hub to OpsSight Config...")
    try:
        # Read the current Config Map Body Object
        opssight_cm = v1.read_namespaced_config_map('opssight', namespace)
        opssight_data = opssight_cm.data
        opssight_data_json = json.loads(opssight_data['opssight.json'])
        if hub_host not in opssight_data_json['Hub']['Hosts']:
            opssight_data_json['Hub']['Hosts'].append(hub_host)
        opssight_data['opssight.json'] = json.dumps(opssight_data_json)
        # Update the Config Map with new Cofig Map Body Object
        opssight_cm.data = opssight_data
        v1.patch_namespaced_config_map('opssight', namespace, opssight_cm)
    except Exception as e:
        jenkins_logger.error("Exception when editing OpsSight Config: %s\n" % e)
        sys.exit(1)

    # Get the route for Skyfire
    jenkins_logger.info("Getting Skyfire Route...")
    skyfire_route = ""
    try: 
        # Expose the service if route doesn't exist
        command = "oc get routes -n {} --no-headers".format(namespace)
        r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
        routes = r.stdout.split(b'\n')
        route_names = [route.split()[0] for route in routes if route != b'']
        if b'skyfire' not in route_names:
            r = subprocess.run("oc expose service skyfire -n {}".format(namespace),shell=True,stdout=subprocess.PIPE)
            # Parse Routes for Skyfire URL
            command = "oc get routes -n {} --no-headers".format(namespace)
            r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
            routes = r.stdout.split(b'\n')
        routes = [route.split() for route in routes if route != b'']
        skyfire_route = [route[1] for route in routes if route[0] == b'skyfire'][0]
        jenkins_logger.info("Skyfire Route: %s",skyfire_route)
    except Exception as e:
        jenkins_logger.error("Exception when exposing Skyfire Route: %s\n" % e)
        sys.exit(1)

    # curl to start skyfire tests
    jenkins_logger.info("Starting Skyfire Tests...")
    jenkins_logger.info("Route: %s",skyfire_route)
    for i in range(10):
        try: 
            url = "http://{}/starttest".format(skyfire_route.decode("utf-8"))
            r = requests.post(url, data={'nothing' : 'nothing'}, verify=False)
            print(url)
            if 200 <= r.status_code <= 299:
                break 
            time.sleep(2)
        except Exception as e:
            jenkins_logger.error("Exception when starting skyfire tests: %s\n" % e)

    # curl to get skyfire results
    jenkins_logger.info("Getting Skyfire Results...")
    results = None
    try: 
        for i in range(100):
            url = "http://{}/testsuite".format(skyfire_route.decode("utf-8"))
            r = requests.get(url, verify=False)
            results = r.json()
            jenkins_logger.info(results)
            if 200 <= r.status_code <= 299:
                if results['state'] == 'FINISHED':
                    break
                else:
                    time.sleep(2)
                    continue
    except Exception as e:
        jenkins_logger.error("Exception when getting skyfire results: %s\n" % e)
        sys.exit(1)

    # print out the results
    return results['summary']




print(main())