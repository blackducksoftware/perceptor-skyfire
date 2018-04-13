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

package report

import (
	"fmt"
	"strings"

	"github.com/blackducksoftware/perceptor-skyfire/pkg/dump"
	"github.com/blackducksoftware/perceptor-skyfire/pkg/kube"
)

type KubePerceptorReport struct {
	JustKubePods        []string
	JustPerceptorPods   []string
	JustKubeImages      []string
	JustPerceptorImages []string

	// TODO:
	// In kube/openshift but not in perceptor scan results:
	// - finished pods (with annotations/labels)
	// - finished images (with annotations/labels)
	FinishedJustKubePods []string

	// In perceptor scan results but not in kube/openshift:
	// - scanned pods
	// - scanned images
	FinishedJustPerceptorPods []string

	PartiallyAnnotatedKubePods []string
	PartiallyLabeledKubePods   []string

	ConflictingAnnotationsPods []string
	ConflictingLabelsPods      []string

	UnanalyzeablePods []string
}

func NewKubePerceptorReport(dump *dump.Dump) *KubePerceptorReport {
	finishedJustKubePods, partiallyAnnotatedKubePods, partiallyLabeledKubePods, conflictingAnnotationsPods, conflictingLabelsPods, unanalyzeablePods := KubeNotPerceptorFinishedPods(dump)
	return &KubePerceptorReport{
		JustKubePods:               KubeNotPerceptorPods(dump),
		JustPerceptorPods:          PerceptorNotKubePods(dump),
		JustKubeImages:             KubeNotPerceptorImages(dump),
		JustPerceptorImages:        PerceptorNotKubeImages(dump),
		FinishedJustKubePods:       finishedJustKubePods,
		FinishedJustPerceptorPods:  PerceptorNotKubeFinishedPods(dump),
		PartiallyAnnotatedKubePods: partiallyAnnotatedKubePods,
		PartiallyLabeledKubePods:   partiallyLabeledKubePods,
		ConflictingAnnotationsPods: conflictingAnnotationsPods,
		ConflictingLabelsPods:      conflictingLabelsPods,
		UnanalyzeablePods:          unanalyzeablePods,
	}
}

func (kr *KubePerceptorReport) HumanReadableString() string {
	return fmt.Sprintf(`
Kubernetes<->Perceptor:
 - we found %d pod(s) in Kubernetes that were not in Perceptor
 - we found %d pod(s) in Perceptor that were not in Kubernetes
 - we found %d image(s) in Kubernetes that were not in Perceptor
 - we found %d image(s) in Perceptor that were not in Kubernetes
 - we found %d pod(s) whose kubernetes annotations did not match their scan results
 - we found %d pod(s) whose kubernetes labels did not match their scan results
 - we found %d pod(s) with kubernetes annotations but no scan results
 - we found %d pod(s) with scan results but not kubernetes annotations
 - we found %d pod(s) in kubernetes that are partially annotated
 - we found %d pod(s) in kubernetes that are partially labeled
	 `,
		len(kr.JustKubePods),
		len(kr.JustPerceptorPods),
		len(kr.JustKubeImages),
		len(kr.JustPerceptorImages),
		len(kr.ConflictingAnnotationsPods),
		len(kr.ConflictingLabelsPods),
		len(kr.FinishedJustKubePods),
		len(kr.FinishedJustPerceptorPods),
		len(kr.PartiallyAnnotatedKubePods),
		len(kr.PartiallyLabeledKubePods))
}

func KubeNotPerceptorPods(dump *dump.Dump) []string {
	pods := []string{}
	for podName := range dump.Kube.PodsByName {
		_, ok := dump.Perceptor.Model.Pods[podName]
		if !ok {
			pods = append(pods, podName)
		}
	}
	return pods
}

func PerceptorNotKubePods(dump *dump.Dump) []string {
	pods := []string{}
	for podName := range dump.Perceptor.Model.Pods {
		_, ok := dump.Kube.PodsByName[podName]
		if !ok {
			pods = append(pods, podName)
		}
	}
	return pods
}

