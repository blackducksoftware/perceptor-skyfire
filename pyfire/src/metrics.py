from prometheus_client import start_http_server, Summary, Counter, Gauge, Histogram
import random
import time


event_counter = Counter('eventCounter', 'internal skyfire events', ['name'], 'perceptor', 'skyfire')
def record_event(name):
    print("recording event:", name)
    event_counter.labels(name=name).inc()


problems_gauge = Gauge(
    'test_issues',
    'names and counts for issues discovered in perceptor testing',
    ['name'],
    'perceptor',
    'skyfire')
def record_problem(name, count):
    problems_gauge.labels(name=name).set(count)


error_counter = Counter('errors', 'internal skyfire errors', ['name'], 'perceptor', 'skyfire')
def record_error(name):
    error_counter.labels(name=name).inc()
