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

package dump

import "github.com/blackducksoftware/perceptor-skyfire/pkg/hub"

type HubDump struct {
	Version           string
	Projects          []*hub.Project
	ProjectsBySha     map[string]*hub.Project
	DuplicateShas     map[string]bool
	ShortProjectNames []string
}

func NewHubDump(version string, projects []*hub.Project) *HubDump {
	hubDump := &HubDump{
		Version:           version,
		Projects:          projects,
		ProjectsBySha:     map[string]*hub.Project{},
		DuplicateShas:     map[string]bool{},
		ShortProjectNames: []string{}}
	hubDump.computeDerivedData()
	return hubDump
}

func (hd *HubDump) computeDerivedData() {
	for _, project := range hd.Projects {
		// handle unexpectedly short names
		if len(project.Name) < 20 {
			hd.ShortProjectNames = append(hd.ShortProjectNames, project.Name)
			continue
		}

		startIndex := len(project.Name) - 20 // TODO is this right?
		sha := project.Name[startIndex:]

		// handle duplicate shas
		_, ok := hd.ProjectsBySha[sha]
		if ok {
			hd.DuplicateShas[sha] = true
			continue
		}

		hd.ProjectsBySha[sha] = project
	}
}
