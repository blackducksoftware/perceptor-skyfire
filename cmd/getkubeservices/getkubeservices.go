package main

import (
	"fmt"
	"net/http"
	"os"
	"time"

	kube "github.com/blackducksoftware/perceptor-skyfire/pkg/kube"
	"github.com/prometheus/client_golang/prometheus"
	log "github.com/sirupsen/logrus"
)

func main() {
	http.Handle("/metrics", prometheus.Handler())
	addr := fmt.Sprintf(":%d", 3010)
	go http.ListenAndServe(addr, nil)

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

	startServicesMetricsRoutine(kubeDumper)
}

func startServicesMetricsRoutine(kubeDumper *kube.KubeClient) {
	for {
		// Get Metrics
		GetServicesMetrics(kubeDumper)
		// Sleep
		time.Sleep(10 * time.Second)
	}
}

func GetServicesMetrics(kubeDumper *kube.KubeClient) {
	DumpServices(kubeDumper)
}

func DumpServices(kubeDumper *kube.KubeClient) {

	// Use Kube Client method to get a Service Dump
	start := time.Now()
	kubeServicesDump, err := kubeDumper.DumpServices()
	if err != nil {
		panic(err)
	}
	elapsedMilliseconds := float64(time.Since(start) / time.Millisecond)

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
	log.Infof("Latency of Query: %f", elapsedMilliseconds)
	recordServicesQuery("Services Query")
	recordNumServices("Number of Services", len(kubeServicesDump.Services))
	recordServicesLatency("Services Latency", elapsedMilliseconds)

}

var servicesQueryCount *prometheus.CounterVec
var numServicesGauge *prometheus.GaugeVec
var servicesLatencyHistogram *prometheus.HistogramVec

func recordServicesQuery(name string) {
	servicesQueryCount.With(prometheus.Labels{"name": name}).Inc()
}

func recordNumServices(name string, count int) {
	numServicesGauge.With(prometheus.Labels{"name": name}).Set(float64(count))
}

func recordServicesLatency(name string, latencymMilliseconds float64) {
	servicesLatencyHistogram.With(prometheus.Labels{"name": name}).Observe(latencymMilliseconds)
}

func init() {

	servicesQueryCount = prometheus.NewCounterVec(prometheus.CounterOpts{
		Namespace: "perceptor",
		Subsystem: "skyfire",
		Name:      "services_queries",
		Help:      "Count of service queries",
	}, []string{"name"})
	prometheus.MustRegister(servicesQueryCount)

	numServicesGauge = prometheus.NewGaugeVec(prometheus.GaugeOpts{
		Namespace: "perceptor",
		Subsystem: "skyfire",
		Name:      "number_services",
		Help:      "Number of services running",
	}, []string{"name"})
	prometheus.MustRegister(numServicesGauge)

	servicesLatencyHistogram = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Namespace: "perceptor",
		Subsystem: "skyfire",
		Name:      "services_latency",
		Help:      "Latency of getting services",
		Buckets:   prometheus.ExponentialBuckets(1, 2, 20),
	}, []string{"name"})
	prometheus.MustRegister(servicesLatencyHistogram)
}
