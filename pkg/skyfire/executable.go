/*
Copyright (C) 2018 Synopsys, Inc.

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
	"fmt"
	"net/http"

	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
)

// RunSkyfire ...
func RunSkyfire(configPath string) {
	stop := make(chan struct{})
	cm := NewConfigManager(configPath, stop)

	config, err := cm.GetConfig()
	logLevel, err := config.GetLogLevel()
	if err != nil {
		panic(err)
	}
	log.SetLevel(logLevel)

	log.Infof("received config %+v", config)

	log.Infof("Launching Skyfire")

	skyfire, err := NewSkyfire(config, stop)
	if err != nil {
		panic(err)
	}
	log.Infof("instantiated skyfire: %+v", skyfire)

	http.Handle("/metrics", prometheus.Handler())
	addr := fmt.Sprintf(":%d", config.Port)
	go http.ListenAndServe(addr, nil)
	log.Infof("running http server on %s", addr)

	go func() {
		newConfig := cm.DidReadConfig()
		for {
			select {
			case <-stop:
				return
			case config := <-newConfig:
				logLevel, err := config.GetLogLevel()
				if err != nil {
					panic(err)
				}
				log.SetLevel(logLevel)
				skyfire.SetHubs(config.HubHosts)
			}
		}
	}()

	<-stop
}
