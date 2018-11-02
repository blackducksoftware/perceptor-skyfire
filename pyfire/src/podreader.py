"""
Example of OpsSight labels and annotations on a pod:

Labels:         image0=openshift.origin-docker-registry
                image0.overall-status=NOT_IN_VIOLATION
                image0.policy-violations=0
                image0.vulnerabilities=21
                pod.overall-status=NOT_IN_VIOLATION
                pod.policy-violations=0
                pod.vulnerabilities=21

Annotations:    image0=docker.io.openshift.origin-docker-registry
                image0.overall-status=NOT_IN_VIOLATION
                image0.policy-violations=0
                image0.project-endpoint=https://ops-0-ops-0.10.1.176.68.xip.io/api/projects/0c1b9d80-7f39-4cd8-afde-6ed89c7b94d3/versions/2d90b0fe-ee22-4eb0-8da3-4cad86703ef6/components
                image0.scanner-version=
                image0.server-version=
                image0.vulnerabilities=21
                pod.overall-status=NOT_IN_VIOLATION
                pod.policy-violations=0
                pod.scanner-version=
                pod.server-version=
                pod.vulnerabilities=21
"""

# Labels

pod_labels = {
    'pod.overall-status': str,
    'pod.policy-violations': int,
    'pod.vulnerabilities': int
}

image_prefix = 'image{}'

image_labels = {
    '': str,
    '.overall-status': str,
    '.policy-violations': int,
    '.vulnerabilities': int
}

def get_image_labels(index):
    prefix = image_prefix.format(index)
    return dict((prefix + key, value) for (key, value) in image_labels.items())

def get_all_image_labels(image_count):
    labels = {}
    for i in range(image_count):
        labels = {**labels, **get_image_labels(i)}
    return labels

def get_all_labels(image_count):
    return {**pod_labels, **get_all_image_labels(image_count)}


# Annotations

pod_annotations = {
    'pod.overall-status': str,
    'pod.policy-violations': int,
    'pod.scanner-version': str,
    'pod.server-version': str,
    'pod.vulnerabilities': int
}

image_annotations = {
    '': str,
    '.overall-status': str,
    '.policy-violations': int,
    '.project-endpoint': str,
    '.scanner-version': str,
    '.server-version': str,
    '.vulnerabilities': int
}

def get_image_annotations(index):
    prefix = image_prefix.format(index)
    return dict((prefix + key, value) for (key, value) in image_annotations.items())

def get_all_image_annotations(image_count):
    annotations = {}
    for i in range(image_count):
        annotations = {**annotations, **get_image_annotations(i)}
    return annotations

def get_all_annotations(image_count):
    return {**pod_annotations, **get_all_image_annotations(image_count)}

if __name__ == "__main__":
    for (key, t) in get_all_labels(3).items():
        print("label:", key, str(t))
    print()
    for (key, t) in get_all_annotations(3).items():
        print("annotation:", key, str(t))