func KubeNotPerceptorImages(dump *dump.Dump) []string {
	images := []string{}
	for sha := range dump.Kube.ImagesBySha {
		_, ok := dump.Perceptor.Model.Images[sha]
		if !ok {
			images = append(images, sha)
		}
	}
	return images
}

func PerceptorNotKubeImages(dump *dump.Dump) []string {
	images := []string{}
	for sha := range dump.Perceptor.Model.Images {
		_, ok := dump.Kube.ImagesBySha[sha]
		if !ok {
			images = append(images, sha)
		}
	}
	return images
}

func KubeNotPerceptorFinishedPods(dump *dump.Dump) (finishedKubePods []string, partiallyAnnotatedKubePods []string, partiallyLabeledKubePods []string, incorrectAnnotationsPods []string, incorrectLabelsPods []string, unanalyzeablePods []string) {
	finishedKubePods = []string{}
	partiallyAnnotatedKubePods = []string{}
	partiallyLabeledKubePods = []string{}
	incorrectAnnotationsPods = []string{}
	incorrectLabelsPods = []string{}
	unanalyzeablePods = []string{}

	for podName, pod := range dump.Kube.PodsByName {
		if pod.HasAnyBDAnnotations() && !pod.HasAllBDAnnotations() {
			partiallyAnnotatedKubePods = append(partiallyAnnotatedKubePods, podName)
		}

		if pod.HasAnyBDLabels() && !pod.HasAllBDLabels() {
			partiallyLabeledKubePods = append(partiallyLabeledKubePods, podName)
		}

		imageShas, err := PodShas(pod)
		if err != nil {
			unanalyzeablePods = append(unanalyzeablePods, podName)
			continue
		}

		if pod.HasAllBDAnnotations() && pod.HasAllBDLabels() {
			_, ok := dump.Perceptor.PodsByName[podName]
			if !ok {
				finishedKubePods = append(finishedKubePods, podName)
			}
		}

		expectedPodAnnotations, err := ExpectedPodAnnotations(podName, imageShas, dump)
		if err == nil {
			missingKeys := []string{} // TODO do we actually need this?
			keysOfWrongValues := []string{}
			for key, expectedVal := range expectedPodAnnotations {
				actualVal, ok := pod.Annotations[key]
				if !ok {
					missingKeys = append(missingKeys, key)
				} else if expectedVal != actualVal {
					keysOfWrongValues = append(keysOfWrongValues, key)
				}
			}

			if len(keysOfWrongValues) > 0 {
				incorrectAnnotationsPods = append(incorrectAnnotationsPods, podName)
			}
		} else {
			unanalyzeablePods = append(unanalyzeablePods, podName)
		}

		expectedPodLabels, err := ExpectedPodLabels(podName, imageShas, dump)
		if err == nil {
			missingKeys := []string{} // TODO do we actually need this?
			keysOfWrongValues := []string{}
			for key, expectedVal := range expectedPodLabels {
				actualVal, ok := pod.Labels[key]
				if !ok {
					missingKeys = append(missingKeys, key)
				} else if expectedVal != actualVal {
					keysOfWrongValues = append(keysOfWrongValues, key)
				}
			}

			if len(keysOfWrongValues) > 0 {
				incorrectLabelsPods = append(incorrectLabelsPods, podName)
			}
		} else {
			unanalyzeablePods = append(unanalyzeablePods, podName)
		}
	}
	return
}

func PerceptorNotKubeFinishedPods(dump *dump.Dump) []string {
	pods := []string{}
	for podName, _ := range dump.Perceptor.PodsByName {
		kubePod, ok := dump.Kube.PodsByName[podName]
		if !ok {
			// this should be handled elsewhere, right?
			continue
		}
		if !(kubePod.HasAllBDAnnotations() && kubePod.HasAllBDLabels()) {
			pods = append(pods, podName)
		}
	}
	return pods
}

