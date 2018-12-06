from kubernetes import client, config
import sys
import subprocess 
import yaml 
import json 
import time 
import requests

client.rest.logger.setLevel("INFO")

def clusterLogIn(cluster_ip, username, password):
    try:
        command = "oc login {} --username={} --password={} --insecure-skip-tls-verify=true".format(cluster_ip,username,password)
        r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
    except Exception as e:
        print(str(e))
        sys.exit(1)

def deployOperator(namespace, reg_key, version):
    # Download Operator
    command = "wget https://github.com/blackducksoftware/synopsys-operator/archive/2018.12.0.tar.gz"
    print("Command: {}".format(command))
    r = subprocess.call(command,shell=True,stdout=subprocess.PIPE)
    # Uncompress and un-tar the operator file
    command = "gunzip 2018.12.0.tar.gz"
    print("Command: {}".format(command))
    r = subprocess.call(command,shell=True,stdout=subprocess.PIPE)
    command = "tar -xvf 2018.12.0.tar"
    print("Command: {}".format(command))
    r = subprocess.call(command,shell=True,stdout=subprocess.PIPE)
    # Clean up an old operator
    command = "./cleanup.sh synopsys-operator"
    print("Command: {}".format(command))
    subprocess.call(command, cwd="synopsys-operator-2018.12.0/install/openshift", shell=True,stdout=subprocess.PIPE)
    waitForNamespaceDelete("synopsys-operator")
    # Install the operator
    command = "./install.sh --blackduck-registration-key tmpkey"
    print("Command: {}".format(command))
    p = subprocess.Popen(command, cwd="synopsys-operator-2018.12.0/install/openshift", shell=True,stdout=subprocess.PIPE,stdin=subprocess.PIPE)
    p.communicate(input=b'\n\n')
    waitForPodsRunning("synopsys-operator")
    # Clean up Operator Tar File
    command = "rm 2018.12.0.tar"
    print("Command: {}".format(command))
    r = subprocess.call(command,shell=True,stdout=subprocess.PIPE)
    # Clean up Operator Folder
    command = "rm -rf synopsys-operator-2018.12.0"
    print("Command: {}".format(command))
    r = subprocess.call(command,shell=True,stdout=subprocess.PIPE)

def deployOpssight(namespace):
    # Delete opssight instance if already exists
    if checkResourceExists("opssights", namespace):
        command = "oc delete opssights opssight-test"
        print("Command: {}".format(command))
        r = subprocess.call(command,shell=True,stdout=subprocess.PIPE)
    # Delete opssight namespace if already exists
    if checkResourceExists("ns", namespace):
        command = "oc delete ns opssight-test"
        print("Command: {}".format(command))
        r = subprocess.call(command,shell=True,stdout=subprocess.PIPE)
        waitForNamespaceDelete("opssight-test")
    # Get Opssight yaml
    command = "wget https://raw.githubusercontent.com/blackducksoftware/opssight-connector/release-2.2.x/examples/opssight.json"
    print("Command: {}".format(command))
    r = subprocess.call(command,shell=True,stdout=subprocess.PIPE)
    time.sleep(2)
    # Create Opssight from yaml
    command = "oc create -f opssight.json"
    print("Command: {}".format(command))
    r = subprocess.call(command,shell=True,stdout=subprocess.PIPE)
    waitForPodsRunning("opssight-test")
    # Clean up Opssight yaml
    command = "rm opssight.json"
    print("Command: {}".format(command))
    r = subprocess.call(command,shell=True,stdout=subprocess.PIPE)

def addHubToConfig(v1, namespace, hub_host):
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
        print("Exception when editing OpsSight Config: %s\n" % e)
        sys.exit(1)

def setSkyfireReplica(v1, namespace, count):
    try:
        # Read the current Config Map Body Object
        skyfire_rc = v1.read_namespaced_replication_controller('skyfire', namespace)
        skyfire_rc_spec = skyfire_rc.spec
        skyfire_rc_spec.replicas = count
        skyfire_rc.spec = skyfire_rc_spec
        # Update the Replication Controller
        v1.patch_namespaced_replication_controller('skyfire', namespace, skyfire_rc)
    except Exception as e:
        print("Exception when editing Skyfire Replication Controller: %s\n" % e)
        sys.exit(1)
    waitForPodsRunning(namespace)

def getSkyfireRoute(namespace):
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
        print("Skyfire Route: %s",skyfire_route)
    except Exception as e:
        print("Exception when exposing Skyfire Route: %s\n" % e)
        sys.exit(1)
    return skyfire_route

