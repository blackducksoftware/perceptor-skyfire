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

type PodLabelKey int

const (
	PodLabelKeyVulnerabilities  PodLabelKey = iota
	PodLabelKeyPolicyViolations PodLabelKey = iota
	PodLabelKeyOverallStatus    PodLabelKey = iota
)

func (pak PodLabelKey) String() string {
	switch pak {
	case PodLabelKeyVulnerabilities:
		return "pod.vulnerabilities"
	case PodLabelKeyPolicyViolations:
		return "pod.policy-violations"
	case PodLabelKeyOverallStatus:
		return "pod.overall-status"
	}
	panic(fmt.Errorf("invalid PodLabelKey value: %d", pak))
}

var podLabelKeys = []PodLabelKey{
	PodLabelKeyVulnerabilities,
	PodLabelKeyPolicyViolations,
	PodLabelKeyOverallStatus,
}

var podLabelKeyStrings = []string{}

func init() {
	for _, key := range podLabelKeys {
		podLabelKeyStrings = append(podLabelKeyStrings, key.String())
	}
}

// type PodLabels struct {
// 	ContainerCount int
// 	KubeLabels     map[string]string
// 	PodImageLabels []*PodImageLabels
// }
//
// func NewPodLabels(containerCount int, labels map[string]string) *PodLabels {
// 	podImageLabels := []*PodImageLabels{}
// 	for i := 0; i < containerCount; i++ {
// 		podImageLabels = append(podImageLabels, NewPodImageLabels(i, labels))
// 	}
// 	return &PodLabels{
// 		ContainerCount: containerCount,
// 		KubeLabels:     labels,
// 		PodImageLabels: podImageLabels,
// 	}
// }
//
// func (pl *PodLabels) hasAllBDPodLabelKeys() bool {
// 	return len(util.Difference(util.MakeSet(PodLabelKeys(pl.ContainerCount)), pl.KubeLabels)) == 0
// }
//
// func hasAnyBDPodLabelKeys(containerCount int, dict map[string]string) bool {
// 	expectedKeys := util.MakeSet(PodLabelKeys(containerCount))
// 	difference := len(util.Difference(expectedKeys, dict))
// 	return difference < len(expectedKeys)
// }
//
// // TODO do we even need this?
// // func GetBDLabelKeys(containerCount int, dict map[string]string) map[string]string {
// // 	return util.Difference(dict, util.MakeSet(PodLabelKeys(containerCount)))
// // }
//
// // TODO implement
// func removeBDLabelKeys(containerCount int, dict map[string]string) map[string]string {
// 	return util.Difference(dict, util.MakeSet(PodLabelKeys(containerCount)))
// }
//
// func (pl *PodLabels) Get(key PodLabelKey) (string, error) {
// 	return getString(pl.KubeLabels, key.String())
// }
//
// func (pa *PodLabels) HasAllBDLabelKeys() bool {
// 	if !pa.hasAllBDPodLabelKeys() {
// 		return false
// 	}
// 	for _, imageLabels := range pa.PodImageLabels {
// 		if !imageLabels.HasAllBDLabelKeys() {
// 			return false
// 		}
// 	}
// 	return true
// }
//
// func (pa *PodLabels) HasAnyBDLabelKeys() bool {
// 	if pa.hasAnyBDPodLabelKeys() {
// 		return true
// 	}
// 	for _, imageLabels := range pa.PodImageLabels {
// 		if imageLabels.HasAnyBDLabelKeys() {
// 			return true
// 		}
// 	}
// 	return false
// }
//
// func (pa *PodLabels) IsPartiallyLabeled() bool {
// 	return pa.HasAnyBDLabelKeys() && !pa.HasAllBDLabelKeys()
// }
//
// func RemoveBDPodLabelKeys(containerCount int, labels map[string]string) map[string]string {
// 	copy := map[string]string{}
// 	keysToDrop := map[string]bool{}
// 	for _, key := range PodLabelKeys {
// 		keysToDrop[key.String()] = true
// 	}
// 	for key, val := range labels {
// 		_, ok := keysToDrop[key]
// 		if !ok {
// 			copy[key] = val
// 		}
// 	}
// 	for i := 0; i < containerCount; i++ {
// 		copy = RemoveBDPodImageAnnotationKeys(i, copy)
// 	}
// 	return copy
// }