func PodShas(pod *kube.Pod) ([]string, error) {
	imageShas := []string{}
	for _, cont := range pod.Containers {
		_, sha, err := cont.Image.ParseImageID()
		if err != nil {
			return []string{}, err
		}
		imageShas = append(imageShas, sha)
	}
	return imageShas, nil
}

func ExpectedPodAnnotations(podName string, imageShas []string, dump *dump.Dump) (map[string]string, error) {
	perceptor := dump.Perceptor
	annotations := map[string]string{}
	pod, ok := perceptor.PodsByName[podName]
	if !ok {
		// didn't find this pod in the scan results?  then there shouldn't be any BD annotations
		return annotations, nil
	}

	for i, sha := range imageShas {
		image, ok := perceptor.ImagesBySha[sha]
		if !ok {
			return nil, fmt.Errorf("unable to find image %s", sha)
		}
		annotations[kube.PodImageAnnotationKeyOverallStatus.String(i)] = image.OverallStatus
		annotations[kube.PodImageAnnotationKeyVulnerabilities.String(i)] = fmt.Sprintf("%d", image.Vulnerabilities)
		annotations[kube.PodImageAnnotationKeyPolicyViolations.String(i)] = fmt.Sprintf("%d", image.PolicyViolations)
		annotations[kube.PodImageAnnotationKeyProjectEndpoint.String(i)] = image.ComponentsURL
		annotations[kube.PodImageAnnotationKeyScannerVersion.String(i)] = dump.Hub.Version
		annotations[kube.PodImageAnnotationKeyServerVersion.String(i)] = dump.Hub.Version
		name, _, _ := dump.Kube.ImagesBySha[sha].ParseImageID() // just ignore errors and missing values!  maybe not a good idea TODO
		name = strings.Replace(name, "/", ".", -1)
		name = strings.Replace(name, ":", ".", -1)
		annotations[kube.PodImageAnnotationKeyImage.String(i)] = name
	}

	annotations[kube.PodAnnotationKeyOverallStatus.String()] = pod.OverallStatus
	annotations[kube.PodAnnotationKeyVulnerabilities.String()] = fmt.Sprintf("%d", pod.Vulnerabilities)
	annotations[kube.PodAnnotationKeyPolicyViolations.String()] = fmt.Sprintf("%d", pod.PolicyViolations)
	annotations[kube.PodAnnotationKeyScannerVersion.String()] = dump.Hub.Version
	annotations[kube.PodAnnotationKeyServerVersion.String()] = dump.Hub.Version

	return annotations, nil
}

func ExpectedPodLabels(podName string, imageShas []string, dump *dump.Dump) (map[string]string, error) {
	perceptor := dump.Perceptor
	labels := map[string]string{}
	pod, ok := perceptor.PodsByName[podName]
	if !ok {
		return labels, nil
	}

	for i, sha := range imageShas {
		image, ok := perceptor.ImagesBySha[sha]
		if !ok {
			return nil, fmt.Errorf("unable to find image %s", sha)
		}
		labels[kube.PodImageLabelKeyOverallStatus.String(i)] = image.OverallStatus
		labels[kube.PodImageLabelKeyVulnerabilities.String(i)] = fmt.Sprintf("%d", image.Vulnerabilities)
		labels[kube.PodImageLabelKeyPolicyViolations.String(i)] = fmt.Sprintf("%d", image.PolicyViolations)
		name, _, _ := dump.Kube.ImagesBySha[sha].ParseImageID() // just ignore errors and missing values!  maybe not a good idea TODO
		name = strings.Replace(name, "/", ".", -1)
		name = strings.Replace(name, ":", ".", -1)
		labels[kube.PodImageLabelKeyImage.String(i)] = name
	}

	labels[kube.PodLabelKeyOverallStatus.String()] = pod.OverallStatus
	labels[kube.PodLabelKeyVulnerabilities.String()] = fmt.Sprintf("%d", pod.Vulnerabilities)
	labels[kube.PodLabelKeyPolicyViolations.String()] = fmt.Sprintf("%d", pod.PolicyViolations)

	return labels, nil
}