def checkResourceExists(resource,resource_name):
    command = "oc get {} --no-headers".format(resource)
    r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
    resources = r.stdout.split(b'\n')
    resource_names = [resource.split()[0].decode("utf-8") for resource in resources if resource != b'']
    print("Resource Names: "+str(resource_names))
    print("Found Resource: "+str(resource_name in resource_names))
    return resource_name in resource_names

def waitForNamespaceDelete(namespace):
    command = "oc get ns --no-headers"
    r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
    namespaces = r.stdout.split(b'\n')
    ns_names = [ns.split()[0].decode("utf-8") for ns in namespaces if ns != b'']
    print(ns_names)
    while namespace in ns_names:
        r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
        namespaces = r.stdout.split(b'\n')
        ns_names = [ns.split()[0].decode("utf-8") for ns in namespaces if ns != b'']
        print(ns_names)
        time.sleep(4)

def waitForPodsRunning(namespace):
    while True:
        command = "oc get pods -n {} --no-headers".format(namespace)
        print(command)
        r = subprocess.run(command,shell=True,stdout=subprocess.PIPE)
        pods = r.stdout.split(b'\n')
        pods_statuses = [pod.split()[2] == b'Running' for pod in pods if pod != b'']
        print([pod.split()[0].decode("utf-8")+" : "+pod.split()[2].decode("utf-8") for pod in pods if pod != b''])
        if pods_statuses != [] and False not in pods_statuses:
            break
        time.sleep(4)

def main():
    if len(sys.argv) != 5:
        print("Usage:\npython3 jenkins-script <hub-host> <cluster-ip:port> <username> <password>")
        sys.exit(1)

    # Parameters to be passed in
    namespace = "opssight-test"
    hub_host = sys.argv[1]
    cluster_ip = "https://" + sys.argv[2]
    username = sys.argv[3]
    password = sys.argv[4]
    print("namespace: %s", namespace)
    print("hub host: %s", hub_host)
    print("cluster ip: %s", cluster_ip)
    print("username: %s", username)
    print("password: %s", password)

    # Login to the Cluster
    #print("Logging In...")
    #clusterLogIn(cluster_ip, username, password)

    # Create Kubernetes Client
    print("Creating Kube Client...")
    config.load_kube_config()
    v1 = client.CoreV1Api()

    # Deploy the Synopsys Operator
    #operator_namespace = "synopsys-operator"
    #operator_reg_key = "abcd" # cannot be numbers
    #operator_version = "master"
    #deployOperator(operator_namespace, operator_reg_key, operator_version)

    # Create OpsSight from Yaml File
    print("Creating OpsSight...")
    opssight_namespace = "opssight-test"
    deployOpssight(opssight_namespace)

    # Edit OpsSight Config to have hub url
    print("Adding Hub to OpsSight Config...")
    addHubToConfig(v1, opssight_namespace, hub_host)

    # Create one instance of skyfire
    print("Creating instance of skyfire")
    setSkyfireReplica(v1, opssight_namespace, 1)

    # Get the route for Skyfire
    print("Getting Skyfire Route...")
    skyfire_route = getSkyfireRoute(namespace)

    # curl to start skyfire tests
    print("Starting Skyfire Tests...")
    print("Route: %s",skyfire_route)
    for i in range(10):
        try: 
            url = "http://{}/starttest".format(skyfire_route.decode("utf-8"))
            r = requests.post(url, data={'nothing' : 'nothing'}, verify=False)
            print(url)
            if 200 <= r.status_code <= 299:
                break 
            time.sleep(2)
        except Exception as e:
            print("Exception when starting skyfire tests: %s\n" % e)

    # curl to get skyfire results
    print("Getting Skyfire Results...")
    results = None
    try: 
        for i in range(100):
            url = "http://{}/testsuite".format(skyfire_route.decode("utf-8"))
            r = requests.get(url, verify=False)
            results = r.json()
            print(results)
            if 200 <= r.status_code <= 299:
                if results['state'] == 'FINISHED':
                    break
                else:
                    time.sleep(2)
                    continue
    except Exception as e:
        print("Exception when getting skyfire results: %s\n" % e)
        sys.exit(1)

    # Remove Skyfire Instance
    print("Removing Skyfire Instance...")
    setSkyfireReplica(v1, opssight_namespace, 0)

    # print out the results
    return results['summary']




print(main())