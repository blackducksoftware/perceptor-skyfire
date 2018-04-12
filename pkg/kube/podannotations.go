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
)

type PodAnnotationKey int

const (
	PodAnnotationKeyVulnerabilities  PodAnnotationKey = iota
	PodAnnotationKeyPolicyViolations PodAnnotationKey = iota
	PodAnnotationKeyOverallStatus    PodAnnotationKey = iota
	PodAnnotationKeyServerVersion    PodAnnotationKey = iota
	PodAnnotationKeyScannerVersion   PodAnnotationKey = iota
)

func (pak PodAnnotationKey) String() string {
	switch pak {
	case PodAnnotationKeyVulnerabilities:
		return "pod.vulnerabilities"
	case PodAnnotationKeyPolicyViolations:
		return "pod.policy-violations"
	case PodAnnotationKeyOverallStatus:
		return "pod.overall-status"
	case PodAnnotationKeyServerVersion:
		return "pod.server-version"
	case PodAnnotationKeyScannerVersion:
		return "pod.scanner-version"
	}
	panic(fmt.Errorf("invalid PodAnnotationKey value: %d", pak))
}

var podAnnotationKeys = []PodAnnotationKey{
	PodAnnotationKeyVulnerabilities,
	PodAnnotationKeyPolicyViolations,
	PodAnnotationKeyOverallStatus,
	PodAnnotationKeyServerVersion,
	PodAnnotationKeyScannerVersion,
}

type PodAnnotations struct {
	ContainerCount      int
	KubeAnnotations     map[string]string
	PodImageAnnotations []*PodImageAnnotations
}

func NewPodAnnotations(containerCount int, annotations map[string]string) *PodAnnotations {
	podImageAnnotations := []*PodImageAnnotations{}
	for i := 0; i < containerCount; i++ {
		podImageAnnotations = append(podImageAnnotations, NewPodImageAnnotations(i, annotations))
	}
	return &PodAnnotations{
		ContainerCount:      containerCount,
		KubeAnnotations:     annotations,
		PodImageAnnotations: podImageAnnotations,
	}
}

func (pa *PodAnnotations) hasAllBDPodAnnotationKeys() bool {
	_, err := pa.VulnerabilityCount()
	if err != nil {
		return false
	}
	_, err = pa.PolicyViolationCount()
	if err != nil {
		return false
	}
	_, err = pa.OverallStatus()
	if err != nil {
		return false
	}
	_, err = pa.ServerVersion()
	if err != nil {
		return false
	}
	_, err = pa.ScannerVersion()
	if err != nil {
		return false
	}
	return true
}

func (pa *PodAnnotations) hasAnyBDPodAnnotationKeys() bool {
	_, err := pa.VulnerabilityCount()
	if err == nil {
		return true
	}
	_, err = pa.PolicyViolationCount()
	if err == nil {
		return true
	}
	_, err = pa.OverallStatus()
	if err == nil {
		return true
	}
	_, err = pa.ServerVersion()
	if err == nil {
		return true
	}
	_, err = pa.ScannerVersion()
	if err == nil {
		return true
	}
	return false
}

func (pa *PodAnnotations) VulnerabilityCount() (int, error) {
	return getInt(pa.KubeAnnotations, PodAnnotationKeyVulnerabilities.String())
}

func (pa *PodAnnotations) PolicyViolationCount() (int, error) {
	return getInt(pa.KubeAnnotations, PodAnnotationKeyPolicyViolations.String())
}

func (pa *PodAnnotations) OverallStatus() (string, error) {
	return getString(pa.KubeAnnotations, PodAnnotationKeyOverallStatus.String())
}

func (pa *PodAnnotations) ServerVersion() (string, error) {
	return getString(pa.KubeAnnotations, PodAnnotationKeyServerVersion.String())
}

func (pa *PodAnnotations) ScannerVersion() (string, error) {
	return getString(pa.KubeAnnotations, PodAnnotationKeyScannerVersion.String())
}

func (pa *PodAnnotations) HasAllBDAnnotationKeys() bool {
	if !pa.hasAllBDPodAnnotationKeys() {
		return false
	}
	for _, imageAnnotations := range pa.PodImageAnnotations {
		if !imageAnnotations.HasAllBDAnnotationKeys() {
			return false
		}
	}
	return true
}

func (pa *PodAnnotations) HasAnyBDAnnotationKeys() bool {
	if pa.hasAnyBDPodAnnotationKeys() {
		return true
	}
	for _, imageAnnotations := range pa.PodImageAnnotations {
		if imageAnnotations.HasAnyBDAnnotationKeys() {
			return true
		}
	}
	return false
}

func (pa *PodAnnotations) IsPartiallyAnnotated() bool {
	return pa.HasAnyBDAnnotationKeys() && !pa.HasAllBDAnnotationKeys()
}

func RemoveBDPodAnnotationKeys(containerCount int, annotations map[string]string) map[string]string {
	copy := map[string]string{}
	keysToDrop := map[string]bool{}
	for _, key := range podAnnotationKeys {
		keysToDrop[key.String()] = true
	}
	for key, val := range annotations {
		_, ok := keysToDrop[key]
		if !ok {
			copy[key] = val
		}
	}
	for i := 0; i < containerCount; i++ {
		copy = RemoveBDPodImageAnnotationKeys(i, copy)
	}
	return copy
}
