import unittest
import podreader


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