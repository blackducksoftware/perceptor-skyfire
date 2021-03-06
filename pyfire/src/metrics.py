from prometheus_client import start_http_server, Summary, Counter, Gauge, Histogram
import random
import time
import logging 

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

metrics_logger = logging.getLogger("Metrics")

requests_counter = Counter(
    'SkyfireRequests',
    'Counts the requests that skyfire handles on the Queue',
    ['name'], 'perceptor', 'skyfire'
)
def record_skyfire_request_event(label):
    metrics_logger.debug("record_skyfire_request_event: {}".format(label))
    requests_counter.labels(name=label).inc()

scrape_counter = Counter(
    'SkyfireScrapes',
    'Counts the scrapes that are generated from Clients',
    ['name'], 'perceptor', 'skyfire'
)
def record_scrape_event(label):
    metrics_logger.debug("record_scrape_event: {}".format(label))
    scrape_counter.labels(name=label).inc()

http_request_counter = Counter(
    'SkyfireHttpRequests',
    'Counts the http requests that Skyfire receives',
    ['name'], 'perceptor', 'skyfire'
)
def record_http_request_event(label):
    metrics_logger.debug("record_http_request_event: {}".format(label))
    http_request_counter.labels(name=label).inc()

error_counter = Counter('errors', 'internal skyfire errors', ['name'], 'perceptor', 'skyfire')
def record_error(label):
    metrics_logger.debug("record_error: {}".format(label))
    error_counter.labels(name=label).inc()


'''
Data Metrics
'''

kube_report_gauge = Gauge(
    'KubeReportValues',
    'Values for OpsSight performance',
    ['name'], 'perceptor', 'skyfire'
)
def record_kube_report(report):
    metrics_logger.debug("record_kube_report")
    kube_report_gauge.labels(name="num_namespaces").set(report.num_namespaces)
    kube_report_gauge.labels(name="num_pods").set(report.num_pods)
    kube_report_gauge.labels(name="num_containers").set(report.num_containers)
    kube_report_gauge.labels(name="num_unique_images").set(report.num_images)
    kube_report_gauge.labels(name="pods_full_label_coverage").set(report.pods_full_label_coverage)
    kube_report_gauge.labels(name="pods_partial_label_coverage").set(report.pods_partial_label_coverage)
    kube_report_gauge.labels(name="pods_full_annotation_coverage").set(report.pods_full_annotation_coverage)
    kube_report_gauge.labels(name="pods_partial_annotation_coverage").set(report.pods_partial_annotation_coverage)

opssight_report_gauge = Gauge(
    'OpsSightReportValues',
    'Values for OpsSight performance',
    ['name'], 'perceptor', 'skyfire'
)
def record_opssight_report(report):
    metrics_logger.debug("record_opssight_report")
    opssight_report_gauge.labels(name="num_hubs").set(report.num_hubs)
    opssight_report_gauge.labels(name="num_images_in_hubs").set(report.num_images_in_hubs)
    opssight_report_gauge.labels(name="num_pods").set(report.num_pods)
    opssight_report_gauge.labels(name="num_containers").set(report.num_containers)
    opssight_report_gauge.labels(name="num_code_loc_shas_in_queue").set(report.num_code_loc_shas_in_queue)

hub_report_gauge = Gauge(
    'HubReportValues',
    'Values for OpsSight performance',
    ['name'], 'perceptor', 'skyfire'
)
def record_hub_report(report):
    metrics_logger.debug("record_hub_report")
    hub_report_gauge.labels(name="num_projects").set(report.num_projects)
    hub_report_gauge.labels(name="num_versions").set(report.num_versions)
    hub_report_gauge.labels(name="num_code_locs").set(report.num_code_locs)
    hub_report_gauge.labels(name="num_code_loc_shas").set(report.num_code_loc_shas)
    hub_report_gauge.labels(name="num_projects_with_one_version").set(report.num_projects_with_one_version)
    hub_report_gauge.labels(name="num_projects_with_multiple_versions").set(report.num_projects_with_multiple_versions)
    hub_report_gauge.labels(name="num_projects_with_no_versions").set(report.num_projects_with_no_versions)
    hub_report_gauge.labels(name="num_code_locations_with_scans").set(report.num_code_locations_with_scans)
    hub_report_gauge.labels(name="num_code_locations_with_no_scans").set(report.num_code_locations_with_no_scans)
    hub_report_gauge.labels(name="num_code_loc_in_multiple_projects").set(report.num_code_loc_in_multiple_projects)
    hub_report_gauge.labels(name="num_code_loc_in_multiple_versions").set(report.num_code_loc_in_multiple_versions)




