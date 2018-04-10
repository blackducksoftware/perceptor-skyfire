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

package inspector

import (
	"fmt"

	"github.com/blackducksoftware/perceptor-skyfire/pkg/hub"
	"github.com/blackducksoftware/perceptor-skyfire/pkg/kube"
	"github.com/blackducksoftware/perceptor/pkg/api"
)

type Dump struct {
	// "raw" data
	KubePods             []*kube.Pod
	HubProjects          []*hub.Project
	PerceptorScanResults *api.ScanResults
	PerceptorModel       *api.Model

	// derived data
	KubePodsByName          map[string]map[string]*kube.Pod
	KubePodsByQualifiedName map[string]*kube.Pod
	KubeImagesBySha         map[string]*kube.Image
	HubProjectsByName       map[string]*hub.Project
	PerceptorPodsByName     map[string]map[string]*api.Pod
	PerceptorImagesBySha    map[string]*api.Image
	// TODO ???
}

func NewDump(kubePods []*kube.Pod, hubProjects []*hub.Project, perceptorScanResults *api.ScanResults, perceptorModel *api.Model) *Dump {
	dump := &Dump{
		KubePods:             kubePods,
		HubProjects:          hubProjects,
		PerceptorScanResults: perceptorScanResults,
		PerceptorModel:       perceptorModel}
	dump.computeDerivedData()
	return dump
}

func (d *Dump) computeDerivedData() {
	d.KubePodsByName = map[string]map[string]*kube.Pod{}
	d.KubePodsByQualifiedName = map[string]*kube.Pod{}
	d.KubeImagesBySha = map[string]*kube.Image{}
	d.HubProjectsByName = map[string]*hub.Project{}
	d.PerceptorPodsByName = map[string]map[string]*api.Pod{}
	d.PerceptorImagesBySha = map[string]*api.Image{}
	for _, kubePod := range d.KubePods {
		d.addKubePod(kubePod)
		for _, kubeContainer := range kubePod.Containers {
			d.addKubeImage(kubeContainer.Image)
		}
	}
}

func (d *Dump) addKubePod(pod *kube.Pod) {
	pods, ok := d.KubePodsByName[pod.Namespace]
	if !ok {
		pods = map[string]*kube.Pod{}
	}
	_, ok = pods[pod.Name]
	if ok {
		panic(fmt.Errorf("can't add pod %+v to pods %+v: pod with name %s/%s is already present", pod, pods, pod.Namespace, pod.Name))
	}
	pods[pod.Name] = pod
	d.KubePodsByName[pod.Namespace] = pods

	_, ok = d.KubePodsByQualifiedName[pod.QualifiedName()]
	if ok {
		panic(fmt.Errorf("can't add pod %+v to qualified pods %+v: pod with qualified name %s is already present", pod, d.KubePodsByQualifiedName, pod.QualifiedName()))
	}
	d.KubePodsByQualifiedName[pod.QualifiedName()] = pod
}

func (d *Dump) addKubeImage(image *kube.Image) {
	_, ok := d.KubeImagesBySha[image.Sha]
	if ok {
		panic(fmt.Errorf("can't add image %+v to images %+v: image with sha %s is already present", image, d.KubeImagesBySha, image.Sha))
	}
	d.KubeImagesBySha[image.Sha] = image
}

// In kube but not in perceptor:
// - pods
// - images
// - annotations
// - labels

func (d *Dump) KubePodsNotInPerceptor() []*kube.Pod {
	kubePods := []*kube.Pod{}
	// TODO
	// for _, kubePod := range d.KubePodsByName {
	//
	// }
	return kubePods
}

// In perceptor but not in kube:
// - pods
// - images
// - scan results

// In perceptor but not in hub:
// - completed images
// - completed pods

// In hub but not in perceptor:
// - completed image

// Extra hub stuff:
// - multiple project versions in a project
// - multiple scan summaries in a project version
// - multiple code locations in a scan summary

func (d *Dump) HubProjectsWrongNumberOfVersions() []*hub.Project {
	projects := []*hub.Project{}
	for _, project := range d.HubProjects {
		if len(project.Versions) != 1 {
			projects = append(projects, project)
		}
	}
	return projects
}

func (d *Dump) HubVersionsWrongNumberOfCodeLocations() []*hub.Version {
	versions := []*hub.Version{}
	for _, project := range d.HubProjects {
		for _, version := range project.Versions {
			if len(version.CodeLocations) != 1 {
				versions = append(versions, version)
			}
		}
	}
	return versions
}

func (d *Dump) HubCodeLocationsWrongNumberOfScans() []*hub.CodeLocation {
	codeLocations := []*hub.CodeLocation{}
	for _, project := range d.HubProjects {
		for _, version := range project.Versions {
			for _, codeLocation := range version.CodeLocations {
				if len(codeLocation.ScanSummaries) != 1 {
					codeLocations = append(codeLocations, codeLocation)
				}
			}
		}
	}
	return codeLocations
}
