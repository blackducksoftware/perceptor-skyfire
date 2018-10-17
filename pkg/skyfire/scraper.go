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

type hubDumper struct {
	client hub.ClientInterface
	dumps  chan *hub.Dump
	stop   chan struct{}
}

// Scraper .....
type Scraper struct {
	KubeDumper            kube.ClientInterface
	KubeDumps             chan *kube.Dump
	KubeDumpInterval      time.Duration
	PerceptorDumper       perceptor.ClientInterface
	PerceptorDumps        chan *perceptor.Dump
	PerceptorDumpInterval time.Duration
	Hubs                  map[string]*hubDumper
	HubDumpPause          time.Duration
	stop                  <-chan struct{}
	createHubClient       func(host string) (hub.ClientInterface, error)
}

// NewScraper .....
func NewScraper(kubeDumper kube.ClientInterface,
	kubeDumpInterval time.Duration,
	createHubClient func(host string) (hub.ClientInterface, error),
	hubDumpInterval time.Duration,
	perceptorDumper perceptor.ClientInterface,
	perceptorDumpInterval time.Duration,
	stop <-chan struct{}) *Scraper {

	scraper := &Scraper{
		KubeDumper:            kubeDumper,
		KubeDumps:             make(chan *kube.Dump),
		KubeDumpInterval:      kubeDumpInterval,
		PerceptorDumper:       perceptorDumper,
		PerceptorDumps:        make(chan *perceptor.Dump),
		PerceptorDumpInterval: perceptorDumpInterval,
		Hubs:                  map[string]*hubDumper{},
		HubDumpPause:          hubDumpInterval,
		stop:                  stop,
		createHubClient:       createHubClient,
	}

	scraper.StartScraping()

	return scraper
}

// SetHubs .....
func (sc *Scraper) SetHubs(hosts []string) {
	// add new ones
	for _, host := range hosts {
		if sc.Hubs[host] == nil {
			client, err := sc.createHubClient(host)
			if err != nil {
				log.Errorf("unable to instantiate hub client for %s: %s", host, err.Error())
				continue
			}
			newDumper := &hubDumper{
				client: client,
				dumps:  make(chan *hub.Dump),
				stop:   make(chan struct{}),
			}
			go func() {
				startHubScrapes(sc.HubDumpPause, newDumper)
			}()
			sc.Hubs[host] = newDumper
		}
	}
	// delete removed ones
	current := map[string]bool{}
	for _, v := range hosts {
		current[v] = true
	}
	toDelete := []string{}
	for old := range sc.Hubs {
		if !current[old] {
			toDelete = append(toDelete, old)
		}
	}
	for _, t := range toDelete {
		hub := sc.Hubs[t]
		close(hub.stop)
		delete(sc.Hubs, t)
		// anything else?
	}
}

// StartHubScrapes .....
func startHubScrapes(dumpPause time.Duration, dumper *hubDumper) {
	for {
		hubDump, err := dumper.client.Dump()
		if err == nil {
			dumper.dumps <- hubDump
			recordEvent("hub dump")
		} else {
			recordError("unable to get perceptor dump")
			log.Errorf("unable to get hub dump: %s", err.Error())
		}
		select {
		case <-dumper.stop:
			return
		case <-time.After(dumpPause):
			// continue
		}
	}
}

// StartKubeScrapes .....
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

// StartPerceptorScrapes .....
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

// StartScraping .....
func (sc *Scraper) StartScraping() {
	go sc.StartKubeScrapes()
	go sc.StartPerceptorScrapes()
}
