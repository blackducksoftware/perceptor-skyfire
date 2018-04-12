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

package dump

import (
	"github.com/blackducksoftware/perceptor-skyfire/pkg/kube"
	log "github.com/sirupsen/logrus"
)

type KubeDump struct {
	Meta              *kube.Meta
	Pods              []*kube.Pod
	PodsByName        map[string]*kube.Pod
	DuplicatePodNames map[string]bool
	// Images     []*kube.Image
	ImagesBySha        map[string]*kube.Image
	DuplicateImageShas map[string]bool
	ImagesMissingSha   []*kube.Image
}

func NewKubeDump(meta *kube.Meta, pods []*kube.Pod) *KubeDump {
	kubeDump := &KubeDump{
		Meta:               meta,
		Pods:               pods,
		PodsByName:         map[string]*kube.Pod{},
		DuplicatePodNames:  map[string]bool{},
		ImagesBySha:        map[string]*kube.Image{},
		DuplicateImageShas: map[string]bool{},
		ImagesMissingSha:   []*kube.Image{}}
	kubeDump.computeDerivedData()
	return kubeDump
}

func (kd *KubeDump) computeDerivedData() {
	for _, pod := range kd.Pods {
		_, ok := kd.PodsByName[pod.QualifiedName()]
		if ok {
			kd.DuplicatePodNames[pod.QualifiedName()] = true
		} else {
			kd.PodsByName[pod.QualifiedName()] = pod
		}
		for _, container := range pod.Containers {
			_, sha, err := container.Image.ParseImageID()
			if err != nil {
				kd.ImagesMissingSha = append(kd.ImagesMissingSha, container.Image)
				log.Errorf("unable to parse sha for pod %s, container %s, image %s: %s", pod.QualifiedName(), container.Name, container.Image.ImageID, err.Error())
			} else {
				_, ok := kd.ImagesBySha[sha]
				if ok {
					kd.DuplicateImageShas[sha] = true
				} else {
					kd.ImagesBySha[sha] = container.Image
				}
			}
		}
	}
}
