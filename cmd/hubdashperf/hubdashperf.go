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

package main

import (
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/blackducksoftware/perceptor-skyfire/pkg/hubdashperf"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
)

func main() {
	configPath := os.Args[1]
	config, err := hubdashperf.ReadConfig(configPath)
	if err != nil {
		panic(err)
	}

	logLevel, err := config.GetLogLevel()
	if err != nil {
		panic(err)
	}
	log.SetLevel(logLevel)

	log.Infof("received config %+v", config)

	urls := map[string]string{
		"risk-profile-dashboard":             "/api/risk-profile-dashboard?limit=100&offset=0",
		"internal-codelocations":             "/api/internal/codelocations?offset=0&limit=100&sort=updatedAt%20DESC&order=desc&includeErrors=true",
		"catalog-risk-profile-projects":      "/api/v1/catalog-risk-profile-projects?limit=100&sortField=name&ascending=true&offset=0",
		"catalog-risk-profile":               "/api/v1/catalog-risk-profile",
		"composite-projects-vulnerabilities": "/api/v1/composite/projects/vulnerabilities?limit=100&sortField=baseScore&ascending=false&offset=0&filterRemediation=REMEDIATION_REQUIRED&filterRemediation=REMEDIATION_COMPLETE&filterRemediation=PATCHED&filterRemediation=NEW&filterRemediation=NEEDS_REVIEW&filterRemediation=MITIGATED&filterRemediation=IGNORED&filterRemediation=DUPLICATE",
	}

	hubPassword, ok := os.LookupEnv(config.HubPasswordEnvVar)
	if !ok {
		panic(fmt.Errorf("unable to get Hub password: environment variable %s not set", config.HubPasswordEnvVar))
	}

	pause := time.Duration(config.HubRequestBatchPauseSeconds) * time.Second
	dpt, err := hubdashperf.NewDashboardPerformanceTester(config.HubHost, config.HubUser, hubPassword, urls, pause)
	if err != nil {
		panic(err)
	}

	log.Infof("instantiated dashboard performance tester: %+v", dpt)

	stop := make(chan struct{})
	dpt.Start(stop)

	http.Handle("/metrics", prometheus.Handler())
	addr := fmt.Sprintf(":%d", config.Port)
	go http.ListenAndServe(addr, nil)
	log.Infof("running http server on %s", addr)

	<-stop
}
