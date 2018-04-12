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

package skyfire

import (
	"time"

	"github.com/blackducksoftware/perceptor-skyfire/pkg/hipchat"
	"github.com/blackducksoftware/perceptor-skyfire/pkg/report"
	log "github.com/sirupsen/logrus"
)

type Daemon struct {
	Skyfire *Skyfire
	Hipchat *hipchat.Hipchat
}

const (
	infoPullPauseMinutes = 1
)

func NewDaemon(configPath string) (*Daemon, error) {
	config, err := ReadConfig(configPath)
	if err != nil {
		return nil, err
	}

	skyfire, err := NewSkyfire(config)
	if err != nil {
		return nil, err
	}

	daemon := &Daemon{
		Skyfire: skyfire,
		Hipchat: hipchat.NewHipchat(config.HipchatRoom),
	}
	go daemon.startPullingInfo()
	return daemon, nil
}

func (d *Daemon) startPullingInfo() {
	for {
		_, report, err := d.Skyfire.GrabDumpAndBuildReport()
		IssueReportMetrics(report)

		if err != nil {
			log.Errorf("unable to build report: %s", err.Error())
		} else {
			str := report.HumanReadableString()
			log.Infof("report: \n%s", str)

			_, err = d.Hipchat.Send(str)
			if err != nil {
				log.Errorf("unable to send hipchat report: %s", err.Error())
			}
		}

		time.Sleep(infoPullPauseMinutes * time.Minute)
	}
}

func IssueReportMetrics(report *report.Report) {
	recordReportProblem("hub_projects_multiple_versions", len(report.Hub.ProjectsMultipleVersions))
	recordReportProblem("hub_versions_multiple_code_locations", len(report.Hub.VersionsMultipleCodeLocations))
	recordReportProblem("hub_code_locations_multiple_scan_summaries", len(report.Hub.CodeLocationsMultipleScanSummaries))

	recordReportProblem("kube_unparseable_images", len(report.Kube.UnparseableKubeImages))

	recordReportProblem("kube-perceptor_images_just_in_kube", len(report.KubePerceptor.JustKubeImages))
	recordReportProblem("kube-perceptor_pods_just_in_kube", len(report.KubePerceptor.JustKubePods))
	recordReportProblem("kube-perceptor_images_just_in_perceptor", len(report.KubePerceptor.JustPerceptorImages))
	recordReportProblem("kube-perceptor_pods_just_in_perceptor", len(report.KubePerceptor.JustPerceptorPods))

	recordReportProblem("perceptor-hub_images_just_in_hub", len(report.PerceptorHub.JustHubImages))
	recordReportProblem("perceptor-hub_images_just_in_perceptor", len(report.PerceptorHub.JustPerceptorImages))
}
