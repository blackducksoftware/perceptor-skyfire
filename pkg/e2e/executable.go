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

package e2e

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

func RunDumper(configPath string) {
	config := ReadConfig(configPath)

	perceptorScanResults, perceptorModel, err := perceptor.RunDumper(config.PerceptorHost, config.PerceptorPort)
	if err != nil {
		panic(err)
	}

	kubePods, err := kube.RunDumper(config.UseInClusterConfig, config.MasterURL, config.KubeConfigPath)
	if err != nil {
		panic(err)
	}

	hubProjects, err := hub.RunDumper(config.HubURL, config.HubUser, config.HubPassword)
	if err != nil {
		panic(err)
	}

	dump := dump.NewDump(kubePods, hubProjects, perceptorScanResults, perceptorModel)
	// fmt.Println(dumpJson(dump))
	report := report.NewReport(dump)
	// fmt.Println(dumpJson(report))
	fmt.Println(report.HumanReadableString())
	_, err = hipchat.Send(report.HumanReadableString())
	if err != nil {
		panic(err)
	}
}

func dumpJson(object interface{}) string {
	bytes, err := json.MarshalIndent(object, "", "  ")
	if err != nil {
		panic(err)
	}
	return string(bytes)
}
