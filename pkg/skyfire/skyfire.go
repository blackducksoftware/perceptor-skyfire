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

	"github.com/blackducksoftware/perceptor-skyfire/pkg/dump"
	"github.com/blackducksoftware/perceptor-skyfire/pkg/hipchat"
	"github.com/blackducksoftware/perceptor-skyfire/pkg/hub"
	"github.com/blackducksoftware/perceptor-skyfire/pkg/kube"
	"github.com/blackducksoftware/perceptor-skyfire/pkg/perceptor"
	"github.com/blackducksoftware/perceptor-skyfire/pkg/report"
)

type Skyfire struct {
	KubeDumper      *kube.KubeClient
	PerceptorDumper *perceptor.PerceptorDumper
	HubDumper       *hub.HubDumper
}

func NewSkyfire(configPath string) (*Skyfire, error) {
	config, err := ReadConfig(configPath)
	if err != nil {
		return nil, err
	}

	kubeDumper, err := kube.NewKubeClient(config.KubeClientConfig())
	if err != nil {
		return nil, err
	}

	perceptorDumper := perceptor.NewPerceptorDumper(config.PerceptorHost, config.PerceptorPort)

	hubDumper, err := hub.NewHubDumper(config.HubHost, config.HubUser, config.HubPassword)
	if err != nil {
		return nil, err
	}

	skyfire := &Skyfire{
		KubeDumper:      kubeDumper,
		PerceptorDumper: perceptorDumper,
		HubDumper:       hubDumper,
	}
	return skyfire, nil
}

func (sf *Skyfire) GrabDumpAndBuildReport() (*dump.Dump, *report.Report, error) {
	scanResults, err := sf.PerceptorDumper.DumpScanResults()
	if err != nil {
		return nil, nil, err
	}

	model, err := sf.PerceptorDumper.DumpModel()
	if err != nil {
		return nil, nil, err
	}

	hubProjects, err := sf.HubDumper.DumpAllProjects()
	if err != nil {
		return nil, nil, err
	}

	kubePods, err := sf.KubeDumper.GetAllPods()
	if err != nil {
		return nil, nil, err
	}

	dump := dump.NewDump(kubePods, hubProjects, scanResults, model)
	report := report.NewReport(dump)
	return dump, report, nil
}

func (sf *Skyfire) BuildReportAndSendToHipChat() error {
	_, report, err := sf.GrabDumpAndBuildReport()
	if err != nil {
		return err
	}
	// fmt.Println(dumpJson(dump))
	// fmt.Println(dumpJson(report))
	str := report.HumanReadableString()
	fmt.Println(str)

	// var room = "CloudNativeEngineering"
	var room = "PushTesting"

	hip := hipchat.NewHipchat(room)
	_, err = hip.Send(str)
	return err
}

func dumpJson(object interface{}) string {
	bytes, err := json.MarshalIndent(object, "", "  ")
	if err != nil {
		panic(err)
	}
	return string(bytes)
}
