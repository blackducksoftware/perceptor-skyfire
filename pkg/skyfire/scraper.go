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

	"github.com/blackducksoftware/perceptor-skyfire/pkg/hub"
	"github.com/blackducksoftware/perceptor-skyfire/pkg/kube"
	"github.com/blackducksoftware/perceptor-skyfire/pkg/perceptor"
	log "github.com/sirupsen/logrus"
)

type Scraper struct {
	KubeDumper            kube.ClientInterface
	KubeDumps             chan *kube.Dump
	KubeDumpInterval      time.Duration
	PerceptorDumper       perceptor.ClientInterface
	PerceptorDumps        chan *perceptor.Dump
	PerceptorDumpInterval time.Duration
	HubDumper             hub.ClientInterface
	HubDumps              chan *hub.Dump
	HubDumpPause          time.Duration
	stop                  <-chan struct{}
}

func NewScraper(kubeDumper kube.ClientInterface, kubeDumpInterval time.Duration, hubDumper hub.ClientInterface, hubDumpInterval time.Duration, perceptorDumper perceptor.ClientInterface, perceptorDumpInterval time.Duration, stop <-chan struct{}) *Scraper {
	scraper := &Scraper{
		KubeDumper:            kubeDumper,
		KubeDumps:             make(chan *kube.Dump),
		KubeDumpInterval:      kubeDumpInterval,
		PerceptorDumper:       perceptorDumper,
		PerceptorDumps:        make(chan *perceptor.Dump),
		PerceptorDumpInterval: perceptorDumpInterval,
		HubDumper:             hubDumper,
		HubDumps:              make(chan *hub.Dump),
		HubDumpPause:          hubDumpInterval,
		stop:                  stop,
	}

	scraper.StartScraping()

	return scraper
}

func (sc *Scraper) StartHubScrapes() {
	for {
		hubDump, err := sc.HubDumper.Dump()
		if err == nil {
			sc.HubDumps <- hubDump
			recordEvent("hub dump")
		} else {
			recordError("unable to get perceptor dump")
			log.Errorf("unable to get hub dump: %s", err.Error())
		}
		select {
		case <-sc.stop:
			return
		case <-time.After(sc.HubDumpPause):
			// continue
		}
	}
}

func (sc *Scraper) StartKubeScrapes() {
	for {
		kubeDump, err := sc.KubeDumper.Dump()
		if err == nil {
			sc.KubeDumps <- kubeDump
			recordEvent("kube dump")
		} else {
			recordError("unable to get kube dump")
			log.Errorf("unable to get kube dump: %s", err.Error())
		}
		select {
		case <-sc.stop:
			return
		case <-time.After(sc.KubeDumpInterval):
			// continue
		}
	}
}

func (sc *Scraper) StartPerceptorScrapes() {
	for {
		perceptorDump, err := sc.PerceptorDumper.Dump()
		if err == nil {
			sc.PerceptorDumps <- perceptorDump
			recordEvent("perceptor dump")
		} else {
			recordError("unable to get perceptor dump")
			log.Errorf("unable to get perceptor dump: %s", err.Error())
		}
		select {
		case <-sc.stop:
			return
		case <-time.After(sc.PerceptorDumpInterval):
			// continue
		}
	}
}

func (sc *Scraper) StartScraping() {
	go sc.StartHubScrapes()
	go sc.StartKubeScrapes()
	go sc.StartPerceptorScrapes()
}
