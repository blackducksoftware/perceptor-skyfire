from prometheus_client import start_http_server, Summary, Counter, Gauge, Histogram
import random
import time

'''
Metric Types:
Counter
- _total : Values being incremented
- _created : When the metric was created
Histogram 
- _bucket
- _sum
- _count
- _created
Summary = 
- 
- _sum
- _count
- _created

Notes
- You can create a metric with one of the above types
- Prometheus with get an element for each of sub-types
- You can give a metric multiple labels (labels are like a flavor of a metric)
- You must access a metric's data through its labels

Example:
Create a Counter metric for errors with labels for 'poor connection', 'function broke'
Create a Coutner metric for dumps with 'kube dump', 'perceptor dump, and 'hub dump'
'''

'''
Skyfire Metrics
'''

requests_counter = Counter(
    'SkyfireRequests',
    'Counts the requests that skyfire handles on the Queue',
    ['name'], 'perceptor', 'skyfire'
)
def record_skyfire_request_event(label):
    requests_counter.labels(name=label).inc()

scrape_counter = Counter(
    'SkyfireScrapes',
    'Counts the scrapes that are generated from Clients',
    ['name'], 'perceptor', 'skyfire'
)
def record_scrape_event(label):
    scrape_counter.labels(name=label).inc()

http_request_counter = Counter(
    'SkyfireHttpRequests',
    'Counts the http requests that Skyfire receives',
    ['name'], 'perceptor', 'skyfire'
)
def record_http_request_event(label):
    http_request_counter.labels(name=label).inc()

'''
Data Metrics
'''

opssight_report_gauge = Gauge(
    'OpsSightReportValues',
    'Values for OpsSight performance',
    ['name'], 'perceptor', 'skyfire'
)
def record_opssight_report(report):
    opssight_report_gauge.labels(name="num_hubs").set(report.num_hubs)
    opssight_report_gauge.labels(name="num_images").set(report.num_images)
    opssight_report_gauge.labels(name="num_pods").set(report.num_pods)
    opssight_report_gauge.labels(name="num_containers").set(report.num_containers)

kube_report_gauge = Gauge(
    'KubeReportValues',
    'Values for OpsSight performance',
    ['name'], 'perceptor', 'skyfire'
)
def record_kube_report(report):
    kube_report_gauge.labels(name="num_namespaces").set(report.num_namespaces)
    kube_report_gauge.labels(name="num_pods").set(report.num_pods)
    kube_report_gauge.labels(name="num_containers").set(report.num_containers)
    kube_report_gauge.labels(name="num_unique_images").set(report.num_unique_images)

hub_report_gauge = Gauge(
    'HubReportValues',
    'Values for OpsSight performance',
    ['name'], 'perceptor', 'skyfire'
)
def record_hub_report(report):
    hub_report_gauge.labels(name="num_projects").set(report.num_projects)
    hub_report_gauge.labels(name="num_versions").set(report.num_versions)
    hub_report_gauge.labels(name="num_code_locations").set(report.num_code_locations)
    hub_report_gauge.labels(name="num_unique_shas").set(report.num_unique_shas)
    hub_report_gauge.labels(name="num_scans").set(report.num_scans)




'''
EXAMPLES
'''


### Guage Example
problems_gauge = Gauge(
    'test_issues',
    'names and counts for issues discovered in perceptor testing',
    ['name'],
    'perceptor',
    'skyfire')
def record_problem(name, count):
    problems_gauge.labels(name=name).set(count)

### Counter Example
error_counter = Counter('errors', 'internal skyfire errors', ['name'], 'perceptor', 'skyfire')
def record_error(label):
    error_counter.labels(name=label).inc()

### Histogram Example
hist = Histogram('my_hist', 'just a hist', ['name'], 'perceptor', 'skyfire')
def do_hist():
    hist.labels("blug").observe(4.7)