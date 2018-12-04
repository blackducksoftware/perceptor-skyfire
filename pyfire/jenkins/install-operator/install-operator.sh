#!/bin/bash

unset DYLD_INSERT_LIBRARIES

echo "args = Namespace, Reg_key, Version of Operator"

NS=$1
REG_KEY=$2
VERSION=$3

echo "creating new project"
oc new-project $NS

echo "Creating secret.yaml"
oc create -f install-operator/secret.yaml -n $NS

DOCKER_REGISTRY=gcr.io
DOCKER_REPO=saas-hub-stg/blackducksoftware

echo "Creating synopsys-operator.yaml"
cat install-operator/synopsys-operator.yaml | \
sed 's/${REGISTRATION_KEY}/'$REG_KEY'/g' | \
sed 's/${NAMESPACE}/'$NS'/g' | \
sed 's/${TAG}/'${VERSION}'/g' | \
sed 's/${DOCKER_REGISTRY}/'$DOCKER_REGISTRY'/g' | \
sed 's/${DOCKER_REPO}/'$(echo $DOCKER_REPO | sed -e 's/\\/\\\\/g; s/\//\\\//g; s/&/\\\&/g')'/g' | \
oc create --namespace=$NS -f -

echo "Exposing the routes"
oc expose rc synopsys-operator --port=80 --target-port=3000 --name=synopsys-operator-tcp --type=LoadBalancer --namespace=${NS}

echo "Getting the svc"
oc get svc -n $NS
