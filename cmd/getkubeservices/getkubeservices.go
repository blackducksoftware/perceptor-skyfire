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

//var linkTypeDurationHistogram *prometheus.HistogramVec
var problemsGauge *prometheus.GaugeVec
var errorCounter *prometheus.CounterVec
var eventCounter *prometheus.CounterVec

/*func recordLinkTypeDuration(linkType LinkType, duration time.Duration) {
	milliseconds := float64(duration / time.Millisecond)
	linkTypeDurationHistogram.With(prometheus.Labels{"linkType": linkType.String()}).Observe(milliseconds)
}*/

func recordReportProblem(name string, count int) {
	problemsGauge.With(prometheus.Labels{"name": name}).Set(float64(count))
}

func recordError(name string) {
	errorCounter.With(prometheus.Labels{"name": name}).Inc()
}

func recordEvent(name string) {
	eventCounter.With(prometheus.Labels{"name": name}).Inc()
}

func init() {
	/*linkTypeDurationHistogram = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Namespace: "perceptor",
		Subsystem: "skyfire",
		Name:      "hub_api_link_duration",
		Help:      "durations for hub API calls in milliseconds, grouped by link type",
		Buckets:   prometheus.ExponentialBuckets(1, 2, 20),
	}, []string{"linkType"})
	prometheus.MustRegister(linkTypeDurationHistogram)*/

	problemsGauge = prometheus.NewGaugeVec(prometheus.GaugeOpts{
		Namespace: "perceptor",
		Subsystem: "skyfire",
		Name:      "test_issues",
		Help:      "names and counts for issues discovered in perceptor testing",
	}, []string{"name"})
	prometheus.MustRegister(problemsGauge)

	errorCounter = prometheus.NewCounterVec(prometheus.CounterOpts{
		Namespace: "perceptor",
		Subsystem: "skyfire",
		Name:      "errors",
		Help:      "internal skyfire errors",
	}, []string{"name"})
	prometheus.MustRegister(errorCounter)

	eventCounter = prometheus.NewCounterVec(prometheus.CounterOpts{
		Namespace: "perceptor",
		Subsystem: "skyfire",
		Name:      "events",
		Help:      "internal skyfire events",
	}, []string{"name"})
	prometheus.MustRegister(eventCounter)
}
