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
	"os"

	"github.com/blackducksoftware/perceptor-skyfire/pkg/hub"
	log "github.com/sirupsen/logrus"
)

func main() {
	hubHost := os.Args[1]
	hubUser := os.Args[2]
	hubPassword := os.Args[3]
	// port := os.Args[4]

	pt, err := hub.NewPerformanceTester(hubHost, hubUser, hubPassword)
	if err != nil {
		panic(err)
	}
	log.Infof("instantiated performance tester: %+v", pt)

	groupedDurations, errors := pt.GetLinks()
	for key, durations := range groupedDurations {
		log.Infof("durations for %s: %+v", key, durations)
	}
	for _, err := range errors {
		log.Errorf("error: %s", err.Error())
	}

	// links, errs := pt.TraverseGraph()
	// for link := range links {
	// 	log.Infof("link: %s", link)
	// }
	// for _, err := range errs {
	// 	log.Errorf("error: %s", err.Error())
	// }

	// http.Handle("/metrics", prometheus.Handler())
	// addr := fmt.Sprintf(":%s", port)
	// go http.ListenAndServe(addr, nil)
	// log.Infof("running http server on %s", addr)
	//
	// select {}
}
