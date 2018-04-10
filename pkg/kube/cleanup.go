/*
Copyright (C) 2018 Black Duck Software, Inc.

Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements. See the NOTICE file
distributed with this work for additional information
regarding copyright ownership. The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. See the License for the
specific language governing permissions and limitations
under the License.
*/

package kube

import (
	"fmt"

	log "github.com/sirupsen/logrus"
	"k8s.io/api/core/v1"
	meta_v1 "k8s.io/apimachinery/pkg/apis/meta/v1"
)

func (client *KubeClient) CleanupAllPods() error {
	pods := client.clientset.CoreV1().Pods(v1.NamespaceAll)
	podList, err := pods.List(meta_v1.ListOptions{})
	if err != nil {
		log.Errorf("unable to list pods: %s", err.Error())
		return err
	}
	for _, pod := range podList.Items {
		log.Debugf("before:\n%+v\n%+v\n", pod.Annotations, pod.Labels)
		updatedAnnotations := removeBDKeys(len(pod.Status.ContainerStatuses), pod.Annotations)
		updatedLabels := removeBDKeys(len(pod.Status.ContainerStatuses), pod.Labels)
		log.Debugf("after:\n%+v\n%+v\n\n", pod.Annotations, pod.Labels)
		pod.SetAnnotations(updatedAnnotations)
		pod.SetLabels(updatedLabels)
		nsPods := client.clientset.CoreV1().Pods(pod.Namespace)
		_, err := nsPods.Update(&pod)
		if err != nil {
			log.Errorf("unable to update pod %+v: %s", pod, err.Error())
			return err
		}
	}
	return nil
}

var podKeys = []string{
	"pod.vulnerabilities",
	"pod.policy-violations",
	"pod.overall-status",
	"pod.server-version",
	"pod.scanner-version",
}

var imageSuffixes = []string{
	".vulnerabilities",
	".policy-violations",
	".overall-status",
	".server-version",
	".scanner-version",
	".project-endpoint",
	"",
}

func removeBDKeys(containerCount int, dict map[string]string) map[string]string {
	copy := map[string]string{}
	for key, val := range dict {
		copy[key] = val
	}
	for i := 0; i < containerCount; i++ {
		for _, suffix := range imageSuffixes {
			key := fmt.Sprintf("image%d%s", i, suffix)
			delete(copy, key)
		}
		for _, key := range podKeys {
			delete(copy, key)
		}
	}
	return copy
}
