package main

import (
	"os"
	"time"

	kube "github.com/blackducksoftware/perceptor-skyfire/pkg/kube"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
)

func main() {
	startServicesMetricsRoutine()
	//DumpServices()
}

func startServicesMetricsRoutine() {
	for i := 0; i < 3; i++ {
		// Get Metrics
		GetServicesMetrics()
		// Sleep
		time.Sleep(3 * time.Second)
	}
}

func GetServicesMetrics() {
	DumpServices()
}

func DumpServices() {
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
	//dict := map[string]interface{}{
	//	"Dump": kubeServicesDump,
	//}

	//bytes, err := json.MarshalIndent(dict, "", "  ")
	//if err != nil {
	//	panic(err)
	//}

	//fmt.Println(string(bytes))

	log.Infof("Number of Services: %d", len(kubeServicesDump.Services))

}

var servicesHistogram *prometheus.HistogramVec

func recordServicesCount(name string, count int) {
	servicesHistogram.With(prometheus.Labels{"name": name}).Observe(float64(count))
}

func init() {
	servicesHistogram = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Namespace: "perceptor",
		Subsystem: "skyfire",
		Name:      "hub_api_services_count",
		Help:      "Number of Services running",
		Buckets:   prometheus.ExponentialBuckets(1, 2, 20),
	}, []string{"servicesCnt"})
	prometheus.MustRegister(servicesHistogram)
}
