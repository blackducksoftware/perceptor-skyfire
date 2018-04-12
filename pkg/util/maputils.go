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

package util

func Difference(a map[string]string, b map[string]string) map[string]string {
	aNotB := map[string]string{}
	for key, val := range a {
		_, ok := b[key]
		if !ok {
			aNotB[key] = val
		}
	}
	return aNotB
}

func Intersection(a map[string]string, b map[string]string) map[string]string {
	aAndB := map[string]string{}
	for key := range a {
		_, ok := b[key]
		if ok {
			aAndB[key] = ""
		}
	}
	return aAndB
}

func DiffMaps(a map[string]string, b map[string]string) (aNotB map[string]string, bNotA map[string]string, aAndB map[string]string) {
	aNotB = Difference(a, b)
	bNotA = Difference(b, a)
	aAndB = Intersection(a, b)
	return
}

func MakeSet(keys []string) map[string]string {
	dict := map[string]string{}
	for _, key := range keys {
		dict[key] = ""
	}
	return dict
}

func RemoveKeysFromMap(dict map[string]string, keys map[string]bool) map[string]string {
	copy := map[string]string{}
	for key, val := range dict {
		_, ok := keys[key]
		if !ok {
			copy[key] = val
		}
	}
	return copy
}
