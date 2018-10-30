from prometheus_client import start_http_server, Summary, Counter, Gauge, Histogram
import random
import time


event_counter = Counter('eventCounter', 'internal skyfire events', ['name'], 'perceptor', 'skyfire')
def recordEvent(name):
    print("recording event:", name)
    event_counter.labels(name=name).inc()


if __name__ == '__main__':
    c = Counter('cc', 'A counter')
    c.inc()

    g = Gauge('gg', 'A gauge')
    g.set(17)

    s = Summary('ss', 'A summary', ['a', 'b'])
    s.labels('c', 'd').observe(17)

    h = Histogram('hh', 'A histogram')
    h.observe(.6)

    start_http_server(8000)
    import time
    while True:
        time.sleep(1)


go = """
package skyfire

import (
    "github.com/prometheus/client_golang/prometheus"
)

var problemsGauge *prometheus.GaugeVec
var errorCounter *prometheus.CounterVec
var eventCounter *prometheus.CounterVec

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
"""