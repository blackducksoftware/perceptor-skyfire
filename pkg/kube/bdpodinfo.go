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

package kube

type BDPodInfo struct {
	KubeInfo     map[string]string
	ExpectedKeys []string
}

func NewBDPodInfo(kubeInfo map[string]string, expectedKeys []string) *BDPodInfo {
	return &BDPodInfo{
		KubeInfo:     kubeInfo,
		ExpectedKeys: expectedKeys,
	}
}

func (b *BDPodInfo) GetKVPairs() map[string]*string {
	kvPairs := map[string]*string{}
	for _, key := range b.ExpectedKeys {
		var value *string = nil
		val, ok := b.KubeInfo[key]
		if ok {
			value = &val
		}
		kvPairs[key] = value
	}
	return kvPairs
}

func (b *BDPodInfo) HasAllBDKeys() bool {
	return HasAllKeys(b.KubeInfo, b.ExpectedKeys)
}

func (b *BDPodInfo) HasAnyBDKeys() bool {
	return HasAnyKeys(b.KubeInfo, b.ExpectedKeys)
}

func (b *BDPodInfo) HasPartialBDKeys() bool {
	return HasAnyKeys(b.KubeInfo, b.ExpectedKeys) && !HasAllKeys(b.KubeInfo, b.ExpectedKeys)
}
