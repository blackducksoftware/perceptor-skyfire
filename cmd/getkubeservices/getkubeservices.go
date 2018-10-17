package main

import (
	"encoding/json"
	"fmt"
	"os"

	kube "github.com/blackducksoftware/perceptor-skyfire/pkg/kube"
)

func main() {
	// Get config file info from command line arguments
	kubeConfigPath := os.Args[1]
	masterURL := os.Args[2]

	// Create KubeClientConfig Struct with Config file info
	config := &kube.KubeClientConfig{KubeConfigPath: kubeConfigPath, MasterURL: masterURL}

	// Create a Kube Client Struct
	kubeDumper, err := kube.NewKubeClient(config)
	if err != nil {
		panic(err)
	}

	// Use Kube Client method to get a Service Dump
	kubeServicesDump, err := kubeDumper.DumpServices()
	if err != nil {
		panic(err)
	}

	// Create a map of the Service Dump for JSON formatting
	dict := map[string]interface{}{
		"Dump": kubeServicesDump,
	}

	bytes, err := json.MarshalIndent(dict, "", "  ")
	if err != nil {
		panic(err)
	}

	fmt.Println(string(bytes))

}
