import unittest
import podreader
from cluster_clients import *
import json 


class TestClients(unittest.TestCase):
    # TODO - make these actually test if scraped out correct data

    def test_perceptor_scrape(self):
        with open("src/TEST_data/staticPerceptorScrapeTemplate.txt") as f:
            pData = json.load(f)
        pScrape = PerceptorScrape(pData)
        self.assertIsInstance(pScrape,PerceptorScrape)

    def test_kube_scrape(self):
        with open("src/TEST_data/staticKubeScrapeTemplate.txt") as f:
            kData = json.load(f)
        kScrape = KubeScrape(kData)
        self.assertIsInstance(kScrape,KubeScrape)

    def test_hub_scrape(self):
        with open("src/TEST_data/staticHubScrapeTemplate.txt") as f:
            hData = json.load(f)
        hScrape = HubScrape(hData)
        self.assertIsInstance(hScrape,HubScrape)

class TestPodreader(unittest.TestCase):
    def test_pod_labels(self):
        self.assertEqual(
            set(podreader.pod_labels.keys()), 
            set(['pod.policy-violations', 'pod.vulnerabilities', 'pod.overall-status']))
    
    def test_image_labels(self):
        self.assertEqual(
            set(podreader.get_image_labels(0)),
            set(['image0.policy-violations', 'image0.overall-status', 'image0', 'image0.vulnerabilities']))

if __name__ == '__main__':
    # unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPodreader)
    unittest.TextTestRunner(verbosity=2).run(suite)

    client_suite = unittest.TestLoader().loadTestsFromTestCase(TestClients)
    unittest.TextTestRunner(verbosity=2).run(client_suite)