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

import "fmt"

type PodImageAnnotationKey int

const (
	PodImageAnnotationKeyVulnerabilities  PodImageAnnotationKey = iota
	PodImageAnnotationKeyPolicyViolations PodImageAnnotationKey = iota
	PodImageAnnotationKeyOverallStatus    PodImageAnnotationKey = iota
	PodImageAnnotationKeyServerVersion    PodImageAnnotationKey = iota
	PodImageAnnotationKeyScannerVersion   PodImageAnnotationKey = iota
	PodImageAnnotationKeyProjectEndpoint  PodImageAnnotationKey = iota
	PodImageAnnotationKeyImage            PodImageAnnotationKey = iota
)

func (pak PodImageAnnotationKey) formatString() string {
	switch pak {
	case PodImageAnnotationKeyVulnerabilities:
		return "image%d.vulnerabilities"
	case PodImageAnnotationKeyPolicyViolations:
		return "image%d.policy-violations"
	case PodImageAnnotationKeyOverallStatus:
		return "image%d.overall-status"
	case PodImageAnnotationKeyServerVersion:
		return "image%d.server-version"
	case PodImageAnnotationKeyScannerVersion:
		return "image%d.scanner-version"
	case PodImageAnnotationKeyProjectEndpoint:
		return "image%d.project-endpoint"
	case PodImageAnnotationKeyImage:
		return "image%d"
	}
	panic(fmt.Errorf("invalid PodImageAnnotationKey value: %d", pak))
}

var podImageAnnotationKeys = []PodImageAnnotationKey{
	PodImageAnnotationKeyVulnerabilities,
	PodImageAnnotationKeyPolicyViolations,
	PodImageAnnotationKeyOverallStatus,
	PodImageAnnotationKeyServerVersion,
	PodImageAnnotationKeyScannerVersion,
	PodImageAnnotationKeyProjectEndpoint,
	PodImageAnnotationKeyImage,
}

func (pak PodImageAnnotationKey) String(index int) string {
	return fmt.Sprintf(pak.formatString(), index)
}

func podImageAnnotationKeyStrings(index int) []string {
	strs := []string{}
	for _, key := range podImageAnnotationKeys {
		strs = append(strs, key.String(index))
	}
	return strs
}

// type PodImageAnnotations struct {
// 	ContainerIndex  int
// 	KubeAnnotations map[string]string
// }
//
// func NewPodImageAnnotations(containerIndex int, annotations map[string]string) *PodImageAnnotations {
// 	return &PodImageAnnotations{
// 		ContainerIndex:  containerIndex,
// 		KubeAnnotations: annotations,
// 	}
// }
//
// func (pa *PodImageAnnotations) HasAllBDAnnotationKeys() bool {
// 	_, err := pa.VulnerabilityCount()
// 	if err != nil {
// 		return false
// 	}
// 	_, err = pa.PolicyViolationCount()
// 	if err != nil {
// 		return false
// 	}
// 	_, err = pa.OverallStatus()
// 	if err != nil {
// 		return false
// 	}
// 	_, err = pa.ServerVersion()
// 	if err != nil {
// 		return false
// 	}
// 	_, err = pa.ScannerVersion()
// 	if err != nil {
// 		return false
// 	}
// 	_, err = pa.ProjectEndpoint()
// 	if err != nil {
// 		return false
// 	}
// 	_, err = pa.Image()
// 	if err != nil {
// 		return false
// 	}
// 	return true
// }
//
// func (pa *PodImageAnnotations) HasAnyBDAnnotationKeys() bool {
// 	_, err := pa.VulnerabilityCount()
// 	if err == nil {
// 		return true
// 	}
// 	_, err = pa.PolicyViolationCount()
// 	if err == nil {
// 		return true
// 	}
// 	_, err = pa.OverallStatus()
// 	if err == nil {
// 		return true
// 	}
// 	_, err = pa.ServerVersion()
// 	if err == nil {
// 		return true
// 	}
// 	_, err = pa.ScannerVersion()
// 	if err == nil {
// 		return true
// 	}
// 	_, err = pa.ProjectEndpoint()
// 	if err == nil {
// 		return true
// 	}
// 	_, err = pa.Image()
// 	if err == nil {
// 		return true
// 	}
// 	return false
// }
//
// func (pa *PodImageAnnotations) VulnerabilityCount() (int, error) {
// 	return getInt(pa.KubeAnnotations, PodImageAnnotationKeyVulnerabilities.String(pa.ContainerIndex))
// }
//
// func (pa *PodImageAnnotations) PolicyViolationCount() (int, error) {
// 	return getInt(pa.KubeAnnotations, PodImageAnnotationKeyPolicyViolations.String(pa.ContainerIndex))
// }
//
// func (pa *PodImageAnnotations) OverallStatus() (string, error) {
// 	return getString(pa.KubeAnnotations, PodImageAnnotationKeyOverallStatus.String(pa.ContainerIndex))
// }
//
// func (pa *PodImageAnnotations) ServerVersion() (string, error) {
// 	return getString(pa.KubeAnnotations, PodImageAnnotationKeyServerVersion.String(pa.ContainerIndex))
// }
//
// func (pa *PodImageAnnotations) ScannerVersion() (string, error) {
// 	return getString(pa.KubeAnnotations, PodImageAnnotationKeyScannerVersion.String(pa.ContainerIndex))
// }
//
// func (pa *PodImageAnnotations) ProjectEndpoint() (string, error) {
// 	return getString(pa.KubeAnnotations, PodImageAnnotationKeyProjectEndpoint.String(pa.ContainerIndex))
// }
//
// func (pa *PodImageAnnotations) Image() (string, error) {
// 	return getString(pa.KubeAnnotations, PodImageAnnotationKeyImage.String(pa.ContainerIndex))
// }
//
// func RemoveBDPodImageAnnotationKeys(containerIndex int, annotations map[string]string) map[string]string {
// 	copy := map[string]string{}
// 	keysToDrop := map[string]bool{}
// 	for _, key := range podImageAnnotationKeys {
// 		keysToDrop[key.String(containerIndex)] = true
// 	}
// 	for key, val := range annotations {
// 		_, ok := keysToDrop[key]
// 		if !ok {
// 			copy[key] = val
// 		}
// 	}
// 	return copy
// }
