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
	"github.com/blackducksoftware/perceptor-skyfire/pkg/kube"
	"github.com/juju/errors"
	log "github.com/sirupsen/logrus"
	"github.com/spf13/viper"
)

// Config .....
type Config struct {
	UseInClusterConfig bool
	MasterURL          string
	KubeConfigPath     string

	KubeDumpIntervalSeconds      int
	PerceptorDumpIntervalSeconds int
	HubDumpPauseSeconds          int

	Port     int
	LogLevel string

	HubHosts              []string
	HubUser               string
	HubUserPasswordEnvVar string

	PerceptorHost string
	PerceptorPort int
}

// GetLogLevel .....
func (config *Config) GetLogLevel() (log.Level, error) {
	return log.ParseLevel(config.LogLevel)
}

// ReadConfig .....
func ReadConfig(configPath string) (*Config, error) {
	viper.SetConfigFile(configPath)
	config := &Config{}
	err := viper.ReadInConfig()
	if err != nil {
		return nil, errors.Trace(err)
	}
	err = viper.Unmarshal(config)
	if err != nil {
		return nil, errors.Trace(err)
	}
	return config, nil
}

// KubeClientConfig .....
func (config *Config) KubeClientConfig() *kube.KubeClientConfig {
	if config.UseInClusterConfig {
		return nil
	}
	return &kube.KubeClientConfig{
		MasterURL:      config.MasterURL,
		KubeConfigPath: config.KubeConfigPath,
	}
}
