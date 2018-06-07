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

package hubdashperf

import (
	"fmt"
	"time"

	"github.com/blackducksoftware/hub-client-go/hubclient"
	log "github.com/sirupsen/logrus"
)

type DashboardPerformanceTester struct {
	HubClient         *hubclient.Client
	URLs              map[string]string
	RequestBatchPause time.Duration
}

func NewDashboardPerformanceTester(hubHost string, username string, password string, urls map[string]string, requestBatchPause time.Duration) (*DashboardPerformanceTester, error) {
	var baseURL = fmt.Sprintf("https://%s", hubHost)
	hubClient, err := hubclient.NewWithSession(baseURL, hubclient.HubClientDebugTimings, 5000*time.Second)
	if err != nil {
		return nil, err
	}
	err = hubClient.Login(username, password)
	if err != nil {
		log.Errorf("unable to log in to hub: %s", err.Error())
		return nil, err
	}
	return &DashboardPerformanceTester{HubClient: hubClient, URLs: urls}, nil
}

func (dpt *DashboardPerformanceTester) Start(stop <-chan struct{}) {
	go func() {
		for {
			select {
			case <-stop:
				return
			default:
				for linkType, url := range dpt.URLs {
					result := map[string]interface{}{}
					start := time.Now()
					err := dpt.HubClient.HttpGetJSON(url, &result, 200)
					if err != nil {
						recordError(fmt.Sprintf("unable to fetch %s", linkType))
					}
					elapsed := time.Since(start)
					recordLinkTypeDuration(linkType, elapsed)
				}
			}
			time.Sleep(dpt.RequestBatchPause)
		}
	}()
}
