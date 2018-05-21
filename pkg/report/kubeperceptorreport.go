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

	"github.com/blackducksoftware/perceptor-skyfire/pkg/kube"
	"github.com/blackducksoftware/perceptor-skyfire/pkg/perceptor"
	log "github.com/sirupsen/logrus"
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

	ConflictingAnnotationsPods []string
	ConflictingLabelsPods      []string

	UnanalyzeablePods []string
}

func NewKubePerceptorReport(kubeDump *kube.Dump, perceptorDump *perceptor.Dump, hubVersion string) *KubePerceptorReport {
	if kubeDump == nil || perceptorDump == nil {
		return nil
	}
	finishedJustKubePods, conflictingAnnotationsPods, conflictingLabelsPods, unanalyzeablePods := KubeNotPerceptorFinishedPods(kubeDump, perceptorDump, hubVersion)
	return &KubePerceptorReport{
		JustKubePods:               KubeNotPerceptorPods(kubeDump, perceptorDump),
		JustPerceptorPods:          PerceptorNotKubePods(kubeDump, perceptorDump),
		JustKubeImages:             KubeNotPerceptorImages(kubeDump, perceptorDump),
		JustPerceptorImages:        PerceptorNotKubeImages(kubeDump, perceptorDump),
		FinishedJustKubePods:       finishedJustKubePods,
		FinishedJustPerceptorPods:  PerceptorNotKubeFinishedPods(kubeDump, perceptorDump),
		ConflictingAnnotationsPods: conflictingAnnotationsPods,
		ConflictingLabelsPods:      conflictingLabelsPods,
		UnanalyzeablePods:          unanalyzeablePods,
	}
}

func (kr *KubePerceptorReport) HumanReadableString() string {
	if kr == nil {
		return `
Kubernetes<->Perceptor:
 - no information
 `
	}
	return fmt.Sprintf(`
Kubernetes<->Perceptor:
 - %d pod(s) in Kubernetes that were not in Perceptor
 - %d pod(s) in Perceptor that were not in Kubernetes
 - %d image(s) in Kubernetes that were not in Perceptor
 - %d image(s) in Perceptor that were not in Kubernetes
 - %d pod(s) whose Kubernetes annotations did not match their scan results
 - %d pod(s) whose Kubernetes labels did not match their scan results
 - %d pod(s) with Kubernetes annotations but no scan results
 - %d pod(s) with scan results but not Kubernetes annotations
	 `,
		len(kr.JustKubePods),
		len(kr.JustPerceptorPods),
		len(kr.JustKubeImages),
		len(kr.JustPerceptorImages),
		len(kr.ConflictingAnnotationsPods),
		len(kr.ConflictingLabelsPods),
		len(kr.FinishedJustKubePods),
		len(kr.FinishedJustPerceptorPods))
}

func KubeNotPerceptorPods(kubeDump *kube.Dump, perceptorDump *perceptor.Dump) []string {
	pods := []string{}
	for podName := range kubeDump.PodsByName {
		_, ok := perceptorDump.Model.Pods[podName]
		if !ok {
			pods = append(pods, podName)
		}
	}
	return pods
}

func PerceptorNotKubePods(kubeDump *kube.Dump, perceptorDump *perceptor.Dump) []string {
	pods := []string{}
	for podName := range perceptorDump.Model.Pods {
		_, ok := kubeDump.PodsByName[podName]
		if !ok {
			pods = append(pods, podName)
		}
	}
	return pods
}

func KubeNotPerceptorImages(kubeDump *kube.Dump, perceptorDump *perceptor.Dump) []string {
	images := []string{}
	for sha := range kubeDump.ImagesBySha {
		_, ok := perceptorDump.Model.Images[sha]
		if !ok {
			images = append(images, sha)
		}
	}
	return images
}

func PerceptorNotKubeImages(kubeDump *kube.Dump, perceptorDump *perceptor.Dump) []string {
	images := []string{}
	for sha := range perceptorDump.Model.Images {
		_, ok := kubeDump.ImagesBySha[sha]
		if !ok {
			images = append(images, sha)
		}
	}
	return images
}

