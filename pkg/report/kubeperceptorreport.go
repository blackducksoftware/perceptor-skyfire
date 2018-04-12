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
	"github.com/blackducksoftware/perceptor-skyfire/pkg/dump"
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

	ConflictingAnnotationsPods map[string]string
	ConflictingLabelsPods      map[string]string
}

func NewKubePerceptorReport(dump *dump.Dump) *KubePerceptorReport {
	finishedJustKubePods, partiallyAnnotatedKubePods, partiallyLabeledKubePods, conflictingAnnotationsPods, conflictingLabelsPods := KubeNotPerceptorFinishedPods(dump)
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
	}
}

func KubeNotPerceptorPods(dump *dump.Dump) []string {
	pods := []string{}
	for podName := range dump.Kube.PodsByName {
		_, ok := dump.Perceptor.PodsByName[podName]
		if !ok {
			pods = append(pods, podName)
		}
	}
	return pods
}

func PerceptorNotKubePods(dump *dump.Dump) []string {
	pods := []string{}
	for podName := range dump.Perceptor.PodsByName {
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
		_, ok := dump.Perceptor.ImagesBySha[sha]
		if !ok {
			images = append(images, sha)
		}
	}
	return images
}

func PerceptorNotKubeImages(dump *dump.Dump) []string {
	images := []string{}
	for sha := range dump.Perceptor.ImagesBySha {
		_, ok := dump.Kube.ImagesBySha[sha]
		if !ok {
			images = append(images, sha)
		}
	}
	return images
}

func KubeNotPerceptorFinishedPods(dump *dump.Dump) (finishedKubePods []string, partiallyAnnotatedKubePods []string, partiallyLabeledKubePods []string, conflictingAnnotationsPods map[string]string, conflictingLabelsPods map[string]string) {
	finishedKubePods = []string{}
	partiallyAnnotatedKubePods = []string{}
	partiallyLabeledKubePods = []string{}
	conflictingAnnotationsPods = map[string]string{}
	conflictingLabelsPods = map[string]string{}
	for podName, pod := range dump.Kube.PodsByName {
		// annotations
		annotations := pod.ParsedAnnotations()
		if annotations.IsPartiallyAnnotated() {
			partiallyAnnotatedKubePods = append(partiallyAnnotatedKubePods, podName)
		}

		// TODO
		// labels
		// hasAllLabels := kube.HasAllBDLabelKeys(len(pod.Containers), pod.Labels)
		// hasAnyLabels := kube.HasAnyBDLabelKeys(len(pod.Containers), pod.Labels)
		// if hasAnyLabels && !hasAllLabels {
		// 	partiallyLabeledKubePods = append(partiallyLabeledKubePods, podName)
		// }
		// isFinished := hasAllAnnotations && hasAllLabels
		// if !isFinished {
		// 	continue
		// }

		// TODO remove this when above is uncommented
		if !annotations.HasAllBDAnnotationKeys() {
			continue
		}

		// we've established that it's finished
		// now, let's check if perceptor agrees
		perceptorPod, ok := dump.Perceptor.PodsByName[podName]
		if !ok {
			finishedKubePods = append(finishedKubePods, podName)
		}
		// okay, so perceptor thinks it's done too
		//   but does it have the same values as kube?
		vCount, _ := annotations.VulnerabilityCount()
		if vCount != perceptorPod.Vulnerabilities {
			conflictingAnnotationsPods[podName] += "vulnerabilities"
		}
		pvCount, _ := annotations.PolicyViolationCount()
		if pvCount != perceptorPod.PolicyViolations {
			conflictingAnnotationsPods[podName] += ",policyviolations"
		}
		overallStatus, _ := annotations.OverallStatus()
		if overallStatus != perceptorPod.OverallStatus {
			conflictingAnnotationsPods[podName] += ",overallstatus"
		}

		// TODO check hub version, scanner version
		// TODO check pod image%d%s annotations
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
		if !kubePod.ParsedAnnotations().HasAllBDAnnotationKeys() {
			pods = append(pods, podName)
		}
	}
	return pods
}
