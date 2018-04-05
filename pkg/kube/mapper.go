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
)

func mapKubePod(kubePod *v1.Pod) *Pod {
	containers := []*Container{}
	for _, newCont := range kubePod.Status.ContainerStatuses {
		name, sha, err := ParseImageIDString(newCont.ImageID)
		if err != nil {
			log.Errorf("unable to parse kubernetes imageID string %s from pod %s/%s: %s", newCont.ImageID, kubePod.Namespace, kubePod.Name, err.Error())
			// continue
			name = "failed to parse"
			sha = fmt.Sprintf("failed to parse -- %s", newCont.ImageID)
		}
		newImage := &Image{
			DockerImage: newCont.Image,
			Name:        name,
			Sha:         sha,
			ImageID:     newCont.ImageID,
		}
		// addedCont := NewContainer(NewImage(name, sha, newCont.Image), newCont.Name)
		addedCont := NewContainer(newImage, newCont.Name)
		containers = append(containers, addedCont)
	}
	return &Pod{kubePod.Name, string(kubePod.UID), kubePod.Namespace, containers}
}