func KubeNotPerceptorFinishedPods(kubeDump *kube.Dump, perceptorDump *perceptor.Dump, hubVersion string) (finishedKubePods []string, incorrectAnnotationsPods []string, incorrectLabelsPods []string, unanalyzeablePods []string) {
	finishedKubePods = []string{}
	incorrectAnnotationsPods = []string{}
	incorrectLabelsPods = []string{}
	unanalyzeablePods = []string{}

	for podName, pod := range kubeDump.PodsByName {
		imageShas, err := PodShas(pod)
		if err != nil {
			unanalyzeablePods = append(unanalyzeablePods, podName)
			continue
		}

		if pod.HasAllBDAnnotations() && pod.HasAllBDLabels() {
			_, ok := perceptorDump.PodsByName[podName]
			if !ok {
				finishedKubePods = append(finishedKubePods, podName)
			}
		}

		expectedPodAnnotations, err := ExpectedPodAnnotations(podName, imageShas, kubeDump, perceptorDump, hubVersion)
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

		expectedPodLabels, err := ExpectedPodLabels(podName, imageShas, kubeDump, perceptorDump)
		if err == nil {
			missingKeys := []string{} // TODO do we actually need this?
			keysOfWrongValues := []string{}
			for key, expectedVal := range expectedPodLabels {
				actualVal, ok := pod.Labels[key]
				if !ok {
					missingKeys = append(missingKeys, key)
				} else if expectedVal != actualVal {
					log.Warnf("conflicting values for key %s: expected %s, actual %s", key, expectedVal, actualVal)
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

func PerceptorNotKubeFinishedPods(kubeDump *kube.Dump, perceptorDump *perceptor.Dump) []string {
	pods := []string{}
	for podName, _ := range perceptorDump.PodsByName {
		kubePod, ok := kubeDump.PodsByName[podName]
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

func ExpectedPodAnnotations(podName string, imageShas []string, kubeDump *kube.Dump, perceptorDump *perceptor.Dump, hubVersion string) (map[string]string, error) {
	annotations := map[string]string{}
	pod, ok := perceptorDump.PodsByName[podName]
	if !ok {
		// didn't find this pod in the scan results?  then there shouldn't be any BD annotations
		return annotations, nil
	}

	for i, sha := range imageShas {
		image, ok := perceptorDump.ImagesBySha[sha]
		if !ok {
			return nil, fmt.Errorf("unable to find image %s", sha)
		}
		annotations[kube.PodImageAnnotationKeyOverallStatus.String(i)] = image.OverallStatus
		annotations[kube.PodImageAnnotationKeyVulnerabilities.String(i)] = fmt.Sprintf("%d", image.Vulnerabilities)
		annotations[kube.PodImageAnnotationKeyPolicyViolations.String(i)] = fmt.Sprintf("%d", image.PolicyViolations)
		annotations[kube.PodImageAnnotationKeyProjectEndpoint.String(i)] = image.ComponentsURL
		annotations[kube.PodImageAnnotationKeyScannerVersion.String(i)] = hubVersion
		annotations[kube.PodImageAnnotationKeyServerVersion.String(i)] = hubVersion
		name, _, _ := kubeDump.ImagesBySha[sha].ParseImageID() // just ignore errors and missing values!  maybe not a good idea TODO
		name = strings.Replace(name, "/", ".", -1)
		name = strings.Replace(name, ":", ".", -1)
		annotations[kube.PodImageAnnotationKeyImage.String(i)] = name
	}

	annotations[kube.PodAnnotationKeyOverallStatus.String()] = pod.OverallStatus
	annotations[kube.PodAnnotationKeyVulnerabilities.String()] = fmt.Sprintf("%d", pod.Vulnerabilities)
	annotations[kube.PodAnnotationKeyPolicyViolations.String()] = fmt.Sprintf("%d", pod.PolicyViolations)
	annotations[kube.PodAnnotationKeyScannerVersion.String()] = hubVersion
	annotations[kube.PodAnnotationKeyServerVersion.String()] = hubVersion

	return annotations, nil
}

// ShortenLabelContent will ensure the data is less than the 63 character limit and doesn't contain
// any characters that are not allowed
func ShortenLabelContent(data string) string {
	newData := RemoveRegistryInfo(data)

	// Label values can not be longer than 63 characters
	if len(newData) > 63 {
		newData = newData[0:63]
	}

	return newData
}

// RemoveRegistryInfo will take a string and return a string that removes any registry name information
// and replaces all / with .
func RemoveRegistryInfo(d string) string {
	s := strings.Split(d, "/")

	// If the data includes a . or : before the first / then that string is most likely
	// a registry name.  Remove it because it could make the data too long and
	// truncate useful information
	if strings.Contains(s[0], ".") || strings.Contains(s[0], ":") {
		s = s[1:]
	}
	return strings.Join(s, ".")
}

func ExpectedPodLabels(podName string, imageShas []string, kubeDump *kube.Dump, perceptorDump *perceptor.Dump) (map[string]string, error) {
	perceptor := perceptorDump
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
		name, _, err := kubeDump.ImagesBySha[sha].ParseImageID()
		// TODO ignoring errors ... not a great idea
		if err != nil {
			log.Errorf("unable to parse image id %s: %s", kubeDump.ImagesBySha[sha].ImageID, err.Error())
		}
		labels[kube.PodImageLabelKeyImage.String(i)] = ShortenLabelContent(name)
	}

	labels[kube.PodLabelKeyOverallStatus.String()] = pod.OverallStatus
	labels[kube.PodLabelKeyVulnerabilities.String()] = fmt.Sprintf("%d", pod.Vulnerabilities)
	labels[kube.PodLabelKeyPolicyViolations.String()] = fmt.Sprintf("%d", pod.PolicyViolations)

	return labels, nil
}
