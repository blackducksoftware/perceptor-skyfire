// figure out how many pods are running
// Get images from the pods and say how many containers are running for them
// figure out how many sha's there are

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
	"strconv"

	perceptor "github.com/blackducksoftware/perceptor-skyfire/pkg/perceptor"
	log "github.com/sirupsen/logrus"
)

func main() {
	url := os.Args[1] // Path to a running perceptor
	port, err := strconv.Atoi(os.Args[2])
	if err != nil {
		panic(err)
	}

	perceptorClient := perceptor.NewClient(url, port)

	perceptorDump, err := perceptorClient.Dump()
	if err != nil {
		panic(err)
	}

	log.Infof("There are %d pods running", len(perceptorDump.Model.CoreModel.Pods))

	//for i,p := range perceptorDump.PodsByName {

	//}

	/*
		perceptorDump.ScanResults
		perceptorDump.PodsByName
		perceptorDump.ImagesBySha

		perceptorDump.Model
		perceptorDump.Model.CoreModel.Images
		perceptorDump.Model.CoreModel.Pods
		perceptorDump.Model.CoreModel.Images
		perceptorDump.Model.CoreModel.ImageTransitions[1].Sha
	*/

	// TODO
}
