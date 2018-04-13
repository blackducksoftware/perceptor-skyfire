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
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/blackducksoftware/perceptor-skyfire/pkg/dump"
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

func NewDaemon(config *Config) (*Daemon, error) {
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
	err := os.Mkdir("dumps", 0777)
	if err != nil {
		log.Errorf("unable to create directory: %s", err.Error())
	}
	for i := 0; ; i++ {
		dump, report, err := d.Skyfire.GrabDumpAndBuildReport()

		if err != nil {
			log.Errorf("unable to build report: %s", err.Error())
		} else {
			IssueReportMetrics(report)

			str := report.HumanReadableString()
			log.Infof("report: \n%s", str)

			writeOut(i, dump, report)

			_, err = d.Hipchat.Send(str)
			if err != nil {
				log.Errorf("unable to send hipchat report: %s", err.Error())
			}
		}

		time.Sleep(infoPullPauseMinutes * time.Minute)
	}
}

func writeOut(i int, dump *dump.Dump, report *report.Report) error {
	f, err := os.Create(fmt.Sprintf("dumps/dump%d", i))
	if err != nil {
		return err
	}
	defer f.Close()
	bytes, err := json.MarshalIndent(map[string]interface{}{
		"Dump":   dump,
		"Report": report,
	}, "", "  ")
	if err != nil {
		return err
	}
	_, err = f.Write(bytes)
	return err
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
	recordReportProblem("kube-perceptor_incorrect_pod_annotations", len(report.KubePerceptor.ConflictingAnnotationsPods))
	recordReportProblem("kube-perceptor_incorrect_pod_labels", len(report.KubePerceptor.ConflictingLabelsPods))
	recordReportProblem("kube-perceptor_finished_pods_just_kube", len(report.KubePerceptor.FinishedJustKubePods))
	recordReportProblem("kube-perceptor_finished_pods_just_perceptor", len(report.KubePerceptor.FinishedJustPerceptorPods))
	recordReportProblem("kube-perceptor_partially_annotated_pods", len(report.KubePerceptor.PartiallyAnnotatedKubePods))
	recordReportProblem("kube-perceptor_partially_labeled_pods", len(report.KubePerceptor.PartiallyLabeledKubePods))

	recordReportProblem("perceptor-hub_images_just_in_hub", len(report.PerceptorHub.JustHubImages))
	recordReportProblem("perceptor-hub_images_just_in_perceptor", len(report.PerceptorHub.JustPerceptorImages))
}
