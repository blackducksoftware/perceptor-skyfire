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
		log.Debugf("annotations before:\n%+v", pod.Annotations)
		log.Debugf("labels before:\n%+v\n", pod.Labels)
		updatedAnnotations := RemoveBDPodAnnotationKeys(len(pod.Status.ContainerStatuses), pod.Annotations)
		updatedLabels := RemoveBDPodLabelKeys(len(pod.Status.ContainerStatuses), pod.Labels)
		log.Debugf("annotations after:\n%+v", pod.Annotations)
		log.Debugf("labels after:\n%+v\n\n", pod.Labels)
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

func RemoveBDPodAnnotationKeys(containerCount int, annotations map[string]string) map[string]string {
	cleanedAnnotations := CopyMap(annotations)
	cleanedAnnotations = RemoveKeys(cleanedAnnotations, podAnnotationKeyStrings)
	for i := 0; i < containerCount; i++ {
		cleanedAnnotations = RemoveKeys(cleanedAnnotations, podImageAnnotationKeyStrings(i))
	}
	return cleanedAnnotations
}

func RemoveBDPodLabelKeys(containerCount int, labels map[string]string) map[string]string {
	cleanedLabels := CopyMap(labels)
	cleanedLabels = RemoveKeys(cleanedLabels, podLabelKeyStrings)
	for i := 0; i < containerCount; i++ {
		cleanedLabels = RemoveKeys(cleanedLabels, podImageLabelKeyStrings(i))
	}
	return cleanedLabels
}

// var podLabelKeys = []string{
// 	"pod.vulnerabilities",
// 	"pod.policy-violations",
// 	"pod.overall-status",
// }
//
// var podLabelImageSuffixes = []string{
// 	".vulnerabilities",
// 	".policy-violations",
// 	".overall-status",
// 	"",
// }
//
// func PodLabelImageKeys(containerCount int) []string {
// 	keys := []string{}
// 	for i := 0; i < containerCount; i++ {
// 		for _, suffix := range podLabelImageSuffixes {
// 			key := fmt.Sprintf("image%d%s", i, suffix)
// 			keys = append(keys, key)
// 		}
// 	}
// 	return keys
// }
//
// func PodLabelKeys(containerCount int) []string {
// 	return append(podLabelKeys, PodLabelImageKeys(containerCount)...)
// }
//
// var podAnnotationKeys = []string{
// 	"pod.vulnerabilities",
// 	"pod.policy-violations",
// 	"pod.overall-status",
// 	"pod.server-version",
// 	"pod.scanner-version",
// }
//
// var podAnnotationImageSuffixes = []string{
// 	".vulnerabilities",
// 	".policy-violations",
// 	".overall-status",
// 	".server-version",
// 	".scanner-version",
// 	".project-endpoint",
// 	"",
// }
//
// func PodAnnotationImageKeys(containerCount int) []string {
// 	keys := []string{}
// 	for i := 0; i < containerCount; i++ {
// 		for _, suffix := range podAnnotationImageSuffixes {
// 			key := fmt.Sprintf("image%d%s", i, suffix)
// 			keys = append(keys, key)
// 		}
// 	}
// 	return keys
// }

// func PodAnnotationKeys(containerCount int) []string {
// 	return append(podAnnotationKeys, PodAnnotationImageKeys(containerCount)...)
// }
//
// func HasAllBDAnnotationKeys(containerCount int, dict map[string]string) bool {
// 	return len(util.Difference(dict, util.MakeSet(PodAnnotationKeys(containerCount)))) == 0
// }
//
// func HasAnyBDAnnotationKeys(containerCount int, dict map[string]string) bool {
// 	return len(util.Difference(dict, util.MakeSet(PodAnnotationKeys(containerCount)))) > 0
// }

// func HasAllBDLabelKeys(containerCount int, dict map[string]string) bool {
// 	return len(util.Difference(dict, util.MakeSet(PodLabelKeys(containerCount)))) == 0
// }
//
// func HasAnyBDLabelKeys(containerCount int, dict map[string]string) bool {
// 	return len(util.Difference(dict, util.MakeSet(PodLabelKeys(containerCount)))) > 0
// }
//
// func GetBDAnnotationKeys(containerCount int, dict map[string]string) map[string]string {
// 	return util.Difference(dict, util.MakeSet(PodAnnotationKeys(containerCount)))
// }
//
// func GetBDLabelKeys(containerCount int, dict map[string]string) map[string]string {
// 	return util.Difference(dict, util.MakeSet(PodLabelKeys(containerCount)))
// }
//
// func removeBDAnnotationKeys(containerCount int, dict map[string]string) map[string]string {
// 	return util.Difference(dict, util.MakeSet(PodAnnotationKeys(containerCount)))
// }
//
// func removeBDLabelKeys(containerCount int, dict map[string]string) map[string]string {
// 	return util.Difference(dict, util.MakeSet(PodLabelKeys(containerCount)))
// }
