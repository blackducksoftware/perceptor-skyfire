# In kube but not in perceptor:
# - pods
# - images
# - annotations
# - labels

# In perceptor but not in kube:
# - pods
# - images
# - scan results

# In perceptor but not in hub:
# - completed images
# - completed pods

# In hub but not in perceptor:
# - completed image

# Extra hub stuff:
# - multiple project versions in a project
# - multiple scan summaries in a project version
# - multiple code locations in a scan summary

class Report(object):
    def __init__(self, kube_pods, hub_projects, scan_results, model):
        self.kube_pods = kube_pods
        self.hub_projects = hub_projects
        self.scan_results = scan_results
        self.model = model
        self.compute_derived_data()

    def to_dict(self):
        return {
            'KubePods': self.kube_pods,
            'HubProjects': self.hub_projects,
            'ScanResults': self.scan_results,
            'Model': self.model,
            'KubePodsByName': self.kube_pods_by_name,
            'KubePodsByQualifiedName': self.kube_pods_by_qualified_name,
            'KubeImagesBySha': self.kube_images_by_sha,
            'PerceptorPodsByName': self.perceptor_pods_by_name,
            'PerceptorPodsByQualifiedName': self.perceptor_pods_by_qualified_name,
            'PerceptorImagesBySha': self.perceptor_images_by_sha
        }

    def generate_report(self):
        # kube pods not in perceptor, perceptor pods not in kube
        just_kube_pods, just_perceptor_pods, kube_and_perceptor_pods = diff_dicts(self.kube_pods_by_qualified_name, self.perceptor_pods_by_qualified_name)
        return {
            'just_kube_pods': list(just_kube_pods),
            'just_perceptor_pods': list(just_perceptor_pods),
            'kube_and_perceptor_pods': list(kube_and_perceptor_pods)
        }

    def compute_derived_data(self):
        # kube pods by name, kube pods by qualified name, kube images by sha
        self.kube_pods_by_name = {}
        self.kube_pods_by_qualified_name = {}
        self.kube_images_by_sha = {}
        for pod in self.kube_pods:
            # TODO handle dupes
            qualified_name = "{}/{}".format(pod['Namespace'], pod['Name'])
            self.kube_pods_by_qualified_name[qualified_name] = pod

            if pod['Namespace'] not in self.kube_pods_by_name:
                self.kube_pods_by_name[pod['Namespace']] = {}
            # TODO handle dupes
            self.kube_pods_by_name[pod['Namespace']][pod['Name']] = pod

            for container in pod['Containers']:
                image = container['Image']
                sha = image['Sha']
                if sha not in self.kube_images_by_sha:
                    self.kube_images_by_sha[sha] = {
                        'ImageSpecs': []
                    }
                # TODO handle dupes
                self.kube_images_by_sha[sha]['ImageSpecs'].append({
                    'Name': image['Name'],
                    'DockerImage': image['DockerImage'],
                    'ImageID': image['ImageID']
                })

        # hub projects by name
        self.hub_projects_by_sha = {}
        for proj in self.hub_projects:
            sha = proj['Name'][-64:]
            self.hub_projects_by_sha[sha] = proj

        # perceptor pods by name, perceptor images by name
        self.perceptor_pods_by_name = {}
        self.perceptor_pods_by_qualified_name = {}
        for pod in self.scan_results['Pods']:
            qualified_name = "{}/{}".format(pod['Namespace'], pod['Name'])
            # TODO handle dupes
            self.perceptor_pods_by_qualified_name[qualified_name] = pod

            if pod['Namespace'] not in self.perceptor_pods_by_name:
                self.perceptor_pods_by_name[pod['Namespace']] = {}
            # TODO handle dupes
            self.perceptor_pods_by_name[pod['Namespace']][pod['Name']] = pod

        self.perceptor_images_by_sha = {}
        for image in self.scan_results['Images']:
            # TODO handle dupes
            self.perceptor_images_by_sha[image['Sha']] = image


def diff_dicts(a, b):
    a_keys = set(a.keys())
    b_keys = set(b.keys())
    return (a_keys - b_keys, b_keys - a_keys, a_keys.intersection(b_keys))


def main():
    import sys
    import json
    data_path = sys.argv[1]
    with open(data_path, 'r') as data_file:
        dump = json.load(data_file)
        report = Report(dump['KubePods'], dump['HubProjects'], dump['PerceptorScanResults'], dump['PerceptorModel'])
        # print json.dumps(report.to_dict())
        # print json.dumps(report.generate_report(), indent=2)
        out = {
            'dump': report.to_dict(),
            'report': report.generate_report()
        }
        print json.dumps(out, indent=2)


main()
