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

package report

import (
	"fmt"

	"github.com/blackducksoftware/perceptor-skyfire/pkg/hub"
	"github.com/blackducksoftware/perceptor-skyfire/pkg/perceptor"
)

type PerceptorHubReport struct {
	JustPerceptorImages []string
	JustHubImages       []string
}

func NewPerceptorHubReport(perceptorDump *perceptor.Dump, hubDump *hub.Dump) *PerceptorHubReport {
	if perceptorDump == nil || hubDump == nil {
		return nil
	}
	return &PerceptorHubReport{
		JustPerceptorImages: PerceptorNotHubImages(perceptorDump, hubDump),
		JustHubImages:       HubNotPerceptorImages(perceptorDump, hubDump),
	}
}

func (p *PerceptorHubReport) HumanReadableString() string {
	if p == nil {
		return `
Perceptor<->Hub:
 - no information
`
	}
	return fmt.Sprintf(`
Perceptor<->Hub:
 - %d image(s) in Perceptor that were not in the Hub
 - %d image(s) in the Hub that were not in Perceptor
	`,
		len(p.JustPerceptorImages),
		len(p.JustHubImages))
}

func PerceptorNotHubImages(perceptorDump *perceptor.Dump, hubDump *hub.Dump) []string {
	images := []string{}
	for sha := range perceptorDump.ImagesBySha {
		sha20 := sha[:20]
		_, ok := hubDump.ProjectsBySha[sha20]
		if !ok {
			images = append(images, sha)
		}
	}
	return images
}

func HubNotPerceptorImages(perceptorDump *perceptor.Dump, hubDump *hub.Dump) []string {
	images := []string{}
	for sha := range hubDump.ProjectsBySha {
		foundMatch := false
		// can't do a dictionary lookup, because hub sha only has first 20 characters
		for _, perceptorImage := range perceptorDump.ScanResults.Images {
			if perceptorImage.Sha[:20] == sha {
				foundMatch = true
				break
			}
		}
		if !foundMatch {
			images = append(images, sha)
		}
	}
	return images
}
