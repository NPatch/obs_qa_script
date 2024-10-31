import threading

class MonitoringThread(threading.Thread):
    
    def __init__(self, target, args=(), kwargs=None):
        super().__init__()
        self.target = target
        self.args = args
        self.kwargs = kwargs if kwargs is not None else {}

    def run(self):
        # Instantiate the target with given arguments
        fsm = self.target(*self.args, **self.kwargs)
        fsm.run()

