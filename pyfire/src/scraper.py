import queue
import time
import threading
import metrics


class Scraper(object):
    def __init__(self, perceptor_pause=30, kube_pause=30, hub_pause=60):
        self.q = queue.Queue()

        self.perceptor_thread = threading.Thread(target=self.perceptor)
        self.perceptor_pause = perceptor_pause

        self.kube_thread = threading.Thread(target=self.kube)
        self.kube_pause = kube_pause

        self.hub_thread = threading.Thread(target=self.hub)
        self.hub_pause = hub_pause

        self.is_running = False
    
    def start(self):
        """
        TODO this can't safely be called more than once
        """
        self.is_running = True
        self.perceptor_thread.start()
        self.kube_thread.start()
        self.hub_thread.start()
    
    def stop(self):
        """
        TODO this can't safely be called more than once, and
        assumes `start` has already been called
        """
        self.is_running = False

    def perceptor(self):
        i = 0
        while self.is_running:
#            print("perceptor", i)
            self.q.put("p" + str(i))
            metrics.record_event("perceptorDump")
            i += 1
            time.sleep(self.perceptor_pause)
    
    def kube(self):
        i = 0
        while self.is_running:
#            print("kube", i)
            self.q.put("k" + str(i))
            metrics.record_event("kubeDump")
            i += 1
            time.sleep(self.kube_pause)

    def hub(self):
        i = 0
        while self.is_running:
#            print("hub", i)
            self.q.put("h" + str(i))
            metrics.record_event("hubDump")
            i += 1
            time.sleep(self.hub_pause)

def reader():
    s = Scraper(perceptor_pause=1.0, kube_pause=1.5, hub_pause=2.0)
    s.start()
    while True:
        item = s.q.get()
        print("got next:", item)
        if item is None:
            break
#        f(item)
        s.q.task_done()


if __name__ == "__main__":
    t = threading.Thread(target=reader)
    t.start()
