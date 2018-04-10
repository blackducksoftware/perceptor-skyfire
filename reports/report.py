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
        self.kube = {'pods': kube_pods}
        self.hub = {'projects': hub_projects}
        self.perceptor = {'scan_results': scan_results, 'model': model}
        self.compute_derived_data()

    def to_dict(self):
        return {
            'Kube': self.kube,
            'Hub': self.hub,
            'Perceptor': self.perceptor
        }

    def generate_report(self):
        # kube pods not in perceptor, perceptor pods not in kube
        kube_not_perceptor_pods, perceptor_not_kube_pods, _ = diff_dicts(
            self.kube['pods_by_qualified_name'],
            self.perceptor['pods_by_qualified_name'])
        kube_not_perceptor_images, perceptor_not_kube_images, _ = diff_dicts(
            self.kube['images_by_sha'],
            self.perceptor['images_by_sha'])

        # annotated pods but perceptor says they're not done
        # TODO

        # perceptor scan results, but no pod annotations

        # perceptor<->hub
        perceptor_not_hub_images, hub_not_perceptor_images, _ = diff_dicts(self.perceptor['images_by_sha'], self.hub['projects_by_sha'])

        # hub -- multiple code locations
        hub_project_multiple_versions = {}
        hub_version_multiple_code_locations = {}
        hub_code_location_multiple_scan_summaries = {}
        for project in self.hub['projects']:
            versions = project['Versions']
            if len(versions) != 1:
                hub_project_multiple_versions[project['Name']] = map(lambda v: v['Name'], versions)
            for version in versions:
                code_locations = version['CodeLocations']
                if len(code_locations) != 1:
                    version_name = "project@{}, version@{}".format(project['Name'], version['Name'])
                    hub_version_multiple_code_locations[version_name] = map(lambda c: c['Name'], code_locations)
                for cl in code_locations:
                    scan_summaries = cl['ScanSummaries']
                    if len(scan_summaries) != 1:
                        cl_name = "project@{}, version@{}, codelocation@{}".format(project['Name'], version['Name'], cl['Name'])
                        hub_code_location_multiple_scan_summaries[cl_name] = map(lambda s: s['Status'], scan_summaries)

        return {
            'kube_perceptor': {
                'just_kube_pods': list(kube_not_perceptor_pods),
                # 'kube_and_perceptor_pods': list(kube_and_perceptor_pods),
                'just_perceptor_pods': list(perceptor_not_kube_pods),
                'just_kube_images': list(kube_not_perceptor_images),
                'just_perceptor_images': list(perceptor_not_kube_images)
            },
            'perceptor_hub': {
                'just_perceptor_images': list(perceptor_not_hub_images),
                'just_hub_images': list(hub_not_perceptor_images)
            },
            'hub': {
                'project_multiple_versions': hub_project_multiple_versions,
                'version_multiple_code_locations': hub_version_multiple_code_locations,
                'code_location_multiple_scan_summaries': hub_code_location_multiple_scan_summaries
            }
        }

    def human_readable_report(self):
        report = self.generate_report()
        return """
        Kubernetes<->Perceptor:
         - we found {} pod(s) in Kubernetes that were not in Perceptor
         - we found {} pod(s) in Perceptor that were not in Kubernetes
         - we found {} image(s) in Kubernetes that were not in Perceptor
         - we found {} image(s) in Perceptor that were not in Kubernetes

        Perceptor<->Hub:
         - we found {} image(s) in Perceptor that were not in the Hub
         - we found {} image(s) in the Hub that were not in Perceptor

        Hub:
         - we found {} project(s) in the Hub with multiple versions
         - we found {} version(s) in the Hub with multiple code locations
         - we found {} code location(s) in the Hub with multiple scan summaries
        """.format(
            len(report['kube_perceptor']['just_kube_pods']),
            len(report['kube_perceptor']['just_perceptor_pods']),
            len(report['kube_perceptor']['just_kube_images']),
            len(report['kube_perceptor']['just_perceptor_images']),
            len(report['perceptor_hub']['just_perceptor_images']),
            len(report['perceptor_hub']['just_hub_images']),
            len(report['hub']['project_multiple_versions']),
            len(report['hub']['version_multiple_code_locations']),
            len(report['hub']['code_location_multiple_scan_summaries']))

    def compute_derived_data(self):
        # kube pods by name, kube pods by qualified name, kube images by sha
        self.kube['pods_by_name'] = {}
        self.kube['pods_by_qualified_name'] = {}
        self.kube['images_by_sha'] = {}
        for pod in self.kube['pods']:
            # TODO handle dupes
            qualified_name = "{}/{}".format(pod['Namespace'], pod['Name'])
            self.kube['pods_by_qualified_name'][qualified_name] = pod

            if pod['Namespace'] not in self.kube['pods_by_name']:
                self.kube['pods_by_name'][pod['Namespace']] = {}
            # TODO handle dupes
            self.kube['pods_by_name'][pod['Namespace']][pod['Name']] = pod

            for container in pod['Containers']:
                image = container['Image']
                sha = image['Sha']
                if sha not in self.kube['images_by_sha']:
                    self.kube['images_by_sha'][sha] = {
                        'ImageSpecs': []
                    }
                # TODO handle dupes
                self.kube['images_by_sha'][sha]['ImageSpecs'].append({
                    'Name': image['Name'],
                    'DockerImage': image['DockerImage'],
                    'ImageID': image['ImageID']
                })

        # hub projects by name
        self.hub['projects_by_sha'] = {}
        for proj in self.hub['projects']:
            sha = proj['Name'][-64:]
            self.hub['projects_by_sha'][sha] = proj

        # perceptor pods by name, perceptor images by name
        self.perceptor['pods_by_name'] = {}
        self.perceptor['pods_by_qualified_name'] = {}
        for pod in self.perceptor['scan_results']['Pods']:
            qualified_name = "{}/{}".format(pod['Namespace'], pod['Name'])
            # TODO handle dupes
            self.perceptor['pods_by_qualified_name'][qualified_name] = pod

            if pod['Namespace'] not in self.perceptor['pods_by_name']:
                self.perceptor['pods_by_name'][pod['Namespace']] = {}
            # TODO handle dupes
            self.perceptor['pods_by_name'][pod['Namespace']][pod['Name']] = pod

        self.perceptor['images_by_sha'] = {}
        for image in self.perceptor['scan_results']['Images']:
            # TODO handle dupes
            self.perceptor['images_by_sha'][image['Sha']] = image


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
        # print json.dumps(out, indent=2)

        print report.human_readable_report()


main()
