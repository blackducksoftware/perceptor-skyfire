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

	"github.com/blackducksoftware/perceptor-skyfire/pkg/dump"
)

type Report struct {
	Kube          *KubeReport
	KubePerceptor *KubePerceptorReport
	PerceptorHub  *PerceptorHubReport
	Hub           *HubReport
}

func NewReport(dump *dump.Dump) *Report {
	return &Report{
		NewKubeReport(dump),
		NewKubePerceptorReport(dump),
		NewPerceptorHubReport(dump),
		NewHubReport(dump),
	}
}

func (r *Report) HumanReadableString() string {
	return fmt.Sprintf(`
Kubernetes:
 - we found %d ImageIDs that were unparseable

Kubernetes<->Perceptor:
 - we found %d pod(s) in Kubernetes that were not in Perceptor
 - we found %d pod(s) in Perceptor that were not in Kubernetes
 - we found %d image(s) in Kubernetes that were not in Perceptor
 - we found %d image(s) in Perceptor that were not in Kubernetes

Perceptor<->Hub:
 - we found %d image(s) in Perceptor that were not in the Hub
 - we found %d image(s) in the Hub that were not in Perceptor

Hub:
 - we found %d project(s) in the Hub with multiple versions
 - we found %d version(s) in the Hub with multiple code locations
 - we found %d code location(s) in the Hub with multiple scan summaries
		 `,
		len(r.Kube.UnparseableKubeImages),
		len(r.KubePerceptor.JustKubePods),
		len(r.KubePerceptor.JustPerceptorPods),
		len(r.KubePerceptor.JustKubeImages),
		len(r.KubePerceptor.JustPerceptorImages),
		len(r.PerceptorHub.JustPerceptorImages),
		len(r.PerceptorHub.JustHubImages),
		len(r.Hub.ProjectsMultipleVersions),
		len(r.Hub.VersionsMultipleCodeLocations),
		len(r.Hub.CodeLocationsMultipleScanSummaries))
}

// In perceptor but not in hub:
// - completed images
// - completed pods

// In hub but not in perceptor:
// - completed image

// Extra hub stuff:
// - multiple projects matching a sha (?)
// - multiple project versions in a project
// - multiple scan summaries in a project version
// - multiple code locations in a scan summary
