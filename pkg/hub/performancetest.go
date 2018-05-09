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

package hub

import (
	"fmt"
	"reflect"
	"time"

	"github.com/blackducksoftware/hub-client-go/hubapi"
	"github.com/blackducksoftware/hub-client-go/hubclient"
	log "github.com/sirupsen/logrus"
)

type PerformanceTester struct {
	HubClient   *hubclient.Client
	HubUsername string
	HubPassword string
}

func NewPerformanceTester(hubHost string, username string, password string) (*PerformanceTester, error) {
	var baseURL = fmt.Sprintf("https://%s", hubHost)
	hubClient, err := hubclient.NewWithSession(baseURL, hubclient.HubClientDebugTimings, 5000*time.Second)
	if err != nil {
		log.Errorf("unable to get hub client: %s", err.Error())
		return nil, err
	}
	pt := &PerformanceTester{HubClient: hubClient, HubUsername: username, HubPassword: password}
	err = hubClient.Login(username, password)
	if err != nil {
		log.Errorf("unable to log in to hub: %s", err.Error())
		return nil, err
	}
	return pt, nil
}

func (pt *PerformanceTester) GetLinks() (map[LinkType][]*time.Duration, []error) {
	root := fmt.Sprintf("%s/api/projects", hubclient.BaseURL(pt.HubClient))
	times, errors := pt.TraverseGraph(root)
	groupedTimes := map[LinkType][]*time.Duration{}
	for link, duration := range times {
		linkType, err := AnalyzeLink(link)
		if err != nil {
			panic(err)
		}
		durations, ok := groupedTimes[*linkType]
		if !ok {
			durations = []*time.Duration{}
		}
		durations = append(durations, duration)
		groupedTimes[*linkType] = durations
	}
	return groupedTimes, errors
}

func (pt *PerformanceTester) TraverseGraph(root string) (map[string]*time.Duration, []error) {
	timings := map[string]*time.Duration{}
	seen := map[string]bool{root: false}
	queue := []string{root}
	errors := []error{}
	for len(queue) > 0 {
		log.Infof("queue size: %d, errors: %d, timings: %d", len(queue), len(errors), len(timings))
		first := queue[0]
		queue = queue[1:]
		start := time.Now()
		json, err := pt.FetchLink(first)
		if err != nil {
			errors = append(errors, err)
			continue
		}
		stop := time.Now().Sub(start)
		timings[first] = &stop
		links, errs := FindLinks(json)
		// links, errs := FindLinksRestricted(json)
		errors = append(errors, errs...)
		for _, link := range links {
			_, err := AnalyzeLink(link)
			if err != nil {
				log.Infof("skipping link %s: %s", link, err.Error())
				continue
			}
			_, ok := seen[link]
			if !ok {
				seen[link] = false
				queue = append(queue, link)
			}
		}
	}
	return timings, errors
}

// func (pt *PerformanceTester) TraverseGraph(root string) (map[string]bool, []error) {
// 	timings := map[string]*time.Duration{}
// 	queue := []string{root}
// 	errors := []error{}
// 	projectList, err := pt.GetProjects()
// 	if err != nil {
// 		errors = append(errors, err)
// 	}
// 	for len(queue) > 0 {
// 		first := queue[0]
// 		queue = queue[1:]
// 		json, err := pt.FetchLink(first)
// 	}
// 	for _, project := range projectList.Items {
// 		for _, link := range project.Meta.Links {
// 			visited, ok := urls[link.Href]
// 			if !ok {
// 				urls[link.Href] = false
// 			} else if !visited {
// 				err := pt.TraverseLink(link.Href)
// 				if err == nil {
// 					urls[link.Href] = true
// 				}
// 			}
// 		}
// 	}
// 	for link := range urls {
// 		linkType, err := pt.AnalyzeLink(link)
// 		if err != nil {
// 			log.Errorf("unable to analyze link %s: %s", link, err.Error())
// 		} else {
// 			log.Infof("url analysis: %s", linkType.String())
// 		}
// 	}
// 	return urls, errors
// }

func (pt *PerformanceTester) FetchLink(link string) (map[string]interface{}, error) {
	result := map[string]interface{}{}
	err := pt.HubClient.HttpGetJSON(link, &result, 200)
	//log.Infof("result and error: %+v, %s", result, err)
	if err != nil {
		log.Errorf("failed to fetch link %s: %s", link, err.Error())
		return nil, err
	}
	log.Infof("successfully fetched link %s", link)
	return result, nil
}

//
// func FindLinksRestricted(obj interface{}) ([]string, []error) {
// 	links := []string{}
// 	errors := []error{}
// 	switch obj.(type) {
// 		case hubapi
// 	}
// }

func FindLinks(obj interface{}) ([]string, []error) {
	switch v := obj.(type) {
	case map[string]interface{}:
		return FindLinksDict(v)
	case []interface{}:
		return FindLinksArray(v)
	default:
		return []string{}, []error{}
	}
}

func FindLinksDict(dict map[string]interface{}) ([]string, []error) {
	links := []string{}
	errors := []error{}
	for key, val := range dict {
		if key == "links" {
			linkObjs, ok := val.([]interface{})
			if ok {
				for _, obj := range linkObjs {
					objDict, ok := obj.(map[string]interface{})
					if ok {
						linkValue, ok := objDict["href"].(string)
						if ok {
							links = append(links, linkValue)
						} else {
							errors = append(errors, fmt.Errorf("invalid type of href: %s", reflect.TypeOf(objDict["href"])))
						}
					} else {
						errors = append(errors, fmt.Errorf("invalid type of links object: %s", reflect.TypeOf(obj)))
					}
				}
			} else {
				errors = append(errors, fmt.Errorf("invalid type of links: %s", reflect.TypeOf(val)))
			}
			continue
		}
		switch v := val.(type) {
		case []interface{}:
			arrayLinks, errs := FindLinksArray(v)
			links = append(links, arrayLinks...)
			errors = append(errors, errs...)
		case map[string]interface{}:
			dictLinks, errs := FindLinksDict(v)
			links = append(links, dictLinks...)
			errors = append(errors, errs...)
		default:
			break
		}
	}
	return links, errors
}

func FindLinksArray(array []interface{}) ([]string, []error) {
	links := []string{}
	errors := []error{}
	for _, item := range array {
		itemLinks, errs := FindLinks(item)
		links = append(links, itemLinks...)
		errors = append(errors, errs...)
	}
	return links, errors
}

func (pt *PerformanceTester) GetProjects() (*hubapi.ProjectList, error) {
	limit := 35000
	options := &hubapi.GetListOptions{Limit: &limit}
	return pt.HubClient.ListProjects(options)
}
