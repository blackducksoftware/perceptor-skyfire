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

import "github.com/blackducksoftware/perceptor-skyfire/pkg/dump"

type KubePerceptorReport struct {
	JustKubePods          []string
	JustPerceptorPods     []string
	JustKubeImages        []string
	JustPerceptorImages   []string
	UnparseableKubeImages []string
}

func NewKubePerceptorReport(dump *dump.Dump) *KubePerceptorReport {
	return &KubePerceptorReport{
		JustKubePods:          KubeNotPerceptorPods(dump),
		JustPerceptorPods:     PerceptorNotKubePods(dump),
		JustKubeImages:        KubeNotPerceptorImages(dump),
		JustPerceptorImages:   PerceptorNotKubeImages(dump),
		UnparseableKubeImages: UnparseableKubeImages(dump),
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

func UnparseableKubeImages(dump *dump.Dump) []string {
	images := []string{}
	for _, image := range dump.Kube.ImagesMissingSha {
		images = append(images, image.ImageID)
	}
	return images
}
